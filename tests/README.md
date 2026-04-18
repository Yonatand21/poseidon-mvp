# tests

Test suites for POSEIDON.

## Layout

| Dir | Charter |
| --- | --- |
| `unit/` | Fast local tests without full runtime graph. |
| `integration/` | End-to-end ROS graph tests with dual runtimes and federation bridge. |
| `determinism/` | Release gate for seeded reproducibility in federated mode. |

## Running

```bash
uv run pytest tests/unit
uv run pytest tests/integration
uv run pytest tests/determinism
```
