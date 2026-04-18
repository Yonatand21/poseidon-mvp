# vehicles

Vehicle artifacts and runtime configs.

Current strategy: start from DAVE/VRX vehicle assets, then incrementally replace with project-owned CAD/config assets.

## Layout (per vehicle)

```text
vehicles/<vehicle_id>/
  source/
    assembly.step
    mass_properties.yaml
    frames.yaml
  meshes/
    visual.gltf
    collision.obj
    hydrodynamic.obj
  config/
    vehicle.dave.yaml
    vehicle.vrx.yaml
    vehicle.urdf
    thrusters.yaml
    sensors.yaml
    nav_config.yaml
```

## Golden rules

- Mass/inertia come from versioned source data, not inferred ad hoc from render meshes.
- Runtime-specific configs are generated from shared canonical metadata where possible.
- Every imported upstream asset records source repo, revision, and license.
