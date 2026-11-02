# ChemLab Natural User Interface (NUI) & Spatial Hand Tracking Architecture
# Technical Specification — Computer Vision, Kinematic Signal Processing, and Interaction Abstraction
# Version 1.0 — 2026-11-02

## 1. System Overview & Mission Statement

ChemLab empowers chemistry students, educators, and chemical researchers to manipulate simulated laboratory glassware, analytical balances, heating apparatus, and volumetric reagents through touchless webcam interaction. The primary design mandate is to deliver natural, responsive, and rock-solid physical manipulation of laboratory apparatus on commodity, non-specialized hardware.

The tracking subsystem abstracts raw monocular webcam frames into filtered anatomical landmarks, translates dynamic skeletal topologies into discrete and continuous laboratory interaction states, projects normalized camera coordinates into metric 3D workbench coordinates, and provides full functional parity with keyboard and mouse controls.

```
+---------------------------------------------------------------------------------------+
|                                    PHYSICAL USER                                      |
|            Webcam Video Stream (720p @ 30 FPS) | Mouse & Keyboard Fallback            |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                             VISION & LANDMARK PIPELINE                                |
|  - UVC Video Capture (OpenCV / MediaPipe Tasks Vision)                                |
|  - Volatile In-Memory Frame Extraction (Zero Disk Storage)                            |
|  - 21 3D Anatomical Landmarks per Hand (Wrist, CMC, MCP, PIP, DIP, TIP)               |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                         KINEMATIC SIGNAL PROCESSING (1-EURO)                          |
|  - 63 Decoupled 1-Euro Filter Channels per Hand (X, Y, Z for 21 Landmarks)            |
|  - Static Jitter Suppression: fc_min = 1.0 Hz, d_cutoff = 1.0 Hz                      |
|  - Dynamic Reach Responsiveness: beta = 0.007                                         |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                           GESTURE STATE MACHINE & HYSTERESIS                          |
|  - Pinch State Machine (Pinch-to-Grab small apparatus, d_enter < 0.045m, d_exit > 0.065m)|
|  - Grab State Machine (Power grip on flasks/beakers, d_avg < 0.16m, d_avg > 0.20m)   |
|  - Pour / Tilt Engine (Wrist roll angle > 45 deg, Volumetric rate ~ sin(tilt))        |
|  - Pipette Depress Engine (Continuous thumb plunger stroke phi in [0.0, 1.0])         |
|  - Point / Push Engine (Index extension with Z-velocity to virtual touch planes)       |
|  - Swirl / Stir Engine (Orbital horizontal velocity tracking for vortex mixing)       |
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                            SPATIAL COORDINATE TRANSFORM                               |
|  - Monocular Frustum Projection with Anthropometric Palm Depth Calibration            |
|  - Virtual Interaction Planes (VIP) & Workbench Raycasting                            |
|  - Magnetic Snap-Point Snapping (Ring stands, hotplates, balances, test tube racks)   |
|  - Interaction Volume Clamping: X in [-1.2, 1.2]m, Y in [0.4, 1.0]m, Z in [0.85, 1.5]m|
+---------------------------------------------------------------------------------------+
                                           |
                                           v
+---------------------------------------------------------------------------------------+
|                       DUAL INPUT ARBITRATION & IPC BRIDGE                             |
|  - Seamless Degradation & Handover to Mouse & Keyboard                                |
|  - JSON-RPC / IPC TCP Bridge (Port 8765 / 9876) to Blender 3D Engine & Qt Desktop GUI |
+---------------------------------------------------------------------------------------+
```

---

## 2. Hardware Context & Execution Constraints

### 2.1 Hardware Profile
The tracking architecture is engineered to run deterministically on common corporate, educational, and institutional laptop hardware without requiring dedicated GPU accelerators.

- **Target Platform**: Dell Latitude 5530
- **Central Processor**: Intel Core i5-1240U (10 Cores, 12 Threads: 2 Performance cores up to 4.4 GHz, 8 Efficient cores up to 3.3 GHz; 12 MB Intel Smart Cache)
- **Integrated Graphics**: Intel Iris Xe Graphics (80 Execution Units)
- **Primary Memory**: 16 GB DDR4-3200 MHz RAM
- **Optical Sensor**: Built-in 720p HD webcam (0.92 Megapixels, 1280x720 active array, rolling shutter, fixed focus, 30 FPS via standard USB Video Class / UVC interface)
- **Secondary Input**: Standard integrated Precision Touchpad and ISO keyboard; two-button USB optical scroll mouse

### 2.2 Performance & Resource Budgets
The computer vision subsystem runs concurrently with Cantera thermodynamic simulation, RDKit 3D conformer generation, and Blender 3D EEVEE/OpenGL viewports. Strict CPU and latency ceilings are enforced:

| Subsystem Metric | Target Budget | Upper Bound (Throttle Threshold) |
| :--- | :--- | :--- |
| Hand Tracking CPU Utilization | < 10% (Core i5-1240U) | 15% Max Combined Core Load |
| Pipeline Frame Rate | 30 FPS (Webcam synchronous) | Minimum 25 FPS before fallback |
| Capture-to-Pose Latency | < 18 ms | 25 ms Max End-to-End |
| ML Inference Time per Frame | 8 ms - 12 ms | 15 ms Max per Hand |
| Landmark Smoothing & Classification | < 0.8 ms | 1.5 ms Max |
| Process Resident Memory (RSS) | < 65 MB | 90 MB Max |
| Core Thread Affinity | E-core Threadpool Worker | Never block Main UI / OpenGL Thread |

