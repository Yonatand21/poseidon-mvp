# coupling (Layer 1 / 2)

Carries / drop handoff state machine and the AUV-SSV comms pipe.

**Design reference:** `SYSTEM_DESIGN.md` Section 11 (Meshed SSV + AUV with
drop handoff) and Section 16 (Coupling topics).

## Responsibilities

- Track whether the AUV is carried by the SSV or free.
- On `/coupling/drop_cmd`, capture SSV pose and velocity, write them as the
  AUV's initial state, switch the AUV from kinematic to dynamic mode, hand
  control to AUV autonomy.
- Publish `/coupling/payload_state`.
- Model the acoustic + RF comms pipe with range cutoff, fixed latency,
  range-dependent drop, and depth-gated mode selection. Three configs:
  `perfect`, `nominal`, `degraded`.
- Publish `/coupling/comms_link` messages with source, dest, payload,
  send_time, receive_time, dropped flag.

## Subdirs

- `src/` - coupling node and comms-pipe node implementations.
