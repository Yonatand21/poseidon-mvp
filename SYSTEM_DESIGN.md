# POSEIDEN MVP - Maritime Test and Evaluation Environment

## One-line framing

A software-based maritime test environment for evaluating AUV and SSV performance across controllable ocean and navigation conditions - including GNSS-denied and contested environments - with classical control, AI augmentation, and AI-driven evaluation, producing repeatable virtual trials that reduce field-test cycles before deployment.

---

## 1. System goal

The platform lets a team:

- Define a parameterized maritime mission environment (bathymetry archetype, sea state, current, visibility, GNSS mode, acoustic environment).
- Place a custom-modeled AUV and SSV into that environment.
- Run a meshed mission where the SSV carries the AUV, transits to a release point, drops the AUV, the AUV executes its mission, and the SSV loiters in overwatch.
- Repeat that mission deterministically across seeds and condition sweeps.
- Augment classical autonomy with safety-sandboxed AI for perception, planning, risk prediction, and anomaly detection.
- Produce measurable outputs: mission success, path error, station-keeping quality, energy use, sensor availability, navigation quality, time-to-detect denial/spoofing, position uncertainty cascades, and AI-generated failure analyses across scenario sweeps.

The headline capability is **repeatable virtual test-and-evaluation under controllable ocean and navigation conditions, with AI augmentation layered on top of a deterministic classical core**, not photorealistic simulation of a specific geography.

---

## 2. Capability headlines (what the demo leads with)

The headlines below describe the full architectural vision. The 24-hour hackathon sprint (Section 18.2) delivers a vertical slice that demonstrates each of them in minimum form; post-hackathon weeks expand each to full capability. Section 17 defines the two runtime profiles (Development/Demo and Edge/Mission) the architecture supports.

1. **Controllable ocean and navigation environment.** Sea state 1-6, current 0-3 m/s with multiple profiles, visibility tiers, GNSS mode (nominal / degraded / jammed / spoofed / denied / intermittent), acoustic-nav infrastructure quality, sound speed profile, five bathymetry archetypes.
2. **GNSS-denied and contested operations.** Full navigation-cascade modeling: SSV GNSS degradation propagates to AUV via USBL; AUV operates on INS + DVL + TAN + acoustic aiding when denied.
3. **Repeatable virtual trials.** Seeded scenarios, deterministic replay, MCAP recordings.
4. **Measurable evaluation outputs.** Mission success, trajectory error, nav-mode transitions, time-to-detect denial, time-to-detect spoofing, position uncertainty growth, USBL fix availability, DVL bottom-lock availability.
5. **Meshed AUV + SSV mission.** One scenario clock, shared environment, drop handoff from SSV to AUV, acoustic comms pipe between them.
6. **AI augmentation, safely sandboxed.** Perception, mission planning, risk prediction, and anomaly detection as advisory inputs to a classical-authoritative control stack. Never in the actuator path.
7. **AI-driven evaluation.** Log mining, failure clustering, scenario-coverage recommendation, and LLM-generated performance summaries across scenario sweeps.
8. **Adaptable fidelity.** Fast design mode, medium evaluation mode, visual demo mode.

---

## 3. Top-level architecture

```
                          Scenario Engine (Python)
                                   |
            reads YAML, generates scene, launches ROS 2 graph,
              ticks mission phases, records MCAP
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
    Layer 1:                  Layer 2:                  Layer 3:
    Stonefish (ROS 2)         Classical stack           AI augmentation
    - AUV + SSV physics       - nav fusion              - perception
    - shared ocean env        - classical control       - planning
    - bathymetry archetype    - safety / failsafes      - risk prediction
    - sensor simulation       - geofence / abort        - anomaly detection
    - wave / current / wind   - nav-mode state machine  advisory only
         |                         |                         |
         +-----> Unreal viz <------+-------------------------+
                         |
                  MCAP recorder
                         |
                  Layer 4: Evaluation AI
                  - metrics, plots, reports (Foxglove)
                  - log mining, failure clustering
                  - scenario recommendation, summaries
```

Key design decisions:

- **Four-layer stratification.** Deterministic simulation truth, classical control and safety, AI augmentation, AI evaluation. The layering is the safety architecture - it is not just organizational.
- **One Stonefish instance runs both vehicles.** Shared world, shared ocean, shared clock, free coupling.
- **ROS 2 Jazzy** on Ubuntu 24.04 is the messaging backbone.
- **Unreal is a consumer only** - it receives vehicle and environment state, renders. It never owns physics.
- **MCAP** for all recording; replayable in Foxglove and ROS 2 tooling.
- **YAML** for scenario files; scenario engine generates Stonefish XML and launches the ROS 2 graph.
- **Python** for scenario engine, evaluation, and AI. **C++** only inside Stonefish plugins or performance-critical sensor models.

---

## 4. Four-layer architecture

The platform is stratified into four layers with strict separation of concerns. Layers never bypass each other. This stratification is what makes AI augmentation safe and credible in a test-and-evaluation context.

### 4.1 Layer 1 - Deterministic simulation truth

**Responsibility.** Produce ground-truth world and sensor state that is seed-deterministic and reproducible.

**Modules.** Physics engine (Stonefish), environment service (ocean forcing, bathymetry archetype, acoustic environment), sensor simulation (IMU, DVL, depth, GNSS, USBL, sonar, camera, radar, compass, speed log, acoustic modem), scenario engine, world generator.

**Rules.**
- Nothing from Layer 2, 3, or 4 writes to Layer 1.
- Layer 1 output is deterministic for a given seed.
- Layer 1 publishes ground-truth state (`/auv/state`, `/ssv/state`) for evaluation only; control loops must not subscribe to ground truth.

### 4.2 Layer 2 - Classical control and safety

**Responsibility.** Estimate state, execute missions, and enforce safety. **This is the actuator-authoritative layer.** All commands to thrusters, rudders, and attitude controls originate here.

**Modules.** Nav fusion (`auv_nav`, `ssv_nav`), classical controllers (waypoint tracking, depth / altitude hold, bottom-following, station keeping, loiter, LOS path following, PID), nav-mode state machine, failsafes (abort-to-surface, geofence, min-altitude, max-depth, max-speed, collision safeguards), scripted mission sequencer.

**Rules.**
- Layer 2 consumes Layer 1 sensor outputs and Layer 3 advisories.
- Layer 2 is the only layer that publishes actuator commands.
- Layer 2 runs fully without Layer 3 (AI-off baseline mode).
- Hard constraints (geofence, min/max envelopes, abort logic) live in Layer 2 regardless of what Layer 3 says.

### 4.3 Layer 3 - AI augmentation (runtime, advisory)

**Responsibility.** Provide machine-learning-based perception, planning recommendations, risk forecasts, and anomaly flags to Layer 2.

**Modules.** Perception (object detection, contact classification, sonar classification, shoreline segmentation), mission planning / route adaptation, risk prediction, anomaly detection.

**Rules.**
- **Layer 3 output is advisory.** It never writes actuator commands.
- **Layer 2 can ignore Layer 3 entirely.** If an AI module is slow, stale, crashed, or absent, Layer 2 continues with its classical decision logic.
- **Layer 3 cannot override failsafes.** Geofence, abort logic, and hard envelopes are unconditional.
- **AI outputs are logged and timestamped** for post-hoc analysis and for reproducibility auditing.
- **AI modules run with pinned weights and seeds.** For determinism in regression tests, the same scenario + same seed produces the same AI advisories. If an AI module is non-deterministic, the scenario engine records it as non-deterministic and flags the run accordingly.

### 4.4 Layer 4 - Evaluation AI (offline, post-hoc)

**Responsibility.** Mine telemetry archives to find patterns, cluster failures, recommend new test scenarios, and generate performance summaries across sweeps.

**Modules.** Log miner, failure clustering, scenario-coverage recommender, performance summarizer (often LLM-assisted).

**Rules.**
- Layer 4 operates exclusively on recorded MCAP files and metric databases. It does not run inline with simulations.
- Layer 4 cannot affect runtime behavior of any prior run.
- Layer 4 outputs are reports, plots, scenario suggestions, and narratives - never code or scenario files that run automatically without review.

### 4.5 Safety architecture across layers

```
                   actuator commands
                          ^
                          |  (only from Layer 2)
                          |
  Layer 1 ground truth ---+
       |                  |
       v                  |
  sensor outputs -----> Layer 2 classical
                          ^         |
                          |         v
                     Layer 3 AI advisories (read-only to Layer 2)
                          |
                          v
                     MCAP log <--- Layer 4 offline AI
```

Three invariants that the platform enforces by design:

1. **Actuator authority is singular.** Only Layer 2 writes to `/auv/thruster_cmd`, `/auv/fin_cmd`, `/ssv/thruster_cmd`, `/ssv/rudder_cmd`. Enforced by ROS 2 topic permissions and by convention.
2. **Classical fallback is always live.** Every AI module has a Layer 2 fallback path that runs continuously whether or not the AI module is healthy.
3. **AI never silences failsafes.** Layer 2 failsafe logic (geofence, abort, min altitude, max depth, emergency surface) evaluates unconditionally and can override normal-mode control at any time.

