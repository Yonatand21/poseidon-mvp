# tools (top-level)

Repo-wide developer tools. Not shipped with the runtime.

Distinct from `poseidon-sim/tools/` which is application-scoped (CAD
pipeline, archetype preview).

## Contents

| File | Purpose |
| --- | --- |
| `setup-mac.sh` | Idempotent toolchain installer for macOS. See [`docs/runbooks/dev-setup.md`](../docs/runbooks/dev-setup.md) Mac section. |
| `setup-linux.sh` | Idempotent toolchain installer for Linux (Ubuntu / Debian / Fedora / RHEL / WSL2 Ubuntu). Auto-detects apt vs dnf. See the dev-setup runbook. |
| `check_layer_permissions.py` | CI lint placeholder enforcing [`AGENTS.md`](../AGENTS.md) Rule 1.1. Planned implementation described in the script docstring. |

## Usage

From the repo root:

```bash
bash tools/setup-mac.sh               # install on macOS
bash tools/setup-mac.sh --check       # verify-only
bash tools/setup-linux.sh             # install on Linux / WSL2
bash tools/setup-linux.sh --check     # verify-only
python3 tools/check_layer_permissions.py   # no-op today, CI gate
```

Both setup scripts are idempotent - safe to re-run after a main pull or
after your laptop reboots.
