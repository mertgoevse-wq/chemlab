# Godot Architecture & Technical Integration Specification

**Document ID:** `GDD-CHEMLAB-GODOT-001`  
**Version:** 1.0.0  
**Engine:** Godot Engine 4.7.2-stable (64-bit console)  
**Renderer:** `gl_compatibility` (OpenGL 3.3 / WebGL 2 compatible for Intel Iris Xe)  
**Date:** 2026-11-04  

---

## 1. Overview & Autoload Pipeline

The ChemLab Godot frontend runs as a client and interactive visualizer for the chemical simulation core. It registers four authoritative Autoload singletons in `game/project.godot`:

```ini
[autoload]
SimulationBridge="*res://scripts/chemistry/simulation_bridge.gd"
InputManager="*res://scripts/input/input_manager.gd"
QuestManager="*res://scripts/quests/quest_manager.gd"
SaveManager="*res://scripts/save/save_manager.gd"
```

### 1.1 Singleton Responsibilities

| Singleton | Script Path | Role |
|-----------|-------------|------|
| **SimulationBridge** | `res://scripts/chemistry/simulation_bridge.gd` | Manages chemical vessel state, reaction kinetics, and dual-mode dispatch (Python TCP IPC @ `127.0.0.1:8765` with fallback to embedded GDScript `ReactionEvaluator`). |
| **InputManager** | `res://scripts/input/input_manager.gd` | OneEuroFilter-smoothed 3D hand tracking, pinch gesture Schmitt triggers, vessel pour/tilt tracking, and mouse/keyboard fallbacks. |
| **QuestManager** | `res://scripts/quests/quest_manager.gd` | Evaluates quest milestones, objective fulfillment, purity/yield checks, and XP gain triggers. |
| **SaveManager** | `res://scripts/save/save_manager.gd` | User profile serialization, encrypted save states, unlocked laboratory equipment, and sandbox experimental recipes. |

---

## 2. Dual-Engine IPC Architecture

```
┌────────────────────────────────────────────────────────┐
│               ChemLab Godot 4.7.2 UI                   │
│   (Vessel 3D Mesh, Liquid Shaders, Glassware Nodes)     │
└───────────────────────────┬────────────────────────────┘
                            │
               ┌────────────┴────────────┐
               │    SimulationBridge     │
               │      (GDScript)         │
               └──────┬────────────┬─────┘
                      │            │
            [TCP / Named Pipe]    [Offline Fallback]
                      │            │
                      ▼            ▼
             ┌────────────────┐  ┌──────────────────┐
             │ Python 3.12    │  │ ReactionEvaluator│
             │ Core IPC       │  │ (Embedded        │
             │ (Cantera/RDKit)│  │  GDScript Math)  │
             └────────────────┘  └──────────────────┘
```

### 2.1 IPC Protocol Specification
- **Endpoint:** `127.0.0.1:8765` (StreamPeerTCP) or `\\.\pipe\chemlab_core` (Windows Named Pipe)
- **Framing:** Line-delimited UTF-8 JSON (`\n`)
- **Request Envelope:**
  ```json
  {
    "request_id": "req_42",
    "command": "mix_vessels",
    "payload": {
      "vessel_id": "beaker_01",
      "add_species": "HCl_1M",
      "volume_ml": 25.0
    }
  }
  ```
- **Response Handling:**
  Implemented in `_parse_ipc_response(data: String)`:
  - Resolves active `_pending_requests[req_id]` callbacks.
  - Emits `reaction_completed(vessel_id, reaction_type, result)` signal.
  - Emits `vessel_state_changed(vessel_id, state)` with pH, volume, temperature, and RGBA color.

---

## 3. Rendering Pipeline & Intel Iris Xe Optimization

1. **Renderer:** `gl_compatibility` (Compatibility mode) ensures rock-solid 60 FPS on integrated Intel Iris Xe / Xe Graphics architectures without crashing on DX12/Vulkan driver quirks.
2. **Material Pipeline:**
   - **Glass Shader (`res://shaders/glass_shader.gdshader`):** Custom screen-reading shader calculating Fresnel reflection, microfacet roughness, and chromatic dispersion.
   - **Liquid Shader (`res://shaders/liquid_shader.gdshader`):** Uses Beer-Lambert volume absorption, dynamic liquid level plane clipping, and meniscus edge distortion.
3. **Headless Verification:**
   The project is verified via headless Godot:
   ```bash
   tools/bin/godot --headless --path game/ --check-only --quit-after 1
   ```
   Exit code 0 confirms zero syntax or autoload initialization errors.