---

## 5. Parameterized mission environment (Layer 1)

The platform does **not** ingest NOAA or BlueTopo data, does **not** perform georeferenced terrain reconstruction, and does **not** reproduce specific real-world locations. Instead it generates **parameterized environment archetypes** procedurally from a seed. This is a deliberate choice to align with the problem statement (adaptable modeling across a range of ocean conditions) and to avoid spending MVP schedule on geospatial tooling that does not directly contribute to evaluation outputs.

What the platform explicitly does not require:

- BlueTopo bathymetry ingest
- NOAA chart GIS layers
- Georeferenced coordinate transforms
- Real shorelines or coastline meshes
- Coverage uncertainty metadata
- AWS Open Data pipelines or credentials

Removing these eliminates roughly two weeks of MVP build effort and avoids coverage gaps, data-handling constraints, and geospatial tooling that does not contribute to evaluation outputs.

### 5.1 Bathymetry archetypes (library of 5)

1. **Open deep water** - flat or gently sloping, 500-3000 m depth. Stresses mid-water transit, GNSS-when-surfaced logic, long-duration energy metrics.
2. **Continental shelf** - sloping from 30 m to 400 m over a configurable distance. Stresses DVL transitions, depth-hold vs. altitude-hold mode switching.
3. **Littoral / coastal** - 5-80 m, variable bottom texture, intermittent seabed features. Stresses shallow-water nav, surface-wave coupling, DVL multi-bounce.
4. **Choke point / narrow channel** ("Strait of Hormuz-style") - narrow navigable corridor, shoaling flanks, 50-100 m channel depth, constrained traffic lanes (`separated_lanes`, `mixed`, `none`), strong directional or tidal-reversing currents. Stresses path adherence under current, contact-dense environments, denied-GNSS transit.
5. **Harbor approach** - shelving bottom, shipping channel, moored obstacles, shore proximity. Stresses cluttered perception, station-keeping near hazards, SSV maneuvering in confined water.

Each archetype exposes a small parameter set (depth range, slope, roughness, feature density, channel width, current profile, traffic density, traffic pattern). A seeded procedural generator produces a heightfield + obstacle set + surface-traffic script consistent with those parameters.

### 5.2 "Strait of Hormuz-style" hero scenario

The choke-point archetype produces named, demo-visible scenarios without reproducing real hydrography. The canonical example:

```yaml
environment:
  archetype: choke_point
  params:
    channel_width_m: 38000        # approximate Hormuz narrowest
    channel_depth_m: 75
    shoal_depth_m: 10
    length_km: 55
    surface_traffic_density: high
    traffic_pattern: separated_lanes
  current:
    profile: tidal_reversing
    speed_mps: 2.2
  gnss:
    mode: intermittent_denied
```

This is "Hormuz-style," not "Hormuz." The narrative value comes from the recognizable geography; the behavior comes entirely from parameters. No politically sensitive data, no classified hydrography, no real-coast rendering.

### 5.3 Ocean forcing parameters

- **Sea state** (Douglas 1-6 presets; drives wave spectrum and significant wave height)
- **Wind** (speed, direction)
- **Current** (profile: uniform, tidal reversing, along-channel, sheared; speed)
- **Visibility** (above-water km, below-water m)
- **Time of day** (drives lighting in Unreal; otherwise not physics-relevant for MVP)

### 5.4 Why bathymetry still matters even without real data

Bathymetry is not decoration - it is a first-class input to AUV behavior and sensor fidelity:

- DVL bottom-lock availability
- Altitude-above-bottom (safety envelope)
- Bottom-following and hover missions
- Obstacle avoidance
- Terrain-aided navigation (reference map comes from the archetype itself)
- Sonar returns
- Survey mission success

Procedural bathymetry is strictly better than real data for T&E: you can dial in exactly the features that stress the system, everything is reproducible, and there are no coverage gaps or data-handling constraints.

---

## 6. Vehicle modeling and CAD pipeline (Layer 1)

Both vehicles (AUV and SSV) are modeled in SolidWorks. The CAD pipeline produces the artifacts needed by physics, visuals, and config.

### 6.1 Per-vehicle artifacts

1. **STEP (AP214)** - lossless source of truth.
2. **Mass properties report** - mass, center of mass, full 3x3 inertia tensor, extracted directly from SolidWorks Mass Properties. **The golden rule: extract mass from SolidWorks, not from meshes.**
3. **Visual mesh** (glTF 2.0) - 50-200K triangles, LODs, textured, for Unreal and Stonefish display.
4. **Collision mesh** (OBJ) - 2-5K triangles, convex-decomposed via V-HACD, for physics contact.
5. **Hydrodynamic mesh** (OBJ) - watertight, 5-20K triangles, integrated by Stonefish for buoyancy and drag.

### 6.2 Tooling

- **SolidWorks** - STEP export, mass properties, thruster/fin reference frames.
- **Blender 4.x** - STEP import (via add-on or FreeCAD intermediate), decimation, UV, glTF export.
- **V-HACD** - convex decomposition for collision meshes.
- **Unreal Engine 5.4 with Datasmith** - direct STEP import when maximum visual fidelity is wanted in the demo.
- **FreeCAD** - optional STEP manipulation path.

### 6.3 Pipeline steps (per vehicle)

1. Establish an explicit vehicle body frame in SolidWorks (CoB for AUV, waterline/midship for SSV).
2. Add named reference coordinate systems for every thruster, fin, and sensor mount.
3. Run SolidWorks Mass Properties with materials assigned; export mass, CoM, inertia tensor to `mass_properties.yaml`.
4. Export the full assembly as STEP AP214; version-control it.
5. Import STEP into Blender; produce the three mesh variants (visual, collision, hydrodynamic) against the same body-frame origin.
6. Author the Stonefish vehicle XML and URDF by hand, referencing meshes and mass properties.
7. Define thrusters in the Stonefish XML using the reference coordinate systems from step 2.
8. Import glTF into Unreal; optionally re-import via Datasmith for hero-asset fidelity. Blueprints subscribe to ROS 2 and drive the actor transform.

### 6.4 What is not extracted from CAD

- Hydrodynamic coefficients (added mass, damping). Stonefish computes drag geometrically for AUV; SSV uses Fossen-style coefficients seeded from published values for a similar hull and tuned.
- Thruster performance curves (from manufacturer data).
- Sensor noise profiles (from datasheets).

### 6.5 CAD directory layout

```
vehicles/
  auv_<name>/
    source/
      assembly.step
      mass_properties.yaml
      frames.yaml
    meshes/
      visual.gltf
      collision.obj
      hydrodynamic.obj
    config/
      vehicle.stonefish.xml
      vehicle.urdf
      thrusters.yaml
      sensors.yaml
      nav_config.yaml
  ssv_<name>/
    (same structure)
```

---

## 7. Sensor architecture (Layer 1)

Sensors are pluggable modules with a common interface: timestamp, frame, validity, noise, latency, ground-truth association.

### 7.1 AUV sensor / nav stack

- IMU (grade-configurable: MEMS / tactical / nav)
- DVL (bottom-lock + water-lock)
- Depth (pressure)
- Compass / magnetometer
- GNSS (surfaced-only, depth-gated)
- USBL responder
- Acoustic modem
- Imaging sonar
- Camera
- TAN input (optional, uses archetype bathymetry as reference map)

### 7.2 SSV sensor / nav stack

- GNSS (mode-configurable)
- IMU (grade-configurable)
- Speed log
- Compass / gyrocompass
- Radar (surface tracking + optional coastline-match nav)
- Camera
- USBL transceiver (nav provider to AUV)
- Acoustic modem
- AIS receiver (optional)

### 7.3 Fidelity tiers

- **Ideal** - good for control bring-up.
- **Noisy** - bias, jitter, latency, dropout.
- **Environment-coupled** - occlusion, turbidity, sea clutter, wave effects, range dependence, lock loss.

---

## 8. Navigation architecture (Layer 2)

Navigation is promoted to a first-class concern because it is the single most differentiated capability of the MVP. GNSS-denied and contested operation is modeled explicitly, not as an afterthought.

### 8.1 AUV navigation stack

GNSS does not work underwater. The AUV's position is a fusion of:

1. **INS (IMU-based dead reckoning)** - always running, drift rate set by IMU grade (MEMS tactical ~1% distance, FOG ~0.1%, RLG ~0.01%).
2. **DVL (Doppler Velocity Log)** - primary drift-bounding sensor.
   - *Bottom lock* when within range of seabed (~30-200 m).
   - *Water lock* otherwise (bounds velocity-over-water, not velocity-over-ground).
