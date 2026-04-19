# unav-sim.Dockerfile - PRIMARY visual rendering image (Layer 5).
#
# Track: rendering. Playbook: docs/runbooks/integration-unav-sim.md (TBD).
# Architecture: SYSTEM_DESIGN.md Section 13 (UNav-Sim primary, PoseidonUE
# fallback), ADR-0002 (UNav-Sim on the cloud box uses an AirSim RPC
# bridge for the live render path; rosbridge stays for fallback +
# replay).
#
# Upstream: https://github.com/open-airlab/UNav-Sim
# UNav-Sim is an AirSim-derived UE5 simulator targeting underwater
# robotics (BlueROV2 Heavy is the canonical vehicle). License is
# NOASSERTION upstream as of UNAV_SIM_REF below; see ADR-0002 for the
# license-clarification follow-up.
#
# This file is a SKELETON. Each TODO block must be filled in by the
# rendering integration track. Until those land, the unav-sim-render
# compose service builds this image and runs `sleep infinity` with a
# banner, mirroring Robert's pattern for sim-ssv-vrx.Dockerfile while
# it was being scaffolded.
#
# Hard host requirement: Linux + NVIDIA GPU. UNav-Sim does not run on
# macOS ARM64. Ubuntu 22.04 (Jammy) is the upstream-tested target;
# Ubuntu 24.04 (Noble, our base-dev image) needs validation - track in
# the integration runbook. See docs/runbooks/cloud-demo-box.md.
#
# Architecture invariants (do not violate while wiring this up):
# - AGENTS.md Rule 1.1: rendering MUST NOT publish actuator topics.
#   UNav-Sim ships motor-PWM APIs (moveByMotorPWMsAsync) - those MUST
#   stay disabled. We only WRITE actor poses; we never read or send
#   any thrust command back into the ROS graph.
# - AGENTS.md Rule 1.2: UNav-Sim is NEVER the source of truth. DAVE
#   owns AUV state; VRX owns SSV state. UNav-Sim's built-in vehicle
#   physics (PhysX-style AirSim dynamics) MUST be disabled - actors
#   are puppets driven by ROS subscriptions only.
# - AGENTS.md Rule 1.5: UNav-Sim consumes /auv/state and /ssv/state
#   from Layer 1; it does NOT consume Layer 2 state estimates.
# - AGENTS.md Section 2: UE5_VERSION and UNAV_SIM_REF below are
#   pinned. Record both in MCAP run metadata.
# - AGENTS.md Section 3: no runtime apt install / pip install / model
#   download. Everything pinned and offline-installable.

ARG BASE_IMAGE=ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev
# hadolint ignore=DL3006
FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.source="https://github.com/Yonatand21/poseidon-mvp"
LABEL org.opencontainers.image.description="POSEIDON MVP UNav-Sim renderer (Layer 5)"
LABEL poseidon.component="unav-sim-render"

# UE5 release tag that UNav-Sim targets per the upstream README.
# Verified at https://github.com/open-airlab/UNav-Sim @ 593386c.
ARG UE5_VERSION=5.1
ARG UE5_INSTALL_PREFIX=/opt/UnrealEngine

# UNav-Sim has no upstream releases; we pin main HEAD as of
# 2025-05-02 (latest commit at the time of ADR-0002).
# Verified via GitHub API:
#   GET /repos/open-airlab/UNav-Sim/commits/main
ARG UNAV_SIM_REF=593386c06850a88f8afc7fb0bec983fb52dda665
ARG UNAV_SIM_PREFIX=/opt/unav-sim

ARG DEBIAN_FRONTEND=noninteractive

USER root

# TODO(rendering): build UE5.1 from source.
# UE5 binaries are not freely redistributable; the Epic license
# requires source builds for derivative works. The integrator must:
#   1. Be a member of the EpicGames GitHub organization (link Epic
#      Games account at https://www.unrealengine.com/account/connections).
#   2. Provide a clone token / SSH key with EpicGames org access at
#      build time, e.g. via BuildKit secret:
#        --secret id=epic_token,src=$HOME/.epic_token
#   3. Run roughly:
#        git clone -b ${UE5_VERSION} \
#            https://oauth2:$(cat /run/secrets/epic_token)@github.com/EpicGames/UnrealEngine.git \
#            ${UE5_INSTALL_PREFIX}
#        cd ${UE5_INSTALL_PREFIX} && ./Setup.sh && ./GenerateProjectFiles.sh && make
#   Note: this build takes ~1 hour and ~100 GB on a cloud GPU box.
#   Cache the built UE5 layer aggressively to avoid rebuilds.

# TODO(rendering): GPU + Vulkan runtime libraries for headless render.
# Per upstream README troubleshooting, Ubuntu 22.04 needs vulkan-tools
# (NOT vulkan-utils, which is the older Ubuntu 20.04 name). Our base
# image is currently Ubuntu 24.04, which uses vulkan-tools - same
# package name. Coordinate with deploy/compose/docker-compose.gpu.yml.
#
# hadolint ignore=DL3008,DL3015
# RUN apt-get update && apt-get install -y --no-install-recommends \
#         libvulkan1 \
#         vulkan-tools \
#         && rm -rf /var/lib/apt/lists/*