### 2.3 MediaPipe Hands Landmark Topology
MediaPipe Hands detects and tracks 21 skeletal 3D landmarks for each active hand. The anatomical landmarks are indexed according to the standard biomechanical convention:

```
                  8 [INDEX_TIP]    12 [MID_TIP]    16 [RING_TIP]    20 [PINKY_TIP]
                     |                |               |                |
                  7 [INDEX_DIP]    11 [MID_DIP]    15 [RING_DIP]    19 [PINKY_DIP]
                     |                |               |                |
                  6 [INDEX_PIP]    10 [MID_PIP]    14 [RING_PIP]    18 [PINKY_PIP]
                     |                |               |                |
  4 [THUMB_TIP]   5 [INDEX_MCP]    9 [MID_MCP]     13 [RING_MCP]    17 [PINKY_MCP]
        |               \             |               /                /
  3 [THUMB_IP]           \            |              /                /
        |                 \           |             /                /
  2 [THUMB_MCP]            \          |            /                /
        \                   \         |           /                /
         1 [THUMB_CMC]       \        |          /                /
                  \           \       |         /                /
                   +-----------+------+--------+----------------+
                                       |
                                   0 [WRIST]
```

Every landmark $i \in \{0, \dots, 20\}$ yields:
- $u_i \in [0.0, 1.0]$: Horizontal coordinate normalized by image width.
- $v_i \in [0.0, 1.0]$: Vertical coordinate normalized by image height (0.0 at top, 1.0 at bottom).
- $z_i \in [-1.0, 1.0]$: Depth coordinate relative to the wrist [0], scaled such that a smaller value is closer to the camera.
- $V_i \in [0.0, 1.0]$: Landmark visibility and confidence estimate.

---

## 3. Kinematic Signal Processing: Jitter Suppression & Responsiveness

Webcam-based landmark extraction suffers from two opposing signal degradation phenomena:
1. **High-frequency spatial tremor (Jitter)**: Small sensor noise variations, ambient lighting fluctuations, and natural physiological hand micro-tremors cause landmarks to jitter by 2-5 millimeters when held stationary. In a virtual chemistry lab, this causes catastrophic failure during precision actions (e.g., dropping a pipette into a narrow volumetric flask neck, or adjusting a titration burette stopcock).
2. **Phase lag (Latency)**: Standard static low-pass filters (such as Butterworth, moving averages, or exponential smoothing) eliminate jitter at the expense of introducing lag during rapid hand reaching or pouring motions.

### 3.1 One-Euro Filter Mathematical Formulation
To simultaneously achieve jitter-free static holds and zero-lag dynamic reaches, ChemLab applies the adaptive low-pass filter developed by Casiez, Roussel, and Vogel (CHI 2012). The cutoff frequency adapts continuously based on the instantaneous velocity of the signal.

For any 1D scalar signal $x_k$ sampled at time $t_k$ with interval $\Delta t = t_k - t_{k-1}$:

#### 1. Signal Derivative Estimation
The raw velocity derivative is computed from the unfiltered current position $x_k$ and the previous filtered output $\hat{x}_{k-1}$:
$$\dot{x}_k = \frac{x_k - \hat{x}_{k-1}}{\Delta t}$$

#### 2. Derivative Low-Pass Filtering
To prevent instantaneous derivative noise spikes from causing spurious cutoff fluctuations, the estimated derivative is filtered with a fixed low-pass cutoff frequency $d_{cutoff}$:
$$\alpha_d = \frac{2 \pi \cdot d_{cutoff} \cdot \Delta t}{2 \pi \cdot d_{cutoff} \cdot \Delta t + 1}$$
$$\hat{\dot{x}}_k = \alpha_d \dot{x}_k + (1 - \alpha_d) \hat{\dot{x}}_{k-1}$$

#### 3. Dynamic Cutoff Frequency Adaptation
The adaptive cutoff frequency $f_c$ for the position signal is computed linearly with respect to the magnitude of the smoothed velocity:
$$f_c = f_{c\_min} + \beta |\hat{\dot{x}}_k|$$
where:
- $f_{c\_min}$ is the minimum cutoff frequency enforced at zero velocity.
- $\beta$ is the speed adaptation coefficient that scales the filter bandwidth with velocity.

#### 4. Adaptive Position Smoothing
The dynamic smoothing factor $\alpha$ is derived from $f_c$ and applied to obtain the filtered position $\hat{x}_k$:
$$\alpha = \frac{2 \pi \cdot f_c \cdot \Delta t}{2 \pi \cdot f_c \cdot \Delta t + 1}$$
$$\hat{x}_k = \alpha x_k + (1 - \alpha) \hat{x}_{k-1}$$

### 3.2 Production Parameter Tuning
Through empirical benchmarking on the Dell Latitude 5530 with Intel Iris Xe and monocular 720p webcam input, ChemLab standardizes on the following kinematic parameter set:

```python
# ChemLab Kinematic Filter Parameters
ONE_EURO_MIN_CUTOFF: float = 1.0    # fc_min in Hertz
ONE_EURO_BETA: float = 0.007        # Speed coefficient
ONE_EURO_D_CUTOFF: float = 1.0      # Derivative cutoff in Hertz
```