3. **Depth sensor** (pressure) - absolute depth always.
4. **Compass / magnetometer** - heading, unreliable near ferromagnetic anomalies.
5. **Acoustic aiding**:
   - *USBL* - single transceiver on the SSV, AUV carries responder. **Default for AUV + mothership operations.**
   - *LBL* - optional, seafloor array.
   - *OWTT ranging* - optional, from beacons of known position.
6. **GNSS when surfaced** - depth-gated, for periodic INS reset and geo-referencing the USBL frame.
7. **Terrain-aided navigation (TAN)** - optional, compares measured depth to archetype bathymetry reference map.
8. **Visual / SLAM** - cameras for close-in nav.

### 8.2 SSV navigation stack

1. **GNSS** - primary, mode-configurable.
2. **IMU** (tactical or nav-grade) - drifts with time when GNSS denied.
3. **Speed log** (EM log equivalent) - speed through water.
4. **Compass / gyrocompass** - heading.
5. **Radar fixed-feature matching** - optional, matched to archetype features.
6. **Vision-based coastline / buoy matching** - optional.
7. **eLORAN / radio beacon LOPs** - optional, not in MVP.

### 8.3 The navigation cascade (the T&E headline)

```
 GNSS env knob ---> SSV GNSS receiver ---> SSV nav solution
                                                |
                                                v
                                        SSV INS / DR fallback
                                                |
                                                v
                                       SSV position uncertainty
                                                |
                                                v  (USBL transceiver on SSV)
                                       AUV USBL fix inherits SSV uncertainty
                                                |
                                                v
                                        AUV nav solution degrades
```

When the GNSS knob degrades, the SSV's position uncertainty grows per its INS/DR quality, the USBL acoustic fixes it delivers to the AUV inherit that growing uncertainty, and the AUV's absolute position error grows even though nothing changed directly for the AUV. This cascade is measurable and is the core T&E story of the platform.

### 8.4 GNSS as a first-class environmental knob

Six modes, each a parameter set, not new code:

```yaml
gnss:
  mode: nominal | degraded | jammed | spoofed | denied | intermittent
  params:
    nominal:
      hdop: 1.2
      position_noise_m: 2.5
      availability: 1.0
    degraded:
      hdop: 4.0
      position_noise_m: 15.0
      availability: 0.9
      multipath_bias_m: [3, 8]
    jammed:
      availability: 0.0
      detection_latency_s: 2.0
    spoofed:
      availability: 1.0
      position_bias_m: [50, 0, 0]
      bias_growth_mps: 0.5
      detection_latency_s: 30.0
    denied:
      availability: 0.0
      known_to_vehicle: true
    intermittent:
      availability_schedule: [...]
```

The critical T&E distinctions:

- **Denied** - vehicle knows, falls back cleanly.
- **Jammed** - vehicle can detect loss of lock, fallback with latency.
- **Spoofed** - vehicle believes its fix; only integrity monitoring catches it. Hardest case, most militarily relevant. This is where Layer 3 anomaly detection earns its keep.

Implementation: a small node in front of the GNSS sensor plugin transforms ground-truth position into reported position according to mode.

### 8.5 AUV GNSS behavior (surfaced-only)

```yaml
auv_gnss:
  mode: inherit_from_scenario
  depth_gate_m: 1.0
  fix_acquisition_time_s: 20.0
  used_for: ["ins_reset", "geo_reference_usbl_frame"]
```

### 8.6 Acoustic navigation as the AUV's environmental knob

Since GNSS is meaningless submerged, the analogous first-class knob for the AUV is acoustic-nav infrastructure and acoustic environment quality:

```yaml
acoustic_nav:
  usbl:
    mode: nominal | degraded | denied
    params:
      nominal:
        range_max_m: 3000
        range_accuracy_pct: 0.2
        bearing_accuracy_deg: 0.5
        update_rate_hz: 1.0
        availability: 1.0
      degraded:
        range_max_m: 1500
        range_accuracy_pct: 1.0
        bearing_accuracy_deg: 2.5
        update_rate_hz: 0.3
        availability: 0.7
      denied:
        availability: 0.0
  acoustic_environment:
    sound_speed_profile: isospeed | summer_thermocline | winter_mixed | custom
    ambient_noise_dB: 60
    multipath_severity: none | moderate | severe
    sound_speed_mps: 1500
```

### 8.7 Acoustic comms pipe (separate from acoustic nav)

```yaml
acoustic_comms:
  range_max_m: 2000
  bandwidth_bps: 1000
  latency_base_s: 1.5
  loss_rate: 0.05
  gated_by_sound_speed_profile: true
```

### 8.8 Navigation-mode state machine (per vehicle)

Each vehicle autonomy stack owns a nav-mode state machine with explicit fallback logic:

- `NOMINAL` -> `DEGRADED` -> `FALLBACK_INERTIAL` -> `ABORT_OR_LOITER`
- Transition triggers: GNSS lock loss, integrity-monitor trip, USBL fix gap exceeded, DVL lock loss timer.
- Each transition is logged; transition log is a first-class evaluation output.
- Layer 3 anomaly detection (Section 10.5) can accelerate transitions by flagging spoofing earlier than the classical integrity monitor would, but it cannot suppress transitions.

---

## 9. Classical autonomy and control (Layer 2)

Classical controls first (PID, LOS path following). Each vehicle autonomy stack exposes the nav-mode state machine from Section 8.8 and a set of safety invariants that run unconditionally.

### 9.1 AUV classical autonomy

- Waypoint tracking
- Depth hold / altitude hold / bottom-following
- Lawnmower / survey patterns
- Surface-to-GNSS-fix routine (scheduled or triggered)
- Abort-to-surface failsafe
- Nav-mode fallback: INS + DVL + TAN + last-known USBL when acoustic denied

### 9.2 SSV classical autonomy

- Waypoint / transit
- Loiter / patrol
- Station keeping (simple for MVP; NMPC is Phase 2)
- Escort / overwatch during AUV mission
- Nav-mode fallback: GNSS -> degraded-GNSS + IMU -> dead reckoning -> radar feature match (optional)

### 9.3 Safety invariants (enforced unconditionally)

Each vehicle enforces the following regardless of what any other layer says:

- **Geofence.** Hard polygon; breach triggers abort behavior.
- **Min altitude above bottom** (AUV).
- **Max depth** (AUV).
- **Max speed** (both).
- **Collision safeguard** (both) - emergency stop on imminent contact with obstacle or other vehicle above a velocity threshold.
- **Abort-to-surface** (AUV) on critical fault (power, leak, nav completely lost, unrecoverable nav-mode fallback).
- **Return-to-launch** (SSV) on critical fault.
- **Comms-timeout** behavior (both) - if no heartbeat from mission authority for N seconds, enter safe behavior.

These invariants are Layer 2 code. Layer 3 can neither weaken nor delay them.

---

## 10. AI augmentation layer (Layer 3)

Layer 3 is where machine-learning and learned policies enter the system. It is strictly advisory to Layer 2 and never commands actuators. The design goal is to make AI useful for perception, planning, and anomaly detection while preserving deterministic, auditable baseline behavior.

### 10.1 Design principles

1. **Advisory, not authoritative.** Layer 3 publishes recommendations. Layer 2 decides whether to act on them. If Layer 3 is absent or stale, Layer 2 continues on classical defaults.
2. **No actuator authority.** Layer 3 nodes cannot publish on `/auv/thruster_cmd`, `/auv/fin_cmd`, `/ssv/thruster_cmd`, or `/ssv/rudder_cmd`. Enforced by ROS 2 topic permissions.
3. **Pinned models, logged decisions.** Every AI model has a version string, file hash, and inference seed recorded with each decision in MCAP. Reproducibility is auditable.
4. **Graceful degradation.** Every Layer 3 module has a Layer 2 fallback. Planning falls back to scripted mission phases. Perception falls back to classical detection (e.g., threshold-based sonar detection). Anomaly detection falls back to the classical integrity monitor. Risk prediction falls back to static margins.
5. **Sandboxed runtime.** Layer 3 modules have bounded CPU/GPU budgets. Exceeding budget triggers a "stale advisory" flag in Layer 2 and the classical path takes over.
6. **Two reproducibility modes.** The scenario engine supports `ai_mode: on` (AI advisories participate in decisions) and `ai_mode: off` (AI advisories are recorded but ignored). Every demo result can be re-run with `ai_mode: off` to verify the classical baseline.

### 10.2 Perception

Learned models that turn raw sensor streams into semantic outputs consumed by planning and decision logic.

**Modules.**

- **Surface-contact detection and classification** (SSV camera + radar fusion) - identifies vessels, buoys, debris, shore features. MVP: pre-trained YOLO-class detector on the RGB camera, fused with radar tracks by bearing/range gating.
- **Sonar contact classification** (AUV imaging sonar) - classifies sonar returns into background, wreck, pinnacle, debris, mine-like object. MVP: lightweight CNN classifier on sonar tiles.
- **Underwater object detection** (AUV camera) - close-range object identification during hover / inspection.
- **Shoreline segmentation** (SSV camera) - semantic mask of shore vs. water, feeds Layer 2 radar-coastline-match nav fallback.

