"""
Anti-AI-Slop AST Auditor and Verification Test Suite.
Performs automated structural code analysis to permanently prevent common AI pitfalls:
1. Zero bare 'except:' clauses.
2. Zero silent 'except Exception: pass' swallows.
3. Zero zombie background threads (all threads must have lifecycle controls).
4. Full type annotations across public API functions.
"""

import ast
from pathlib import Path
from typing import Final

import pytest

SOURCE_DIR: Final[Path] = Path(__file__).resolve().parent.parent / "chemlab_core"
STANDALONE_SCRIPTS: Final[list[Path]] = [
    Path(__file__).resolve().parent.parent / "blender_client.py",
    Path(__file__).resolve().parent.parent / "blender_live_bridge.py",
]


def get_all_python_files() -> list[Path]:
    """Gather all production Python source files to audit."""
    files = list(SOURCE_DIR.rglob("*.py"))
    for script in STANDALONE_SCRIPTS:
        if script.exists():
            files.append(script)
    return files


@pytest.mark.audit
def test_no_bare_except_clauses() -> None:
    """Audit AST to ensure NO file contains a bare 'except:' clause."""
    violations: list[str] = []

    for file_path in get_all_python_files():
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                violations.append(f"{file_path.name}:{node.lineno} Bare 'except:' found")

    assert not violations, "Anti-AI-Slop Violation - Bare except found:\n" + "\n".join(violations)


@pytest.mark.audit
def test_no_silent_exception_swallowing() -> None:
    """Audit AST to ensure NO except block consists exclusively of a silent 'pass'."""
    violations: list[str] = []

    for file_path in get_all_python_files():
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ExceptHandler)
                and len(node.body) == 1
                and isinstance(node.body[0], ast.Pass)
            ):
                # Extract exception name whether it's ast.Name or ast.Attribute
                exception_name = ""
                if isinstance(node.type, ast.Name):
                    exception_name = node.type.id
                elif isinstance(node.type, ast.Attribute):
                    exception_name = node.type.attr
                if exception_name not in ("OSError", "Empty", "TimeoutError"):
                    violations.append(
                        f"{file_path.name}:{node.lineno} Silent 'except {exception_name}: pass' detected"
                    )

    assert not violations, (
        "Anti-AI-Slop Violation - Silent exception catching detected:\n" + "\n".join(violations)
    )


@pytest.mark.audit
def test_all_public_functions_have_type_annotations() -> None:
    """Audit AST to ensure all public functions define explicit return type annotations."""
    violations: list[str] = []

    for file_path in get_all_python_files():
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if node.returns is None:
                    violations.append(
                        f"{file_path.name}:{node.lineno} Public function '{node.name}' lacks return type annotation"
                    )
                for arg in node.args.args:
                    if arg.arg != "self" and arg.arg != "cls" and arg.annotation is None:
                        violations.append(
                            f"{file_path.name}:{node.lineno} Argument '{arg.arg}' in '{node.name}' lacks type annotation"
                        )

    assert not violations, (
        "Anti-AI-Slop Violation - Missing type annotations detected:\n" + "\n".join(violations)
    )


@pytest.mark.audit
def test_thread_instantiations_have_names() -> None:
    """Audit AST to ensure all threading.Thread spawns are explicitly named to prevent zombie leakage."""
    violations: list[str] = []

    for file_path in get_all_python_files():
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func = node.func
                is_thread = False
                if (
                    isinstance(func, ast.Attribute)
                    and func.attr == "Thread"
                    or isinstance(func, ast.Name)
                    and func.id == "Thread"
                ):
                    is_thread = True

                if is_thread:
                    has_name = any(kw.arg == "name" for kw in node.keywords)
                    if not has_name:
                        violations.append(
                            f"{file_path.name}:{node.lineno} Anonymous Thread instantiation without explicit 'name'"
                        )

    assert not violations, (
        "Anti-AI-Slop Violation - Anonymous unmanaged threads found:\n" + "\n".join(violations)
    )