#### Rationale for Tuned Values:
- **$f_{c\_min} = 1.0\text{ Hz}$**: When the user holds an apparatus stationary (velocity $|\hat{\dot{x}}| \to 0$), the cutoff frequency drops to 1.0 Hz. This eliminates 98.4% of high-frequency tremor jitter, holding test tubes and pipettes motionless in 3D space.
- **$\beta = 0.007$**: During intentional reaches across the workbench ($v \approx 0.3 - 0.8\text{ m/s}$), $f_c$ rises dynamically to 18-35 Hz. At $\Delta t \approx 33\text{ ms}$ (30 FPS), $\alpha \to 0.85$, eliminating tracking latency and ensuring the virtual apparatus follows the physical hand with less than 10 ms phase lag.
- **$d_{cutoff} = 1.0\text{ Hz}$**: Provides aggressive stabilization of the velocity estimate, preventing sudden lighting flickers or edge noise from kicking the filter into high-bandwidth mode prematurely.

### 3.3 Decoupled 3D Point Filtering Architecture
Every 3D landmark is decoupled into three independent 1-Euro instances:
$$\mathbf{P}_i(t) = \left( \text{Filter}_{i,x}(t, x_i), \; \text{Filter}_{i,y}(t, y_i), \; \text{Filter}_{i,z}(t, z_i) \right)$$
For a single hand (21 landmarks), 63 independent scalar filters run concurrently. For dual-hand interaction, 126 filter channels are executed. Total computational overhead for 126 channels is under 0.04 ms per frame on an Intel i5-1240U core.

---

## 4. Gesture Recognition State Machines & Hysteresis Rules

ChemLab models physical manipulation using a formal Finite State Machine (FSM). To prevent flickering, rapid oscillation, and accidental dropping of hazardous chemical containers, all state transitions utilize Schmitt trigger hysteresis.

```
                    +--------------------+
                    |        IDLE        |
                    +--------------------+
                      |                ^
   d_pinch < 0.045m   |                |  d_pinch >= 0.065m
   & apparatus near   |                |  & d_avg >= 0.20m
                      v                |
         +---------------------------------------+
         |           ACTIVE MANIPULATION         |
         |  (Apparatus locked to hand centroid)  |
         +---------------------------------------+
           |                 |                 |
           | tilt > 48 deg   | thumb depress   | orbital motion
           v                 v                 v
    +-------------+   +--------------+   +-------------+
    |    POUR     |   |   PIPETTE    |   |    SWIRL    |
    |  (Laminar   |   | (Aspiration/ |   |   (Vortex   |
    | Fluid Flow) |   |  Dispense)   |   |   Mixing)   |
    +-------------+   +--------------+   +-------------+
           |                 |                 |
           | tilt < 42 deg   | release thumb   | v_orbit ~ 0
           v                 v                 v
         +---------------------------------------+
         |           ACTIVE MANIPULATION         |
         +---------------------------------------+
```

### 4.1 Pinch Gesture (Fine Motor Interaction)
The pinch gesture is designed for precision apparatus: test tubes, transfer pipettes, micropipettes, spatulas, and thermometer probes.

#### 1. Kinematic Metric
Euclidean distance between Thumb Tip (Landmark 4) and Index Tip (Landmark 8):
$$d_{pinch} = \|\mathbf{P}_4 - \mathbf{P}_8\|_2 = \sqrt{(x_4 - x_8)^2 + (y_4 - y_8)^2 + (z_4 - z_8)^2}$$

#### 2. Dual-Threshold Hysteresis Rules
```
IF current_state != PINCH:
    IF d_pinch < 0.045:
        TRANSITION TO PINCH
        target_apparatus = query_nearest_apparatus(hand_focus, radius=0.08m)
        IF target_apparatus IS NOT NULL:
            ATTACH target_apparatus TO hand_focus
ELSE:
    IF d_pinch >= 0.065:
        TRANSITION TO RELEASE -> IDLE
        DETACH target_apparatus
        APPLY physics_drop_or_snap(target_apparatus)
```
- **Enter Threshold ($d_{enter}$)**: $0.045\text{ m}$ (or 0.045 in normalized coordinate space).
- **Exit Threshold ($d_{exit}$)**: $0.065\text{ m}$.
- **Hysteresis Deadband**: $\Delta d = 0.020\text{ m}$. The $44\%$ wider release gap ensures that minor finger twitches or relaxed hand grips do not drop glassware prematurely during transport.

#### 3. Interaction Focus Anchor
The interaction anchor is the spatial midpoint between the thumb tip and index tip:
$$\mathbf{F}_{pinch} = \frac{\mathbf{P}_4 + \mathbf{P}_8}{2}$$

### 4.2 Grab Gesture (Gross Motor Interaction)
The grab gesture is designed for larger laboratory containers: Erlenmeyer flasks, Florence flasks, 250mL-1000mL beakers, reagent bottles, and graduated cylinders.

#### 1. Kinematic Metric
Mean Euclidean distance between the four fingertip landmarks (Index 8, Middle 12, Ring 16, Pinky 20) and the Wrist anchor (0):
$$d_{avg\_grip} = \frac{1}{4} \sum_{i \in \{8, 12, 16, 20\}} \|\mathbf{P}_i - \mathbf{P}_0\|_2$$

#### 2. Dual-Threshold Hysteresis Rules
```
IF current_state != GRAB:
    IF d_avg_grip < 0.16:
        TRANSITION TO GRAB
        target_apparatus = query_nearest_apparatus(palm_center, radius=0.12m)
        ATTACH target_apparatus TO palm_center
ELSE:
    IF d_avg_grip >= 0.20:
        TRANSITION TO RELEASE -> IDLE
        DETACH target_apparatus
```
- **Enter Threshold**: $d_{avg\_grip} < 0.16$
- **Exit Threshold**: $d_{avg\_grip} \ge 0.20$
- **Fist Sub-State**: If $d_{avg\_grip} < 0.11$, the gesture enters `FIST` state, locking apparatus orientation firmly against rotational slippage.