**Outputs.** Semantic detections with confidence, bounding geometry, and sensor-frame reference, published on `/ai/perception/*`.

### 10.3 Mission planning / route adaptation

Learned or search-based planners that propose adjustments to the scripted mission in response to observed conditions.

**Modules.**

- **Adaptive sweep pattern** (AUV) - adjusts lawnmower spacing and heading given observed bathymetry and current.
- **Energy-aware transit** (SSV) - proposes transit paths minimizing thruster energy against current and wind.
- **Dynamic rendezvous replan** (both) - adjusts drop location or recovery approach to account for real-time nav quality cascade.
- **Traffic-aware routing** (SSV) - proposes deviations around detected surface contacts while respecting traffic-separation constraints.

**Outputs.** Proposed waypoint lists, pattern parameter adjustments, or rendezvous points, published on `/ai/planner/*`. Layer 2 decides whether to adopt them based on classical safety checks (geofence, min-altitude, envelope).

### 10.4 Risk prediction

Forecasts of future mission conditions or failure likelihood, used by Layer 2 to adjust margins or trigger proactive behaviors.

**Modules.**

- **Mission success probability** given current environment + nav quality.
- **Sensor degradation forecast** - predicts turbidity-driven vision degradation, sea-state-driven sonar degradation, thermocline-driven USBL degradation.
- **Energy margin forecast** - predicts remaining mission capability given current energy use rate and environmental drag.
- **Nav denial forecast** - when scenarios include scheduled or learned GNSS degradation patterns, predicts time-to-next-denial and uncertainty growth.

**Outputs.** Scalar risk scores, margin forecasts, and confidence intervals published on `/ai/risk/*`. Layer 2 can use these to tighten abort thresholds or widen safety buffers but it is not required to.

### 10.5 Anomaly detection

The module with the highest military T&E value, because it is the second line of defense against spoofing and subtle faults.

**Modules.**

- **GNSS spoofing detection** (SSV) - compares GNSS position to IMU + speed-log dead reckoning, flags inconsistencies faster than a classical innovation gate alone would. MVP approach: residual-based with a learned threshold; upgrade path is a multi-signal consistency classifier.
- **Nav integrity monitor** (both) - ML-augmented residual monitor across all nav sensors, emits a running integrity score.
- **Sensor fault detection** (both) - detects stuck readings, impossible gradients, and distributional drift in IMU, DVL, sonar, camera.
- **Actuator health monitor** (both) - detects thruster response deviation by comparing commanded vs. observed dynamics.
- **Acoustic anomaly detection** (AUV) - flags sonar returns inconsistent with modeled sea state and ambient noise.

**Outputs.** Anomaly flags with severity and source, published on `/ai/anomaly/*`. Layer 2 nav-mode state machine can use these to transition earlier than the classical monitor would, but the classical monitor continues to run in parallel.

### 10.6 MVP scope for Layer 3

For a 10-week medium-fidelity MVP we do not train from scratch. The realistic Layer 3 demo scope is:

**In MVP:**

- One perception module: pre-trained YOLO-class surface-contact detector on SSV camera. Pre-trained weights, no fine-tuning.
- One anomaly-detection module: GNSS spoofing detection via residual-based classifier. Minimal training on synthetic residual signatures generated from the scenario engine.
- Scaffolding for the remaining modules: ROS 2 node skeletons, interface contracts, fallback plumbing, `ai_mode` toggle. Not full models.

**Deferred post-MVP:**

- Sonar classification, shoreline segmentation, adaptive planning, energy-aware routing, sensor degradation forecasting, actuator health, acoustic anomaly detection.
- Online learning. All MVP models are fixed-weight.
- RL / DRL controllers. Classical controls only for the actuator path; any learned policy is advisory and sits in Layer 3.

### 10.7 AI-related scenario controls

The scenario YAML exposes Layer 3 knobs:

```yaml
ai:
  mode: on | off | shadow        # shadow = AI runs and logs but Layer 2 ignores
  perception:
    model_ref: models/yolo_v8_surface_contacts_v3.onnx
    inference_seed: 42
  anomaly:
    spoof_detector_ref: models/gnss_spoof_rf_v1.joblib
  risk:
    enabled: false
  planner:
    enabled: false
```

`shadow` mode is the honest way to A/B test AI. Both the AI and classical paths run; Layer 2 uses classical; MCAP records both for post-hoc comparison. This is the default for baseline evaluation runs.

---

## 11. Meshed SSV + AUV with drop handoff (Tier B)

### 11.1 Concept

The SSV carries the AUV as a payload during transit, releases it at a scripted point, and the AUV initializes with the SSV's pose and velocity at that instant. No recovery is implemented in MVP.

### 11.2 Implementation (recommended path)

**Kinematic attach, event-based release.** The AUV runs in kinematic mode rigidly following a stern reference frame on the SSV. At the release event, the coupling node captures the SSV's pose and velocity, writes them as the AUV's initial state, switches the AUV to dynamic mode, and hands control to AUV autonomy. Cheap, clean, physically defensible.

### 11.3 Coupling node responsibilities

- Carried / released state machine.
- `/coupling/drop_cmd` listener.
- Publishes `/coupling/payload_state`.
- Notifies scenario engine of release completion.

### 11.4 Comms pipe (minimum viable)

A ROS 2 node that relays between AUV and SSV with:

- Hard range cutoff (e.g., 1000 m acoustic when AUV submerged, 5 km RF when AUV surfaced).
- Fixed latency (e.g., 1.5 s acoustic, 50 ms RF).
- Range-dependent drop probability.
- Depth-gated mode selection (RF only when AUV depth < 1 m).

Three configs: `perfect`, `nominal`, `degraded`.

### 11.5 What we explicitly do not build in MVP

- Full launch-and-recovery (cradle, davit, ramp, contact mechanics, tether dynamics).
- Rendezvous geometry under sea state.
- Multi-AUV / multi-SSV beyond 1+1 (architecture supports N+M; demo does not need it).

---

## 12. Scenario engine

The scenario file is the single artifact that defines a run. Same scenario + same seed + same `ai_mode` => same run.

### 12.1 Example scenario YAML (full)

```yaml
scenario:
  name: choke_point_gnss_denied_transit
  seed: 42
  duration_s: 2400
  real_time_factor: 1.0

environment:
  archetype: choke_point
  params:
    channel_width_m: 38000
    channel_depth_m: 75
    shoal_depth_m: 10
    length_km: 55
    surface_traffic_density: high
    traffic_pattern: separated_lanes
  sea_state: 3
  wind:
    speed_mps: 8
    direction_deg: 225
  current:
    profile: along_channel
    speed_mps: 1.8
    direction_deg: 270
  visibility:
    above_water_km: 8
    below_water_m: 3

  gnss:
    mode: intermittent
    availability_schedule:
      - { t_start_s:    0, t_end_s:  600, state: nominal }
      - { t_start_s:  600, t_end_s: 1200, state: jammed  }
      - { t_start_s: 1200, t_end_s: 1800, state: spoofed, position_bias_m: [80, -30, 0] }
      - { t_start_s: 1800, t_end_s: 2400, state: denied  }

  acoustic_nav:
    usbl:
      mode: degraded
      params:
        range_max_m: 2000
        bearing_accuracy_deg: 2.0
    acoustic_environment:
      sound_speed_profile: summer_thermocline
      ambient_noise_dB: 68
      multipath_severity: moderate

  acoustic_comms:
    range_max_m: 2000
    bandwidth_bps: 1000
    latency_base_s: 1.5
    loss_rate: 0.1

ai:
  mode: shadow
  perception:
    model_ref: models/yolo_v8_surface_contacts_v3.onnx
    inference_seed: 42
  anomaly:
    spoof_detector_ref: models/gnss_spoof_rf_v1.joblib
  risk:
    enabled: false
  planner:
    enabled: false

vehicles:
  - id: ssv_01
    ref: vehicles/ssv_mothership
    autonomy: ssv_transit_with_nav_fallback
    nav_config:
      imu_grade: tactical
      backup_nav_priority: [radar_coast_match, dead_reckoning]
    initial_pose: [0, 0, 0]
    sensor_profile: nominal

  - id: auv_01
    ref: vehicles/auv_surveyor
    carried_by: ssv_01
    autonomy: auv_bottom_survey
    nav_config:
      imu_grade: tactical
      dvl_preferred_mode: bottom_lock
      usbl_enabled: true
      tan_enabled: true
      tan_reference: "from_environment"
      surface_for_gnss_every_s: 0
    sensor_profile: nominal

mission:
  phases:
    - name: transit
      vehicle: ssv_01
      waypoints: [...]
      end_condition: { type: at_waypoint, tolerance_m: 20 }
    - name: drop
      action: release_payload
      payload: auv_01
      end_condition: { type: payload_released }
    - name: survey_denied
      vehicle: auv_01
      pattern: lawnmower
      area: [...]
      depth_m: 45
      spacing_m: 40
      end_condition: { type: area_complete }
    - name: overwatch
      vehicle: ssv_01
      center: [x, y]
      radius_m: 300
      parallel_with: survey_denied

faults: []

recording:
  mcap: true
  topics: [all]
  video: false

evaluation:
  metrics:
    - mission_success
    - ssv_time_to_detect_gnss_denial
    - ssv_time_to_detect_gnss_spoofing
    - ssv_position_uncertainty_growth_rate
    - auv_usbl_fix_availability_pct
    - auv_dvl_bottom_lock_pct
    - auv_position_error_at_waypoints
    - path_rms_error_m
    - min_altitude_above_bottom_m
    - near_miss_count
    - station_keeping_radius_m
    - thruster_energy_j
    - sensor_uptime_pct
    - nav_mode_transition_log
    - time_to_complete_s
    - ai_spoof_detector_latency_s
    - ai_perception_precision_recall
    - ai_shadow_vs_classical_disagreements
```

