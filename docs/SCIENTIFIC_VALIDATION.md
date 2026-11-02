# ChemLab — Scientific Validation & Physical Chemistry Reference
**Document ID:** `DOC-CHEMLAB-SCI-001`  
**Version:** 1.0.0  
**Status:** Approved / Authoritative Reference  
**Date:** 2026-11-02  
**Target Engine:** ChemLab Scientific Core (Embedded Python / Godot 4 Client)  

---

## 1. Zero-Hallucination Policy & Scientific Grounding

In compliance with the ChemLab Autonomous Master Development Charter, **no physical constants, thermodynamic state variables, Arrhenius kinetic parameters, or molecular structures may be hallucinated or synthetically approximated**.

All simulation calculations derive from authoritative, peer-reviewed empirical datasets:
- **NIST Chemistry WebBook** (NIST Standard Reference Database Number 69)
- **CRC Handbook of Chemistry and Physics** (104th Edition, 2023–2024)
- **IUPAC Compendium of Chemical Terminology** (Gold Book)
- **RDKit Cheminformatics Engine** (ETKDGv3 / UFF force field parameterizations)
- **Perry's Chemical Engineers' Handbook** (9th Edition, Thermodynamics & Fluid Mechanics)

---

## 2. Chemical Thermodynamics & Phase Equilibrium

### 2.1 Standard Enthalpy, Entropy, and Gibbs Free Energy of Reaction

For any balanced stoichiometric chemical reaction:
$$\sum_{r} |\nu_r| \, R_r \longrightarrow \sum_{p} \nu_p \, P_p$$

The standard enthalpy of reaction at standard reference temperature ($T^\circ = 298.15\text{ K}$, $P^\circ = 100\text{ kPa}$) is calculated via Hess's Law:
$$\Delta H^\circ_{\text{rxn}} = \sum_{p} \nu_p \, \Delta H^\circ_{f,p} - \sum_{r} |\nu_r| \, \Delta H^\circ_{f,r}$$

Similarly, the standard reaction entropy:
$$\Delta S^\circ_{\text{rxn}} = \sum_{p} \nu_p \, S^\circ_{p} - \sum_{r} |\nu_r| \, S^\circ_{r}$$

The standard Gibbs free energy of reaction as a function of temperature $T$:
$$\Delta G^\circ(T) = \Delta H^\circ_{\text{rxn}} - T \, \Delta S^\circ_{\text{rxn}}$$

### 2.2 Thermodynamic Equilibrium Constant ($K_{\text{eq}}$)

The equilibrium constant is linked directly to Gibbs energy by the van 't Hoff relation:
$$K_{\text{eq}}(T) = \exp\left( -\frac{\Delta G^\circ(T)}{R \cdot T} \right)$$
where $R = 8.314462618\text{ J}\cdot\text{mol}^{-1}\cdot\text{K}^{-1}$ (molar gas constant).

**Numerical Stability Guard:**
To prevent IEEE 754 floating-point overflow (`inf`) or underflow (`0.0`), the exponent is strictly clamped to $[-700, 700]$:
$$z = \text{clamp}\left(-\frac{\Delta G^\circ(T)}{R \cdot T}, -700.0, 700.0\right)$$
$$K_{\text{eq}} = \exp(z)$$

### 2.3 Temperature-Dependent Heat Capacities ($C_p(T)$)

Isobaric molar heat capacity is evaluated via the standard Shomate polynomials (NIST):
$$C_p^\circ(t) = A + B \cdot t + C \cdot t^2 + D \cdot t^3 + \frac{E}{t^2}$$
where $t = T / 1000$ (with $T$ in Kelvin) and $A, B, C, D, E$ are substance-specific NIST regression coefficients.

---

## 3. Chemical Kinetics & Differential Equation Solvers

### 3.1 Arrhenius Rate Constant

Reaction velocity constants follow the empirical Arrhenius formulation:
$$k(T) = A \cdot \exp\left(-\frac{E_a}{R \cdot T}\right)$$
where:
- $A$: Pre-exponential frequency factor ($\text{s}^{-1}$ for 1st order, $\text{L}\cdot\text{mol}^{-1}\cdot\text{s}^{-1}$ for 2nd order)
- $E_a$: Activation energy ($\text{J}\cdot\text{mol}^{-1}$)
- $T$: Absolute temperature in Kelvin

The reaction rate $r$ for $aA + bB \to \text{Products}$:
$$r = k(T) \cdot [A]^\alpha \cdot [B]^\beta$$

