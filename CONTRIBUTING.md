# Contributing to POSEIDON MVP

## Before you start

1. Read `README.md`, then `SYSTEM_DESIGN.md` Sections 1-4 and 18.
2. Read `AGENTS.md`. The invariants there are non-negotiable.
3. Skim `OPEN_SOURCE_STACK.md` Section 2 for the component your change touches.

## Development environment

```
git clone <repo>
cd poseidon-mvp
uv sync                      # Python environment
pre-commit install           # commit hooks
docker compose -f deploy/compose/docker-compose.yml config --quiet
helm lint charts/poseidon-platform
```

## Branching

- `main` is protected. Require passing CI + at least one CODEOWNER approval.
- Feature branches: `<owner>/<scope>-<short-desc>`, e.g. `robert/auv_nav-ekf-tuning`.
- Rebase on `main` before merging. Prefer small, reviewable PRs.

## Commit messages

Follow Conventional Commits where practical:

```
feat(scenario_engine): add YAML schema for acoustic_nav
fix(auv_nav): clamp DVL innovation gate on water-lock transition
docs(system_design): clarify nav cascade diagram
chore(ci): add helm lint to CI matrix
```

The first line is imperative and under 72 chars. Body explains the why, not
the what.

## Pull request checklist

- [ ] CI green.
- [ ] `AGENTS.md` rules respected (layer separation, determinism, offline-first).
- [ ] New module has a `README.md` citing its design section.
- [ ] Any change to `poseidon-sim/autonomy_*` or `poseidon-sim/ai/**` reviewed
      by the module's CODEOWNER.
- [ ] Any new Python dep justified in the PR description; license recorded in
      `OPEN_SOURCE_STACK.md`.
- [ ] Any new container image is signed (cosign) and scanned (grype/trivy)
      before release; PR flagged accordingly if adding one.
- [ ] No emojis added to code.

## Large artifacts

CAD, meshes, AI model weights, and MCAP recordings go through Git LFS.
See `.gitattributes` for tracked extensions. Do not commit binary blobs as
regular Git objects.

## Code style

- Python: ruff + black defaults (configured in `pyproject.toml` when deps land).
- C++: clang-format with Google or ROS 2 style (decided per-package; configured
  when the first C++ package lands).
- YAML: 2-space indent, no trailing whitespace, enforced by yamllint.
- Markdown: markdownlint-cli2 defaults.

## Tests

- Unit tests in `tests/unit/` for pure-Python logic.
- Integration tests in `tests/integration/` exercising ROS 2 topic contracts.
- Determinism tests in `tests/determinism/` assert bit-identical outputs for
  fixed scenario + seed + `ai_mode: off`.
- A release is not edge-supported until the deterministic regression suite
  passes on Profile B (Ubuntu 22.04 + ROS 2 Humble).

## Reporting issues

Open a GitHub issue with:

- Repro scenario YAML + seed.
- Expected vs. observed behavior.
- Platform profile (A or B), OS version, ROS 2 distro.
- MCAP attached or linked from object storage.
