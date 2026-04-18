#!/usr/bin/env bash
# setup-linux.sh - POSEIDON MVP dev tooling installer for Linux.
#
# Supports:
#   - Ubuntu / Debian (apt)          [primary path]
#   - Fedora / RHEL / Rocky (dnf)    [secondary path]
#   - WSL2 Ubuntu on Windows         [runs as Ubuntu]
#
# Idempotent. Safe to re-run.
#
# Usage:
#   bash tools/setup-linux.sh            # full install
#   bash tools/setup-linux.sh --check    # verify-only, do not install
#
# What it does NOT install (must be handled per-distro by the user):
#   - NVIDIA driver + CUDA - see docs/runbooks/cloud-demo-box.md for the
#     Ubuntu 24.04 + RTX 4090 path. Not needed on non-GPU dev boxes.
#   - Docker Desktop on Windows - install BEFORE running this script from
#     inside WSL2. See docs/runbooks/dev-setup.md Windows section.
#
# Reference: docs/runbooks/dev-setup.md

set -euo pipefail

MODE="install"
if [[ "${1:-}" == "--check" ]]; then
    MODE="check"
fi

RED=$'\033[0;31m'
GREEN=$'\033[0;32m'
YELLOW=$'\033[0;33m'
BOLD=$'\033[1m'
RESET=$'\033[0m'

ok()    { printf "%s[ ok ]%s %s\n" "$GREEN" "$RESET" "$1"; }
warn()  { printf "%s[warn]%s %s\n" "$YELLOW" "$RESET" "$1"; }
fail()  { printf "%s[fail]%s %s\n" "$RED" "$RESET" "$1"; }
info()  { printf "%s[info]%s %s\n" "$BOLD" "$RESET" "$1"; }

# -----------------------------------------------------------------------------
# Distro and environment detection
# -----------------------------------------------------------------------------

if [[ "$(uname -s)" != "Linux" ]]; then
    fail "This script is Linux-only. Detected $(uname -s). Use tools/setup-mac.sh on macOS."
    exit 1
fi

PKG_MGR=""
DISTRO_ID=""
IS_WSL2="no"

if grep -qi "microsoft" /proc/version 2>/dev/null; then
    IS_WSL2="yes"
fi

if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    DISTRO_ID="${ID:-unknown}"
fi

case "$DISTRO_ID" in
    ubuntu|debian|pop|linuxmint)
        PKG_MGR="apt"
        ;;
    fedora|rhel|rocky|centos|almalinux)
        PKG_MGR="dnf"
        ;;
    *)
        if command -v apt >/dev/null 2>&1; then
            PKG_MGR="apt"
            DISTRO_ID="${DISTRO_ID:-unknown-debian-like}"
        elif command -v dnf >/dev/null 2>&1; then
            PKG_MGR="dnf"
            DISTRO_ID="${DISTRO_ID:-unknown-rhel-like}"
        else
            fail "Unsupported Linux distro: $DISTRO_ID. Only apt and dnf are implemented."
            exit 1
        fi
        ;;
esac

info "POSEIDON MVP - Linux dev environment ($MODE)"
info "Distro: $DISTRO_ID  |  Package manager: $PKG_MGR  |  WSL2: $IS_WSL2"

SUDO="sudo"
if [[ "$(id -u)" == "0" ]]; then
    SUDO=""
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

pkg_install_apt() {
    local pkgs=("$@")
    $SUDO apt-get update -qq
    $SUDO DEBIAN_FRONTEND=noninteractive apt-get install -y -q "${pkgs[@]}"
}

pkg_install_dnf() {
    local pkgs=("$@")
    $SUDO dnf install -y -q "${pkgs[@]}"
}

pkg_install() {
    if [[ "$PKG_MGR" == "apt" ]]; then
        pkg_install_apt "$@"
    else
        pkg_install_dnf "$@"
    fi
}

need_cmd() {
    local cmd="$1"
    local pkg="${2:-$1}"
    if command -v "$cmd" >/dev/null 2>&1; then
        ok "$cmd present"
        return 0
    fi
    if [[ "$MODE" == "check" ]]; then
        fail "$cmd missing"
        return 1
    fi
    info "installing $cmd ($PKG_MGR: $pkg)"
    pkg_install "$pkg"
    ok "$cmd installed"
}

# -----------------------------------------------------------------------------
# Baseline CLI tools available in distro repos
# -----------------------------------------------------------------------------

need_cmd curl       curl
need_cmd git        git
need_cmd git-lfs    git-lfs
need_cmd ca-certificates "ca-certificates"
need_cmd gpg        "gnupg"
need_cmd yamllint   yamllint

git lfs install --skip-repo >/dev/null 2>&1 || true

# -----------------------------------------------------------------------------
# Docker Engine (Linux host) vs Docker Desktop (WSL2)
# -----------------------------------------------------------------------------

if [[ "$IS_WSL2" == "yes" ]]; then
    if ! command -v docker >/dev/null 2>&1; then
        fail "docker CLI not available inside WSL2. Install Docker Desktop for Windows and enable WSL2 integration for this distro, then re-run."
        fail "See: docs/runbooks/dev-setup.md (Windows section)"
        exit 1
    fi
    ok "docker present via Docker Desktop WSL2 integration"
