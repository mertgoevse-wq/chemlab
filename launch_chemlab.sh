#!/usr/bin/env bash
# ChemLab: Origins — Cross-Platform Desktop Launcher
# Launches Godot 4 3D Application using GLES3 Compatibility backend

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="${SCRIPT_DIR}/game"

echo "========================================================"
echo " Starting ChemLab: Origins (Godot 4.3+ GLES3 Compatibility)"
echo " Target: Intel Iris Xe Graphics / Windows & Linux Desktop"
echo "========================================================"

"${SCRIPT_DIR}/tools/bin/godot" --path "${PROJECT_DIR}" "$@"
