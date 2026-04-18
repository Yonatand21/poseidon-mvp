# ADR-0001: Unreal Engine <-> ROS 2 bridge

- Status: **Accepted**
- Date: 2026-04-18
- Deciders: Yonatan (owner), open to team input
- Supersedes: N/A

## Context

Unreal Engine 5 is the visual consumer of POSEIDON state (`SYSTEM_DESIGN.md`
Section 14). It needs to receive:

- Vehicle transforms (`/auv/state`, `/ssv/state`) at up to 60 Hz for
  smooth rendering.
- Environment state (sea state, visibility, time-of-day) at ~5 Hz.
- Discrete events: `/coupling/drop_cmd`, nav-mode transitions, alerts.

UE5 must **never** publish actuator commands (`AGENTS.md` Rule 1.1), which
eliminates the usual simulator-style bidirectional bridge. This is a
read-mostly path with a small command surface (drop-event trigger from
UI for demos, scenario clock control).

The team runs UE5 on macOS (light editor use) and on a Linux + NVIDIA
cloud box (demo rendering). The ROS 2 graph runs only in containers and
is always Linux.

## Decision drivers

1. **Time-to-first-frame.** 24-hour sprint deliverable (`SYSTEM_DESIGN.md`
   Section 18.2.2) needs a vehicle actor visibly moving in UE5 by
   checkpoint T+12.
2. **Cross-platform.** Must work on macOS ARM64 editor and Linux amd64
   runtime.
3. **Plugin build risk.** UE plugins have to match the UE version and the
   compiler toolchain. Upgrading UE later is a plugin rebuild every time.
4. **Frame rate.** 60 Hz TF streaming is the visual quality bar for
   demo. 20-30 Hz is acceptable for T+12 checkpoint.
5. **Debuggability.** When the demo breaks the night before, we want to
   inspect the wire format without recompiling UE.
6. **Layer separation.** UE cannot smuggle actuator commands back to ROS
   2. The bridge protocol must make that architecturally impossible, not
   just socially discouraged.

## Options considered

### Option A - rclUE

Source: <https://github.com/rapyuta-robotics/rclUE>

Mature Unreal plugin wrapping `rclcpp`. Used by Open-RMF. C++. Supports
publishers, subscribers, services, actions.

Pros:
- First-class ROS 2 performance; direct DDS link, 60+ Hz TF feasible.
- One codebase for all message types via ROS 2 IDL codegen.
- Well-documented, actively maintained.

Cons:
- Must be rebuilt per UE version (5.4, 5.5, ...).
- Brings `rclcpp` + DDS into the UE process - adds ~50 MB of libs and
  increases UE cook time.
- macOS support is experimental; the plugin is battle-tested on Linux +
  Windows only. Apple Silicon is untested territory.
- Steeper learning curve; adding a new ROS message type means IDL
  generation inside the UE build.
- Layer-separation enforcement is by code review only; nothing prevents
  a future contributor from calling `CreatePublisher<Thrust>` for an
  actuator topic.

### Option B - UNav-Sim's built-in bridge

Source: <https://arxiv.org/abs/2310.11927>, repo per `OPEN_SOURCE_STACK.md`
Section 2.2.

UNav-Sim is an underwater-specific UE5 simulator that ships with its own
ROS 2 integration. Since we are already adopting UNav-Sim for underwater
visuals, we could reuse its bridge.

Pros:
- Zero incremental adoption cost if we are already pulling UNav-Sim in.
- Purpose-built for underwater vehicle topics.

Cons:
- Couples our bridge lifecycle to UNav-Sim releases.
- UNav-Sim's bridge design (at time of this ADR) is closely tied to its
  own vehicle abstraction; using it for our `/auv/state` and `/ssv/state`
  topics may require adapter layers.
- Licensing path unclear at the time of decision (MIT per repo check,
  but needs double-check before we depend on it structurally).
- macOS support same concern as rclUE; UNav-Sim assumes Linux-first.

### Option C - rosbridge_websocket + JSON

Source: <https://github.com/RobotWebTools/rosbridge_suite>

A small ROS 2 node (`rosbridge_server`) serves a WebSocket endpoint that
accepts JSON-serialized ROS messages. UE connects as a plain WebSocket
client. No UE plugin to build; UE uses the built-in `FWebSocketsModule`
plus `FJsonObject`.

Pros:
- No UE plugin build, no DDS inside UE, no platform-specific binaries.
  Runs identically on macOS ARM64, Linux amd64, and Windows.
