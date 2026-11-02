@echo off
REM ChemLab: Origins — Windows Desktop Launcher
REM Launches Godot 4 3D Application using GLES3 Compatibility backend

set PROJECT_DIR=%~dp0game
echo ========================================================
echo  Starting ChemLab: Origins (Godot 4.3+ GLES3 Compatibility)
echo  Target: Dell Latitude 5530 (Intel Iris Xe Graphics)
echo ========================================================

call "%~dp0tools\bin\godot.cmd" --path "%PROJECT_DIR%" %*
