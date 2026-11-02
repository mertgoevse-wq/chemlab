# ChemLab Performance & Graphics Optimization Report

## Executive Summary

This document establishes the official performance baseline, graphics optimization architecture, simulation time-step budgeting, and memory partitioning strategy for **ChemLab**. 

The primary target platform is the **Dell Latitude 5530** enterprise mobile workstation running Windows 11 Pro. Operating within the constraints of Intel Iris Xe integrated graphics (80 Execution Units) and shared DDR4 system memory requires strict hardware budgeting across geometry, materials, physics solving, and real-time computer vision tracking.

This report formalizes the technical specifications implemented in `src/chemlab/graphics/iris_xe_optimizer.py`, verified in `tests/test_iris_xe_optimizer.py`, and enforced through automated quality gates (`tests/validate_scene_assets.py` and `tests/headless_blender_test.py`).

---

## 1. Target Hardware Architecture & Bottlenecks

### 1.1 Hardware Profile: Dell Latitude 5530
- **CPU**: Intel Core i5-1245U (12th Gen Alder Lake U-series)
  - Core Topology: 10 physical cores / 12 threads (2 Performance-cores @ up to 4.40 GHz + 8 Efficient-cores @ up to 3.30 GHz)
  - Cache: 12 MB Intel Smart Cache (L3)
  - Power Envelope: 15 W Base TDP / 55 W Maximum Turbo Power
- **Integrated GPU**: Intel Iris Xe Graphics G7 (Alder Lake-U)
  - Execution Units: 80 EUs (640 FP32 Arithmetic Logic Units)
  - Peak Engine Clock: 1.20 GHz
  - Theoretical Compute: ~1.536 TFLOPS (FP32)
  - Theoretical Fill-Rate: ~19.2 GTexels/s texture fill, ~9.6 GPixels/s pixel fill
- **System Memory & Memory Controller**:
  - Capacity: 16 GB DDR4-3200 MHz (2x 8 GB Dual-Channel SODIMM)
  - Memory Bus Width: 128-bit dual channel
  - Theoretical Peak Bandwidth: ~51.2 GB/s (shared dynamically between CPU cores and GPU execution units)
- **Host OS**: Microsoft Windows 11 Pro (64-bit, WDDM 3.0+ driver model)

### 1.2 Unified Memory Architecture (UMA) & Bandwidth Contention
The single most critical hardware constraint on the Dell Latitude 5530 is memory bandwidth contention:
1. **Shared Bus Saturation**: Discrete GPUs utilize dedicated high-speed VRAM (GDDR6 at 256–512 GB/s). On Iris Xe, all CPU workloads (OS background services, Python interpreter, MediaPipe camera frame ingestion, ODE physics stepping) and GPU workloads (framebuffers, depth/stencil passes, shadow maps, texture reads) compete for the same 51.2 GB/s DDR4 bus.
2. **Dedicated vs. Shared VRAM Partitioning**: Windows reports a nominal **128 MB dedicated video memory** slice. This slice is strictly reserved for GPU hardware ring buffers, command queues, and active swapchain presentation surfaces. Textures, vertex buffers, and post-processing buffers reside in **dynamic shared system memory** (up to 8,192 MB).
3. **Staging Buffer Strategy**: To prevent thrashing the memory bus, `IntelIrisXeOptimizer.create_memory_partition_plan` restricts high-resolution asset staging in system RAM to a maximum of 6,144 MB (40% of 16 GB), while clamping texture dimensions to $\le 1024 \times 1024$.

```
+-------------------------------------------------------------------------+
|                  16 GB Dual-Channel DDR4-3200 (51.2 GB/s)               |
+------------------------------------+------------------------------------+
|         CPU System Memory          |       Dynamic Shared VRAM Pool     |
|  - Windows 11 & Background: ~4.0 GB|  - Active Framebuffers (128 MB slice)|
|  - ChemLab Core & Py: < 250 MB     |  - Geometry Buffers: < 200 MB      |
|  - CV Ring Buffers: < 200 MB       |  - Clamped Textures (1K): < 384 MB |
|  - Static Asset Staging: < 6.0 GB  |  - EEVEE Shadow & SSR Targets      |
+------------------------------------+------------------------------------+
```

