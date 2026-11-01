---
name: quality-gate
description: ChemLab Automated Quality Gate. Enforces pre-commit and pre-merge validation across code formatting, static typing, Blender headless scene verification, asset budget limits, and chemical solver stability.
---

# ChemLab Automated Quality Gate (/quality-gate)

Use this skill to execute the unified quality assurance gate across the ChemLab repository. The quality gate must be invoked before pushing commits, saving final scene states, or handing off features between agents.

## Execution Sequence

Run the master quality gate runner:
```bash
python "C:/Users/Win11 Pro/Desktop/chemlab/scripts/run_quality_gate.py"
```

The master script automatically executes 5 verification stages in sequence:

### Stage 1: Static Code Linting & Style
- **Python Code**: Executes `ruff check scripts/ tests/` and `black --check scripts/ tests/`.
  - Flags unused imports, syntax errors, and style regressions.
- **Node / MCP Scripts**: Runs `npx eslint blender_mcp_server.mjs`.

### Stage 2: Static Type Checking
- Executes `mypy --ignore-missing-imports scripts/ tests/`.
- Verifies mathematical function signatures, vector dimensions, and data structures.

### Stage 3: Blender Headless Scene Verification
- Invokes Blender in background mode without GUI:
  ```bash
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "C:/Users/Win11 Pro/Desktop/chemlab/chemlab.blend" -P "C:/Users/Win11 Pro/Desktop/chemlab/tests/headless_blender_test.py"
  ```
- Asserts:
  - Valid collection hierarchy (`01_Architecture` through `05_Lighting_Cameras`).
  - Active render engine set to `BLENDER_EEVEE_NEXT`.
  - Zero missing image or library datablocks.
  - Camera and lighting fixtures exist and are active.

### Stage 4: Scene Asset & Hardware Budget Validation
- Executes asset scanner:
  ```bash
  "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b "C:/Users/Win11 Pro/Desktop/chemlab/chemlab.blend" -P "C:/Users/Win11 Pro/Desktop/chemlab/tests/validate_scene_assets.py"
  ```
- Enforces Iris Xe constraints:
  - Total triangle count $\le 250,000$.
  - All objects have applied scale `(1.0, 1.0, 1.0)`.
  - All materials contain valid Principled BSDF or Volume nodes.

### Stage 5: Chemical Kinetics Numerical Stability
- Runs unit tests for chemical differential equation solvers:
  ```bash
  python -m unittest discover -s "C:/Users/Win11 Pro/Desktop/chemlab/tests" -p "test_*.py"
  ```
- Confirms stability of stiff ODE solvers (e.g., Belousov-Zhabotinsky Oregonator).

## Gate Policy
- **Zero-Tolerance on Errors**: Any stage failure immediately halts the pipeline.
- **Automatic Fix Option**: For linting/formatting errors, run with `--fix` (`ruff --fix`, `black`).