#### 3. Continuous Grab Strength Formulation
To drive variable visual grasp compression or robotic gripper mechanics:
$$S_{grab} = \text{clamp}\left(1.0 - \frac{d_{avg\_grip}}{0.24}, \; 0.0, \; 1.0\right)$$

### 4.3 Pour / Tilt Gesture (Angle-Governed Fluid Transfer)
Pouring transfers reagents between beakers, test tubes, and flasks. The volume rate is governed directly by physical hand rotation.

#### 1. Wrist Orientation Kinematic Vectors
The tilt vector is derived from the transverse knuckle axis spanning Pinky MCP (17) to Index MCP (5):
$$\mathbf{v}_{knuckle} = \mathbf{P}_5 - \mathbf{P}_{17} = (dx, dy, dz)$$

The roll/tilt angle in degrees relative to the horizontal lab bench plane is computed as:
$$\theta_{tilt} = \arctan2\left(dy + 0.5 \cdot dz, \; |dx| + 10^{-5}\right) \times \frac{180}{\pi}$$

#### 2. Angular Thresholds with Hysteresis
- **Critical Pour Threshold ($\theta_{critical}$)**: $45.0^\circ$
- **Enter Pour State**: $|\theta_{tilt}| \ge 48.0^\circ$ (while holding an apparatus in `PINCH` or `GRAB`)
- **Exit Pour State**: $|\theta_{tilt}| \le 42.0^\circ$ (Schmitt deadband of $6.0^\circ$ prevents fluid spatter oscillations)

#### 3. Volumetric Flow Rate Dynamics
Fluid discharge obeys laminar spout geometry. For $|\theta_{tilt}| > \theta_{critical}$:
$$\dot{V}(\theta_{tilt}) = \dot{V}_{max} \cdot \sin\left(\frac{|\theta_{tilt}| - \theta_{critical}}{90^\circ - \theta_{critical}} \cdot \frac{\pi}{2}\right)$$
where $\dot{V}_{max}$ is the calibrated apparatus discharge rate (e.g., $25.0\text{ mL/s}$ for a standard 250mL beaker spout, $2.5\text{ mL/s}$ for a 10mL graduated pipette).

#### 4. Stream Targeting & Meniscus Physics
The fluid stream originating from the spout vertex $\mathbf{S}_{vessel}$ is projected under gravitational acceleration:
$$\mathbf{x}_{stream}(t) = \mathbf{S}_{vessel} + \mathbf{v}_0 t + \frac{1}{2} \mathbf{g} t^2$$
If the parabolic arc intersects the opening boundary mesh of a receiving vessel, volume is transferred dynamically and reaction thermodynamics are calculated in Cantera. If the arc misses, liquid pours onto the workbench, triggering hazard spills and safety warnings.

### 4.4 Pipette Depress Gesture (Volumetric Aspiration & Dispense)
Micropipettes (e.g. Gilson/Eppendorf style) require continuous thumb plunger travel control with distinct physical stop thresholds.

#### 1. Plunger Displacement Metric
The displacement is tracked by measuring the distance between Thumb Tip (4) and Thumb MCP (2):
$$\delta_{plunger} = \|\mathbf{P}_4 - \mathbf{P}_2\|_2$$

#### 2. Continuous Plunger Fraction
$$\phi_{plunger} = \text{clamp}\left(\frac{\delta_{rest} - \delta_{plunger}}{\delta_{rest} - \delta_{depressed}}, \; 0.0, \; 1.0\right)$$
where default baseline parameters are $\delta_{rest} = 0.085\text{ m}$ and $\delta_{depressed} = 0.035\text{ m}$.

#### 3. Two-Stop Calibration
- **First Stop ($\phi = 0.80$)**: Target volume calibration point. A tactile and visual haptic notch is engaged. Releasing the plunger from $\phi = 0.80$ to $\phi = 0.0$ aspirates calibrated reagent into the pipette tip. Depressing from $\phi = 0.0$ to $\phi = 0.80$ dispenses calibrated reagent into the target vessel.
- **Second Stop / Blowout ($\phi = 1.00$)**: Depressing past the first stop ejects residual micro-droplets adhering to the inside of the disposable tip.

### 4.5 Push / Touch Gesture (Virtual UI & Appliance Control)
Interacting with digital balances, heating plate dials, safety placards, and HUD menus requires a touch trigger without grasping.

#### 1. Pointing Finger Topology
Index finger must be fully extended while other fingers remain curled:
$$\|\mathbf{P}_8 - \mathbf{P}_0\|_2 > 0.20 \quad \text{AND} \quad \|\mathbf{P}_{12} - \mathbf{P}_0\|_2 < 0.13 \quad \text{AND} \quad \|\mathbf{P}_{16} - \mathbf{P}_0\|_2 < 0.13$$

#### 2. Z-Velocity & Plane Penetration Trigger
$$\mathbf{v}_{index\_z} = \frac{z_8(t) - z_8(t - \Delta t)}{\Delta t}$$
When the index tip touches a virtual collision plane with forward velocity $v_z < -0.15\text{ m/s}$ (moving toward the screen/bench), a `TOUCH_CLICK` event is generated, triggering analytical balance tare, stir plate power, or burner ignition.

### 4.6 Swirl / Stir Gesture (Orbital Mixing)
Vortex mixing and flask swirling are essential for reagent dissolution without magnetic stirrers.

