# Immersive 3D Chemistry Lab — Design Specification

## 1. Executive Summary

Synthesis of best design concepts from Labster, Foldit, ChemCollective, PhET, and RSC Simulations into a unified, actionable specification for an immersive 3D chemistry laboratory.

## 2. Platform Best-Practice Extraction

### 2.1 Labster
- **3D Interactive Models**: Molecular structures, equipment models with realistic physics
- **Realistic Equipment**: Authentic lab equipment (spectrophotometers, titration rigs, fume hoods)
- **Unlimited Play Attempts**: Safe experimentation without real-world consequences
- **Embedded Assessment**: Quiz customization, automated grading
- **Narrative Scaffolding**: Story-driven scenarios with characters and mission framing
- **Equipment Interaction Model**: Click-to-pick, drag-to-place, snap-to-anchor with visual affordances

### 2.2 Foldit
- **Crowdsourcing Core Loop**: Players contribute to real scientific research
- **Scoring System**: Energy-based scoring (Rosetta energy function), higher score = more stable
- **Leaderboards**: Soloist + group (evolver) leaderboards
- **Recipes**: Player-authored automation scripts (procedural macros)
- **Social Layer**: Forums, groups, profiles, chat
- **Tutorial Onboarding**: Progressive skill unlocking
- **Puzzle Difficulty Tiers**: Introductory → Advanced → Expert → Science (real research)
- **Visual Feedback**: Color-coded energy per residue (blue=good, red=bad)

### 2.3 PhET
- **Sandbox-First Design**: No fixed goal; exploration encouraged
- **Layered Complexity**: Checkboxes to show/hide: atoms, bonds, charges, lone pairs, etc.
- **Real-time Visualization**: Instant feedback on changes
- **Macro-Micro Linking**: Connect macroscopic phenomena to molecular view
- **Accessibility**: Screen-reader support, colorblind-safe palettes, keyboard navigation
- **Embeddable**: HTML5 iframe-friendly, works on mobile

### 2.4 ChemCollective
- **Virtual Lab Metaphor**: Drag-and-drop reagents from stockroom to bench
- **Quantitative Focus**: Exact concentrations, volumes, moles calculations
- **Report Generation**: Lab report with data, calculations, conclusions
- **Scenario-Based**: Real-world problem contexts (e.g., "Identify unknown")
- **Free-form Experimentation**: No scripted sequence; student designs procedure

### 2.5 RSC Simulations
- **Curriculum Alignment**: Mapped to specific learning objectives
- **Teacher Dashboard**: Class management, progress tracking
- **Short Form Factor**: 5-15 min activities, modular
- **3D Molecular Viewer**: Rotate, zoom, measure bond lengths/angles
- **Mobile-First**: Touch-optimized

## 3. Unified Design System

### 3.1 Core Interaction Model
```
State Machine: LabState
  - IDLE (nothing selected)
  - SELECTING (hovering pickable)
  - CARRYING (object in hand)
  - PLACING (snap preview)
  - OPERATING (equipment active)
  - OBSERVING (reaction in progress)
  - RECORDING (data capture)
```

### 3.2 Object System (ECS)
```typescript
interface LabEntity {
  id: string;
  type: "reagent" | "equipment" | "sample" | "instrument" | "notebook";
  transform: { position: Vec3; rotation: Quat; scale: Vec3 };
  physics: { mass: number; friction: number; collidable: boolean };
  interactable: { pickupable: boolean; snapPoints: SnapPoint[] };
  chemical?: ChemicalComponent;  // if contains/reagent
  state: Record<string, any>;
}

interface ChemicalComponent {
  formula: string;          // "H2O"
  concentration: number;     // mol/L
  volume: number;           // L
  temperature: number;       // K
  pH?: number;
  phase: "solid" | "liquid" | "gas" | "aqueous";
}
```

### 3.3 Reaction Engine
```typescript
interface Reaction {
  id: string;
  reactants: { species: string; stoich: number }[];
  products: { species: string; stoich: number }[];
  catalysts?: string[];
  conditions: { T_min, T_max, P_min, P_max, pH_min, pH_max };
  rateLaw: (conc: Map<string, number>, T: number) => number;  // mol/L/s
  deltaH: number;  // kJ/mol
  equilibriumK: number;
  visualEffect: "color_change" | "precipitate" | "gas_bubble" | "heat_glow" | "none";
}

// Rate law example: Arrhenius
// k = A * exp(-Ea/(R*T))
// rate = k * [A]^m * [B]^n
```

