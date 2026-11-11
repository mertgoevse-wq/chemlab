"""Execute the real GDScript save manager without gameplay autoloads or player saves."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _godot_command() -> list[str]:
    configured = os.environ.get("GODOT_BIN")
    if configured:
        return [configured]
    for name in ("godot", "godot4"):
        executable = shutil.which(name)
        if executable:
            return [executable]
    win_godot = Path(
        r"C:\Users\Win11 Pro\AppData\Local\Microsoft\WinGet\Packages\GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe\Godot_v4.7.2-stable_win64_console.exe"
    )
    if win_godot.is_file():
        return [str(win_godot)]
    # Keep the repository's executable location in its existing wrapper, not in this test.
    bash = shutil.which("bash")
    wrapper = ROOT / "tools" / "bin" / "godot"
    if bash and wrapper.is_file():
        probe = subprocess.run(
            [bash, str(wrapper), "--headless", "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        if probe.returncode == 0:
            return [bash, str(wrapper)]
    pytest.skip("Godot not available; set GODOT_BIN to enable runtime save regression tests")


def test_save_slots_round_trip_without_touching_player_saves(tmp_path: Path) -> None:
    """Catch wrong-slot I/O, failed-load state replacement and partial-write data loss."""
    command = _godot_command()
    user_data = tmp_path / "user_data"
    user_data.mkdir()
    (tmp_path / "project.godot").write_text(
        '[application]\nconfig/name="Athanor Save Regression"\n'
        "config/use_custom_user_dir=true\n"
        f"config/custom_user_dir={json.dumps(user_data.as_posix())}\n"
        '[rendering]\nrenderer/rendering_method="gl_compatibility"\n',
        encoding="utf-8",
    )
    save_dir = tmp_path / "scripts" / "save"
    save_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "game/scripts/save/save_manager.gd", save_dir / "save_manager.gd")
    shutil.copy2(ROOT / "game/scripts/save/save_manager.gd", tmp_path / "save_manager.gd")
    shutil.copy2(ROOT / "game/tests/test_save_manager_slots.gd", tmp_path / "test_runner.gd")
    env = {**os.environ, "ATHANOR_TEST_USER_DIR": str(user_data)}
    result = subprocess.run(
        [*command, "--headless", "--path", str(tmp_path), "--script", "res://test_runner.gd"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=45,
        check=False,
        env=env,
    )
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "SCRIPT ERROR" not in output, output
    assert "SAVE SLOT REGRESSION: PASS" in output, output