### 1.3 Execution Unit (EU) & Fill-Rate Limitations
With 80 EUs organized into 5 Subslice clusters:
- **Instruction Cache Constraints**: Each subslice possesses compact L1/L2 instruction caches. Shaders with procedural complexity exceeding **45 nodes** or excessive branching trigger instruction cache thrashing and register spills, reducing EU occupancy below 40%.
- **Overdraw & Transparency Bottleneck**: In ChemLab, laboratory glassware (borosilicate beakers, Erlenmeyer flasks, burettes) and fluid menisci overlap in the camera frustum. Multiple blended transmission layers cause fill-rate saturation on the 9.6 GPixel/s raster pipeline.
- **Raymarching Overhead**: Screen-Space Reflections (SSR) and screen-space refraction raymarching across 80 EUs can rapidly consume the entire frame time if step sizes and ray counts are unconstrained.

---

## 2. Framerate Targets & Quality Presets

### 2.1 Framerate Envelopes
- **Base Resolution Target**: 1280x720 (720p) windowed or fullscreen.
- **Minimum Acceptable Framerate**: Solid 30 FPS (maximum frame time 33.33 ms, 1% low $\ge 25$ FPS).
- **Target Smooth Framerate**: 60 FPS (target frame time 16.67 ms, 1% low $\ge 52$ FPS).

### 2.2 Quality Preset Matrix

| Parameter | Low ("Ultra Performance") | Balanced ("Performance / Quality") | High ("Native Showcase") |
| :--- | :--- | :--- | :--- |
| **Internal Render Scale** | 50% (640x360 or 960x540 dynamic) | 71% - 75% (~960x540 viewport) | 100% Native (1280x720) |
| **Upscaling Algorithm** | Bilinear / Edge-Preserving CAS | XeSS / FSR 1.0 Analogue | Native 1.0x (No Upscale) |
| **Target Framerate** | 60 FPS locked | 45 - 60 FPS | 30 - 45 FPS |
| **Viewport Samples** | 16 samples | 24 samples | 64 samples |
| **Shadow Cube Size** | 512x512 | 1024x1024 | 2048x2048 |
| **Screen Space Reflections** | Disabled | Half-Resolution Trace (`enable_half_res_trace=True`) | Full-Resolution Trace |
| **Glass Refraction Shader** | Simple single-layer forward alpha | Single-pass Screen-Space Refraction (IOR 1.474) | Multi-pass chromatic refraction + volumetric absorption |
| **Ambient Occlusion** | Disabled | Localized distance ($0.4\text{ m}$) | Extended distance ($1.0\text{ m}$) |
| **Volumetric Fog / Smoke** | Disabled or 8px coarse tile grid | 4px tile grid (steam / reaction smoke) | 2px fine tile grid |
| **Bloom** | Disabled | Disabled (handled via UI compositor) | Clamped at 5.0 |
| **Max Material Draw Calls** | $\le 45$ | $\le 65$ | $\le 85$ |

### 2.3 Upscaling & Edge-Preserving Reconstruction Pipeline
The implementation in `IntelIrisXeOptimizer.calculate_internal_resolution` provides dynamic resolution scaling. For 720p output:
- **Low (50% scale)**: 640x360 pixels rendered internal, representing only 25% of the native fragment workload.
- **Balanced (71% scale)**: 910x512 pixels rendered internal, representing ~50% of the native fragment workload.
- **Reconstruction Filter**: A compute-pass Contrast Adaptive Sharpening (CAS) kernel is applied prior to HUD compositing, eliminating blur on text and liquid graduation markings while preserving high EU throughput.

---

## 3. Chemistry Solver & Simulation Budget

### 3.1 Decoupled Dual-Rate Architecture
To prevent chemical simulation spikes from causing frame drops, the chemistry ODE solver is fully decoupled from the graphics rendering thread:
- **Graphics Render Thread**: 60 Hz variable (driven by display VSync, frame budget 16.67 ms).
- **Physics & Chemistry Simulation Thread**: Fixed 20 Hz tick rate ($\Delta t = 0.050\text{ s}$ / 50 ms).
- **Hermite / Linear Snapshot Interpolation**: The render thread reads the two most recent simulation snapshots $(S_{k-1}, S_k)$ and interpolates meniscus levels, foam expansion volumes, temperatures, and solution RGB absorption colors based on normalized frame time:
  $$\alpha = \frac{t_{\text{render}} - t_{k-1}}{t_k - t_{k-1}}, \quad \alpha \in [0, 1]$$
  This provides visual fluidity at 60 FPS while capping chemistry CPU overhead to 20 evaluations per second.

```
Time (ms)  0        16.6      33.3      50.0      66.6      83.3      100.0
Render:    |---F1---|---F2---|---F3---|---F4---|---F5---|---F6---|---F7---| (60 Hz)
Interp:    [ S0 ]------>------>------>[ S1 ]------>------>------>[ S2 ]
Chem Tick: |============= Tick 0 =============|============= Tick 1 =============| (20 Hz)
```

