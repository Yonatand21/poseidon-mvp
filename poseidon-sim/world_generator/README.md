# world_generator (Layer 1)

Procedural seeded world generation for mission scenarios.

Outputs are projected to all runtime consumers:

- DAVE/Gazebo artifacts for AUV runtime.
- VRX/Gazebo artifacts for SSV runtime.
- Unreal artifacts for UNav-Sim/PoseidonUE rendering.

## Archetypes

- open_water
- continental_shelf
- littoral
- choke_point
- harbor_approach

## Determinism

Same archetype + params + seed must produce identical output artifacts.

