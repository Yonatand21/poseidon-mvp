# ADR-0002: UNav-Sim ROS 2 bridge

- Status: **Proposed**
- Date: 2026-04-19
- Deciders: Yonatan (owner), render track owner
- Supersedes: extends ADR-0001 for the cloud-box live-render path
  (`docs/architecture/0001-unreal-ros2-bridge.md`)

## Context

ADR-0001 adopted `rosbridge_websocket` as the UE5 bridge for the 24-hour
sprint. That decision was scoped to "PoseidonUE on macOS / Linux dev
hosts" and explicitly listed "macOS ARM64 plugin-build risk" as the
dominant constraint
([`0001-unreal-ros2-bridge.md`](0001-unreal-ros2-bridge.md) lines 134-141).

We are now ready to bring **UNav-Sim** online as the primary visual path
per `SYSTEM_DESIGN.md` Section 13. UNav-Sim is an AirSim-derived UE5
simulator targeting underwater robotics
([UNav-Sim paper](https://arxiv.org/abs/2310.11927),
upstream at <https://github.com/open-airlab/UNav-Sim>,
`OPEN_SOURCE_STACK.md` Section 2.2). UNav-Sim runs only on Linux with
NVIDIA GPU.

Verified upstream facts at the time of this ADR (GitHub API,
2026-04-19):

| Fact | Value | Implication |
| --- | --- | --- |
| Default branch | `main` | Pin a SHA, not a tag. |
| Latest commit | `593386c06850a88f8afc7fb0bec983fb52dda665` (2025-05-02) | Repo has been quiet for ~12 months. Maintenance risk is real; we do not get a steady upstream cadence. |
| Releases | None | Cannot pin a semver tag. Pin SHA per `AGENTS.md` Section 2. |
| UE5 target | **5.1** (built from source via EpicGames GitHub org) | Not 5.4. Source build requires Epic Games account linked to a GitHub identity in the EpicGames org. |
| Heritage | AirSim fork | "Native ROS bridge" actually means the AirSim RPC API surface plus UNav-Sim's `ros2/src/` packages, which are VSLAM consumers - not pose-driven actor controllers. |
| Native vehicles | BlueROV2 Heavy (AUV) | No surface vehicle. WAM-V is not shipped. |
| License | NOASSERTION (no SPDX) | Real concern - see Risks below. |
| Topics | `airsim, auv, bluerov2` | Confirms AUV-only positioning. |

Two of those facts changed the architectural picture relative to the
original framing of this ADR and are worth calling out explicitly:

1. **"UNav-Sim native bridge" is a misnomer.** The upstream project
   exposes camera streams through AirSim's standard
   `airsim_ros_pkgs`-derived layer, but it does not expose a
   "subscribe to `/auv/state` and move the actor" node. We have to
   write that bridge ourselves: a small ROS 2 node that subscribes to
   `/auv/state` and `/ssv/state` and calls AirSim's RPC
   `simSetVehiclePose(pose, ignore_collision, vehicle_name)` per
   message. This is materially the same work as PoseidonUE's
   `UPoseidonBridge` + `AVehicleActor`, just inside UNav-Sim's
   project. Calling it "native" understated the engineering cost.
2. **UNav-Sim is AUV-only.** The SSV (WAM-V) has no native render
   path. Either we import the WAM-V mesh as a custom AirSim
   Car-style vehicle with physics disabled, or we render the SSV in
   PoseidonUE separately. Both options are real; the MVP
   recommendation is below.

The architectural question this ADR answers: when UNav-Sim is the live
renderer on the cloud demo box, does the `/auv/state` -> rendered AUV
pose path go through (A) a custom POSEIDON pose-bridge ROS 2 node that
calls AirSim RPC inside the UNav-Sim image, or (B) our existing
`rosbridge_websocket` service consumed by a UNav-Sim plugin we'd have
to write?

This is **not** a question about layer authority. Per `AGENTS.md` Rule
1.2 and 1.3, UNav-Sim never owns simulation truth. DAVE remains the
authority for AUV state and AUV non-visual sensors. VRX remains the
authority for SSV state and SSV non-visual sensors. UNav-Sim subscribes
to those topics and renders them. AirSim's motor-PWM APIs
(`moveByMotorPWMsAsync`) and built-in physics MUST stay disabled so
UNav-Sim is a pure puppet. This ADR only governs the transport between
the ROS graph and UNav-Sim.

## Decision drivers

1. **Layer separation enforcement.** `AGENTS.md` Rule 1.1 forbids
   rendering from publishing actuator commands. The enforcement must
   be architectural, not social.
2. **Latency.** UNav-Sim renders perception-grade camera images that
   feed Layer 3 AI consumers. Per-frame latency on `/auv/state` and
   `/ssv/state` translates directly into actor-pose lag on rendered
   camera frames.
3. **Determinism.** Per `AGENTS.md` Section 2 and `SYSTEM_DESIGN.md`
   Section 16, MCAP replay must reproduce the same rendered frames
   for a fixed seed set. The transport must not introduce
   non-determinism.
4. **Cross-host portability.** PoseidonUE remains the fallback per
   `SYSTEM_DESIGN.md` Section 13 and runs on macOS dev workstations
   where UNav-Sim cannot. The fallback path must keep working.
5. **Operability under the layer-permission lint.**
   `tools/check_layer_permissions.py` validates the rosbridge
   allowlist. Whatever path UNav-Sim uses must be lintable for the
   same Rule 1.1 guarantee.
6. **Lifecycle coupling.** UNav-Sim is dormant upstream (~12 months
   since last commit). The transport choice should not couple our
   render uptime to upstream UNav-Sim release timing more than
   necessary, and we should be ready to fork or vendor if upstream
   stays cold.

## Options considered

### Option A - Custom POSEIDON pose-bridge ROS 2 node inside UNav-Sim image; `rosbridge_websocket` for fallback and replay

Inside the `unav-sim-render` container we run a small ROS 2 node we
write (`poseidon-sim/rendering/unav_sim/poseidon_pose_bridge/`) that
subscribes directly over DDS to `/auv/state`, `/ssv/state`, `/env/*`,
`/coupling/*`, `/scenario/*`, `/ai/anomaly/*` and applies them to
UNav-Sim actors via AirSim's RPC API
(`simSetVehiclePose`, world-parameter setters). Our `unreal-bridge`
(rosbridge_websocket) service stays deployed and continues to serve
PoseidonUE on macOS/dev workstations and the MCAP replay path
(`docs/runbooks/ue5-mcap-replay.md`).

Pros:

- Direct DDS link: ~1 ms latency, matches Option A in ADR-0001.
- No JSON serialization in the live cloud path; full bandwidth
  available for camera-stream publishing.
- Linux + NVIDIA host removes the macOS plugin-build risk that drove
  ADR-0001 to rosbridge in the first place. The original constraint
  does not apply here.
- PoseidonUE + rosbridge stays healthy as the fallback, so dev-laptop
  workflow and MCAP replay are unchanged.
- Layer-separation enforcement: the pose-bridge node has a checked-in
  subscription manifest. The same lint
  (`tools/check_layer_permissions.py`) extended one rule -
  "subscription manifest must not contain actuator topics" -
  enforces Rule 1.1 architecturally at config-time.
- The pose-bridge node is OURS. If UNav-Sim upstream stays dormant we
  can still maintain the ROS surface that matters to us.

Cons:

- We write and maintain a UNav-Sim-side ROS 2 node. Not free, but it
  is the same scope as Option B's WebSocket-side plugin (see below).
- Two transport implementations in the repo (DDS pose-bridge + JSON
  rosbridge), though they serve different lifecycles.
- The pose-bridge node depends on AirSim's RPC C++/Python client
  ABI. AirSim API surface has been stable for years, but it is an
  upstream we do not control.

### Option B - `rosbridge_websocket` for everything, including UNav-Sim

UNav-Sim consumes `/auv/state` etc. through our existing
`unreal-bridge` (rosbridge_websocket) service. We write a UE5 plugin
inside the UNav-Sim project that speaks the rosbridge JSON protocol
over WebSocket and applies updates to actors via AirSim RPC -
effectively the same engineering as PoseidonUE's `UPoseidonBridge`,
ported into UNav-Sim's project.

Pros:

- One transport, one allowlist, one place to enforce Rule 1.1.
- Identical wire format for live and replay paths - debuggable with
  `wscat` regardless of which renderer is active.
- No DDS in the UNav-Sim container.

Cons:

- JSON + WebSocket adds ~5-15 ms per message vs DDS. Not fatal, but
  meaningful when multiplied by camera-frame processing budgets.
- Requires writing a UE5 plugin inside UNav-Sim's project. UE5
  plugin work on a foreign UE5.1 project (built from source) is
  exactly the cost ADR-0001 picked rosbridge to avoid.
- UNav-Sim's project is AirSim-derived. UE5 plugins layered on
  AirSim have additional integration constraints that POSEIDON does
  not control.

## Decision

**Adopt Option A: custom POSEIDON pose-bridge ROS 2 node inside the
`unav-sim-render` container for the live cloud-box render path. Keep
`unreal-bridge` (rosbridge_websocket) deployed for PoseidonUE on dev
workstations and for the MCAP replay path on any host.**

Rationale:

1. The dominant constraint that drove ADR-0001 (macOS ARM64 plugin
   build risk) does not apply on the cloud demo box (Linux + NVIDIA).
   ADR-0001's "follow-up trigger" section already named host-platform
   change as a revisit condition.
2. Perception-grade rendering is the value UNav-Sim adds over
   PoseidonUE per `SYSTEM_DESIGN.md` Section 13. That value is
   largely wasted if camera-frame producers are bottlenecked behind a
   JSON serialization layer for their own pose updates.
3. The work surface is comparable between A and B. Both require a
   custom bridge component on the UNav-Sim side. A's bridge is a
   plain ROS 2 Python/C++ node we own outright; B's bridge is a UE5
   plugin compiled against UNav-Sim's foreign UE5.1 project.
   Maintenance cost over a year favors A.
4. Layer separation (Rule 1.1) is enforced at the same architectural
   strength via a checked-in subscription manifest + lint extension -
   not at network strength as in ADR-0001, but at config-time
   strength checked by CI. Acceptable trade for the latency win.
5. PoseidonUE is not orphaned. It remains the macOS-portable
   fallback per `SYSTEM_DESIGN.md` Section 13 and continues to
   consume the existing rosbridge allowlist. No work is thrown away.
6. MCAP replay path is unaffected because it always goes through
   `unreal-bridge` regardless of the renderer in use
   (`docs/runbooks/ue5-mcap-replay.md`).

## Decision (SSV asset coverage)

UNav-Sim has no native surface vehicle. Two sub-options:

- **A1 (recommended for MVP)**: UNav-Sim renders the AUV only.
  PoseidonUE renders the SSV. Both consume the same ROS topic
  contract via their respective bridges. Operationally a little
  busier (two renderers up during a demo), but each tool does what
  it is good at and there is no custom mesh import work for week 1.
- **A2 (Phase 2)**: Import VRX's WAM-V mesh into UNav-Sim as a
  custom AirSim Car-style vehicle with physics disabled. Visual
  parity but adds vehicle-plumbing work that UNav-Sim was not
  designed for.

Adopt A1 for MVP. Revisit when surface scenes become demo-critical.

## Consequences

- `deploy/docker/unav-sim.Dockerfile` (added in this PR as a
  skeleton) builds UE5.1 from source + UNav-Sim @
  `593386c06850a88f8afc7fb0bec983fb52dda665`. UE5 source clone
  requires an Epic Games GitHub identity provided as a build secret;
  see the TODO blocks in the Dockerfile.
- A new file
  `poseidon-sim/rendering/unav_sim/poseidon_pose_bridge/` (added in
  the integration PR) hosts the custom ROS 2 node. Owns the actual
  `simSetVehiclePose` calls.
- A new file
  `poseidon-sim/rendering/unav_sim/subscription_manifest.yaml`
  (added in the integration PR) declares exactly which topics the
  pose-bridge node subscribes to. The manifest is the source of
  truth for Rule 1.1 compliance on the live render path.
- `tools/check_layer_permissions.py` gains a third rule:
  `subscription_manifest.yaml` must not contain any of the four
  actuator topics. Lint failure blocks merge.
- A new file
  `poseidon-sim/rendering/unav_sim/airsim_settings.json` (added in
  the integration PR) is the AirSim settings file that disables
  vehicle physics on every spawned actor. Mounted into
  `~/Documents/AirSim/settings.json` in the container.
- `unreal-bridge` (rosbridge_websocket) compose service stays in the
  `viz` profile and keeps serving PoseidonUE + MCAP replay. No
  regression to the existing path.
- `unav-sim-render` compose service builds the new Dockerfile under
  the `viz` profile. Until the integration work lands, the service
  starts and `sleep infinity`s with a TODO banner, mirroring the
  pattern Robert used for `sim-ssv-vrx.Dockerfile` while it was a
  skeleton.
- For MVP per A1, SSV continues to render in PoseidonUE only;
  UNav-Sim renders AUV only. Both renderers can run simultaneously
  during demo if needed.
- Camera-stream publishing back into ROS (`/auv/sensors/camera`) is
  AirSim's responsibility once configured via `settings.json`.
  Document those topics in the subscription manifest as outbound
  publishes for clarity.

## Risks

1. **Upstream UNav-Sim is dormant.** Last commit 2025-05-02; no
   releases. If our pinned SHA reveals a critical bug we cannot get
   an upstream fix. Mitigation: vendor the UNav-Sim source under
   `vendor/unav-sim/` if it becomes load-bearing, or fork to
   `Yonatand21/unav-sim`. Track this as a follow-up trigger.
2. **License is NOASSERTION upstream.** GitHub API reports
   `license.spdx_id = "NOASSERTION"`. The README says "View
   license" but the file is not a recognized SPDX identifier.
   Before we ship a binary that statically links UNav-Sim or
   AirSim, the integration PR MUST clarify the license with the
   open-airlab maintainers (open a GitHub issue) and record the
   answer alongside `OPEN_SOURCE_STACK.md` Section 2.2.
3. **Epic Games credential handling.** UE5 source build requires
   personal credentials. CI cannot easily build this image; document
   that the cloud demo box performs the build manually and the
   resulting layer is cached, not rebuilt per PR. `AGENTS.md`
   Section 3 (offline-installable) is preserved at deploy time but
   needs an attended bootstrap.
4. **Ubuntu version.** UNav-Sim is upstream-tested on Ubuntu 22.04;
   `poseidon-base-dev` is Ubuntu 24.04. Validate the build on Noble
   in the integration runbook; downgrade to Jammy in
   `unav-sim.Dockerfile` if needed without touching `base-dev`.

## Follow-up trigger: when to revisit

Revisit this decision and consider migrating to Option B (rosbridge
for UNav-Sim too) when any of:

- Measured live-path latency for `/auv/state` to rendered actor pose
  exceeds 10 ms on the cloud box. (Either path should be well under
  this budget; if Option A is not, we have lost the original
  justification.)
- AirSim RPC API changes break our pose-bridge node more than once
  per six months.
- macOS becomes a supported live-render host and the macOS ARM64
  plugin-build risk reasserts itself.
- UNav-Sim upstream stays dormant past 18 months and we have to
  fork; at that point we may simplify by collapsing onto a single
  transport.

## References

- `SYSTEM_DESIGN.md` Sections 13, 14, 16.
- `AGENTS.md` Rules 1.1, 1.2, 1.3, 1.5; Sections 2 (determinism),
  3 (edge posture).
- `OPEN_SOURCE_STACK.md` Section 2.2 (UNav-Sim).
- ADR-0001 ([`0001-unreal-ros2-bridge.md`](0001-unreal-ros2-bridge.md)).
- UNav-Sim upstream: <https://github.com/open-airlab/UNav-Sim>
  pinned at `593386c06850a88f8afc7fb0bec983fb52dda665`.
- UNav-Sim paper: <https://arxiv.org/abs/2310.11927>.
- AirSim API reference for `simSetVehiclePose`:
  <https://microsoft.github.io/AirSim/api_docs/html/>.
- `docs/runbooks/ue5-mcap-replay.md` (replay path, unchanged by
  this ADR).