- Bridge is a ROS 2 node on the server side - same deploy/debug model as
  any other node.
- Wire format is human-readable; `wscat` + a scenario playback gives
  instant visibility.
- **Architectural layer-separation enforcement:** the
  `rosbridge_server` runs with a restricted topic allowlist via its
  own config. We allowlist only `/auv/state`, `/ssv/state`, `/env/*`,
  `/coupling/*`, `/ai/anomaly/*` for UE subscription. Actuator topics
  are not exposed - UE literally cannot see them over the socket.
- Easiest disaster-recovery: if UE breaks, the Python
  `rosbridge_server` keeps publishing and we can attach any other
  client.

Cons:
- JSON + WebSocket has higher per-message overhead than direct DDS.
  Benchmarks elsewhere show ~1000-2000 Hz throughput ceiling; we need
  60 Hz, well inside the ceiling but with higher per-message CPU than
  Option A.
- No native ROS 2 message type generation in UE; we write light C++
  adapters per message type (one-time, ~30 min per type).
- Latency ~5-15 ms added vs Option A's ~1 ms.

## Decision

**Adopt Option C (rosbridge_websocket) for the 24-hour sprint and Weeks
1-2. Re-evaluate Option A or B in Week 3 once we have measured actual
throughput demands.**

Rationale:

1. **Time-to-first-frame risk is the dominant constraint.** Option A /
   B both have real plugin build-time risk on macOS ARM64 that we
   cannot de-risk in 24 hours. Option C is a guaranteed "first frame
   in 2 hours" path.
2. **The layer-separation story is actually stronger with Option C.**
   The allowlist in the rosbridge config makes it architecturally
   impossible for UE to see actuator topics, which directly enforces
   `AGENTS.md` Rule 1.1 at the network layer.
3. **60 Hz is comfortable.** Profile runs (public benchmarks, our own
   spot-checks on this ADR) show rosbridge JSON + WebSocket supports
   well over 1 kHz for simple TransformStamped payloads; 60 Hz is not
   near the ceiling.
4. **Cross-platform comes for free.** `FWebSocketsModule` is in vanilla
   UE; no plugin build anywhere.
5. **Migration path is cheap.** If Week 3 profiling shows we are CPU-
   bound on JSON serialization or need sub-5-ms latency for a specific
   metric, the bridge abstraction on the UE side (a `UPoseidonBridge`
   UObject) stays the same; only the transport implementation swaps.

## Consequences

- `poseidon-sim/rendering/bridge/` hosts the rosbridge launch + allowlist
  config. It is a ROS 2 Python node (actually `rosbridge_server` invoked
  with a subset config).
- `poseidon-sim/rendering/unreal/PoseidonUE/Source/PoseidonUE/`
  grows a `Bridge/` subfolder with one `UPoseidonBridge` UObject that
  owns the WebSocket connection, and per-topic subscriber UObjects
  (`UAuvStateSubscriber`, `USsvStateSubscriber`, ...).
- The bridge is deployed as a new compose service named
  `unreal-bridge` (already declared in
  [`deploy/compose/docker-compose.yml`](../../deploy/compose/docker-compose.yml)).
- Message types supported at sprint time: `nav_msgs/Odometry`,
  `geometry_msgs/TransformStamped`, `std_msgs/String`,
  `std_msgs/Float32MultiArray`. More added as needed.
- Layer-permission lint (`tools/check_layer_permissions.py`) learns a
  second rule: `rosbridge_allowlist.yml` in the bridge dir must not
  contain any actuator topic. Added when the real lint lands.

## Follow-up trigger: when to revisit

Revisit this decision and consider migrating to rclUE when any of:

- Measured TF stream throughput exceeds 250 Hz and we need to go higher.
- JSON serialization shows up as >10% of the UE frame budget in a
  profiler.
- A second UE-native feature (e.g. reverse commands to trigger scenario
  resets) needs sub-5-ms latency.
- Windows becomes a supported host for team contributors and rclUE's
  Windows support is preferable to WebSocket there.

## References

- `SYSTEM_DESIGN.md` Sections 14, 16.
- `AGENTS.md` Rule 1.1 (actuator authority).
- `OPEN_SOURCE_STACK.md` Section 2.2 (Unreal + UNav-Sim).
- rclUE: <https://github.com/rapyuta-robotics/rclUE>
- rosbridge_suite: <https://github.com/RobotWebTools/rosbridge_suite>
- UNav-Sim paper: <https://arxiv.org/abs/2310.11927>