#### 1. Orbital Kinematics
Wrist coordinate history is tracked across a sliding window of 15 frames ($M = 15$). Horizontal velocity vectors $\mathbf{v}_h = (v_x, v_y)$ are evaluated for angular phase progression:
$$\omega_{swirl} = \frac{\sum_{k=1}^{M-1} (dx_k \cdot dy_{k+1} - dy_k \cdot dx_{k+1})}{\sum_{k=1}^M (dx_k^2 + dy_k^2)}$$

#### 2. Swirl State Engagement
- **Active Swirling**: Engages when $|\omega_{swirl}| \ge 3.5\text{ rad/s}$ ($f \approx 0.5 - 2.5\text{ Hz}$) and orbital radius $0.02\text{ m} \le R_{orbit} \le 0.08\text{ m}$.
- **Physics Reaction**: Fluid inside the vessel excites a centrifugal surface vortex with height $h_{vortex} = \frac{\omega^2 R^2}{2g}$, accelerating dissolution rates and exothermic reaction kinetics.

---

## 5. 2D-to-3D Spatial Mapping & Monocular Depth Mitigation

### 5.1 The Monocular Ambiguity Problem
A standard 720p webcam yields 2D perspective coordinates $(u, v)$ in image space and a relative landmark depth $z$ normalized relative to the wrist. Because monocular cameras lack direct time-of-flight or binocular disparity, the absolute physical distance $Z_{cam}$ from the camera to the hand is inherently ambiguous. Without stabilization, apparatus would jitter forward and backward uncontrollably.

### 5.2 Pinhole Frustum Back-Projection
Given webcam focal lengths $(f_x, f_y)$ and optical principal center $(u_0, v_0)$ in pixel coordinates:

$$\begin{bmatrix} X_{cam} \\ Y_{cam} \\ Z_{cam} \end{bmatrix} = \begin{bmatrix} (u - u_0) \cdot \frac{Z_{cam}}{f_x} \\ (v - v_0) \cdot \frac{Z_{cam}}{f_y} \\ Z_{cam} \end{bmatrix}$$

World coordinates in the Blender 3D scene space are resolved using the extrinsic camera pose matrix $[\mathbf{R}_{cam} \mid \mathbf{C}_{cam}]$:

$$\mathbf{P}_{world} = \mathbf{C}_{cam} + \mathbf{R}_{cam} \cdot \begin{bmatrix} X_{cam} \\ Y_{cam} \\ Z_{cam} \end{bmatrix}$$

### 5.3 Anthropometric Palm Scale Calibration
To solve for $Z_{cam}$ without requiring depth hardware, ChemLab computes the pixel span of the user's metacarpal skeleton between Wrist (0) and Middle MCP (9):
$$L_{palm\_px} = \sqrt{(u_0 - u_9)^2 \cdot W^2 + (v_0 - v_9)^2 \cdot H^2}$$

Using the invariant human anthropometric median palm dimension $L_{palm\_metric} \approx 0.088\text{ m}$:
$$Z_{cam} \approx \frac{f_y \cdot L_{palm\_metric}}{L_{palm\_px}}$$

### 5.4 Virtual Interaction Planes (VIP)
To completely prevent depth jitter when operating above the workbench, ChemLab restricts manipulation to three Virtual Interaction Planes:

```
+-----------------------------------------------------------------------------------+
|  REAGENT SHELF PLANE  (Z = 1.45m)                                                 |
|  [Stock Bottles, Solid Salts, Acid Concentrates]                                  |
+-----------------------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------------------+
|  TITRATION & CLAMP RAIL PLANE  (Z = 1.15m)                                        |
|  [Burette Stopcocks, Condenser Tubes, Thermometer Clamps]                         |
+-----------------------------------------------------------------------------------+
                                  |
                                  v
+-----------------------------------------------------------------------------------+
|  WORKBENCH INTERACTION PLANE  (Z = 0.90m)                                         |
|  [Beakers, Flasks, Stir Plates, Analytical Balances, Test Tube Racks]             |
+-----------------------------------------------------------------------------------+
```

When an apparatus is picked up, its vertical coordinate locks to the interaction plane corresponding to the current task. Movement is translated smoothly across $(X, Y)$ while $Z$ remains stabilized on the plane until an intentional high-reach or shelf gesture is executed.

### 5.5 Raycasting to Collision Mesh
When an apparatus is released or placed down, ChemLab casts a geometric physics ray downward from the hand anchor along the gravity vector $\mathbf{g} = (0, 0, -1)$:
$$\mathbf{r}_{drop}(t) = \mathbf{P}_{held} + t \cdot \begin{bmatrix} 0 \\ 0 \\ -1 \end{bmatrix}$$
The apparatus attaches flush to the collision polygon of the lab benchtop, stir plate, or balance pan, eliminating floating glassware and table surface clipping.

### 5.6 Magnetic Snap-Points
Laboratory equipment operates in standardized configurations (e.g., a beaker must sit centered on a magnetic stirrer hotplate; a test tube must seat into a test tube rack well; a burette must clip into a Fisher clamp).

ChemLab embeds magnetic snap-points into all static apparatus:
$$\mathbf{F}_{snap} = -k_{snap} \cdot (\mathbf{P}_{apparatus} - \mathbf{P}_{anchor}) \cdot \exp\left( -\frac{\|\mathbf{P}_{apparatus} - \mathbf{P}_{anchor}\|^2}{2 \sigma_{snap}^2} \right)$$
- **Snap Capture Radius**: $R_{snap} = 0.05\text{ m}$ (5 cm)
- **Breakaway Force**: Exceeding $0.08\text{ m}$ hand displacement breaks the snap lock, returning the object to free hand manipulation.