else
    if ! command -v docker >/dev/null 2>&1; then
        if [[ "$MODE" == "check" ]]; then
            fail "docker missing"
        else
            info "installing Docker Engine + Compose plugin"
            if [[ "$PKG_MGR" == "apt" ]]; then
                # Docker's official apt repo
                $SUDO install -m 0755 -d /etc/apt/keyrings
                curl -fsSL "https://download.docker.com/linux/${DISTRO_ID}/gpg" | \
                    $SUDO gpg --dearmor -o /etc/apt/keyrings/docker.gpg
                $SUDO chmod a+r /etc/apt/keyrings/docker.gpg
                CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"
                echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/${DISTRO_ID} ${CODENAME} stable" | \
                    $SUDO tee /etc/apt/sources.list.d/docker.list >/dev/null
                $SUDO apt-get update -qq
                $SUDO apt-get install -y -q docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            else
                $SUDO dnf -y install dnf-plugins-core
                $SUDO dnf config-manager --add-repo "https://download.docker.com/linux/${DISTRO_ID}/docker-ce.repo"
                $SUDO dnf install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
                $SUDO systemctl enable --now docker
            fi
            $SUDO usermod -aG docker "$USER" || true
            warn "You may need to log out and back in for docker group membership to apply."
            ok "Docker Engine installed"
        fi
    else
        ok "docker present"
    fi
fi

# -----------------------------------------------------------------------------
# Tools not in distro repos (pull from upstream)
# -----------------------------------------------------------------------------

install_helm() {
    curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
}

install_kubectl() {
    local arch
    arch="$(uname -m)"
    case "$arch" in
        x86_64) arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
    esac
    local ver
    ver="$(curl -L -s https://dl.k8s.io/release/stable.txt)"
    curl -fsSLo /tmp/kubectl "https://dl.k8s.io/release/${ver}/bin/linux/${arch}/kubectl"
    $SUDO install -o root -g root -m 0755 /tmp/kubectl /usr/local/bin/kubectl
    rm -f /tmp/kubectl
}

install_gh() {
    if [[ "$PKG_MGR" == "apt" ]]; then
        curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | \
            $SUDO dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
        $SUDO chmod a+r /usr/share/keyrings/githubcli-archive-keyring.gpg
        echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | \
            $SUDO tee /etc/apt/sources.list.d/github-cli.list >/dev/null
        $SUDO apt-get update -qq
        $SUDO apt-get install -y -q gh
    else
        $SUDO dnf install -y 'dnf-command(config-manager)'
        $SUDO dnf config-manager --add-repo https://cli.github.com/packages/rpm/gh-cli.repo
        $SUDO dnf install -y gh
    fi
}

install_uv() {
    # uv installer writes to ~/.local/bin; if the user's ~/.local is root-owned,
    # fall back to /usr/local/bin.
    if [[ -w "$HOME/.local" ]] || [[ ! -e "$HOME/.local" ]]; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
    else
        warn "$HOME/.local is not writable by $USER; installing uv to /usr/local/bin"
        curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/tmp/uv-install sh
        $SUDO install -m 0755 /tmp/uv-install/uv /usr/local/bin/uv
        rm -rf /tmp/uv-install
    fi
}

install_k3d() {
    curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | $SUDO bash
}

# helm
if ! command -v helm >/dev/null 2>&1; then
    [[ "$MODE" == "check" ]] && fail "helm missing" || { info "installing helm"; install_helm; ok "helm installed"; }
else
    ok "helm present"
fi

# kubectl
if ! command -v kubectl >/dev/null 2>&1; then
    [[ "$MODE" == "check" ]] && fail "kubectl missing" || { info "installing kubectl"; install_kubectl; ok "kubectl installed"; }
else
    ok "kubectl present"
fi

# gh
if ! command -v gh >/dev/null 2>&1; then
    [[ "$MODE" == "check" ]] && fail "gh missing" || { info "installing gh"; install_gh; ok "gh installed"; }
else
    ok "gh present"
fi

# uv
if ! command -v uv >/dev/null 2>&1; then
    [[ "$MODE" == "check" ]] && fail "uv missing" || { info "installing uv"; install_uv; ok "uv installed"; }
else
    ok "uv present"
fi

# k3d (optional, for local Helm testing)
if ! command -v k3d >/dev/null 2>&1; then
    if [[ "$MODE" == "check" ]]; then
        warn "k3d missing (optional - only needed for local Helm chart testing)"
    else
        info "installing k3d"
        install_k3d && ok "k3d installed" || warn "k3d install failed; not blocking"
    fi
else
    ok "k3d present"
fi

# -----------------------------------------------------------------------------
# Project-level verification
# -----------------------------------------------------------------------------

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

info "running project-level checks"

if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    docker compose -f deploy/compose/docker-compose.yml config --quiet && ok "docker compose config" || fail "docker compose config"
fi

command -v helm >/dev/null 2>&1 && helm lint charts/poseidon-platform >/dev/null 2>&1 && ok "helm lint" || fail "helm lint"

if command -v uv >/dev/null 2>&1; then
    UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache-poseidon}" uv lock --check >/dev/null 2>&1 && ok "uv lock --check" || fail "uv lock --check (run 'uv lock' to refresh)"
fi

printf "\n%s[done]%s Linux dev environment ready for POSEIDON MVP backbone work.\n" "$GREEN" "$RESET"
printf "Next: docker compose -f deploy/compose/docker-compose.yml --profile core up\n"
