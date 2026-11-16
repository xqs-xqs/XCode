"""Materialise SWE-bench Verified tasks so the lite runner can grade them natively.

The Harbor line grades in Docker images. Where no Docker daemon is available,
pure-Python repositories can still be graded on the host: check the repository
out at the task's base commit, give the agent that tree, and grade a candidate
patch on a fresh copy with the task's test patch applied, running the official
FAIL_TO_PASS and PASS_TO_PASS tests.

Differences from the upstream harness, all recorded in the manifest:

- tests run under the host interpreter given by --python, not the per-version
  conda environment, so only tasks that calibrate here are kept;
- PASS_TO_PASS is restricted to the tests that pass with the reference patch
  in this environment (FAIL_TO_PASS is never relaxed);
- the completion gate's visible check is only that the package imports; the
  official tests stay hidden from the agent.

A task is kept only if the reference patch passes and the empty patch fails.

    python evals/swe_native/prepare.py --dataset .eval/swe/verified.json \\
        --repo-cache .eval/swe/repos --output .eval/swe/tasks \\
        --python .eval/swe/venv/bin/python --manifest evals/swe_native/sympy-v1.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "evals" / "lite"))

import lite_lib  # noqa: E402

DIFFICULTY_ORDER = ["<15 min fix", "15 min - 1 hour", "1-4 hours", ">4 hours"]
GRADER = Path(__file__).with_name("grade_tests.py")
PROMPT = "Resolve the following issue in the repository in the current directory. Fix the library code; the issue is not resolved by changing tests alone.\n\n"


def version_tuple(text: str) -> tuple:
    return tuple(int(part) for part in text.split("."))


def run(args: list, cwd: Path, **kwargs) -> subprocess.CompletedProcess:
    return subprocess.run(args, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False, **kwargs)


def export_commit(cache: Path, repository: str, commit: str, destination: Path) -> None:
    """Fetch one commit without history and export its tree."""
    repo = cache / repository.split("/")[-1]
    if not (repo / ".git").is_dir():
        repo.mkdir(parents=True, exist_ok=True)
        run(["git", "init", "-q"], repo)
        run(["git", "remote", "add", "origin", f"https://github.com/{repository}"], repo)
    if run(["git", "cat-file", "-e", f"{commit}^{{commit}}"], repo).returncode:
        fetched = run(["git", "fetch", "-q", "--depth", "1", "origin", commit], repo)
        if fetched.returncode:
            raise RuntimeError(f"fetch {commit} failed: {fetched.stderr.decode(errors='replace')[-400:]}")
    destination.mkdir(parents=True, exist_ok=True)
    archive = subprocess.Popen(["git", "archive", commit], cwd=str(repo), stdout=subprocess.PIPE)
    extracted = subprocess.run(["tar", "-x", "-C", str(destination)], stdin=archive.stdout, check=False)
    archive.wait()
    if archive.returncode or extracted.returncode:
        raise RuntimeError(f"export {commit} failed")


def patched_files(base: Path, patch: str) -> dict:
    """Apply a patch to a scratch copy of base and return the files it touched."""
    with tempfile.TemporaryDirectory() as scratch:
        tree = Path(scratch) / "tree"
        shutil.copytree(base, tree)
        patch_file = Path(scratch) / "change.patch"
        patch_file.write_text(patch, encoding="utf-8")
        applied = run(["git", "apply", "--whitespace=nowarn", str(patch_file)], tree)
        if applied.returncode:
            raise RuntimeError(f"patch did not apply: {applied.stderr.decode(errors='replace')[-400:]}")
        touched = sorted(set(re.findall(r"^diff --git a/(\S+) b/(\S+)", patch, re.M)))
        return {new: (tree / new).read_bytes() for _, new in touched if (tree / new).is_file()}


def write_files(root: Path, files: dict) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def materialise(row: dict, cache: Path, output: Path, python_exe: str, timeout: int) -> dict:
    task_dir = output / row["instance_id"]
    if task_dir.exists():
        shutil.rmtree(task_dir)
    starter = task_dir / "starter"
    export_commit(cache, row["repo"], row["base_commit"], starter)
    # Keep the agent's own state out of captured patches.
    with (starter / ".gitignore").open("a", encoding="utf-8") as handle:
        handle.write("\n" + lite_lib.WORKSPACE_GITIGNORE)

    write_files(task_dir / "solution", patched_files(starter, row["patch"]))
    test_files = patched_files(starter, row["test_patch"])
    hidden = task_dir / "hidden"
    write_files(hidden, test_files)
    shutil.copyfile(GRADER, hidden / ".swe_grade.py")

    fail_to_pass = json.loads(row["FAIL_TO_PASS"])
    pass_to_pass = json.loads(row["PASS_TO_PASS"])
    spec = {"test_files": sorted(name for name in test_files if name.endswith(".py")),
            "fail_to_pass": fail_to_pass, "pass_to_pass": pass_to_pass, "timeout": timeout}
    (hidden / ".swe_spec.json").write_text(json.dumps(spec, indent=2), encoding="utf-8")

    package = row["repo"].split("/")[-1]
    meta = {
        "schema_version": 1,
        "id": row["instance_id"],
        "language": "python",
        "kind": "swe",
        "prompt": PROMPT + row["problem_statement"].strip(),
        "acceptance": [],
        "tags": ["swe-bench-verified", row["repo"], f"version-{row['version']}", row["difficulty"]],
        "policy": "swe-python.json",
        "verify_commands": [["{python}", "-c", f"import {package}"]],
        "hidden_command": [["{python}", ".swe_grade.py"]],
    }
    (task_dir / "task.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return lite_lib.load_task(task_dir)


def passed_tests(task: dict, patch: bytes, python_exe: str, timeout: int) -> tuple:
    """Grade a patch and return (status, names of tests that passed)."""
    scratch = lite_lib.scratch_directory()
    try:
        result = lite_lib.grade(task, patch, scratch / "grade", python_exe, timeout + 60)
        output = result["runs"][0]["output"] if result.get("runs") else result.get("reason", "")
        match = re.search(r"^SWE_PASSED=(.*)$", output, re.M)
        return result["status"], set(json.loads(match.group(1))) if match else set(), output[-600:]
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def calibrate(task: dict, row: dict, python_exe: str, timeout: int) -> dict:
    """Reference patch must pass, empty patch must fail; narrow PASS_TO_PASS to this host."""
    scratch = lite_lib.scratch_directory()
    try:
        gold = lite_lib.build_overlay_patch(task, task["_dir"] / "solution", scratch / "gold")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    spec_path = task["_dir"] / "hidden" / ".swe_spec.json"
    spec = json.loads(spec_path.read_text(encoding="utf-8"))

    _, passed, tail = passed_tests(task, gold, python_exe, timeout)
    missing = [name for name in spec["fail_to_pass"] if name not in passed]
    record = {"id": row["instance_id"], "official_pass_to_pass": len(spec["pass_to_pass"])}
    if missing or not passed:
        return {**record, "calibrated": False, "reason": f"reference patch does not pass here: {missing[:3]} {tail[-200:]}"}
    kept = [name for name in spec["pass_to_pass"] if name in passed]
    spec["pass_to_pass"] = kept
    spec_path.write_text(json.dumps(spec, indent=2), encoding="utf-8")
    record["kept_pass_to_pass"] = len(kept)

    gold_status, _, tail = passed_tests(task, gold, python_exe, timeout)
    if gold_status != "passed":
        return {**record, "calibrated": False, "reason": f"reference patch unstable after narrowing: {tail[-200:]}"}
    # An empty patch is rejected by the grader before any test runs, so prove
    # discrimination with a patch that changes nothing the tests exercise.
    scratch = lite_lib.scratch_directory()
    try:
        lite_lib.prepare_workspace(task, scratch / "noop")
        (scratch / "noop" / "NOOP_CALIBRATION.txt").write_text("no change\n", encoding="utf-8")
        noop = lite_lib.capture_patch(scratch / "noop", scratch / "noop.patch")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    noop_status, _, _ = passed_tests(task, noop, python_exe, timeout)
    if noop_status != "failed":
        return {**record, "calibrated": False, "reason": "tests pass without the fix"}
    return {**record, "calibrated": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dataset", required=True, help="SWE-bench Verified rows as a JSON list")
    parser.add_argument("--repo-cache", required=True)
    parser.add_argument("--output", required=True, help="task directory root (large; keep it out of git)")
    parser.add_argument("--python", dest="python_exe", required=True, help="interpreter with the project's dependencies")
    parser.add_argument("--manifest", required=True, help="where to write the frozen task list")
    parser.add_argument("--repo", default="sympy/sympy")
    parser.add_argument("--min-version", default="1.6", help="oldest project version that runs on the host interpreter")
    parser.add_argument("--min-difficulty", default="15 min - 1 hour", choices=DIFFICULTY_ORDER)
    parser.add_argument("--timeout", type=int, default=600, help="seconds allowed for one grading run")
    parser.add_argument("--only", default="", help="comma-separated instance ids (for authoring)")
    args = parser.parse_args()

    rows = json.loads(Path(args.dataset).read_text(encoding="utf-8"))
    floor = DIFFICULTY_ORDER.index(args.min_difficulty)
    selected = [
        row for row in rows
        if row["repo"] == args.repo
        and version_tuple(row["version"]) >= version_tuple(args.min_version)
        and DIFFICULTY_ORDER.index(row["difficulty"]) >= floor
    ]
    if args.only:
        wanted = set(args.only.split(","))
        selected = [row for row in selected if row["instance_id"] in wanted]
    selected.sort(key=lambda row: int(row["instance_id"].rsplit("-", 1)[-1]))

    output, cache = Path(args.output), Path(args.repo_cache)
    output.mkdir(parents=True, exist_ok=True)
    entries = []
    for row in selected:
        try:
            task = materialise(row, cache, output, args.python_exe, args.timeout)
            result = calibrate(task, row, args.python_exe, args.timeout)
        except (RuntimeError, lite_lib.TaskError, OSError) as error:
            result = {"id": row["instance_id"], "calibrated": False, "reason": str(error)[:300]}
        result.update({
            "version": row["version"], "difficulty": row["difficulty"], "base_commit": row["base_commit"],
            "fail_to_pass": len(json.loads(row["FAIL_TO_PASS"])),
            "problem_sha256": hashlib.sha256(row["problem_statement"].encode()).hexdigest(),
        })
        entries.append(result)
        print(("[ok  ] " if result["calibrated"] else "[drop] ") + row["instance_id"] + ("" if result["calibrated"] else f": {result['reason'][:160]}"), flush=True)
        if not result["calibrated"]:
            shutil.rmtree(output / row["instance_id"], ignore_errors=True)

    manifest = {
        "schema_version": 1,
        "dataset": "princeton-nlp/SWE-bench_Verified",
        "repository": args.repo,
        "selection_rule": f"version >= {args.min_version}, difficulty >= '{args.min_difficulty}', "
                          "reference patch passes and a no-op patch fails on the host interpreter",
        "host_python": subprocess.run([args.python_exe, "--version"], stdout=subprocess.PIPE).stdout.decode().strip(),
        "tasks": entries,
    }
    Path(args.manifest).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    kept = sum(entry["calibrated"] for entry in entries)
    print(f"calibrated {kept}/{len(entries)}; manifest: {args.manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