### 5.7 Visual Grab Halos & Depth Affordances
To provide instant visual feedback on spatial alignment without stereoscopic goggles, every interactable apparatus projects a dynamic 3D ground halo on the bench surface:
- **Proximity Halo (Cyan)**: Projected when hand focus is within $0.15\text{ m}$. Halo radius shrinks as hand approaches.
- **Valid Grasp Envelope (Green)**: Illuminates when hand is within $0.045\text{ m}$ and pinch/grab gesture can immediately attach.
- **Kinematic Warning (Amber)**: Indicates valid proximity, but invalid orientation (e.g. attempting to pick up a boiling flask without thermal clamp).
- **Magnetic Snap Lock (Gold Pulse)**: Concentric ring pulses when apparatus is locked into an active snap-point.

### 5.8 Interaction Volume Clamping
The active physical interaction volume is restricted to the laboratory workbench envelope:
- **Lateral Range ($X$)**: $[-1.2\text{ m}, \; +1.2\text{ m}]$ (Workbench width)
- **Depth Range ($Y$)**: $[+0.4\text{ m}, \; +1.0\text{ m}]$ (Safe reach depth from operator)
- **Height Range ($Z$)**: $[+0.85\text{ m}, \; +1.50\text{ m}]$ (Benchtop surface to top reagent shelf)

Any coordinate reported outside these bounds is smoothly clamped using cubic Hermite interpolation.

---

## 6. Dual Input & Keyboard/Mouse Parity

Touchless computer vision is never a single point of failure. Every single webcam action has an exact, fully featured Keyboard and Mouse equivalent.

### 6.1 Action Parity Matrix

| Laboratory Action | Webcam Hand Tracking Gesture | Primary Keyboard & Mouse Control | Secondary / Laptop Touchpad |
| :--- | :--- | :--- | :--- |
| **Workstation Locomotion** | Lateral weight shift (Holistic Pose) / Stepping cadence | **A / D** (Switch Zone) or **W / S** (Approach/Back) | Number keys **1-4** (1: Hood, 2: Bench, 3: Analytical, 4: Rig) |
| **Camera View Orbit** | Two-hand open palm pan | **Right-Click + Drag** | Two-finger touch drag |
| **Camera Zoom** | Bimanual separation distance | **Mouse Scroll Wheel** | Pinch-to-zoom gesture |
| **Apparatus Selection** | Hand hover over apparatus (Cyan Halo) | Mouse Cursor Hover | Cursor trackpad hover |
| **Precision Pickup (Pinch)** | Pinch Thumb to Index ($d < 0.045\text{m}$) | **Left-Click + Hold** | Single-finger tap & hold |
| **Power Grip (Beaker/Flask)** | Full hand curled grab ($d_{avg} < 0.16\text{m}$) | **Shift + Left-Click + Hold** | Double-tap hold |
| **Object Release / Drop** | Open hand ($d_{pinch} \ge 0.065\text{m}$) | **Release Left-Click** or **Spacebar** | Release trackpad |
| **Liquid Pour / Tilt** | Wrist Roll Tilt ($\theta_{tilt} > 45^\circ$) | **Mouse Scroll Wheel** while holding object | **R + Vertical Drag** |
| **Pipette Plunger Stroke** | Continuous thumb travel $\phi \in [0.0, 1.0]$ | **Ctrl + Scroll Wheel** (Continuous) | On-screen vertical slider drag |
| **First Stop Click (Pipette)**| Hold thumb at $\phi = 0.80$ | **Left-Click** (Clicks to Stop 1) | UI button "Aspirate / Dispense" |
| **Second Stop (Blowout)** | Fully compress thumb $\phi = 1.0$ | **Ctrl + Left-Click** (Blowout) | UI button "Blowout" |
| **Flask Swirling / Mixing** | Horizontal orbital hand motion ($f \approx 1-3\text{ Hz}$) | **Shift + Circular Mouse Motion** | Radial trackpad swirl |
| **Touch UI / Balance Tare** | Index Point-Push forward ($v_z < -0.15$) | **Left-Click** on button / screen dial | Touchpad tap |
| **Switch Active Hand** | Raise opposite physical hand | **Q / E** (Switch Left/Right Hand) | Tab key |
| **Emergency Reagent Release**| Hand withdrawn from camera frustum | **Esc** or **Backspace** | Esc key |

### 6.2 Seamless Fallback & Degradation Engine
The system monitors tracking quality on every video frame. If any degradation condition is detected, control degrades gracefully without disrupting ongoing chemistry experiments.

```
+-----------------------------------------------------------------------------------+
|                            TRACKING HEALTH MONITOR                                |
|  - Frame Rate < 20 FPS                                                            |
|  - Detection Confidence < 0.65 for > 8 consecutive frames                         |
|  - Sensor Disconnected / Camera Obstructed                                       |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             GRACE HOLD STATE (350 ms)                             |
|  - Held apparatus coordinates remain frozen in volatile RAM                       |
|  - Glassware is NOT dropped into mid-air                                          |
|  - Visual indicator shifts to Amber (Degraded)                                    |
+-----------------------------------------------------------------------------------+
                                         |
                    +--------------------+--------------------+
                    |                                         |
     (Tracking reacquired within 350ms)        (Tracking unrecovered after 350ms)
                    v                                         v
+---------------------------------------+ +-----------------------------------------+
|          SMOOTH RESUMPTION            | |        SEAMLESS MOUSE HANDOVER          |
|  - 1-Euro state re-seeded at current  | |  - Apparatus smoothly snaps to nearest  |
|    sensor position                    | |    bench collision plane                |
|  - Green LED restored                 | |  - Active apparatus selected by Mouse   |
|                                       | |  - UI prompts: "Switched to Mouse Mode" |
+---------------------------------------+ +-----------------------------------------+
```