### 12.2 Scenario engine responsibilities

1. Validate the YAML against the schema.
2. Invoke the environment archetype generator to produce bathymetry, currents, traffic.
3. Emit the Stonefish scene XML referencing the vehicle configs.
4. Launch the ROS 2 graph (Stonefish, sensor nodes, nav nodes, classical autonomy, Layer 3 AI modules per the `ai` block, coupling, comms, evaluation recorder).
5. Tick mission phases; issue `/coupling/drop_cmd`, transition conditions, fault injections, GNSS schedule.
6. Manage the simulation clock; record MCAP for the configured duration.
7. On completion, invoke the evaluation pipeline (Layer 4).

---

## 13. Evaluation and metrics (Layer 4)

Every run produces three classes of output:

1. **Animation / replay** - MCAP playable in Foxglove; optional Unreal replay.
2. **Telemetry logs** - vehicle state, sensor outputs, commands, environment values, AI advisories and classical decisions, all timestamped and seeded.
3. **Metrics report** - auto-generated from MCAP.

### 13.1 Core metrics

- Mission success / failure (with reason)
- Trajectory RMS error vs. reference path
- Time to complete mission
- Thruster energy integral (proxy for energy use)
- Near-miss and collision count
- Station-keeping radius (SSV)
- Minimum altitude above bottom (AUV)
- Sensor uptime / degraded intervals

### 13.2 Navigation-specific metrics

- Time-to-detect GNSS denial (SSV)
- Time-to-detect GNSS spoofing (SSV) - both classical and AI paths; delta is a headline metric
- Position uncertainty growth rate (both vehicles, m/min of denied op)
- USBL fix availability during mission (AUV)
- AUV position error vs. SSV GNSS mode (the cascade chart)
- DVL bottom-lock availability (AUV)
- Nav-mode transition log (timeline of fallback events)
- Position error at critical mission events (drop, rendezvous, waypoint, abort)

### 13.3 AI-specific metrics

- Perception precision / recall / false-alarm rate by class
- Anomaly detector latency and false-positive rate
- Classifier calibration (predicted vs. empirical confidence)
- Shadow-mode disagreement rate (AI vs. classical)
- AI inference latency and budget compliance
- AI decisions ignored by Layer 2 (and why)
- AI vs. classical outcome delta per metric (does AI actually help?)

### 13.4 Comparison / sweep reports

The evaluation pipeline supports multi-run comparisons: run one scenario with controller A and controller B across GNSS modes nominal/degraded/jammed/spoofed/denied, produce a single PDF report with the deltas. This capability is what makes the platform a *test-and-evaluation* tool rather than a simulator.

### 13.5 Evaluation AI (Layer 4)

Layer 4 operates on the MCAP archive and metric database produced by scenario runs. It is offline; it does not affect any run's runtime behavior.

**Log mining.**

- Causal analysis of failure runs: which environment parameters and nav-mode transitions preceded an abort?
- Pattern discovery across hundreds of runs: common preconditions for high path error, common sequences leading to station-keeping loss.
- Time-series motif finding on telemetry.

**Failure clustering.**

- Automatic categorization of mission failures into clusters by reason, trajectory shape, and environment conditions.
- Dimensionality-reduced trajectory embedding (UMAP / t-SNE) with cluster labels.
- Identification of "new" failure modes not previously catalogued.

**Scenario recommendation.**

- Coverage gap analysis: which combinations of (archetype, sea state, GNSS mode, seed band) are under-sampled?
- Adversarial scenario suggestion: propose parameter settings most likely to trigger failure in the current system.
- Regression suggestion: propose scenarios that should be in the CI suite based on observed failure neighborhoods.

**Performance summarization.**

- LLM-generated executive summary from a sweep's MCAPs and metric database: "Controller B outperformed Controller A in 14 of 20 conditions; primary failure mode in Controller A was spoofing-triggered abort; primary failure mode in Controller B was DVL-loss recovery timing."
- Auto-generated comparison narratives for PDF reports.
- Regression detection with human-readable explanations.

**Rules.**

- Layer 4 outputs are always reports, plots, or scenario suggestions; they are never auto-committed to the scenario library or to CI without human review.
- LLM-generated narratives cite the MCAP runs and specific metrics they reference.
- Clustering and recommendation models are versioned and the version is logged in every report.

---

## 14. Unreal visual layer

Unreal is the visual and scenario-review environment, not the source of truth for vehicle physics.

### 14.1 Unreal responsibilities

- Render the site (archetype terrain + water + weather + lighting).
- Render the vehicles (glTF import, optionally Datasmith for hero fidelity).
- Drive thruster FX (spin rate, cavitation) from `/thruster_cmd`.
- Provide camera presets: chase, top-down, onboard, drop-event cinematic.
- Replay MCAP files.

### 14.2 Unreal non-responsibilities

- No physics ownership.
- No sensor simulation authority (Unreal may render a camera feed for demo, but the sensor plugin in Stonefish is the one whose output goes to autonomy).
- No scenario orchestration.
- No AI inference (Layer 3 lives in ROS 2 Python nodes, not in Unreal).

### 14.3 Bridge

A ROS 2 bridge node streams `/tf` and vehicle/env state topics into Unreal. Blueprints subscribe and drive actor transforms. Target 60 Hz, capped to avoid starving the ROS 2 graph.

---

## 15. Repository layout

```
poseiden-sim/
  env_service/                  # Layer 1: ocean state
    src/
    config/
  world_generator/              # Layer 1: procedural archetypes
    archetypes/
      open_water.py
      continental_shelf.py
      littoral.py
      choke_point.py
      harbor_approach.py
    procedural/
      heightfield.py
      obstacles.py
      traffic.py
      currents.py
    output/
      to_stonefish.py
      to_unreal.py
  auv_sim/                      # Layer 1: Stonefish integration for AUV
    src/
    plugins/
  ssv_sim/                      # Layer 1: Stonefish integration for SSV
    src/
  coupling/                     # Layer 1/2: carries, drop, comms pipe
    src/
  sensor_models/                # Layer 1: sensor plugin library
    imu/ depth/ dvl/ sonar/ gnss/ compass/ radar/ camera/
    usbl/
    acoustic_modem/
  nav/                          # Layer 2: nav stacks per vehicle
    auv_nav/
    ssv_nav/
    gnss_env/                   # Layer 1: GNSS mode node
    acoustic_env/               # Layer 1: SSP + noise + multipath
  autonomy_auv/                 # Layer 2: classical AUV autonomy
    waypoint/ depth_hold/ bottom_follow/ survey/ failsafe/ nav_state_machine/
    safety_invariants/
  autonomy_ssv/                 # Layer 2: classical SSV autonomy
    waypoint/ station_keep/ loiter/ escort/ nav_state_machine/
    safety_invariants/
  ai/                           # Layer 3: AI augmentation (runtime)
    perception/
      surface_contacts/
      sonar_classification/
      underwater_objects/
      shoreline_segmentation/
    planner/
      adaptive_sweep/
      energy_aware_transit/
      dynamic_rendezvous/
      traffic_aware_routing/
    risk/
      mission_success/
      sensor_degradation/
      energy_margin/
      nav_denial_forecast/
    anomaly/
      gnss_spoof_detector/
      nav_integrity_monitor/
      sensor_fault_detector/
      actuator_health_monitor/
      acoustic_anomaly_detector/
    common/
      interfaces/
      fallback/
      sandbox/
      model_registry/
  models/                       # pinned AI model artifacts + hashes
  scenario_engine/
    src/
    schemas/
    scenarios/
  evaluation/                   # Layer 4: evaluation (classical + AI)
    metrics/
    plots/
    dashboards/
    reports/
    ai/
      log_miner/
      failure_clustering/
      scenario_recommender/
      performance_summarizer/
  rendering/
    unreal/
    bridge/
  vehicles/                     # CAD artifacts per Section 6
    auv_surveyor/
    ssv_mothership/
  tools/
    cad_pipeline/
    archetype_preview/
  docs/
```

---

## 16. Interface contracts