### 3.2 Numerical ODE Solver for Stiff Kinetic Systems

Oscillating and autocatalytic reaction networks (such as the Briggs-Rauscher and Belousov-Zhabotinsky systems) exhibit stiff differential behavior across multiple timescales:
$$\frac{d\vec{C}}{dt} = \mathbf{S} \cdot \vec{r}(\vec{C}, T)$$
where $\mathbf{S}$ is the stoichiometric matrix and $\vec{C}$ is the vector of species concentrations.

**Solver Selection:**
1. Standard reactions: 4th-order Runge-Kutta (RK4) with adaptive step size:
   $$\vec{C}_{n+1} = \vec{C}_n + \frac{\Delta t}{6}(k_1 + 2k_2 + 2k_3 + k_4)$$
2. Stiff Oscillators: Radau IIA / Implicit Rosenbrock (L-stable) preventing numerical blowing-up during sharp autocatalytic spikes.

---

## 4. Analytical Acid-Base Chemistry & Henderson-Hasselbalch

### 4.1 Monoprotic & Diprotic Weak Acid Titrations

For a weak monoprotic acid $HA$ titrated with strong base $NaOH$:
1. **Initial pH:**
   $$\text{pH}_0 = -\log_{10}\left( \sqrt{K_a \cdot c_{HA}} \right)$$
2. **Buffer Region ($0 < V_{\text{titrant}} < V_{\text{eq}}$):**
   $$\text{pH} = \text{p}K_a + \log_{10}\left( \frac{[A^-]}{[HA]} \right)$$
3. **Equivalence Point ($V = V_{\text{eq}}$):**
   Hydrolysis of the conjugate base $A^- + H_2O \rightleftharpoons HA + OH^-$:
   $$\text{pOH}_{\text{eq}} = -\log_{10}\left( \sqrt{\frac{K_w}{K_a} \cdot c_{A^-,\text{diluted}}} \right)$$
   $$\text{pH}_{\text{eq}} = 14.0 - \text{pOH}_{\text{eq}}$$
4. **Excess Titrant ($V > V_{\text{eq}}$):**
   $$\text{pH} = 14.0 + \log_{10}\left( \frac{[OH^-]_{\text{excess}}}{V_{\text{total}}} \right)$$

---

## 5. 3D Cheminformatics & Molecular Mechanics (RDKit)

### 5.1 Distance Geometry Conformation Generation (ETKDGv3)

ChemLab uses Experimental Torsion Knowledge Distance Geometry (ETKDGv3) implemented in RDKit:
1. Conversion of 1D SMILES string into molecular graph.
2. Canonical explicit hydrogen addition (`Chem.AddHs`).
3. Pairwise distance bounds matrix construction from covalent bond lengths, angles, and torsional database priors:
   $$l_{ij} \le d_{ij} \le u_{ij}$$
4. Metric matrix distance geometry embedding in 3D Euclidean space with fixed random seed ($42$).

### 5.2 Universal Force Field (UFF) Energy Minimization

Embedded 3D conformers are minimized using Rappé et al. (1992) Universal Force Field:
$$E_{\text{total}} = E_R + E_\theta + E_\phi + E_\omega + E_{\text{vdw}} + E_{\text{el}}$$
where:
- $E_R$: Harmonic bond stretching: $E_R = \frac{1}{2} k_{ij} (r_{ij} - r_0)^2$
- $E_\theta$: Angle bending: $E_\theta = \frac{k_{ijk}}{C_2} [C_0 - C_1 \cos \theta + C_2 \cos 2\theta]$
- $E_\phi$: Dihedral torsion: $E_\phi = \frac{1}{2} V_\phi [1 - \cos(n\phi_0) \cos(n\phi)]$
- $E_{\text{vdw}}$: Lennard-Jones 6-12 non-bonded potential:
  $$E_{\text{vdw}} = D_{ij} \left[ \left(\frac{x_{ij}}{r}\right)^{12} - 2\left(\frac{x_{ij}}{r}\right)^6 \right]$$

Iterated through 500 gradient steps until $\nabla E < 10^{-4}\text{ kcal}\cdot\text{mol}^{-1}\cdot\text{Å}^{-1}$.

---

## 6. Safety Physics & Hazardous Phenomenon Modeling

### 6.1 Semenov Thermal Explosion & Critical Heat Balance

For an exothermic reaction inside a closed or semi-closed vessel of volume $V$, surface area $S$, and heat transfer coefficient $U$:
$$\rho C_p V \frac{dT}{dt} = V \cdot (-\Delta H_{\text{rxn}}) \cdot A \exp\left(-\frac{E_a}{RT}\right) - U S (T - T_a)$$