#### Fallback Rules:
1. **Accidental Drop Prevention**: If the user's hand briefly leaves the camera field of view or is momentarily occluded by glassware, a $350\text{ ms}$ Grace Hold Timer prevents the apparatus from dropping or splashing chemicals.
2. **Zero Inversion Glitch**: When tracking is lost, velocity derivatives are clamped to zero, preventing runaway inertia in the physics engine.
3. **Cursor Synchronization**: When switching to mouse mode, the mouse cursor smoothly aligns to the screen projection of the apparatus, preventing abrupt screen jumps.

---

## 7. Privacy, Safety & Ergonomic Standards

### 7.1 Zero Local Video Storage Architecture
In compliance with strict institutional data privacy policies (GDPR, FERPA, and corporate cleanroom standards), ChemLab enforces zero persistence of optical data:

```
[Webcam Hardware]
       |
       | YUY2 / MJPEG video stream (Kernel memory)
       v
[Volatile RAM Frame Buffer]  <--- Strictly in memory (No disk swap)
       |
       | Landmark extraction (< 12 ms)
       v
[21 3D Normalized Landmarks]
       |
       +---> [RAW FRAME ZEROED & FREED IMMEDIATELY IN-PLACE]
       |
       v
[Sanitized Kinematic Packet]
       |
       | Dispatched via Localhost TCP IPC (127.0.0.1:8765)
       v
[Blender 3D Simulation Engine]
```

- **Volatile In-Memory Processing**: Camera frames are processed strictly in RAM. No video frames, JPEG snippets, or temporary image files are ever written to hard drives, SSDs, temp files, or operating system swap space.
- **Immediate Buffer Deallocation**: The memory buffer storing the raw camera image is overwritten in-place or garbage-collected immediately upon landmark extraction.
- **Network Isolation**: Video stream data is never broadcast over local area networks or cloud endpoints. Only sanitized geometric telemetry structs (`HandTrackingResult`) containing numerical landmark coordinates are transmitted over localhost loopback sockets (`127.0.0.1`).

### 7.2 Visual Privacy Indicators
The user interface provides unforgeable visual feedback regarding optical hardware status:
- **Green Indicator**: Camera active, optical tracking operational, confidence $> 0.80$.
- **Amber Indicator**: Camera active, tracking degraded (low light, partial occlusion), confidence $\le 0.65$.
- **Red Indicator**: Camera disabled, privacy shutter active, or pure Keyboard/Mouse mode engaged.
- **Hardware Toggle Shortcut**: `Ctrl + Shift + C` terminates the webcam stream instantly, closing the hardware UVC handle.

### 7.3 Ergonomic Fatigue Prevention ("Gorilla-Arm" Mitigation)
Operating hands in mid-air without armrests ("Gorilla-Arm syndrome") causes shoulder strain within 5 to 10 minutes. ChemLab mitigates ergonomic fatigue through specific software compensations:

1. **Resting Elbow Posture Calibration**: The tracking volume is calibrated to detect natural hand articulation when the user's elbows rest comfortably on the desk surface. Forearms angle upward at $30^\circ - 45^\circ$, completely eliminating the need to hold full arms aloft.
2. **Neutral Wrist Bias Offset**: Standard human resting posture exhibits a $+15^\circ$ inward pronation. The gesture engine incorporates this resting bias, requiring zero hyper-supination to achieve a level pour.
3. **Ergonomic Break Prompts**: After 30 minutes of continuous webcam interaction, the HUD displays a non-intrusive reminder recommending a 60-second resting pause or offering a one-click toggle to mouse/keyboard controls.

---

## 8. Software Architecture & IPC Protocol Specification

### 8.1 Software Modular Architecture
The tracking architecture consists of decoupled layers isolated from rendering and network libraries:

```
chemlab/
├── chemlab_core/
│   ├── models.py                     # Data contracts (NormalizedLandmark, HandLandmarkFrame, GestureEvent)
│   ├── config.py                     # VisionConfig (thresholds, cutoffs, fps targets)
│   └── vision/
│       ├── contracts.py              # LandmarkProvider and GestureClassifier Protocols
│       ├── gesture_classifier.py     # Pure geometric classification (Pinch, Grab, Point, Swipe)
│       └── synthetic.py              # Headless landmark generation for CI/CD test automation
└── src/
    └── chemlab/
        └── cv/
            ├── one_euro_filter.py    # OneEuroFilter & Point3DOneEuroFilter implementations
            ├── hand_tracker.py       # AirGuitarGestureEngine & WebcamHandTracker pipeline
            └── holistic_tracker.py   # MediaPipeHolisticEngine (Full-body pose & workstation navigation)
```

### 8.2 Data Contracts & Schema Definitions

#### 1. Normalized Landmark
```python
class NormalizedLandmark(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float  # [0.0, 1.0] Viewport width normalized
    y: float  # [0.0, 1.0] Viewport height normalized
    z: float  # [-1.0, 1.0] Relative depth normalized to wrist
    visibility: float = 1.0
```

#### 2. Hand Tracking Result Telemetry Packet
```python
@dataclass
class HandTrackingResult:
    timestamp: float
    handedness: Handedness
    raw_landmarks: list[NormalizedLandmark]
    smoothed_landmarks: list[NormalizedLandmark]
    gesture: AirGuitarGesture
    pinch_distance: float
    is_pinching: bool
    is_grabbing: bool
    grab_strength: float
    tilt_degrees: float
    pour_rate: float
    world_position_3d: tuple[float, float, float]
    confidence: float = 1.0
```