ROS 2 topic conventions (lock these down early). Topics are grouped by layer so subscription permissions can be enforced.

```
# Layer 1 - Environment and ground truth
/env/bathymetry_query
/env/current
/env/wave_state
/env/wind
/env/visibility
/env/sound_speed_profile
/env/ambient_noise_dB

/auv/state                      # ground-truth 6-DOF (evaluation only)
/ssv/state                      # ground-truth 6-DOF (evaluation only)

# Layer 1 - Sensor outputs (Layer 2 and 3 subscribers)
/auv/sensors/imu /auv/sensors/depth /auv/sensors/dvl
/auv/sensors/sonar /auv/sensors/camera /auv/sensors/gnss
/auv/sensors/usbl_fix /auv/sensors/tan_fix

/ssv/sensors/gnss /ssv/sensors/imu
/ssv/sensors/compass /ssv/sensors/speed_log
/ssv/sensors/radar_tracks /ssv/sensors/camera
/ssv/sensors/usbl_transceiver

# Layer 2 - State estimates and commands
/auv/state_estimate /auv/nav_mode /auv/position_uncertainty
/auv/thruster_cmd /auv/fin_cmd                 # ACTUATOR - Layer 2 only

/ssv/state_estimate /ssv/nav_mode /ssv/position_uncertainty
/ssv/thruster_cmd /ssv/rudder_cmd              # ACTUATOR - Layer 2 only

# Layer 3 - AI advisories (read by Layer 2, never write actuators)
/ai/perception/surface_contacts
/ai/perception/sonar_classifications
/ai/perception/underwater_objects
/ai/perception/shoreline_mask
/ai/planner/sweep_adjustment
/ai/planner/transit_proposal
/ai/planner/rendezvous_replan
/ai/planner/traffic_avoidance
/ai/risk/mission_success_prob
/ai/risk/sensor_degradation
/ai/risk/energy_margin
/ai/risk/nav_denial_forecast
/ai/anomaly/gnss_spoof_flag
/ai/anomaly/nav_integrity_score
/ai/anomaly/sensor_fault
/ai/anomaly/actuator_health
/ai/anomaly/acoustic_event

# Coupling and comms
/coupling/payload_state
/coupling/drop_cmd
/coupling/comms_link

# Scenario control
/scenario/clock
/scenario/event
/scenario/fault_inject
/scenario/gnss_mode
/scenario/ai_mode                # on | off | shadow
```

Message conventions:

- Vehicle state: `nav_msgs/Odometry` with ENU world and FLU body.
- Sensors: `sensor_msgs/*` where possible for tooling compatibility.
- Comms link: custom msg with source, dest, payload, send_time, receive_time, dropped flag.
- Nav mode: custom enum-typed msg with mode and transition timestamp.
- AI advisory: custom msg with source module, model version, model hash, inference seed, confidence, payload, timestamp.
- AI anomaly: custom msg with anomaly type, severity, source, confidence, suggested action, timestamp.

ROS 2 permission policy:

- Only `autonomy_auv/*` and `autonomy_ssv/*` nodes have publish rights on `/auv/thruster_cmd`, `/auv/fin_cmd`, `/ssv/thruster_cmd`, `/ssv/rudder_cmd`.
- `ai/*` nodes are denied actuator publish rights in the DDS security policy.
- All actuator commands pass through a guard node that logs the publisher and rejects unauthorized sources.

---

## 17. Platform profiles and edge deployability

The primary integration risk for this platform is not any one package version. It is treating the newest development stack as the default operational stack. For national-security and edge deployments the platform must support a **mission-stable runtime profile** that prioritizes supportability, deterministic behavior, offline operation, and accreditation readiness over access to the newest OS and middleware features.

This section defines two supported runtime profiles, a mandatory split between mission-essential and mission-enhancing components, a set of operational invariants that apply unconditionally to the edge profile, and the platform compatibility matrix.

### 17.1 Two runtime profiles

The platform ships two validated runtime profiles. Code is shared; what differs is OS baseline, middleware version, enabled components, install path, and network assumptions.

**Profile A - Development / Demo**

- Ubuntu 24.04 LTS
- ROS 2 Jazzy
- Unreal Engine 5 enabled
- Python orchestration and evaluation
- Full dashboard, replay, and visualization stack
- Latest validated AI runtime (Layer 3 perception, Layer 4 evaluation AI)
- Online registries, model hubs, and package mirrors permitted
- Optimized for internal iteration speed and stakeholder demos

**Profile B - Edge / Mission Runtime**

- Ubuntu 22.04 LTS or RHEL / Rocky 9 host, selected per release based on best-supported simulator and plugin compatibility
- ROS 2 Humble where package support is stronger on the target host; validated Jazzy subset acceptable only after full compatibility testing
- Unreal disabled by default; headless operation is the baseline
- No dependency on external registries, model hubs, package mirrors, or cloud APIs
- Classical Layer 2 stack always available and self-sufficient
- Layer 3 AI optional, installable as separate signed packages, fully removable at deploy time
- Layer 4 AI optional and offline; no LLM API calls in the critical path
- Deterministic replay and classical-only mode always available

The development profile maximizes iteration speed. It is **not** assumed to be the mission runtime. No release is declared edge-supported until it passes the deterministic regression suite on the edge profile's target baseline.

### 17.2 Mission-essential core vs. mission-enhancing components

For edge accreditation and support the platform is explicitly partitioned into a trusted core and optional enhancements. The core must run on its own without any enhancing component present.

**Mission-essential core (required in every deployment):**

- Scenario engine
- Stonefish (or equivalent truth simulator)
- Layer 1 environment service, sensor simulation, ground-truth publication
- Layer 2 navigation fusion, classical controllers, safety invariants, nav-mode state machine
- MCAP recorder
- Metrics pipeline
- CLI and minimal operator interface

**Mission-enhancing (installable, removable, not required for core T&E):**

- Unreal visual layer
- Web dashboard
- Layer 3 AI perception, planning, risk, anomaly modules
- Layer 4 LLM-based summarization
- Multi-tenant gateway and SaaS features
- Observability stack beyond local log capture

The core T&E function - scenario execution, vehicle simulation, classical navigation and control, recording, and metric generation - remains fully functional without Unreal, without Layer 3 AI, and without network connectivity. This is a hard platform invariant.

### 17.3 Edge profile operational invariants

For any release declared edge-supported, the following invariants apply unconditionally.

**Offline and air-gap.**
- Every release is installable and runnable from an offline artifact bundle.
- No component requires runtime `apt install`, `pip install`, or model download.
- No component requires outbound network or license-check callbacks.
- Air-gap operation is a first-class supported deployment profile, not a degraded afterthought.

**Deterministic fallback.**
- Every scenario runs in classical-only mode with bit-identical ground-truth outputs for a given seed.
- Every scenario runs without Unreal.
- Every scenario runs without outbound connectivity.
- Every release ships with at least one deterministic regression pack that the partner can execute locally to validate installation.
- Every AI-enabled result is reproducible against a classical baseline run on the same seed.

**Versioning and provenance.**
- Every container is pinned by digest, not tag.
- Every Python package is pinned and vendored (wheelhouse-exported).
- Every AI model is versioned, signed, and packaged offline.
- Every MCAP records the full version stack it was produced by (platform version, image digests, model hashes, scenario hash).

**Python boundary.**
- Python is used for scenario orchestration, evaluation, and AI inference only.
- Control loops, timing-sensitive simulation bridges, and critical sensor pipelines remain in C++ or hardened compiled components.
- Python failures cannot take Layer 2 control offline.

**Hardware baseline.**
- Minimum deployable kit: one Linux host with NVIDIA GPU and local object storage.
- GPU-absent degraded mode: regression tests execute on CPU with rendering disabled; baseline T&E outputs remain valid at reduced fidelity.
- AI-absent mode: platform runs with identical classical behavior; evaluation marks the run as `classical-only`, `shadow`, or `active`.

**Security posture (edge-specific).**
- Non-root containers where practical.
- Read-only root filesystems.
- Minimal Linux capabilities per container.
- SELinux or AppArmor profiles shipped with every component.
- DDS-Security / SROS2 policy bundles enforced.
- STIG-aligned host hardening supported.
- Administrative interfaces removable in operational mode.
- Operator actions fully audit-logged.
- Signed artifact verification enforced at install time and at runtime.

### 17.4 Platform compatibility matrix

The following is the initial target matrix. It is versioned in `OPEN_SOURCE_STACK.md` and updated per release. A release is not declared edge-supported until every row it claims support for passes the deterministic regression suite.

| Profile | Host OS | ROS 2 | Unreal | Layer 3 AI | Layer 4 AI | Offline install | Support posture |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Development / Demo | Ubuntu 24.04 | Jazzy | Enabled | Enabled | Enabled | Optional | Primary for internal engineering and stakeholder demos |
| Edge / Mission (baseline) | Ubuntu 22.04 LTS | Humble (or validated Jazzy subset) | Disabled by default | Optional, signed packages | Optional, offline only | Required | Primary for partner on-prem, national security, air-gap |
| Edge / Mission (RHEL family) | RHEL / Rocky 9 | Humble or Jazzy per validation | Disabled by default | Optional, signed packages | Optional, offline only | Required | Partner environments requiring RHEL-family hosts |
| Analyst replay | Ubuntu 24.04 or Windows viewer | Not required | Optional | Not required | Not required | Optional | Post-run replay and report review |

