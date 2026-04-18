# Pull Request

## Summary

<!-- One or two sentences: what does this change and why. Link to the design
section it implements or the issue it fixes. -->

## Design reference

<!-- SYSTEM_DESIGN.md section, OPEN_SOURCE_STACK.md entry, or
INFRASTRUCTURE_DESIGN.md section this change aligns with. -->

## Layer(s) touched

- [ ] Layer 1 - Deterministic simulation truth
- [ ] Layer 2 - Classical control and safety
- [ ] Layer 3 - AI augmentation (advisory only)
- [ ] Layer 4 - Evaluation (offline)
- [ ] Scenario engine / orchestration
- [ ] Infrastructure (containers, charts, CI)
- [ ] Documentation only

## AGENTS.md invariants

- [ ] Layer separation preserved. Layer 3 does not publish actuator topics.
- [ ] Layer 2 has a fallback for any new Layer 3 advisory.
- [ ] Safety invariants in `autonomy_*/safety_invariants` are unconditional.
- [ ] Ground-truth `/auv/state` and `/ssv/state` not consumed outside evaluation.
- [ ] Determinism preserved (`ai_mode: off` still produces bit-identical outputs
      for a given seed).
- [ ] No runtime network fetches added (apt, pip, model hub).
- [ ] No emojis in code.

## Profile support

- [ ] Profile A (Dev / Demo, Ubuntu 24.04 + Jazzy) tested or not applicable.
- [ ] Profile B (Edge / Mission, Ubuntu 22.04 + Humble) tested or not applicable.

## Test plan

<!-- Manual steps, scenarios run, seeds used, expected vs. observed metrics. -->

## Risk

<!-- What can this break? What is the rollback path? -->
