# Session Subagent Cost

**Session:** `b2728aaf-c88c-4517-9396-0d681b64ce96`  
**Updated:** 20261110_190332

Subagent spawns this session: **11**

| Agent | Spawns |
|-------|--------|
| workflow-subagent | 10 |
| lead-programmer | 1 |

Each spawn is a fresh context window that re-reads its own inputs.
To reduce this: lower `modes.review_mode` (`/settings modes.review_mode=solo`)
or `modes.rigor` (`/settings modes.rigor=minimal`).
