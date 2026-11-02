# GitHub Chemistry Simulation / Molecular Visualization / Lab-Game — Integration Spec

Target project: ChemLab (interactive virtual chemistry lab, Blender 5.2 + MediaPipe hand tracking + HTML/JS dashboard, Python 3.12, Windows 11, i5-1240U / Iris Xe).

## Top 20 Repositories + Integration Notes

1. **3Dmol.js** — https://github.com/3dmol/3Dmol.js
   - Purpose: WebGL molecular viewer (PDB/mmCIF/SDF/SMILES input).
   - Integration: Drop-in `<script>` in `gallery.html` dashboard; render molecules via `viewer.addModel(data,"pdb")`. License MIT.
   - Data flow: Blender exports PDB of equipment; 3Dmol renders overlays.

2. **NGL (nglviewer)** — https://github.com/nglviewer/ngl
   - Purpose: High-performance WebGL molecular graphics (protein/ligand).
   - Integration: ES module import; `new NGL.Stage("viewport")`; supports trajectory (MDAnalysis). Good for reaction-mechanism walkthroughs.
   - Pattern: `stage.loadFile("mol.sdf", {defaultRepresentation:true})`.

3. **RDKit (rdkit/rdkit)** — https://github.com/rdkit/rdkit
   - Purpose: Cheminformatics toolkit (SMILES, fingerprints, 2D/3D coords, reactions).
   - Integration: Python side via `rdkit` pip; generate 3D conformers (`AllChem.EmbedMolecule`), export SDF to 3Dmol. Used in `chemlab_core/models.py` for substance definitions.
   - Equation: ETKDGv3 conformer generation; MMFF94 optimization.

4. **Open Babel (openbabel/openbabel)** — https://github.com/openbabel/openbabel
   - Purpose: File-format conversion (SMILES↔PDB↔MOL2↔CIF).
   - Integration: CLI `obabel -i smi -o pdb` in build pipeline; Python bindings for runtime conversion.

5. **MDAnalysis (MDAnalysis/mdanalysis)** — https://github.com/MDAnalysis/mdanalysis
   - Purpose: Molecular dynamics trajectory analysis.
   - Integration: Load GROMACS/AMBER trajectories for replaying reactions; compute RMSD, RDF. Feeds 3Dmol/NGL animation frames.

6. **chemlab (chemlab/chemlab)** — https://github.com/chemlab/chemlab
   - Purpose: Python chemistry lab simulation framework (glassware, solutions, reactions).
   - Integration: Reuse `chemlab.core.Substance`, `Experiment` abstractions; port reaction templates to `chemlab_core`.

7. **chempy (bjodah/chempy)** — https://github.com/bjodah/chempy
   - Purpose: Chemical kinetics, equilibrium, thermodynamics.
   - Integration: Solve ODE kinetics for Brigg-Rauscher oscillation; `chempy.kinetics` rate laws. Exact: d[species]/dt = sum stoichiometric*rate.

8. **PySCF (pyscf/pyscf)** — https://github.com/pyscf/pyscf
   - Purpose: Quantum chemistry (HF, DFT).
   - Integration: Optional high-fidelity property calc for substance database; too heavy for real-time — precompute.

9. **Mol* (molstar/molstar)** — https://github.com/molstar/molstar
   - Purpose: Modern WebGL molecular viewer (used by PDB).
   - Integration: React/TS component for web dashboard; supports volume rendering of electron density.

10. **Speck (tylerjered/speck)** — https://github.com/tylerjered/speck
    - Purpose: WebGL 3D molecular editor/viewer (Three.js based).
    - Integration: Embeddable viewer with editing; good for sandbox "build your molecule" mode.

11. **Miew (miewjs/miew)** — https://github.com/miewjs/miew
    - Purpose: 3D molecular viewer (WebGL, mmCIF/PDB).
    - Integration: Lightweight alternative to NGL for dashboard.

12. **Kekule.js (partridgejiang/Kekule.js)** — https://github.com/partridgejiang/Kekule.js
    - Purpose: JavaScript cheminformatics (2D structure editor, 3D viewer, reactions).
    - Integration: In-browser structure drawing + SMILES parse; no backend needed.

13. **ChemDoodle (iChemLabs/ChemDoodleWeb)** — https://github.com/iChemLabs/ChemDoodleWeb
    - Purpose: 2D/3D molecular graphics in browser.
    - Integration: UI components for formula rendering and 2D previews.

14. **molecular-dynamics (various: indosyn/MolecularDynamics)** — ReaxFF force field in JS.
    - Integration: Browser-side MD for small systems; educational demos.

15. **OpenMM (openmm/openmm)** — https://github.com/openmm/openmm
    - Purpose: GPU-accelerated MD.
    - Integration: Python backend for accurate dynamics; stream frames to frontend.

16. **GROMACS (gromacs/gromacs)** — https://github.com/gromacs/gromacs
    - Purpose: MD engine.
    - Integration: Precompute trajectories; not real-time.

17. **Blender (blender/blender)** + **bpy** — https://github.com/blender/blender
    - Purpose: 3D asset creation (already used).
    - Integration: Python `bpy` scripts export glTF/PDB; live bridge already in repo (`blender_live_bridge.py`).

18. **MediaPipe (google/mediapipe)** — https://github.com/google/mediapipe
    - Purpose: Hand tracking (already used).
    - Integration: Existing; 21 landmarks @60fps.

19. **OpenCV (opencv/opencv)** — https://github.com/opencv/opencv
    - Purpose: Computer vision.
    - Integration: Already via Python; color detection for reaction colorimetry.

20. **FastAPI (tiangolo/fastapi)** — https://github.com/tiangolo/fastapi
    - Purpose: WebSocket/HTTP server for dashboard.
    - Integration: Replace `http.server` with FastAPI + WebSocket for real-time state sync between Blender/Python and browser.

## Integration Architecture

```
Blender 5.2 (assets) --glTF/PDB--> Python core (rdkit/chempy/OpenMM)
   |                                   |
   | MediaPipe hands (60fps)            v
   +---> TCP socket 127.0.0.1:8765 ---> FastAPI WS ---> Browser dashboard
                                                (3Dmol/NGL/Mol*/Kekule)
```

## Data Structures

```python
@dataclass
class Substance:
    id: str
    name: str
    formula: str
    smiles: str
    color_rgb: tuple[float,float,float]
    density_g_ml: float
    molar_mass_g_mol: float
    ph: float | None
    hazard_ghs: list[str]

@dataclass
class Reaction:
    reactants: list[tuple[Substance, float]]  # (substance, moles)
    products: list[tuple[Substance, float]]
    rate_law: Callable[[dict], float]
    delta_h_kj: float
    color_change: tuple | None
```

## Key Equations

- Neutralization: H+ + OH- -> H2O, ΔH = -55.8 kJ/mol
- Brigg-Rauscher oscillation: IO3- + 2H2O2 + CH2(COOH)2 + H+ -> ICH(COOH)2 + 2O2 + 3H2O (rate via FKN mechanism)
- Beer-Lambert: A = ε·c·l (colorimetry)
- Ideal gas: PV = nRT (gas volume effects)
- Arrhenius: k = A·exp(-Ea/RT) (temperature dependence)

## Recommended First Integrations (priority order)

1. RDKit (substance model + 3D conformers) — backend.
2. 3Dmol.js (molecular overlays in dashboard) — frontend.
3. chempy (kinetics for oscillation) — simulation.
4. FastAPI+WebSocket (replace http.server) — transport.
5. Kekule.js (in-browser structure editor) — sandbox mode.