### 17.5 Implication for Unreal

Unreal is a development, demo, and analyst-replay tool. It is not part of the edge runtime.

- Unreal remains in Profile A for internal iteration, stakeholder demos, cinematic replay, and analyst review.
- Unreal is not part of the baseline on-prem mission runtime.
- In edge deployments, Unreal consumes recorded MCAP after the fact; it does not run in-line with the simulation.
- The edge runtime ships headless by default and delivers all core T&E outputs without any visual rendering.

This separation is explicit because a military-facing platform must be able to state unambiguously: the core T&E function runs without internet, without Unreal, and without AI.

### 17.6 Implication for AI

AI is advisory at runtime (Layer 3) and **removable at deploy time**.

- AI modules are installable as separate signed packages. The edge distribution does not include AI modules unless the partner installs them explicitly.
- The classical baseline is fully functional with no AI module present.
- Evaluation output marks every run with its AI mode: `classical-only`, `shadow`, or `active`.
- Layer 4 LLM-based summarization runs offline in edge deployments; no LLM API calls are allowed in the critical path.
- Partner policy determines AI activation; the platform does not assume AI is available.

This addresses accreditation variability, export-control variations, compute-budget constraints, and operator-trust requirements in a single policy.

### 17.7 Policy summary

The single-sentence version of this section, which every downstream decision must be consistent with:

**The newest development stack is acceptable for Profile A. Profile B - the edge mission runtime - must be conservative, offline-installable, headless-capable, AI-removable, deterministic-by-default, and signed end-to-end. No release is declared edge-supported until it passes the deterministic regression suite on Profile B.**

---

## 18. Execution plan

The architecture in Sections 4-16 is the target. The execution plan has two phases: a **24-hour hackathon sprint** that delivers a vertical slice end-to-end, and a **post-hackathon 10-week roadmap** that expands that slice to the full architecture.

### 18.1 Team and ownership

Four people. Ownership maps domain expertise to architectural layers.

| Person | Primary domain | Owns | 24-hour deliverables |
| --- | --- | --- | --- |
| **John** | Physics | Section 4.1 physics core, 5.3 ocean forcing, 8.3 acoustic environment, Stonefish tuning, wave / current / buoyancy, hydrodynamics | Stonefish environment running; both vehicles simulate stably; wave + current forcing active; sea-state presets switchable |
| **Robert** | Vehicle | Section 6 vehicle configs, 7 sensors, 8.1-8.2 per-vehicle nav stacks, 9 classical autonomy, 11 coupling | Both vehicle configs live; core sensors publishing; basic nav fusion; waypoint PID autonomy for both vehicles; GNSS-denial toggle on SSV |
| **Robbie** | Mission profiles, KPIs, environmental geometries | Section 5 archetypes, 12 scenario engine, 13 metrics and evaluation, 13.1-13.4 KPI definitions | Choke-point archetype generator; scenario YAML schema + validator; hero demo scenario; KPI pipeline with 3-5 metrics; comparison plot |
| **Yonatan** | Unreal Engine 5, UI, generalist glue | Section 14 Unreal layer, 16 bridge, integration support, optional web UI | UE5 project with archetype terrain + water; ROS 2 bridge streaming vehicle state; 2-3 camera presets (chase, top-down, drop cinematic); optional lightweight dashboard |

Coordination protocol:
- Shared Git repo. Feature branches per owner; merge to `main` via PR with domain-owner approval.
- Shared chat (Discord / Slack) in real time.
- Shared scenario YAML is the integration contract - anyone can propose changes, Robbie owns the schema.
- Hourly standups at T+2, T+6, T+12, T+18, T+22. Two-minute max per person.
- Integration checkpoint at T+12 is a hard gate. If end-to-end run does not produce a playable MCAP by T+12, scope cuts are mandatory.

### 18.2 24-hour hackathon sprint

Goal: deliver an end-to-end vertical slice of the architecture. One vehicle pair, one scenario, one archetype, one GNSS-denial event, MCAP recording, Unreal replay, KPI dashboard. Everything else in Sections 4-16 is scaffolded or stubbed.

#### 18.2.1 Aggressive scope cuts for 24 hours

Out of 24-hour scope (deferred to 10-week roadmap):

- **Custom CAD pipeline.** Use stock Stonefish Girona500 for AUV and stock Stonefish surface vessel (or borrowed VRX WAM-V coefficients) for SSV.
- **Full meshed drop handoff.** Simplified: both vehicles co-exist; drop is a scripted teleport + mode-switch, not a proper kinematic attach with state handoff.
- **Full nav cascade (SSV -> USBL -> AUV).** One-shot GNSS denial on SSV; AUV keeps nominal USBL. Full cascade is a Week 5-6 deliverable.
- **Five archetypes.** One archetype only: choke-point.
- **Layer 3 AI.** Scaffolding only. One stub anomaly detector that publishes but has no real model behind it. Demonstrates the interface contract, not real capability.
- **Layer 4 Evaluation AI.** Out. Classical metrics and plots only.
- **Autonomy beyond waypoint + station-keep.** Out.
- **Multi-seed sweep studies.** Token 2-3 seed run at most.
- **Safety invariants beyond geofence and max-depth.** Out; documented as deferred.

In scope for 24 hours:

- Stonefish running both vehicles in one scene.
- Procedural choke-point bathymetry.
- Core sensors per vehicle (IMU, depth, DVL, GNSS for AUV; GNSS, IMU, compass for SSV).
- Basic nav fusion via robot_localization with default config.
- Waypoint + PID control per vehicle.
- Scripted mission: SSV transits, releases AUV (teleport), AUV follows a short survey line, SSV loiters.
- GNSS-denial event on SSV at a scripted time; nav-mode transition logged.
- MCAP recording of the full run.
- Unreal live view + replay with 2-3 camera presets.
- KPI pipeline producing 3-5 metrics.
- Hero demo scenario locked as a YAML file in `main`.

#### 18.2.2 Phases

**Phase 1 (T+0 -> T+2) - Foundations.**

All four, parallel:
- All: clone repo, Docker dev env up, ROS 2 Jazzy working.
- John: stock Stonefish Girona500 demo running; ROS 2 topics verified.
- Robert: vehicle config scaffolding; pick stock SSV model.
- Robbie: scenario YAML schema + Pydantic validator; placeholder archetype generator scaffolded.
- Yonatan: UE5 project init; ROS 2 bridge decision (off-the-shelf plugin vs. thin custom).

**Phase 2 (T+2 -> T+6) - Parallel vertical slices.**

- John: both vehicles simulating in one Stonefish instance; wave + current forcing via JONSWAP preset and uniform current.
- Robert: IMU, depth, DVL, GNSS (AUV); GNSS, IMU, compass (SSV); PID waypoint controller per vehicle.
- Robbie: choke-point heightfield generator producing a Stonefish-ready scene; metrics node recording path RMS, time-to-complete, collision count into a SQLite or CSV.
- Yonatan: bridge streaming vehicle transforms into UE5; stock actor meshes attached to transforms; chase camera working.

**Checkpoint T+6:** Each person demos their vertical slice in a 10-minute round-robin. Integration gaps listed and prioritized.

**Phase 3 (T+6 -> T+12) - First integration.**

- All: branches merged; first end-to-end run attempt.
- John: physics tuning so neither vehicle explodes, sinks, or oscillates; steady heading hold.
- Robert: autonomy integration test - SSV transits a 3-waypoint path; AUV executes a short survey line.
- Robbie: hero scenario YAML written; scenario engine launches the ROS 2 graph; MCAP recording verified end-to-end.
- Yonatan: Unreal replay from MCAP OR live streaming (whichever is faster to ship); at least one working camera preset.

**Checkpoint T+12 (HARD GATE):** End-to-end run produces a playable MCAP. If not, invoke scope-cut protocol: drop to single-vehicle demo, drop GNSS event, drop Unreal polish.

**Phase 4 (T+12 -> T+18) - Demo features.**

- John: sea state switchable across 2 / 3 / 5; visibly different vehicle response.
- Robert: GNSS-denial event injection at scripted time; SSV nav-mode transition logged on `/ssv/nav_mode`; console shows state change.
- Robbie: demo scenario polished; KPI dashboard (Foxglove layout or static plots); 2-3 seed comparison of nominal vs. denied.
- Yonatan: Unreal polish - water surface, drop-event cinematic camera, vehicle skins. If time permits: Streamlit / Dash single-page UI showing run metadata and KPIs.

**Checkpoint T+18:** Full demo performable end-to-end; narration script drafted.

