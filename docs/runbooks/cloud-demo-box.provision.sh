#!/usr/bin/env bash
# cloud-demo-box.provision.sh
#
# One-shot provisioner for the shared POSEIDON cloud demo box
# (Ubuntu 24.04 + NVIDIA RTX 4090). Idempotent. Run AFTER
# tools/setup-linux.sh has installed Docker + core CLI tools.
#
# What this adds on top of setup-linux.sh:
#   - NVIDIA Container Toolkit (GPU in containers)
#   - poseidon user with docker + sudo membership
#   - Persistent /srv/poseidon data dir (attached volume mount point)
#   - Image pre-pull for the base-dev + sim images
#
# Reference: docs/runbooks/cloud-demo-box.md

set -euo pipefail

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

ok()    { printf "%s[ ok ]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()  { printf "%s[warn]%s %s\n" "$YELLOW" "$RESET" "$1"; }
fail()  { printf "%s[fail]%s %s\n" "$RED" "$RESET" "$1"; exit 1; }
info()  { printf "%s[info]%s %s\n" "$BOLD" "$RESET" "$1"; }

# Sanity checks
if [[ "$(uname -s)" != "Linux" ]]; then
    fail "Must run on Linux."
fi

if ! command -v docker >/dev/null 2>&1; then
    fail "Docker not installed. Run tools/setup-linux.sh first."
fi

if ! command -v nvidia-smi >/dev/null 2>&1; then
    fail "NVIDIA driver not detected. On Lambda Cloud this is pre-installed; on a bare VM install with 'sudo ubuntu-drivers install' and reboot."
fi

info "NVIDIA driver detected:"
nvidia-smi | head -n 4

# NVIDIA Container Toolkit
# Reference: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html
if ! dpkg -s nvidia-container-toolkit >/dev/null 2>&1; then
    info "installing NVIDIA Container Toolkit"
    curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey \
        | sudo gpg --yes --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
    curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list \
        | sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' \
        | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list >/dev/null

    sudo apt-get update -qq
    sudo apt-get install -y -q nvidia-container-toolkit
    sudo nvidia-ctk runtime configure --runtime=docker
    sudo systemctl restart docker
    ok "nvidia-container-toolkit installed and Docker restarted"
else
    ok "nvidia-container-toolkit already installed"
fi

# GPU smoke test
info "running GPU smoke test inside a container"
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi >/dev/null
ok "GPU visible inside containers"

# Poseidon user
if ! id poseidon >/dev/null 2>&1; then
    info "creating poseidon user"
    sudo useradd -m -s /bin/bash -G docker,sudo poseidon
    sudo passwd -l poseidon       # no password; SSH keys only
    sudo mkdir -p /home/poseidon/.ssh
    sudo chmod 700 /home/poseidon/.ssh
    sudo touch /home/poseidon/.ssh/authorized_keys
    sudo chmod 600 /home/poseidon/.ssh/authorized_keys
    sudo chown -R poseidon:poseidon /home/poseidon/.ssh
    ok "poseidon user created"
    warn "Add team SSH public keys to /home/poseidon/.ssh/authorized_keys"
else
    ok "poseidon user already exists"
fi

# Persistent data dir on attached volume
if [[ ! -d /srv/poseidon ]]; then
    info "creating /srv/poseidon directory"
    sudo mkdir -p /srv/poseidon/recordings /srv/poseidon/models /srv/poseidon/scenarios
    sudo chown -R poseidon:poseidon /srv/poseidon
    ok "/srv/poseidon ready"
else
    ok "/srv/poseidon present"
fi

# Image pre-pull (optional, speeds up first docker compose up)
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    info "pre-pulling POSEIDON images from GHCR"
    gh auth token | docker login ghcr.io -u "$(gh api user -q .login)" --password-stdin >/dev/null
    for img in poseidon-base-dev poseidon-sim; do
        docker pull --platform linux/amd64 \
            "ghcr.io/yonatand21/poseidon-mvp/${img}:dev" 2>&1 | tail -2 || \
            warn "pull of ${img}:dev failed (image may not exist yet)"
    done
    ok "images pre-pulled"
else
    warn "gh not authenticated; skipping image pre-pull. Run 'gh auth login' then re-run this script."
fi

# Cron: stop-when-idle placeholder
if [[ ! -f /home/poseidon/stop-when-idle.sh ]]; then
    sudo tee /home/poseidon/stop-when-idle.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
# Stop the instance if no interactive SSH sessions for 60 minutes.
# This is a placeholder; wire it into cloud provider's instance stop API
# based on the actual provider (Lambda, AWS, Paperspace, etc.).
set -e
IDLE_MINUTES=$(( ($(date +%s) - $(stat -c %Y /var/log/wtmp)) / 60 ))
if [[ $IDLE_MINUTES -gt 60 ]] && [[ -z "$(who)" ]]; then
    echo "$(date -Iseconds) idle > 60m; would stop instance"
    # e.g. curl -X POST "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate" ...
fi
EOF
    sudo chmod +x /home/poseidon/stop-when-idle.sh
    sudo chown poseidon:poseidon /home/poseidon/stop-when-idle.sh
    ok "stop-when-idle placeholder created (wire to provider API before enabling)"
fi

printf "\n%s[done]%s Cloud demo box provisioned. Next:\n" "$GREEN" "$RESET"
printf "  1. Add team SSH keys to /home/poseidon/.ssh/authorized_keys\n"
printf "  2. Set billing alert in the provider console (target: 80%% of \$200/mo)\n"
printf "  3. Record the instance IP / provider in docs/runbooks/cloud-demo-box.md under 'Current deployment'\n"
printf "  4. Team can now: docker compose -f deploy/compose/docker-compose.yml -f deploy/compose/docker-compose.gpu.yml --profile core up\n"
