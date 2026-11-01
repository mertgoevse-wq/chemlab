#!/usr/bin/env python3
"""
ChemLab Unified Quality Gate Runner
Executes comprehensive studio verification pipeline:
1. Python Unit & Reaction Kinetics Tests
2. Code Linting & Static Analysis (Ruff)
3. Headless Blender Scene Verification
4. Scene Asset & Iris Xe Hardware Budget Validation
"""

import os
import subprocess
import sys
import time
from pathlib import Path

BLENDER_CANDIDATES = [
    r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    r"C:\Program Files\Blender Foundation\Blender\blender.exe",
    "blender",
]


def find_blender() -> str | None:
    for candidate in BLENDER_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    # Try finding in PATH
    try:
        res = subprocess.run(["where", "blender"], capture_output=True, text=True, check=False)
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def run_step(step_name: str, cmd: list[str], cwd: Path | None = None) -> bool:
    print(f"\n>>> [GATE STEP] {step_name}")
    print(f"Command: {' '.join(cmd)}")
    start_time = time.time()
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=False)
        duration = time.time() - start_time
        if res.stdout:
            print(res.stdout)
        if res.stderr and res.returncode != 0:
            print(f"STDERR:\n{res.stderr}", file=sys.stderr)

        if res.returncode == 0:
            print(f"[PASS] {step_name} completed successfully ({duration:.2f}s).")
            return True
        else:
            print(
                f"[FAIL] {step_name} failed with exit code {res.returncode} ({duration:.2f}s).",
                file=sys.stderr,
            )
            return False
    except FileNotFoundError as exc:
        print(f"[FAIL] Command executable not found: {exc}", file=sys.stderr)
        return False
    except Exception as exc:
        print(f"[FAIL] Step execution error: {exc}", file=sys.stderr)
        return False


def main() -> int:
    chemlab_dir = Path(__file__).resolve().parent.parent
    blend_file = chemlab_dir / "chemlab.blend"

    print("=" * 70)
    print("ChemLab Studio Automated Quality Gate")
    print(f"Root: {chemlab_dir}")
    print(f"Target Scene: {blend_file}")
    print("=" * 70)

    blender_exe = find_blender()
    if not blender_exe:
        print("FATAL: Blender executable not found at any candidate path.", file=sys.stderr)
        return 1
    print(f"Blender Executable: {blender_exe}")

    results = []

    # Step 1: Unit & Reaction Kinetics Tests (pytest)
    step1_cmd = [sys.executable, "-m", "pytest", "tests/test_chemical_kinetics.py", "-v"]
    results.append(
        (
            "Chemical Kinetics Numerical Solvers",
            run_step("Chemical Kinetics Numerical Solvers", step1_cmd, cwd=chemlab_dir),
        )
    )

    # Step 2: Code Linting
    step2_cmd = [sys.executable, "-m", "ruff", "check", "scripts", "tests"]
    # Check if ruff is available
    try:
        subprocess.run([sys.executable, "-m", "ruff", "--version"], capture_output=True, check=True)
        results.append(
            ("Code Linting (Ruff)", run_step("Code Linting (Ruff)", step2_cmd, cwd=chemlab_dir))
        )
    except Exception:
        print(
            "\n>>> [GATE STEP] Code Linting: Ruff module not installed in Python env; using AST syntax scan."
        )
        ast_cmd = [
            sys.executable,
            "-c",
            "import py_compile, glob; [py_compile.compile(f, doraise=True) for f in glob.glob('scripts/*.py') + glob.glob('tests/*.py')]",
        ]
        results.append(
            (
                "AST Syntax Compilation Scan",
                run_step("AST Syntax Compilation Scan", ast_cmd, cwd=chemlab_dir),
            )
        )

    # Step 3: Blender Headless Scene Verification
    step3_cmd = [
        blender_exe,
        "-b",
        str(blend_file),
        "-P",
        str(chemlab_dir / "tests" / "headless_blender_test.py"),
    ]
    results.append(
        (
            "Blender Headless Scene Verification",
            run_step("Blender Headless Scene Verification", step3_cmd, cwd=chemlab_dir),
        )
    )

    # Step 4: Scene Asset & Iris Xe Budget Validation
    step4_cmd = [
        blender_exe,
        "-b",
        str(blend_file),
        "-P",
        str(chemlab_dir / "tests" / "validate_scene_assets.py"),
    ]
    results.append(
        (
            "Scene Asset & Iris Xe Budget Audit",
            run_step("Scene Asset & Iris Xe Budget Audit", step4_cmd, cwd=chemlab_dir),
        )
    )

    # Final Summary
    print("\n" + "=" * 70)
    print("ChemLab Quality Gate Final Summary")
    print("=" * 70)
    all_passed = True
    for name, passed in results:
        status_label = "[PASSED]" if passed else "[FAILED]"
        print(f"  {status_label:<10} | {name}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if all_passed:
        print("OVERALL RESULT: QUALITY GATE PASSED")
        return 0
    else:
        print("OVERALL RESULT: QUALITY GATE FAILED", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