**Phase 5 (T+18 -> T+22) - Polish and backup.**

- All: second full dry-run.
- Fix any blockers. Re-record canonical MCAP.
- Lock demo scenario file; no more config changes.
- Capture screenshots and a backup video clip in case live sim fails on demo day.
- Prepare the "canned MCAP replay" fallback path.

**Phase 6 (T+22 -> T+24) - Final dry-runs and demo.**

- Two full dry-runs minimum, end-to-end with narration.
- Roles assigned for demo day: narrator, operator, backup operator.
- Backup plan rehearsed.
- Deliver demo.

#### 18.2.3 Deliverables at T+24

- `main` branch: running end-to-end, `docker compose up` or equivalent single-command bring-up.
- `scenarios/hero_choke_point_gnss_denied.yaml` - the canonical demo scenario.
- One canonical MCAP recorded from a dry-run, committed or archived.
- KPI dashboard accessible (Foxglove layout or web UI).
- 2-3 minute demo narration script.
- README with architecture diagram and quick-start.
- Backup video clip (2-3 minutes) of a successful dry-run.

#### 18.2.4 Risk protocol during the 24 hours

Specific hazards and pre-decided responses:

| Risk | Early warning | Response |
| --- | --- | --- |
| Stonefish build fails on someone's laptop | T+2 standup | Consolidate to John's machine; others work off shared SSH into his box |
| Vehicles unstable in physics | T+6 standup | John pins down; Robert uses lower-fidelity motion model temporarily |
| MCAP -> Unreal bridge flaky | T+12 checkpoint | Drop live stream; use MCAP replay only |
| GNSS-denial plumbing blocks everything | T+12 checkpoint | Drop to scripted `mode` flag injected via a topic; no full mode machine |
| UE5 performance too low | T+18 checkpoint | Drop to rviz2 for the demo; Unreal becomes "post-event" glamour shot only |
| Integration breaks at T+18+ | Any time after T+18 | Freeze last known good commit; no new features after T+18 |

### 18.3 Post-hackathon roadmap (10 weeks)

The 24-hour sprint is a vertical slice. The 10-week roadmap expands it to the full architecture, ordered by demo-to-effort return.

- **Week 2** - CAD pipeline: SolidWorks STEP + mass properties -> visual / collision / hydrodynamic meshes; replace stock models with real vehicles.
- **Week 3** - SSV proper Fossen dynamics; four more archetypes.
- **Week 4** - Full sensor layer: USBL, acoustic modem, imaging sonar, radar tracks, TAN.
- **Week 5** - Navigation stacks: `auv_nav` and `ssv_nav` with robot_localization; GNSS environment node with all six modes; nav-mode state machines.
- **Week 6** - Classical autonomy full scope + safety invariants + meshed drop with proper kinematic attach.
- **Week 7** - Scenario engine full schema; metrics pipeline with all nav-specific metrics; sweep harness.
- **Week 8** - Layer 3 AI: pre-trained YOLO on SSV camera, GNSS spoof detector, shadow mode, sandbox budgets.
- **Week 9** - Layer 4 Evaluation AI: failure clustering, scenario coverage, LLM-based sweep summarizer. Unreal polish.
- **Week 10** - 20-seed sweep study across sea state and GNSS mode with `ai_mode: off` and `ai_mode: on`. Comparison PDF. Stakeholder demo.

---

## 19. Risk register

1. **CAD mesh quality.** Bad collision meshes cause physics instability. Mitigation: V-HACD convex decomposition, automated spawn-and-settle tests.
2. **Mass properties mismatches.** Most common behavioral bug. Mitigation: single source of truth in `mass_properties.yaml`, tests that read it into both Stonefish XML and URDF.
3. **SSV hydrodynamic tuning.** Fossen coefficients from reference hulls need tuning. Mitigation: define a small library of step-response tests (turning circle, zig-zag) and tune to published expected behavior.
4. **Unreal-ROS 2 bridge performance.** Transform streaming can starve the ROS 2 graph. Mitigation: cap at 60 Hz, dedicated DDS partition or QoS profile, benchmark early.
5. **One Stonefish instance for both vehicles.** Architectural bet. Mitigation: coupling node is the only module that assumes it; splitting to two instances + env service is a week of work, not a rewrite.
6. **Scenario reproducibility with AI on.** AI modules may introduce non-determinism. Mitigation: pin weights, pin seeds, use fixed-precision inference, record model hash per run, provide `ai_mode: off` as the deterministic regression baseline.
7. **Navigation-fusion fidelity.** Real INS/DVL/USBL fusion is a research topic; MVP needs "credible," not "textbook." Mitigation: use an off-the-shelf EKF skeleton, tune by eye against expected position-drift rates. Document assumptions.
8. **Spoofing detection over-claim.** Easy to oversell AI-based spoof detection. Mitigation: report classical baseline detection latency alongside AI latency; report false-positive rates; honest eval report.
9. **AI budget overrun.** Inference may exceed CPU/GPU budget and stall the ROS 2 graph. Mitigation: bounded budgets enforced by sandbox node; automatic "stale advisory" flagging; Layer 2 never waits on AI.
10. **Layer violations.** Risk that AI modules are wired to actuators by accident. Mitigation: DDS permissions, guard node, CI test that attempts unauthorized publish and expects rejection.
11. **LLM summarizer hallucination.** Offline summaries may misrepresent data. Mitigation: constrain summaries to cite specific metrics and MCAP runs; human review before any report ships; prompt templates with explicit grounding.

---

## 20. What we explicitly do not do in MVP

- No real-site bathymetry ingest. Specifically: no BlueTopo pipeline, no NOAA chart GIS layers, no georeferenced coordinate transforms, no real shorelines or coastline meshes, no coverage uncertainty metadata, no AWS Open Data pipelines. All of this is replaced by the parameterized archetypes in Section 5.
- No kinetic / weapons layer.
- No launch-and-recovery (recovery is Phase 2).
- No hardware-in-the-loop.
- No multi-AUV / multi-SSV beyond 1+1.
- No learning-based controllers in the actuator path. Classical controls only for Layer 2. All learned components are Layer 3 advisory.
- No online learning. MVP AI models are fixed-weight.
- No RL / DRL for control. If explored, it is offline policy research in Layer 3 advisory mode only.
- No full acoustic propagation (Bellhop / Kraken). Acoustic environment is parameterized, not physically simulated.
- No blast / shockwave / cavitation modeling.
- No classified data path. Architecture supports swapping sensor / vehicle configs for a classified deployment later, but MVP is unclass.
- No HLA / DIS / TENA interop. Architectural seam left in the telemetry bus for a future gateway.
- No automatic scenario generation from Layer 4 recommendations into CI without human review.

---

## 21. Alignment with the problem statement

| Problem-statement demand | Where it lives in this design |
| --- | --- |
| Software-based maritime simulation environment | Sections 3, 4, 5, 15 (architecture, layers, env, repo) |
| Virtual testing and evaluation of AUVs and SSVs | Sections 11, 12, 13 (meshed sim, scenarios, metrics + Evaluation AI) |
| Across a range of ocean conditions | Section 5 (archetypes, sea state, current, visibility) and Section 8 (GNSS modes, acoustic environment) |
| Realistic, adaptable modeling | Section 6 (CAD-driven vehicles), Section 5 (parameterized env), Section 7 (fidelity tiers) |
| AI assistance for autonomy and evaluation | Section 10 (Layer 3 augmentation), Section 13.5 (Layer 4 Evaluation AI) |
| Reduce physical testing burden | Section 13 (comparison / sweep reports + Evaluation AI summaries), Section 12 (deterministic scenario files), Section 19 (reproducibility risk mitigations) |
| Edge deployability for military / on-prem partners | Section 17 (platform profiles, mission-essential core, offline invariants, compatibility matrix) |

---

## 22. Open questions to resolve before kickoff

1. Which vehicles are in scope for week 2-3? If CAD is still evolving, freeze a "demo vehicle" version and let design continue separately.
2. What IMU grade do we assume in the nominal nav_config? Drives drift expectations and tuning.
3. What is the demo compute environment? Unreal-grade visuals want a dedicated GPU (RTX 4070+). AI inference (even pre-trained) prefers a GPU. Single-box or two-box demo?
4. Which GNSS modes do we feature in the final stakeholder demo? Recommend `nominal -> jammed -> spoofed -> denied` progression to tell the cascade story in one run, and include the AI spoof-detection delta as a headline metric.
5. Which archetype is the hero scenario for demo day? Recommend `choke_point` with the Strait-of-Hormuz-style parameter set because it produces the richest nav-cascade behavior.
6. Which Layer 3 modules beyond the two MVP ones (perception + spoof detection) do we want stubbed for demo narrative (even if not fully implemented)? Recommend scaffolding all four categories (perception, planner, risk, anomaly) with at least placeholder advisories so the architecture story is complete.
7. What is the LLM choice for Layer 4 performance summarization? Local vs. API? Affects data-handling story for any classified deployment path.
