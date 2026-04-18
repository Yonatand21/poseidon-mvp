# vehicles

Per-vehicle CAD artifacts and runtime configs. Large binary files in this
tree are routed through Git LFS - see the top-level `.gitattributes`.

**Design reference:** `SYSTEM_DESIGN.md` Section 6 (Vehicle modeling and
CAD pipeline).

## Layout (per vehicle)

```
vehicles/<vehicle_id>/
  source/
    assembly.step            # SolidWorks export, AP214
    mass_properties.yaml     # mass, center of mass, 3x3 inertia tensor
    frames.yaml              # named reference frames per thruster/fin/sensor mount
  meshes/
    visual.gltf              # 50-200K triangles, LODs, textured
    collision.obj            # 2-5K triangles, V-HACD decomposed
    hydrodynamic.obj         # watertight, 5-20K triangles, for Stonefish
  config/
    vehicle.stonefish.xml    # Stonefish scene fragment
    vehicle.urdf             # ROS 2 URDF
    thrusters.yaml           # per-thruster placement, thrust curves
    sensors.yaml             # sensor suite, mounting, fidelity tier
    nav_config.yaml          # IMU grade, DVL mode, USBL enabled, TAN enabled
```

## Golden rule

**Extract mass from SolidWorks, not from meshes.** `mass_properties.yaml`
is the single source of truth for mass, CoM, and inertia.

## Vehicles

| Id | Role | Status |
| --- | --- | --- |
| `auv_surveyor/` | AUV payload for the hero choke-point scenario. | Placeholder. First real pass lands in Week 2 per `SYSTEM_DESIGN.md` Section 18.3. |
| `ssv_mothership/` | Surface support vessel carrying the AUV. | Placeholder. First real pass lands in Week 2-3. |

Until real CAD lands, scenarios reference stock Stonefish Girona500 and a
stock surface vessel (or borrowed VRX WAM-V coefficients) per the 24-hour
sprint scope cuts in `SYSTEM_DESIGN.md` Section 18.2.1.
