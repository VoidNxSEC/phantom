#!/usr/bin/env python3
import os
import subprocess
import sys
from datetime import datetime
from typing import NamedTuple

# Configuration
LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
JUST_CMD = "just"

class TestCase(NamedTuple):
    recipe: str
    args: list[str] = []
    description: str = ""
    expect_success: bool = True
    skip: bool = False
    skip_reason: str = ""

# Define the test suite
TEST_SUITE = [
    # --- Info & Stats ---
    TestCase("info", description="Show environment info"),
    TestCase("stats", description="Show project statistics"),
    TestCase("resources", description="Check system resources"),
    TestCase("show", description="Show flake outputs"),

    # --- Code Quality ---
    # Running lint might fail if there are issues, but the command itself should run.
    # We expect success if the codebase is clean. If not, we record the exit code.
    TestCase("lint", description="Run all linters"),
    TestCase("mypy", description="Type check"),

    # --- Testing ---
    # Running a subset of tests to save time
    TestCase("test-unit", description="Run unit tests"),

    # --- Validation & Tools ---
    TestCase("vram", args=['1', 'Q4_0', '128'], description="VRAM calculator (dry run)"),
    TestCase("docs-arch", description="Generate architecture diagrams"),

    # --- Search ---
    TestCase("search", args=['def '] , description="Search codebase"),

    # --- Skipped / Dangerous / Interactive ---
    TestCase("dev", skip=True, skip_reason="Interactive shell"),
    TestCase("update", skip=True, skip_reason="Modifies lock file/Network"),
    TestCase("install", skip=True, skip_reason="Requires Sudo"),
    TestCase("serve", skip=True, skip_reason="Blocking process"),
    TestCase("desktop", skip=True, skip_reason="Blocking process"),
    TestCase("clean", skip=True, skip_reason="Destructive"),
    TestCase("clean-all", skip=True, skip_reason="Destructive"),
    TestCase("fix-all", skip=True, skip_reason="Modifies code"),
]

def ensure_log_dir():
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    # Create a session dir
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    session_dir = os.path.join(LOG_DIR, f"run_{timestamp}")
    os.makedirs(session_dir)
    return session_dir

def run_test(test: TestCase, session_dir: str):
    if test.skip:
        print(f"⏭️  {test.recipe:<20} SKIPPED ({test.skip_reason})")
        return "SKIPPED"

    cmd = [JUST_CMD, test.recipe] + test.args
    cmd_str = " ".join(cmd)

    print(f"Testing: {cmd_str:<40}", end="", flush=True)

    log_file_base = os.path.join(session_dir, f"{test.recipe}")
    stdout_file = f"{log_file_base}.stdout.log"
    stderr_file = f"{log_file_base}.stderr.log"

    try:
        # Run command
        with open(stdout_file, "w") as out_f, open(stderr_file, "w") as err_f:
            result = subprocess.run(
                cmd,
                stdout=out_f,
                stderr=err_f,
                text=True,
                check=False
            )

        if result.returncode == 0:
            print(f"\r✅ {test.recipe:<20} PASSED")
            return "PASSED"
        else:
            print(f"\r❌ {test.recipe:<20} FAILED (Exit Code: {result.returncode})")
            print(f"   See logs: {stderr_file}")
            return "FAILED"

    except Exception as e:
        print(f"\r💥 {test.recipe:<20} ERROR: {str(e)}")
        return "ERROR"

def main():
    print("🚀 Starting Justfile Validation Suite")
    print(f"📂 Logs will be saved to: {LOG_DIR}")

    session_dir = ensure_log_dir()

    results = {"PASSED": 0, "FAILED": 0, "SKIPPED": 0, "ERROR": 0}

    for test in TEST_SUITE:
        outcome = run_test(test, session_dir)
        results[outcome] += 1

    print("\n" + "="*40)
    print("SUMMARY")
    print("="*40)
    print(f"✅ Passed:  {results['PASSED']}")
    print(f"❌ Failed:  {results['FAILED']}")
    print(f"⏭️  Skipped: {results['SKIPPED']}")
    print(f"💥 Errors:  {results['ERROR']}")

    if results['FAILED'] > 0 or results['ERROR'] > 0:
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
