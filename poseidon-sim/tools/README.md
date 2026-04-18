# tools

Developer-facing tools. Not part of the runtime; used to prepare inputs to
the simulation.

**Design reference:** `SYSTEM_DESIGN.md` Section 6 (CAD pipeline),
Section 5.1 (archetype preview).

## Subdirs

| Dir | Purpose |
| --- | --- |
| `cad_pipeline/` | Scripts that convert SolidWorks STEP exports + mass properties into visual / collision / hydrodynamic meshes and the Stonefish vehicle XML. Uses Blender, V-HACD, trimesh. |
| `archetype_preview/` | CLI to render a generated archetype heightfield + traffic + obstacles as a 2D map for sanity-check before running a full scenario. |
