# Biochemical Pathway Simulation — Design Specification

## 1. Scope
Real-time, interactive simulation of enzyme kinetics, central carbon metabolism
(glycolysis + Krebs/TCA cycle), and protein folding, rendered as an extension of
the ChemLab immersive 3D lab. Targets 60 fps on integrated GPU, educational +
research-grade accuracy.

## 2. Enzyme Kinetics

### 2.1 Michaelis–Menten (Briggs–Haldane steady state)
```
E + S ⇌[k1][k-1] ES →[kcat] E + P
v = d[P]/dt = (Vmax [S]) / (Km + [S])
Vmax = kcat [E]T
Km = (k-1 + kcat) / k1
```
Unit check: v in mol·L⁻¹·s⁻¹; Km in mol·L⁻¹.

### 2.2 Hill (cooperative / allosteric)
```
v = Vmax [S]^n / (K0.5^n + [S]^n)
```
n = Hill coefficient (>1 positive cooperativity, <1 negative).

### 2.3 Inhibition models
- Competitive:     v = Vmax[S]/(Km(1+[I]/Ki)+[S]);  Vmax unchanged, Km↑
- Uncompetitive:   v = Vmax[S]/(Km+[S](1+[I]/Ki));  Vmax↓, Km↓
- Non-competitive: v = Vmax[S]/((Km+[S])(1+[I]/Ki)); Vmax↓, Km unchanged
- Mixed:           v = Vmax[S]/(Km(1+[I]/Ki)+[S](1+[I]/Ki'));  both Vmax,Km change
- Substrate inhibition: v = Vmax[S]/(Km+[S]+[S]²/Ksi)

### 2.4 Allosteric (MWC concerted model)
```
R0 ⇌ T0  (L = [T0]/[R0])
Y = ( (1+α)^n + L c^n (1+cα)^n? ... ) / ( (1+α)^n + L(1+cα)^n )
α = [S]/K_R,  c = K_R/K_T
```
Use Monod-Wyman-Changeux with n protomers.

### 2.5 Temperature / pH dependence
```
k(T) = A exp(-Ea/(R T))          # Arrhenius
k_pH = k_opt * 10^(-|pH-pHopt|)  # bell curve via two ionizable groups
pH profile: k = kmax / (1 + 10^(pKa1-pH) + 10^(pH-pKa2))
```

### 2.6 Stochastic regime (low copy numbers)
Gillespie SSA: propensity a_j = c_j ∏ x_i^{ν_ij}; τ = (1/a0) ln(1/r1);
select reaction j with cumulative a. Use for single-cell / organelle scale.

## 3. Metabolic Pathways

### 3.1 Glycolysis (10 reactions)
| # | Reaction | Enzyme | ΔG°' (kJ/mol) |
|---|----------|--------|---------------|
| 1 | Glc + ATP → G6P + ADP | Hexokinase | -16.7 |
| 2 | G6P ⇌ F6P | PGI | +1.7 |
| 3 | F6P + ATP → F1,6BP + ADP | PFK-1 | -14.2 |
| 4 | F1,6BP ⇌ DHAP + GAP | Aldolase | +23.8 |
| 5 | DHAP ⇌ GAP | TPI | +7.5 |
| 6 | GAP + Pi + NAD+ → 1,3BPG + NADH + H+ | GAPDH | +6.3 |
| 7 | 1,3BPG + ADP → 3PG + ATP | PGK | -18.8 |
| 8 | 3PG ⇌ 2PG | PGM | +4.4 |
| 9 | 2PG → PEP + H2O | Enolase | +1.7 |
|10 | PEP + ADP → Pyr + ATP | Pyruvate kinase | -31.4 |

Net: Glc + 2 NAD+ + 2 ADP + 2 Pi → 2 Pyr + 2 NADH + 2 H+ + 2 ATP + 2 H2O.

### 3.2 Krebs (TCA) cycle (8 reactions)
Acetyl-CoA + 3 NAD+ + FAD + GDP + Pi + 2 H2O → 2 CO2 + 3 NADH + FADH2 + GTP + 2 H+ + CoA.

Steps: citrate synthase, aconitase, isocitrate dehydrogenase, α-KG dehydrogenase, succinyl-CoA synthetase, succinate dehydrogenase, fumarase, malate dehydrogenase.

### 3.3 Dynamics (ODE)
For species vector x ∈ ℝⁿ:
```
dx_i/dt = Σ_j S_ij v_j(x, p)   # stoichiometric matrix S (m×n) × flux v
```
Integrate with RK4 or adaptive (Dormand-Prince) in Web Worker; dt default 0.01 s sim,
scaled by time controller (0.1×–10×).

### 3.4 Regulation
- PFK-1: activated by AMP/F2,6BP, inhibited by ATP/citrate.
- Pyruvate kinase: activated by F1,6BP, inhibited by ATP/alanine.
- PDH: inhibited by acetyl-CoA/NADH; activated by Ca²⁺/insulin.
- TCA: isocitrate DH inhibited by NADH/ATP; activated by ADP/Ca²⁺.
Model via Hill modifiers multiplying base v.

### 3.5 Flux Balance (steady-state analysis)
Maximize cᵀv s.t. Sv=0, v_min ≤ v ≤ v_max (linear programming). Use for
yield prediction and gene-knockout (FBA) scenarios.

## 4. Protein Folding Visualization

### 4.1 Thermodynamics
```
ΔG = ΔH - TΔS
Native state = global minimum of Gibbs free energy (Anfinsen).
Folding funnel: energy decreases, conformational entropy decreases,
hydrophobic burial drives collapse.
```

### 4.2 Energy function (Rosetta-like, simplified)
```
E = E_vdw + E_elec + E_hbond + E_solv + E_ramachandran + E_rotamer
```
Per-residue color: blue (favorable, E<0) → red (unfavorable, E>0), Foldit style.

### 4.3 Lattice HP model (educational)
2D/3D square/cubic lattice; H (hydrophobic) contacts gain -1; maximize H-H contacts.
Monte Carlo: Metropolis, T controls acceptance. Visualize collapse.

### 4.4 Molecular dynamics (coarse-grained)
- Bead-spring (Cα model): bonds, angles, dihedrals, Lennard-Jones, electrostatics.
- Integrator: Velocity Verlet; timestep 10 fs; thermostat (Berendsen/Langevin).
- Secondary structure: DSSP assignment (H/E/C/T/G/B/S/I).

### 4.5 Visualization modes
- Ribbon (cartoon), backbone trace, ball-and-stick, surface (MSMS/SAS).
- Ramachandran plot (φ,ψ) with allowed regions.
- Contact map (residue i vs j distance < 8 Å).
- Folding trajectory: RMSD vs native, radius of gyration Rg, energy vs time.
- Hydrogen-bond network overlay; disulfide bridges.

## 5. Data Structures

```typescript
interface Species { id: string; name: string; compartment: string; }
interface Reaction {
  id: string; reactants: { species: string; coeff: number }[];
  products: { species: string; coeff: number }[];
  enzymes: string[]; reversible: boolean;
  rateLaw: (x: Map<string, number>, p: Params, T: number, pH: number) => number;
  deltaG0: number; // kJ/mol
}
interface Pathway { id: string; species: Species[]; reactions: Reaction[]; }
interface Enzyme {
  id: string; name: string; ec: string; km: number; kcat: number; vmax: number;
  inhibitors: { id: string; ki: number; mode: "competitive"|"uncompetitive"|"noncompetitive"|"mixed" }[];
  allosteric: { n: number; L: number; c: number } | null;
  pHopt: number; pKa1: number; pKa2: number; Ea: number; // kJ/mol
}
interface Protein {
  sequence: string; // amino acids
  structure: { atoms: { element: string; pos: Vec3; residue: number }[];
              bonds: { a: number; b: number }[];
              ss: ("H"|"E"|"C"|"T")[]; };
  energy: number;
}
interface SimState {
  pathway: Pathway; x: Map<string, number>; t: number; dt: number;
  temperature: number; pH: number; volume: number;
  history: { t: number; x: Record<string, number> }[]; // for plots
}
```

Python (Pydantic) mirrors with `numpy.ndarray` for x and Jacobian.

## 6. Code Patterns

### 6.1 ODE integration (Web Worker)
```ts
// worker.ts
self.onmessage = ({ data }) => {
  const { x, t, dt, pathway, params } = data;
  const dx = (s: number[]) => pathway.reactions.reduce((acc, r) => {
    const v = r.rateLaw(toMap(s), params, T, pH);
    r.reactants.forEach(({species,coeff}) => acc[id(species)] -= coeff*v);
    r.products.forEach(({species,coeff}) => acc[id(species)] += coeff*v);
    return acc;
  }, new Array(n).fill(0));
  // RK4
  const k1=dx(x), k2=dx(add(x,scale(k1,dt/2))), ...;
  const xn = add(x, scale(add(k1,scale(k2,2),scale(k3,2),k4), dt/6));
  self.postMessage({ x: xn, t: t+dt, measurements });
};
```

### 6.2 3D pathway graph (R3F)
Nodes = metabolites (spheres, size ∝ concentration), edges = reactions (tubes,
thickness ∝ flux, animated particles along direction). Color by ΔG (exergonic
blue → endergonic red). Click node → concentration time series panel.

### 6.3 Protein viewer (R3F + Drei)
Load PDB → parse atoms → render cartoon via spline (Catmull-Rom) through Cα;
per-residue color by energy or secondary structure (helix red, sheet blue, coil gray).
Animate folding: interpolate between unfolded (extended) and native coords using
MD trajectory; show Rg and RMSD sparklines.

### 6.4 State (Zustand)
```ts
const useSim = create((set) => ({
  state: initialSimState, running: false,
  step: (dt) => set(s => ({ state: integrate(s.state, dt) })),
  setParam: (id, v) => set(s => mutateParam(s, id, v)),
}));
```

## 7. Rendering & Performance
- Instanced spheres for atoms (max 50k); LOD for proteins > 2000 residues.
- Particle system for metabolite flow (GPU instancing).
- OffscreenCanvas + Web Worker for ODE + MD.
- Budget: scene ≤ 500k tris, texture ≤ 256 MB.

## 8. Assessment / Scenarios
- "Predict Km from Lineweaver-Burk plot" (fit v vs [S]).
- "Identify rate-limiting step in glycolysis" (flux control coefficients).
- "Fold a 36-residue protein; reach RMSD < 2 Å."
- xAPI + LTI 1.3; export CSV of trajectories.

## 9. Tech Stack
Frontend: React + R3F + Drei + Zustand + Immer; Chemistry: RDKit.js (WASM),
OpenMM (WASM) optional; Plots: Recharts; Backend: FastAPI + PostgreSQL;
MD: OpenMM or custom Cα (WASM). PDB/mmCIF parser (mmcif.js).

## 10. MVP (Phase 1)
1. Michaelis-Menten interactive curve (v vs [S], inhibitor toggles).
2. Glycolysis ODE with 10 reactions, concentration plots.
3. Krebs cycle steady-state flux.
4. Protein: load PDB, cartoon render, Ramachandran, Rg plot.
5. 2 scenarios: enzyme inhibition; glycolysis regulation by ATP/AMP.

## 11. Validation
- Unit tests: rate laws vs analytic (MM), ODE conservation (mass balance), FBA.
- Reference: compare glycolysis metabolite levels to published steady states.
- MD: energy drift < 0.1% over 1 ns.
- Accessibility: colorblind-safe (Okabe-Ito), keyboard nav, screen-reader labels.
