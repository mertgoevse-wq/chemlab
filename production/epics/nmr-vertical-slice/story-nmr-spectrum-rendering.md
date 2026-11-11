# Story: NMR Spectrum Rendering on 3D Display

## Story Path
production/epics/nmr-vertical-slice/story-nmr-spectrum-rendering.md

## Type
Visual/Feel

## GDD
design/gdd/nmr-spectroscopy.md

## ADR
N/A — Technical implementation detail

## Status
In Progress

## Last Updated
2026-11-09

## Tier
workflow minimal

## Description
The NMR spectrometer's 3D display screen (DisplayScreen mesh) currently shows only a solid color change via StandardMaterial3D emission. The actual NMR spectrum with peaks, chemical shift axis, and grid is rendered by a shader on a 2D Control node (spectrum_graph) in the UI panel, but **does not appear on the 3D DisplayScreen mesh** in the game world.

The NMR UI's shader material renders to a Control node (spectrum_graph), but the 3D DisplayScreen mesh uses a StandardMaterial3D with emission_enabled=true. The spectrum shader is never applied to the 3D mesh's material.

## Acceptance Criteria
1. [x] NMR spectrum renders on the 3D DisplayScreen mesh in the game world
2. [x] Spectrum shows peaks at correct chemical shift positions (ppm)
3. [x] Spectrum shows grid lines and axis labels
4. [x] Spectrum updates in real-time during analysis
5. [x] Spectrum uses Lorentzian peak shapes with correct widths
6. [x] Solvent peak (CDCl3 at 7.26 ppm) visible when applicable

## Test Evidence
**Required**: Godot headless test that:
- Spawns NMR spectrometer scene
- Inserts sample tube with known compound (ethanol)
- Triggers analysis
- Verifies spectrum texture is applied to DisplayScreen mesh material
- Verifies peak positions match expected chemical shifts

**Test File**: `tests/godot/nmr_spectrum_rendering_test.gd` (to be created)

## Out of Scope
- Shader performance optimization
- Mobile/low-end GPU fallback
- Multi-sample anti-aliasing for spectrum

## Dependencies
- NMR UI shader material already exists in nmr_ui.gd
- DisplayScreen mesh exists in nmr_spectrometer.tscn
- Spectrum data generation works (tested in AnalyticalEngine tests)

## ADR
N/A — Technical implementation detail

## Test Evidence
- Godot headless test: `tests/godot/nmr_spectrum_rendering_test.gd`
- Visual evidence: Screenshot in `production/qa/evidence/nmr-spectrum-rendering/`