# coupling (Layer 1 / 2)

Federation bridge and cross-runtime coupling services.

**Design reference:** `SYSTEM_DESIGN.md` Section 10 (Federated mission coupling)
and Section 14 (Interface contracts).

## Responsibilities

- Publish synchronized `/scenario/clock` from `/sim/auv/clock` and `/sim/ssv/clock`.
- Publish `/federation/runtime_health` and `/federation/sync_state`.
- Accept `/coupling/drop_cmd` and emit deterministic `/federation/drop_commit`.
- Serve as the authoritative event-ordering layer between DAVE (AUV) and VRX (SSV).

## Subdirs

- `src/federation_bridge.py` - MVP bridge implementation.