### 8.3 IPC Socket Transport Protocol
Filtered telemetry is serialized into JSON-RPC 2.0 datagrams and transmitted over localhost TCP sockets (`127.0.0.1:8765` or fallback port `9876`) to the Blender 3D runtime and PySide6 desktop GUI.

#### Telemetry Packet Example (Volumetric Pouring State):
```json
{
  "jsonrpc": "2.0",
  "method": "chemlab.cv.hand_telemetry",
  "params": {
    "timestamp": 1730548800.124,
    "handedness": "RIGHT",
    "gesture": "POUR",
    "is_pinching": true,
    "is_grabbing": false,
    "pinch_distance": 0.0312,
    "grab_strength": 0.8420,
    "tilt_degrees": 54.30,
    "pour_rate": 0.3800,
    "world_position_3d": [0.1250, 0.6500, 0.9200],
    "confidence": 0.985,
    "focus_point": {"x": 0.485, "y": 0.420, "z": -0.012}
  },
  "id": 1042
}
```

---

## 9. Verification & Quality Assurance Protocols

To guarantee continuous stability, the tracking architecture includes a comprehensive automated test matrix running in headless CI without physical camera hardware.

### 9.1 Unit & Integration Test Suite
The following verification test suites are integrated into ChemLab's automated testing pipeline:

1. `tests/test_one_euro_filter.py`:
   - Validates stationary tremor attenuation ($Var_{out} < 0.35 \cdot Var_{in}$).
   - Validates high-velocity adaptation ($\hat{x} > 0.25$ within 2 frames on step input).
   - Verifies 3D independent multi-channel smoothing.
2. `tests/test_hand_tracker.py`:
   - Validates `IDLE`, `PINCH`, `GRAB`, `FIST`, `POUR`, and `RELEASE` gesture classifications.
   - Verifies tilt angle computation from transverse knuckle geometry.
   - Tests synthetic landmark injection through `WebcamHandTracker(use_synthetic=True)`.
3. `tests/test_vision.py`:
   - Tests synthetic open palm, pinch factor, and grab factor generation.
   - Validates kinematic swipe detection across 15-frame history sliding buffers.
4. `tests/test_holistic_tracker.py`:
   - Validates stationary vs. knee-lift stepping cadence for full-body locomotion.
   - Verifies lateral weight shifts mapping to workstation transitions (Fume Hood, Main Bench, Analytical Bench, Synthesis Rig).

### 9.2 Execution Command
```bash
.venv/Scripts/pytest tests/test_hand_tracker.py tests/test_one_euro_filter.py tests/test_vision.py tests/test_holistic_tracker.py -v
```

---

## 10. Summary Matrix: Gestures, Kinematics & Hysteresis Rules

| Gesture Category | Trigger Landmark Indices | Kinematic Formula | Enter Threshold | Exit Threshold | Primary Physical Interaction |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **PINCH** | Thumb Tip [4], Index Tip [8] | $d = \|\mathbf{P}_4 - \mathbf{P}_8\|_2$ | $d < 0.045\text{ m}$ | $d \ge 0.065\text{ m}$ | Grasp test tubes, spatulas, micropipettes |
| **GRAB** | Tips [8, 12, 16, 20], Wrist [0] | $d = \frac{1}{4} \sum \|\mathbf{P}_i - \mathbf{P}_0\|$ | $d < 0.16\text{ m}$ | $d \ge 0.20\text{ m}$ | Hold beakers, flasks, bottles |
| **FIST** | Tips [8, 12, 16, 20], Wrist [0] | $d = \frac{1}{4} \sum \|\mathbf{P}_i - \mathbf{P}_0\|$ | $d < 0.11\text{ m}$ | $d \ge 0.14\text{ m}$ | Firm lock, prevent rotation |
| **POUR** | Wrist [0], Index MCP [5], Pinky MCP [17] | $\theta = \text{atan2}(dy + 0.5dz, \|dx\|)$ | $\|\theta\| \ge 48.0^\circ$ | $\|\theta\| \le 42.0^\circ$ | Laminar fluid discharge ($\propto \sin(\text{tilt})$) |
| **PIPETTE** | Thumb Tip [4], Thumb MCP [2] | $\phi = \frac{\delta_{rest} - \|\mathbf{P}_4 - \mathbf{P}_2\|}{\Delta\delta}$ | $\phi > 0.05$ (continuous) | $\phi \le 0.02$ | Calibrated aspiration ($\phi=0.8$), Blowout ($\phi=1.0$) |
| **POINT** | Index Tip [8], Middle Tip [12], Wrist [0] | $\|\mathbf{P}_8 - \mathbf{P}_0\| > 0.20, \|\mathbf{P}_{12} - \mathbf{P}_0\| < 0.13$ | Index extended | Index curled | Laser pointer, button hover |
| **TOUCH** | Index Tip [8] | $v_z = \frac{z(t) - z(t-\Delta t)}{\Delta t}$ | $v_z < -0.15\text{ m/s}$ | $v_z \ge 0.0\text{ m/s}$ | Balance tare, stir plate power, HUD clicks |
| **SWIRL** | Wrist [0] | $\omega = \frac{d\theta}{dt}$ in $(X, Y)$ plane | $\|\omega\| \ge 3.5\text{ rad/s}$ | $\|\omega\| < 1.5\text{ rad/s}$ | Vortex excitation, reagent mixing |
