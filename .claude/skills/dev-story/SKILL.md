---
name: dev-story
description: ChemLab Feature Development Workflow. Decomposes experimental laboratory features into actionable, verifiable multi-agent user stories with physical requirements, apparatus specs, and acceptance criteria.
---

# ChemLab Feature Development Story Protocol (/dev-story)

Use this skill when initiating or breaking down any feature, laboratory apparatus, or chemical experiment in ChemLab. It ensures that every feature has unambiguous scientific backing, 3D asset specifications, and verifiable acceptance criteria before code is written.

## Story Structure Template

When creating a new feature story, formulate it using this mandatory structure:

```markdown
# STORY-[ID]: [Title: e.g., Belousov-Zhabotinsky Reaction in Petri Dish]

## 1. Feature Intent & Scientific Grounding
- **User Experience**: What does the player observe and interact with?
- **Governing Equations**: List all chemical rate laws, ODEs, or physical formulas.
- **Stoichiometry & Kinetics**: Reagents, catalysts, rate constants, temperature limits.

## 2. Multi-Agent Task Allocations
- **Physics Lead**: Implement numerical solver, ODE integration, and kinetic state machine.
- **Graphics Lead**: Model 3D mesh, apply borosilicate glass/fluid shaders, tune EEVEE lighting.
- **Input Specialist**: Define hand gestures (pipette dispensing, stirring, dish tilting).
- **QA Lead**: Author headless Blender assertions and numerical stability unit tests.

## 3. Asset & Performance Budget (Intel Iris Xe)
- **Target Collection**: `04_Apparatus_Chemicals` (or appropriate collection).
- **Vertex / Triangle Limit**: (e.g. $\le 3,500$ triangles).
- **Texture / Material Count**: Maximum 1 shared material or procedural node setup $\le 30$ nodes.
- **Draw Call Impact**: $\le 2$ draw calls.

## 4. Acceptance Criteria (DoD - Definition of Done)
- [ ] Reaction equations integrate stably without NaN or runaway values over 10,000 steps.
- [ ] 3D models conform to `/design-system` physical dimensions and IOR standards.
- [ ] Automated headless test in `tests/` passes with 0 warnings.
- [ ] Live preview updates over `blender_client.py` without socket disconnections.
- [ ] Framerate benchmark confirms $\ge 50$ FPS on Intel Iris Xe.
```

## Workflow Execution Steps
1. **Story Elaboration**: Game Director drafts the story and validates resource budgets.
2. **Parallel Implementation**:
   - Physics Lead produces the kinetic solver module (`scripts/kinetics_<reaction>.py`).
   - Graphics Lead constructs or updates Blender geometry (`scripts/module_<apparatus>.py`).
   - Input Specialist updates interaction bindings.
3. **Integration**: Link state variables via `blender_client.py` to live viewport properties.
4. **Trigger Verification**: Invoke `/quality-gate` once implementation is complete.
