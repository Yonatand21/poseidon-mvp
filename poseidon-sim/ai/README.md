# ai (Layer 3 - AI augmentation, advisory only)

Runtime AI augmentation. Every module here is **advisory**. None may publish
actuator topics. Every module has a Layer 2 fallback that runs
unconditionally.

**Design reference:** `SYSTEM_DESIGN.md` Section 10 (AI augmentation layer)
and Section 4.3 (Layer 3 rules).

## Four categories

| Dir | Purpose | MVP? |
| --- | --- | --- |
| `perception/` | Learned sensor-to-semantic outputs (surface contacts, sonar classification, underwater objects, shoreline). | Partial - one pre-trained YOLO detector for SSV surface contacts. |
| `planner/` | Mission / route adaptation proposals (adaptive sweep, energy-aware transit, dynamic rendezvous, traffic-aware routing). | Scaffolding only. |
| `risk/` | Risk forecasts (mission success probability, sensor degradation, energy margin, nav denial forecast). | Scaffolding only. |
| `anomaly/` | Anomaly detectors (GNSS spoof, nav integrity, sensor fault, actuator health, acoustic anomaly). | Partial - one residual-based GNSS spoof detector. |

## Common infrastructure

| Dir | Purpose |
| --- | --- |
| `common/interfaces/` | `ai_advisory.msg`, `ai_anomaly.msg` schemas; base classes for advisory publishers. |
| `common/fallback/` | Shared helpers for Layer 2 classical fallbacks corresponding to each AI module. |
| `common/sandbox/` | CPU/GPU budget enforcement; stale-advisory flagging. |
| `common/model_registry/` | Model version lookup, hash verification, offline loader. |

## Non-negotiables

From [AGENTS.md](../../AGENTS.md):

1. No actuator publications. Enforced by DDS permissions and CI lint.
2. Every advisory records model version, file hash, and inference seed.
3. Layer 2 MUST NOT block on AI module availability.
4. `ai_mode: off` disables all AI inference; scenario still produces
   bit-identical outputs against the classical baseline.
5. `ai_mode: shadow` runs AI and logs advisories but Layer 2 ignores them.

## Topics

All published on `/ai/*`. See `SYSTEM_DESIGN.md` Section 16.