**Semenov Criterion for Criticality ($\psi_{\text{crit}}$):**
$$\psi = \frac{V (-\Delta H) E_a A \exp(-E_a / R T_a)}{U S R T_a^2} \le \frac{1}{e} \approx 0.368$$
If $\psi > 0.368$, heat generation outpaces cooling, triggering a **thermal runaway**.

### 6.2 Antoine Vapor Pressure & Overpressurization

Vapor pressure $P_{\text{vap}}$ is computed using the Antoine equation:
$$\log_{10}(P_{\text{vap}}) = A - \frac{B}{T + C}$$
where $P_{\text{vap}}$ is in bar and $T$ in Kelvin.

### 6.3 Stopper Pop Launch Ballistics

When $P_{\text{internal}} > P_{\text{friction}} + P_{\text{atm}}$, projectile muzzle velocity for a rubber stopper of mass $m$:
$$v_0 = \sqrt{\frac{2 \cdot \Delta P \cdot V_{\text{headspace}}}{m}}$$

### 6.4 ANSI/AIHA Z9.5 Fume Hood Aerodynamics

Face velocity $v_{\text{face}}$ across sash height $h$ and width $W$:
$$v_{\text{face}} = \frac{Q_{\text{exhaust}}}{W \cdot h}$$
Acceptable containment standard: $0.4\text{ m/s} \le v_{\text{face}} \le 0.6\text{ m/s}$ ($80\text{--}120\text{ fpm}$). If $h$ is raised past maximum working height, face velocity drops below $0.3\text{ m/s}$, triggering containment failure warnings and simulated airborne vapor escape.

---

## 7. Canonical Reference Constants Table

| Compound | Formula | $\Delta H^\circ_f$ ($\text{kJ}\cdot\text{mol}^{-1}$) | $S^\circ$ ($\text{J}\cdot\text{mol}^{-1}\cdot\text{K}^{-1}$) | $C_p$ ($\text{J}\cdot\text{mol}^{-1}\cdot\text{K}^{-1}$) | Density ($\text{g}\cdot\text{mL}^{-1}$) |
|---|---|---|---|---|---|
| **Water (l)** | $H_2O$ | $-285.83$ | $69.95$ | $75.38$ | $0.998$ |
| **Water (g)** | $H_2O$ | $-241.83$ | $188.84$ | $33.60$ | $0.0008$ |
| **Hydrochloric acid (aq)** | $HCl$ | $-167.15$ | $56.50$ | $72.00$ | $1.180$ |
| **Sodium hydroxide (aq)** | $NaOH$ | $-469.15$ | $48.10$ | $87.00$ | $1.210$ |
| **Sulfuric acid (l)** | $H_2SO_4$ | $-813.99$ | $156.90$ | $138.90$ | $1.840$ |
| **Salicylic acid (s)** | $C_7H_6O_3$ | $-589.90$ | $183.00$ | $156.00$ | $1.443$ |
| **Acetic anhydride (l)** | $C_4H_6O_3$ | $-648.50$ | $238.00$ | $182.00$ | $1.082$ |
| **Aspirin (s)** | $C_9H_8O_4$ | $-757.90$ | $215.00$ | $220.00$ | $1.400$ |
| **Acetic acid (l)** | $C_2H_4O_2$ | $-484.50$ | $159.80$ | $124.30$ | $1.049$ |
| **4-Aminophenol (s)** | $C_6H_7NO$ | $-179.90$ | $175.00$ | $160.00$ | $1.290$ |
| **Paracetamol (s)** | $C_8H_9NO_2$ | $-450.00$ | $210.00$ | $205.00$ | $1.293$ |

---

## 8. Boundaries & Limitations of Simulation

1. **Relativistic Quantum Mechanics:** Not simulated in real time. Molecular orbitals and UV/Vis absorption spectra are calculated via empirical Beer-Lambert / Kubelka-Munk parameters rather than DFT/ab-initio Schrödinger equations.
2. **Macroscopic CFD:** Multiphase turbulent Navier-Stokes fluid dynamics are replaced with Eulerian compartment liquid levels and SPH visual particle approximations to sustain 60 FPS on 15W Intel Iris Xe graphics.
3. **Safety Prohibitions:** In strict adherence to AI safety guidelines, chemical weapon agents (e.g., Sarin, VX), illicit drug clandestine synthesis routes, and high-order military explosives are explicitly omitted from the accessible reaction database.