### 3.2 ODE Solver Step Budget
- **Maximum Execution Time**: $< 5.0\text{ ms}$ per 50 ms tick.
- **Headroom Margin**: 90% (45 ms idle/sleep time per physics tick on the dedicated worker).
- **Numerical Integration Method**: 4th-Order Runge-Kutta (RK4) with sub-stepping for stiff systems (e.g., Belousov-Zhabotinsky Oregonator reactions, Briggs-Rauscher oscillations, and thermal runaway kinetics):
  $$k_1 = f(t_n, y_n), \quad k_2 = f\left(t_n + \frac{h}{2}, y_n + \frac{h}{2}k_1\right)$$
  $$k_3 = f\left(t_n + \frac{h}{2}, y_n + \frac{h}{2}k_2\right), \quad k_4 = f(t_n + h, y_n + hk_3)$$
  $$y_{n+1} = y_n + \frac{h}{6}(k_1 + 2k_2 + 2k_3 + k_4)$$

### 3.3 Game Pacing Compression & Numerical Safety
- **Kinetic Pacing Factor ($\tau$)**: Real-world chemical kinetics (which can take minutes or hours) are scaled by a tunable acceleration factor $\tau \in [1\times, 20\times]$. An oscillating BZ cycle completes in **8 to 15 seconds** instead of 3 to 5 minutes, maintaining user engagement without altering stoichiometric ratios.
- **Positivity Enforcement**: Chemical concentrations are strictly clamped:
  $$\forall i: [C_i]_{n+1} = \max(0.0, [C_i]^*)$$
- **Numerical Divergence Guard**: Every step verifies that $\text{NaN}$ and $\text{Inf}$ values are strictly absent. If an integration step exceeds bounded energy thresholds, the solver automatically halves sub-step $h$ and logs a telemetry event.

---

## 4. MediaPipe Webcam Inference Budget

### 4.1 Multi-Threaded Tracking Pipeline
Vision-based gesture tracking ("Air-Guitar" interaction and full-body posture tracking) is partitioned into an asynchronous worker pipeline:
1. **Camera Ingestion Worker**: Acquires raw video frames from the webcam at 30 FPS (resolution 640x480 or 1280x720) in a dedicated capture thread.
2. **Inference Worker**: Throttled to **15 - 20 Hz** execution rate. A non-blocking `try_acquire` ring buffer drops stale frames if the previous inference step is still evaluating.
3. **Tracking Latency vs. Throughput**: The pipeline maintains an end-to-end motion-to-interaction latency under **65 ms**.

### 4.2 CPU Allocation & Core Affinity
- **Target CPU Overhead**: $< 15\%$ of total host CPU capacity (equivalent to $\le 1.8$ Alder Lake core threads).
- **Core Affinity Configuration**: MediaPipe threads are explicitly affinitized to the **8 Efficient-cores (E-cores)** of the i5-1245U. The 2 high-frequency Performance-cores (P-cores) are kept entirely clear for OS messaging, Blender EEVEE rendering dispatch, and UI event loops.
- **No GPU Inference Contention**: MediaPipe executes using CPU XNNPACK/TFLite delegates rather than OpenCL/DirectML GPU delegates, preventing GPU execution units and DDR4 memory bandwidth from being stolen from graphics rendering.

### 4.3 Landmark Smoothing (1-Euro Filter)
To eliminate hand jitter on glassware interactions without adding perceptible lag, all 21 hand landmarks and 33 holistic body landmarks pass through an adaptive **1-Euro Filter**:
- Minimum cutoff frequency: $f_c^{\min} = 1.0\text{ Hz}$ (eliminates tremor when holding beakers stationary).
- Speed coefficient: $\beta = 0.007$ (eliminates lag during swift pouring, swirling, or reaching gestures).
- Derivative cutoff frequency: $f_{c, d} = 1.0\text{ Hz}$.

---

## 5. Global Memory Budget & Asset Hygiene

### 5.1 16 GB System Memory Allocation

| Subsystem / Allocation | Hard Budget Limit | Typical Working Set | Notes |
| :--- | :--- | :--- | :--- |
| **Windows 11 OS & Background Services** | 4,500 MB | 3,800 MB | OS base, DWM, background services |
| **Iris Xe Dynamic VRAM Allocation** | 2,048 MB | 1,200 MB | Active framebuffers, render targets, shadow maps |
| **Python Embedded Runtime & ChemLab Core** | **250 MB** | **180 MB** | NumPy, Cantera, RDKit, ODE histories |
| **Blender Viewport & Geometry Datablocks** | 350 MB | 260 MB | Mesh vertices, normals, UVs, scene graph |
| **MediaPipe Pipeline & Frame Buffers** | 200 MB | 140 MB | 3-frame circular buffer, TFLite weights |
| **UI, Audio, & Asset Staging** | 400 MB | 280 MB | Staged audio, HUD sprites, fonts |
| **Total ChemLab Application RAM** | **< 1,500 MB** | **~860 MB** | Well within the 1.5 GB peak budget |
| **Available Unallocated Headroom** | > 8,000 MB | ~9,500 MB | Safety margin preventing page swapping |