# TODO(rendering): clone and build UNav-Sim against UE5.1.
# Steps mirror the upstream README (sections 1.2 and 1.3):
#
# RUN git clone https://github.com/open-airlab/UNav-Sim.git ${UNAV_SIM_PREFIX} && \
#     cd ${UNAV_SIM_PREFIX} && git checkout ${UNAV_SIM_REF} && \
#     ./setup.sh && ./build.sh
#
# Then build the Blocks example environment (or our scenario world)
# against the UE5 install:
#   cd ${UNAV_SIM_PREFIX}/Unreal/Environments/Blocks
#   ${UE5_INSTALL_PREFIX}/Engine/Build/BatchFiles/Linux/Build.sh \
#     BlocksEditor Linux Development \
#     -project="$PWD/Blocks.uproject" -waitmutex

# TODO(rendering): import vehicle visual assets.
# UNav-Sim ships with BlueROV2 Heavy (AUV) by default. Asset coverage
# we need:
#
# - AUV: BlueROV2 Heavy is acceptable for MVP. If we want to render
#   DAVE's actual AUV asset (RexROV / LAUV / Kingfisher) for visual
#   parity with the physics runtime, import the .dae/.obj from the
#   DAVE package or vehicles/auv_kingfisher/meshes/.
#
# - SSV: UNav-Sim has NO native surface vehicle. WAM-V is not
#   shipped. Two options to evaluate (decision deferred to the
#   integration PR):
#     A) Import VRX's WAM-V mesh into UNav-Sim as a custom AirSim
#        Car-style vehicle with physics disabled. Visual parity with
#        VRX runtime, but adds custom vehicle plumbing.
#     B) Render SSV in PoseidonUE only. UNav-Sim renders AUV only.
#        Cleaner separation but two UE5 projects to maintain.
#   Per ADR-0002 Consequences, B is the MVP recommendation; revisit
#   for full visual demo if surface scenes are demo-critical.
#
# Important: imported meshes are VISUAL only. Disable any physics or
# collision components AirSim auto-attaches. Per AGENTS.md Rule 1.2,
# vehicle dynamics live in DAVE/VRX, never here.

# TODO(rendering): write the POSEIDON pose-bridge node.
# UNav-Sim does NOT ship a "subscribe to /auv/state and move actor"
# node out of the box. Its ROS 2 packages at ${UNAV_SIM_PREFIX}/ros2/src
# are visual-localization consumers (VSLAM), not pose-driven actor
# controllers. We need a small ROS 2 node that:
#
#   1. Subscribes to /auv/state and /ssv/state (nav_msgs/Odometry).
#   2. Calls AirSim's RPC simSetVehiclePose(pose, ignore_collision,
#      vehicle_name) for each message.
#   3. Optionally subscribes to /env/visibility, /env/wave_state,
#      /coupling/drop_cmd and adjusts world parameters.
#
# This node lives at:
#   poseidon-sim/rendering/unav_sim/poseidon_pose_bridge/
# (added in the integration PR, not this skeleton).
#
# The subscription manifest at
#   poseidon-sim/rendering/unav_sim/subscription_manifest.yaml
# (added in the integration PR) is the source of truth for which
# topics this node subscribes to. tools/check_layer_permissions.py
# will lint that file against the actuator-topic blocklist (ADR-0002
# Consequences).
#
# Required subscriptions for MVP:
#   /auv/state                       (nav_msgs/Odometry)
#   /ssv/state                       (nav_msgs/Odometry)  [if Option A above]
#   /env/visibility                  (std_msgs/Float32)
#   /env/wave_state                  (std_msgs/Float32MultiArray)
#   /env/wind                        (geometry_msgs/Vector3Stamped)
#   /coupling/drop_cmd               (std_msgs/Empty)
#   /scenario/clock                  (builtin_interfaces/Time)
#   /scenario/event                  (std_msgs/String)
#   /ai/anomaly/gnss_spoof_flag      (std_msgs/Bool)
#   /ai/anomaly/nav_integrity_score  (std_msgs/Float32)
#
# Required publishes back into ROS (UNav-Sim/AirSim cameras):
#   /auv/sensors/camera              (sensor_msgs/Image)
#   /ssv/sensors/camera              (sensor_msgs/Image)  [if Option A above]
#
# Forbidden subscriptions (will fail layer-permission lint):
#   /auv/thruster_cmd, /auv/fin_cmd
#   /ssv/thruster_cmd, /ssv/rudder_cmd
# Anything under /<vehicle>/state_estimate (Layer 2 territory).

USER poseidon
WORKDIR /workspace

# AirSim settings file lives here per upstream README section 2.
# The integration PR will mount or copy a POSEIDON-specific
# settings.json that disables AirSim physics on every vehicle and
# routes camera streams to the topic names above.
ENV AIRSIM_SETTINGS_DIR=/home/poseidon/Documents/AirSim

# TODO(rendering): replace the placeholder CMD once UNav-Sim is wired.
# Final CMD will look approximately like:
#   CMD ["bash", "-lc", \
#        "source /opt/ros/${ROS_DISTRO}/setup.bash && \
#         ros2 launch /workspace/poseidon-sim/rendering/unav_sim/unav_sim.launch.py \
#             scenario_seed:=${POSEIDON_SCENARIO_SEED:-42}"]
CMD ["bash", "-lc", \
     "echo 'unav-sim-render skeleton - awaiting integration per ADR-0002 + integration-unav-sim runbook' && \
      echo \"  upstream: https://github.com/open-airlab/UNav-Sim @ ${UNAV_SIM_REF}\" && \
      echo \"  ue5: ${UE5_VERSION} (built from source, requires Epic Games credentials)\" && \
      sleep infinity"]
