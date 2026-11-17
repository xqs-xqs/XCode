"""Summarise lite runs: outcome, cost and completion-gate behaviour per cell.

Reads the files run_lite.py already wrote (grade.json, run.json, events.jsonl)
for one or more run directories and calls no model. Several run directories are
treated as repeated trials of the same cells.

    python evals/lite/analyze_lite.py .eval/lite/runs/<run-id> [more run dirs]

Definitions:
  resolved          hidden suite passes on a fresh tree (the score)
  claimed           the agent ended with stop_reason=completed
  false completion  claimed, but the hidden suite fails
  gate blocked      the completion gate rejected at least one claim
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def load_trial(task_dir: Path) -> dict | None:
    grade_path = task_dir / "grade.json"
    if not grade_path.is_file():
        return None
    record = json.loads(grade_path.read_text(encoding="utf-8"))["record"]
    run = {}
    if (task_dir / "run.json").is_file():
        run = json.loads((task_dir / "run.json").read_text(encoding="utf-8"))
    usage = (run.get("model") or {}).get("usage") or {}
    blocked_verify = blocked_review = blocked_other = passed = spawned = degraded = 0
    events_path = task_dir / "events.jsonl"
    if events_path.is_file():
        for line in events_path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind, data = event.get("kind"), event.get("data") or ""
            if kind == "completion.gate.blocked":
                if "reviewer found issues" in data:
                    blocked_review += 1
                elif "verify command" in data:
                    blocked_verify += 1
                else:
                    blocked_other += 1
            elif kind == "completion.gate.passed":
                passed += 1
            elif kind == "agent.spawned":
                spawned += 1
            elif kind == "review.degraded":
                degraded += 1
    return {
        "id": record["id"],
        "resolved": bool(record.get("resolved")),
        "grade_status": record.get("grade_status"),
        "stop_reason": run.get("stop_reason") or run.get("status") or "unknown",
        "claimed": run.get("stop_reason") == "completed",
        "tokens": int(usage.get("total_tokens") or 0),
        "calls": int((run.get("model") or {}).get("calls") or 0),
        "wall": float(record.get("wall_time_sec") or 0),
        "blocked_verify": blocked_verify,
        "blocked_review": blocked_review,
        "blocked_other": blocked_other,
        "gate_passed": passed,
        "spawned": spawned,
        "degraded": degraded,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", help="run directories under .eval/lite/runs")
    parser.add_argument("--json", default="", help="also write the summary as JSON to this path")
    args = parser.parse_args()

    trials = defaultdict(list)  # cell -> [trial]
    matrix = defaultdict(lambda: defaultdict(list))  # task -> cell -> [resolved]
    for run in args.runs:
        run_dir = Path(run)
        for cell_dir in sorted(path for path in run_dir.iterdir() if path.is_dir()):
            for task_dir in sorted(path for path in cell_dir.iterdir() if path.is_dir()):
                trial = load_trial(task_dir)
                if trial is None:
                    continue
                trials[cell_dir.name].append(trial)
                matrix[trial["id"]][cell_dir.name].append(trial["resolved"])

    order = [cell for cell in ("single", "single-review", "pipeline") if cell in trials]
    order += [cell for cell in sorted(trials) if cell not in order]
    summary = {}
    print(f"runs: {', '.join(args.runs)}\n")
    header = ("cell", "resolved", "claimed", "false compl.", "blocked runs", "by tests", "by reviewer",
              "recovered", "tokens/run", "calls/run", "sec/run")
    print("| " + " | ".join(header) + " |")
    print("|" + "|".join("---" for _ in header) + "|")
    for cell in order:
        rows = trials[cell]
        total = len(rows)
        resolved = sum(row["resolved"] for row in rows)
        claimed = sum(row["claimed"] for row in rows)
        false_completion = sum(row["claimed"] and not row["resolved"] for row in rows)
        blocked = [row for row in rows if row["blocked_verify"] + row["blocked_review"] + row["blocked_other"]]
        by_tests = sum(1 for row in rows if row["blocked_verify"])
        by_review = sum(1 for row in rows if row["blocked_review"])
        recovered = sum(1 for row in blocked if row["resolved"])
        stats = {
            "total": total, "resolved": resolved, "claimed": claimed, "false_completion": false_completion,
            "blocked_runs": len(blocked), "blocked_by_tests": by_tests, "blocked_by_reviewer": by_review,
            "resolved_after_block": recovered,
            "tokens_per_run": round(sum(row["tokens"] for row in rows) / total) if total else 0,
            "calls_per_run": round(sum(row["calls"] for row in rows) / total, 1) if total else 0,
            "seconds_per_run": round(sum(row["wall"] for row in rows) / total, 1) if total else 0,
            "stop_reasons": dict(sorted(_count(row["stop_reason"] for row in rows).items())),
            "degraded_reviews": sum(row["degraded"] for row in rows),
        }
        summary[cell] = stats
        print(f"| {cell} | {resolved}/{total} | {claimed} | {false_completion} | {len(blocked)} | {by_tests} | "
              f"{by_review} | {recovered} | {stats['tokens_per_run']} | {stats['calls_per_run']} | {stats['seconds_per_run']} |")

    print("\nstop reasons:")
    for cell in order:
        print(f"  {cell}: {summary[cell]['stop_reasons']}  degraded reviews: {summary[cell]['degraded_reviews']}")

    print("\ntasks not resolved by every cell in every trial:")
    for task in sorted(matrix):
        cells = matrix[task]
        if all(all(cells.get(cell, [False])) for cell in order):
            continue
        marks = "  ".join(f"{cell}={sum(cells.get(cell, []))}/{len(cells.get(cell, []))}" for cell in order)
        print(f"  {task}: {marks}")

    if args.json:
        Path(args.json).write_text(json.dumps({"runs": args.runs, "cells": summary}, indent=2), encoding="utf-8")
    return 0


def _count(values) -> dict:
    counts = defaultdict(int)
    for value in values:
        counts[value] += 1
    return counts


if __name__ == "__main__":
    sys.exit(main())
