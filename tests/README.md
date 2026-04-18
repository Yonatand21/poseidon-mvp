# tests

Three test trees with distinct charters.

## Layout

| Dir | Charter |
| --- | --- |
| `unit/` | Pure-Python unit tests. Fast, no ROS 2 graph, no Stonefish. |
| `integration/` | ROS 2 topic contracts, scenario-engine launches a small graph, metrics pipeline end-to-end on recorded MCAPs. |
| `determinism/` | **Release gate for Profile B edge support.** Asserts bit-identical ground-truth outputs for fixed scenario + seed + `ai_mode: off`. See `SYSTEM_DESIGN.md` Section 17.3 and `INFRASTRUCTURE_DESIGN.md` Section 11. |

## Running

```
uv run pytest tests/unit
uv run pytest tests/integration   # requires Docker Compose stack up
uv run pytest tests/determinism   # release gate; slow
```

## Release gate

A release is not declared edge-supported until `tests/determinism/` passes
on Profile B (Ubuntu 22.04 + ROS 2 Humble).
