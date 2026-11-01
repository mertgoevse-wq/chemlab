---
name: story-done
description: ChemLab Story Completion Protocol. Verifies Definition of Done (DoD), runs multi-agent sign-offs, checks asset budgets, and persists state into chemlab.blend before closing tasks.
---

# ChemLab Story Completion Protocol (/story-done)

Use this skill when closing a development story or submitting a major asset/feature to the project. No story is marked completed without passing all verification gates defined here.

## 1. Multi-Disciplinary Sign-Off Checklist

Before declaring a story done, verify each discipline's contribution:

### A. Physics & Chemical Fidelity (Physics Lead Sign-Off)
- [ ] Stoichiometric balance verified ($|\sum \Delta m| < 10^{-6}$).
- [ ] No unbounded divergence or numerical instability under variable $\Delta t \in [0.001, 0.05]\text{s}$.
- [ ] Visual indicators correlate accurately with pH and concentration state machines.

### B. Graphics & Material Hygiene (Graphics Lead Sign-Off)
- [ ] Glassware conforms to Borosilicate IOR `1.474` and thickness specifications.
- [ ] Normals are recalculate-outside, transforms applied ($1.0, 1.0, 1.0$ scale).
- [ ] Object origins are anchored to realistic pivot points.
- [ ] Node setups contain no unlinked sockets or dead nodes.

### C. Input & Interaction (Input Specialist Sign-Off)
- [ ] 3D interaction bounding boxes match physical meshes.
- [ ] Smoothing filters (1-Euro) active to prevent jitter during manipulation.
- [ ] Mouse/keyboard fallback fully operational.

### D. Quality Assurance & Performance (QA Lead Sign-Off)
- [ ] Headless Blender test passes: `python tests/headless_blender_test.py`.
- [ ] Asset validation passes: `python tests/validate_scene_assets.py`.
- [ ] Total scene polygon and VRAM budgets within Intel Iris Xe limits.

## 2. Automated Persistence & Blend File Commit
1. Save the active Blender scene state:
   ```bash
   python "C:/Users/Win11 Pro/Desktop/chemlab/blender_client.py" --save
   ```
2. Verify that `chemlab.blend` has been updated and no backup file conflicts remain.
3. Commit changes using conventional commit conventions:
   - `feat(kinetics): ...`
   - `feat(assets): ...`
   - `fix(materials): ...`
