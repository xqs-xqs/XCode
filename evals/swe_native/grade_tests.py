"""Run a task's official tests and decide pass or fail.

Copied into the grading tree as .swe_grade.py next to .swe_spec.json. Exit code
0 means every FAIL_TO_PASS and PASS_TO_PASS test passed. The line starting with
SWE_PASSED= lists the tests that passed, for calibration.
"""

import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, ".swe_spec.json"), encoding="utf-8") as handle:
        spec = json.load(handle)
    report = os.path.join(tempfile.mkdtemp(prefix="swe-grade-"), "report.xml")
    command = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-q", "--no-header",
               "-o", "addopts=", "--junitxml", report, *spec["test_files"]]
    try:
        result = subprocess.run(command, cwd=here, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                timeout=spec.get("timeout", 600), check=False)
        tail = result.stdout.decode("utf-8", errors="replace")[-1500:]
    except subprocess.TimeoutExpired:
        print("SWE_RESULT=timeout")
        return 1

    passed = set()
    if os.path.exists(report):
        for case in ET.parse(report).getroot().iter("testcase"):
            if any(child.tag in ("failure", "error", "skipped") for child in case):
                continue
            name = case.get("name", "")
            passed.add(name)
            passed.add(name.split("[", 1)[0])
    required = spec["fail_to_pass"] + spec["pass_to_pass"]
    missing = [name for name in required if name not in passed]
    print(tail)
    print("SWE_PASSED=" + json.dumps(sorted(passed)))
    print(f"SWE_RESULT={'pass' if not missing else 'fail'} required={len(required)} missing={missing[:10]}")
    return 0 if required and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