### 3.4 Scoring (Foldit-inspired)
```
Score = f(energy, accuracy, efficiency, safety)
  energyScore = -E_total (lower energy = better, like Foldit)
  accuracyScore = 100 * (1 - |measured - true|/true)
  efficiencyScore = max(0, 100 - 10 * (steps - optimalSteps))
  safetyScore = 100 - 25 * violations
  total = 0.4*energy + 0.3*accuracy + 0.2*efficiency + 0.1*safety
```

### 3.5 Visual Feedback System
- **Color coding**: Reagent bottles color-coded by hazard class (GHS)
- **Heat map**: Temperature visualization on glassware (thermal camera overlay)
- **Concentration gradient**: Color intensity in solutions
- **Reaction progress**: Animated particles, color transitions
- **Safety indicators**: Red glow for spills, ventilation indicators for fumes

## 4. Data Structures

### 4.1 Lab Session
```json
{
  "sessionId": "uuid",
  "userId": "uuid",
  "scenario": { "id": "titration-acid-base", "objectives": [...] },
  "entities": [LabEntity],
  "reactions": [Reaction],
  "measurements": [{ "time": 0, "instrument": "ph_meter", "value": 7.0 }],
  "score": { "energy": 0, "accuracy": 0, "efficiency": 0, "safety": 0 },
  "hints": [{ "trigger": "no_progress_30s", "text": "..." }]
}
```

### 4.2 Molecule Data (SMILES → 3D)
```typescript
interface Molecule {
  smiles: string;
  atoms: { element: string; position: Vec3 }[];
  bonds: { from: number; to: number; order: 1|2|3 }[];
  energy: number;  // kJ/mol (MMFF94)
  properties: { mw, logP, tpsa, hDonors, hAcceptors };
}
```

## 5. Code Patterns

### 5.1 React Three Fiber Lab Scene
```tsx
import { Canvas } from "@react-three/fiber";
import { OrbitControls, useGLTF } from "@react-three/drei";

function LabScene({ entities }) {
  return (
    <Canvas camera={{ position: [0, 1.6, 3], fov: 60 }}>
      <ambientLight intensity={0.4} />
      <directionalLight position={[5,5,5]} intensity={0.8} />
      <LabBench />
      {entities.map(e => <LabEntity key={e.id} entity={e} />)}
      <OrbitControls minDistance={1} maxDistance={8} />
    </Canvas>
  );
}
```

### 5.2 Drag-and-Drop with Drei
```tsx
import { useDrag } from "@use-gesture/react";
const bind = useDrag(({ offset }) => {
  entity.transform.position = offset;
  checkSnapPoints(entity);
});
```

### 5.3 Reaction Tick (Web Worker)
```typescript
// worker.ts
self.onmessage = ({ data }) => {
  const { entities, dt } = data;
  const reactions = detectReactions(entities);
  reactions.forEach(r => advanceReaction(r, dt));
  self.postMessage({ entities, measurements });
};
```

## 6. Accessibility & Inclusivity
- Colorblind-safe palette (Okabe-Ito)
- Keyboard navigation: Tab between interactables, Space to pick/place
- Screen reader: ARIA labels on all entities, live regions for reactions
- Reduced motion: respect prefers-reduced-motion
- Text scaling: UI scales to 200%

## 7. Performance Budget
- Target: 60fps on mid-range laptop (integrated GPU)
- Max triangles: 500k scene total
- Texture budget: 256MB
- LOD: 3 levels per complex model
- Instancing for repeated objects (test tubes, atoms)

## 8. Assessment Integration
- xAPI statements: "completed", "interacted", "scored"
- LTI 1.3 for LMS integration
- Export: CSV of all measurements, PDF lab report

## 9. Recommended Tech Stack
- Frontend: React + Three.js (R3F) + Drei
- State: Zustand + Immer
- Chemistry: RDKit.js (WASM) for SMILES parsing, molecule rendering
- Physics: Rapier (WASM) for rigid body
- Backend: Node.js + PostgreSQL (session persistence)
- Real-time: WebSocket for multiplayer/collab
- Auth: Clerk or Auth0

## 10. MVP Scope (Phase 1)
1. Single bench scene with 5 equipment types
2. 3 reaction types (acid-base, precipitation, gas evolution)
3. Drag-drop reagent system
4. Measurement instruments (pH, thermometer, balance)
5. Basic scoring + lab report export
6. 2 scenarios: "Identify unknown salt", "Titration curve"

## Sources
- Labster: https://www.labster.com/
- Foldit: https://fold.it/
- PhET: https://phet.colorado.edu/
- ChemCollective: https://chemcollective.org/
- RSC: https://www.rsc.org/