### 5.2 Asset Hygiene & Texture Budgeting
- **Texture Resolution Limit**: $\le 1024 \times 1024$ for apparatus, table surfaces, and architectural elements. Secondary props (plugs, valves, indicators) clamped to $512 \times 512$.
- **Texture Format**: BC7 / DXT5 compressed textures or packed channel maps (Roughness, Metallic, AO in RGB channels) to save memory bandwidth.
- **Scene Geometry Envelope**:
  - Maximum total scene triangles: $\le 250,000$ tris.
  - Maximum single object triangles: $\le 35,000$ tris.
  - Per-item glassware apparatus budget: $\le 4,000$ tris with smooth normal auto-smoothing.
- **Memory Leak Prevention**:
  - Circular bounded queues for reaction history graphs (clamped to max 1,000 steps).
  - Explicit garbage collection (`gc.collect()`) triggered on lab workstation transitions.
  - Strict destruction of temporary textures and framebuffers on resolution changes.

---

## 6. Empirical Verification Protocols & Quality Gate

### 6.1 Automated Verification Scripts

#### 1. Headless Blender Verification (`tests/headless_blender_test.py`)
Executed via:
```bash
blender.exe -b chemlab.blend -P tests/headless_blender_test.py
```
Validates:
- Scene datablock integrity and active EEVEE / EEVEE Next engine selection.
- Scene collection graph conforms to standard numbered collections:
  - `01_Architecture`
  - `02_Furniture`
  - `03_Fume_Safety` (or `03_Safety_Equipment`)
  - `04_Apparatus_Chemicals`
  - `05_Lighting_Cameras` (or `05_Cameras`)
- Camera and lighting presence.
- Zero missing image files, missing libraries, or unlinked datablocks.

#### 2. Scene Asset & Hardware Budget Validator (`tests/validate_scene_assets.py`)
Executed inside Blender to enforce hardware limits:
- Zero unapplied non-uniform scale vectors ($S_x = S_y = S_z = 1.0 \pm 0.01$).
- Total scene triangle count $\le 250,000$.
- No individual mesh exceeds $35,000$ triangles.
- Zero unassigned materials.
- Borosilicate glass materials adhere to Pyrex standard Index of Refraction ($n = 1.474 \pm 0.05$).
- Zero generic placeholder names (`Cube.001`, `Sphere.002`).

#### 3. Optimizer Unit Suite (`tests/test_iris_xe_optimizer.py`)
Executed via pytest:
```bash
pytest tests/test_iris_xe_optimizer.py -v
```
Validates:
- Intel integrated GPU detection and UMA memory classification.
- EEVEE viewport settings adjustment (viewport samples $\le 24$, half-res trace enabled, shadow map $\le 1024$).
- Dynamic resolution scaling calculations across all presets.
- VRAM partition planning and system RAM staging allocation.

### 6.2 Telemetry Logging Protocol
ChemLab includes a continuous runtime telemetry collector logging the following metrics at 1 Hz intervals:

```json
{
  "timestamp": 1729482104.25,
  "fps": 59.4,
  "frame_time_ms": 16.83,
  "1_percent_low_fps": 53.1,
  "gpu_draw_calls": 58,
  "gpu_triangles": 184520,
  "dynamic_vram_used_mb": 1184,
  "process_ram_rss_mb": 842.6,
  "ode_step_time_ms": 1.42,
  "mediapipe_infer_hz": 18.2,
  "mediapipe_cpu_pct": 11.4,
  "active_preset": "BALANCED"
}
```

### 6.3 Quality Gate Enforcement (`/quality-gate`)
No pull request or asset bundle may be merged into the master branch unless the following criteria pass with zero errors:
1. All headless Blender tests return exit code 0 (`VERIFICATION RESULT: PASSED`).
2. Asset budget audit verifies total scene triangles $\le 250,000$.
3. Procedural shader node complexity $\le 45$ nodes per material.
4. Pytest suite passes 100% of unit and integration tests.
5. Telemetry profile verifies 0 memory leaks across 10,000 simulated ODE steps.
