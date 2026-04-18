# Backbone verification runbook

Verifies that the Yonatan backbone work (Dockerfiles, Compose,
Helm, bridge, UE5 scaffolding, setup scripts) actually runs - not just
that it lints. Four tiers ordered by time cost.

## Tiers

| Tier | Where | Time | Covers |
| --- | --- | --- | --- |
| **T0** | Any | ~1 min | Lints: yamllint, helm lint, docker compose config, uv lock, shellcheck, layer-permission lint. Runs in CI automatically. |
| **T1** | Mac M4 with Docker Desktop | ~10 min | Build poseidon-base-dev for the host arch, smoke-test ros2/python/uv, colcon-build the mock sim package, publish /auv/state, compose up the core profile. |
| **T2** | Mac M4 | ~3 min | Streamlit dashboard launches and reads recordings dir. |
| **T3** | Linux + NVIDIA GPU (cloud box) | ~60 min | setup-linux.sh end-to-end, cloud-demo-box.provision.sh, poseidon-sim image builds (Stonefish from source, ~30-45 min), full compose with GPU overlay, real /auv/state from Stonefish. |
| **T4** | Mac or Linux with UE5 5.4 installed | ~30 min | PoseidonUE.uproject compiles via UnrealBuildTool, Bridge/VehicleActor/CameraDirector resolve, rosbridge connection works from UE. |

Gate: **we do not push any commits until the tier appropriate to the
artifact has passed.** See below for which tier gates which commits.

---

## T0: Lints (already passing locally)

Run any time:

```bash
bash tools/setup-mac.sh --check                                         # Mac env
/tmp/poseidon-lint-venv/bin/yamllint -c .yamllint.yml .                 # YAML
helm lint charts/poseidon-platform                                       # Helm
docker compose -f deploy/compose/docker-compose.yml config --quiet       # Compose
docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.gpu.yml config --quiet
UV_CACHE_DIR=/tmp/uv-cache-poseidon uv lock --check                      # uv
shellcheck -S warning tools/*.sh docs/runbooks/*.sh poseidon-sim/rendering/bridge/*.sh
python3 tools/check_layer_permissions.py                                 # layer lint
```

All six commands exit 0.

## T1: Mac local Docker (one command)

**Run this before pushing any of the Dockerfile / compose / mock-sim commits.**

```bash
bash tools/verify-backbone-t1.sh
```

What it does (exits non-zero on any failure, logs to `.verify-t1.log`):

1. Checks Docker daemon is up.
2. `docker buildx build` `poseidon-base-dev` for the host arch
   (`linux/arm64` on M4, `linux/amd64` on Intel).
3. Runs inside the built image: `ros2 --help`, `python3 --version`,
   `uv --version`.
4. Mounts `poseidon-sim/auv_sim/mock` into the image, colcon-builds
   it, verifies `ros2 pkg list | grep poseidon_sim_mock`.
5. Runs the mock node for 3 seconds and confirms `/auv/state` is
   publishing with `ros2 topic hz`.
6. Brings up the `core` compose profile with local-tag images,
   confirms at least one service is running.
7. Tears down unless `--keep` is passed.

### Expected output

```
[PASS] docker daemon reachable
[PASS] poseidon-base-dev image present as poseidon-base-dev:verify-t1
[PASS] ros2 --help runs
[PASS] python3 runs
[PASS] uv runs
[PASS] poseidon_sim_mock colcon-builds and exposes mock_world executable
[PASS] mock sim publishes /auv/state
[PASS] compose core profile is up
[DONE] Tier 1 verification passed.
```

If any step fails, the log at `.verify-t1.log` has the full command
output. Paste it back into the thread for debugging.

### If T1 fails on the first build

Likely causes in order of probability:

- Docker Desktop resource limits too low. Settings -> Resources, bump
  CPUs to 8, memory to 12 GB, disk to 80 GB.
- ROS 2 apt key rotated upstream. Apt error about GPG signature would
  appear in the log - we would bump the key fetch line in the Dockerfile.
- Stonefish-only deps failed in base-dev (libsdl2, libglm). Those are
  in base-dev for downstream reuse; if one fails the Dockerfile needs
  a package-name update for Ubuntu 24.04.

## T2: Streamlit dashboard

```bash
# From repo root
cd poseidon-sim/evaluation/dashboards/web
uv run --with streamlit --with plotly streamlit run app.py \
    -- --recordings ../../../../recordings
```

Open <http://localhost:8501>. Expect "No runs yet" page (no MCAPs yet).
Pass = the page loads without exceptions in the terminal.

## T3: Linux + NVIDIA cloud box

Only run after T1 passes on the Mac.

```bash
# On the provisioned Ubuntu 24.04 + RTX 4090 instance
git clone https://github.com/Yonatand21/poseidon-mvp.git
cd poseidon-mvp

bash tools/setup-linux.sh --check          # should flag only NVIDIA toolkit missing
bash docs/runbooks/cloud-demo-box.provision.sh

# Build the heavy image. This is the 30-45 min one.
docker buildx build --platform linux/amd64 \
    -f deploy/docker/poseidon-sim.Dockerfile \
    -t poseidon-sim:verify-t3 .

# Bring up full compose with GPU overlay
docker compose \
    -f deploy/compose/docker-compose.yml \
    -f deploy/compose/docker-compose.gpu.yml \
    --profile core up -d

sleep 20
docker compose logs sim | tail -40
docker run --rm --network container:poseidon-mvp-sim-1 \
    poseidon-base-dev:latest ros2 topic hz /auv/state
```

Pass = Stonefish logs show sim stepping, `/auv/state` publishes at or
near the configured rate.

## T4: UE5 project

Only run after T1 passes. Requires UE5 5.4 installed locally OR on the
cloud box.

1. Open `poseidon-sim/rendering/unreal/PoseidonUE/PoseidonUE.uproject`
   in UE5 5.4.
2. When prompted "Missing PoseidonUE Modules, rebuild?", click Yes.
3. Expected: compile succeeds, editor opens.
4. Known risks documented in
   [`../architecture/0001-unreal-ros2-bridge.md`](../architecture/0001-unreal-ros2-bridge.md).

If compile fails, the error log goes at `.../Saved/Logs/`. Paste the
error back in the thread.

---

## Commit gating

| Tier passes | Safe to push |
| --- | --- |
| T0 only | Docs, README, setup scripts, CI workflow, layer-permission lint, ADRs, runbooks |
| T0 + T1 | base-dev.Dockerfile, poseidon-sim.Dockerfile (arm64 path only), mock sim package, docker-compose.yml, docker-compose.gpu.yml |
| T0 + T1 + T3 | poseidon-sim.Dockerfile (amd64 Stonefish path), GPU overlay in production use |
| T0 + T4 | UE5 project source (actors, cameras, bridge subsystem) |

This keeps the team from discovering a broken image the first time CI
runs.
