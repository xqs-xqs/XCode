"""Copy the small, durable part of lite runs into the repository.

Run directories under .eval/ are large and not tracked. This keeps, per run:
the run's settings, one row per task (verdict, stop reason, tokens, requests,
seconds, gate rejections) and the candidate patches. Event logs are left out.

    python evals/lite/export_runs.py --output evals/results .eval/lite/runs/<run-id> [...]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from analyze_lite import load_trial  # noqa: E402

KEEP_SETTINGS = ("run_id", "label", "binary_sha256", "git_revision", "developer", "reviewer", "cells",
                 "max_tokens", "max_model_calls", "max_steps", "timeout_sec", "thinking", "reasoning_effort",
                 "provider_retries", "generated_at")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+")
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    output = Path(args.output)
    lines = ["# Exported run results", "",
             "One row per run and cell. `resolved` is decided by hidden tests on a fresh tree; "
             "`claimed` counts runs that ended with stop_reason=completed. A run still in progress "
             "shows fewer tasks than its set.", "",
             "| run | cell | developer | reviewer | resolved | claimed | tokens/run | total tokens |",
             "|---|---|---|---|---:|---:|---:|---:|"]
    for run in args.runs:
        run_dir = Path(run)
        target = output / run_dir.name
        target.mkdir(parents=True, exist_ok=True)
        settings = {}
        if (run_dir / "report.json").is_file():
            report = json.loads((run_dir / "report.json").read_text(encoding="utf-8"))
            settings = {key: report[key] for key in KEEP_SETTINGS if key in report}
        cells = {}
        for cell_dir in sorted(path for path in run_dir.iterdir() if path.is_dir()):
            rows = []
            for task_dir in sorted(path for path in cell_dir.iterdir() if path.is_dir()):
                trial = load_trial(task_dir)
                if trial is None:
                    continue
                run_json = task_dir / "run.json"
                if run_json.is_file() and not settings.get("developer"):
                    config = json.loads(run_json.read_text(encoding="utf-8")).get("config", {})
                    settings.setdefault("developer_model", config.get("model"))
                rows.append(trial)
                patch = task_dir / "model.patch"
                if patch.is_file() and patch.stat().st_size and patch.stat().st_size < 200_000:
                    destination = target / "patches" / cell_dir.name / f"{trial['id']}.patch"
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(patch, destination)
            if rows:
                cells[cell_dir.name] = rows
                total = sum(row["tokens"] for row in rows)
                lines.append(
                    f"| {run_dir.name} | {cell_dir.name} | {settings.get('developer') or settings.get('developer_model') or ''} "
                    f"| {settings.get('reviewer', '')} | {sum(row['resolved'] for row in rows)}/{len(rows)} "
                    f"| {sum(row['claimed'] for row in rows)} | {round(total / len(rows))} | {total} |")
        (target / "results.json").write_text(
            json.dumps({"settings": settings, "cells": cells}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines[4:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
