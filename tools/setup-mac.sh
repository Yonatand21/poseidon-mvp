#!/usr/bin/env bash
# setup-mac.sh - POSEIDON MVP dev tooling installer for macOS (Apple Silicon).
#
# Idempotent. Safe to re-run.
# Covers everything a new engineer needs on a Mac before `docker compose up`.
#
# Usage:
#   bash tools/setup-mac.sh            # full install
#   bash tools/setup-mac.sh --check    # verify-only, do not install
#
# What it does NOT install (GUI installers, do these manually):
#   - Docker Desktop for Mac
#       https://docs.docker.com/desktop/install/mac-install/
#   - Unreal Engine 5.4.4 via Epic Games Launcher
#       https://www.unrealengine.com/en-US/download
#
# Reference: docs/runbooks/mac-dev-setup.md

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

need_cmd() {
    local cmd="$1"
    local brew_pkg="${2:-$1}"
    local install_type="${3:-formula}"  # formula | cask
    if command -v "$cmd" >/dev/null 2>&1; then
        ok "$cmd present ($(command -v "$cmd"))"
        return 0
    fi
    if [[ "$MODE" == "check" ]]; then
        fail "$cmd missing"
        return 1
    fi
    info "installing $cmd via brew ($install_type: $brew_pkg)"
    if [[ "$install_type" == "cask" ]]; then
        brew install --cask "$brew_pkg"
    else
        brew install "$brew_pkg"
    fi
    ok "$cmd installed"
}

info "POSEIDON MVP - Mac dev environment ($MODE)"

if [[ "$(uname -s)" != "Darwin" ]]; then
    fail "This script is macOS-only. Detected $(uname -s)."
    exit 1
fi

if [[ "$(uname -m)" != "arm64" ]]; then
    warn "Running on $(uname -m) - Intel Macs work but are not the primary target."
fi

# Homebrew
if ! command -v brew >/dev/null 2>&1; then
    if [[ "$MODE" == "check" ]]; then
        fail "Homebrew missing. Install from https://brew.sh/ then re-run."
        exit 1
    fi
    info "installing Homebrew"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
ok "brew present"

# CLI tools
need_cmd git       git
need_cmd git-lfs   git-lfs
need_cmd gh        gh
need_cmd helm      helm
need_cmd kubectl   kubectl
need_cmd k3d       k3d
need_cmd yamllint  yamllint

# Initialize git-lfs for the user if not yet
if [[ "$MODE" == "install" ]]; then
    git lfs install --skip-repo >/dev/null 2>&1 || true
    ok "git-lfs hooks initialized"
fi

# uv - prefer brew (matches the rest of the tooling); astral installer as fallback
if ! command -v uv >/dev/null 2>&1; then
    if [[ "$MODE" == "check" ]]; then
        fail "uv missing"
    else
        info "installing uv via brew"
        if brew install uv; then
            ok "uv installed via brew"
        else
            warn "brew install uv failed; falling back to astral installer"
            curl -LsSf https://astral.sh/uv/install.sh | sh
            export PATH="$HOME/.local/bin:$PATH"
            ok "uv installed via astral script"
        fi
    fi
else
    ok "uv present ($(command -v uv))"
fi

# Casks (GUI apps via brew cask)
need_cmd code "visual-studio-code" cask || true
# Foxglove lands as a .app in /Applications
if [[ -d "/Applications/Foxglove Studio.app" ]] || [[ -d "/Applications/Foxglove.app" ]]; then
    ok "Foxglove Studio present"
elif [[ "$MODE" == "install" ]]; then
    info "installing Foxglove Studio"
    brew install --cask foxglove-studio || warn "Foxglove install failed; install manually from https://foxglove.dev/download"
else
    warn "Foxglove Studio missing"
fi

# Docker Desktop - only a check; cannot be scripted
if ! command -v docker >/dev/null 2>&1; then
    fail "Docker Desktop missing. Install manually from https://docs.docker.com/desktop/install/mac-install/ and re-run."
    exit 1
fi
ok "docker present ($(docker --version))"

if ! docker info >/dev/null 2>&1; then
    warn "docker CLI works but daemon is not responding. Start Docker Desktop."
fi

# Unreal Engine - check only, manual install via Epic Launcher
ue5_found="no"
for d in "/Users/Shared/Epic Games"/UE_5.*; do
    if [[ -d "$d" ]]; then
        ue5_found="yes"
        break
    fi
done
if [[ "$ue5_found" == "yes" ]]; then
    ok "Unreal Engine 5.x detected under /Users/Shared/Epic Games/"
else
    warn "Unreal Engine 5.4 not detected. Install via Epic Games Launcher: https://www.unrealengine.com/en-US/download"
    warn "UE5 is only required for the rendering track (Week 2 of Yonatan plan). Not blocking for backbone work."
fi

# VS Code extensions
if command -v code >/dev/null 2>&1 && [[ "$MODE" == "install" ]]; then
    info "installing VS Code extensions"
    for ext in \
        ms-azuretools.vscode-docker \
        ms-vscode-remote.remote-ssh \
        ms-python.python \
        redhat.vscode-yaml \
        ms-kubernetes-tools.vscode-kubernetes-tools \
        davidanson.vscode-markdownlint \
        charliermarsh.ruff; do
        code --install-extension "$ext" --force >/dev/null 2>&1 && ok "ext $ext" || warn "ext $ext failed"
    done
fi

# Project-level verification
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

info "running project-level checks"
docker compose -f deploy/compose/docker-compose.yml config --quiet && ok "docker compose config" || fail "docker compose config"
helm lint charts/poseidon-platform >/dev/null 2>&1 && ok "helm lint" || fail "helm lint"

if command -v uv >/dev/null 2>&1; then
    UV_CACHE_DIR="${UV_CACHE_DIR:-/tmp/uv-cache-poseidon}" uv lock --check >/dev/null 2>&1 && ok "uv lock --check" || fail "uv lock --check (run 'uv lock' to refresh)"
fi

if command -v pre-commit >/dev/null 2>&1; then
    ok "pre-commit present"
else
    if [[ "$MODE" == "install" ]] && command -v uv >/dev/null 2>&1; then
        info "installing pre-commit via uv tool"
        uv tool install pre-commit && ok "pre-commit installed"
    fi
fi

if [[ -d ".git/hooks" ]] && [[ ! -f ".git/hooks/pre-commit" ]] && command -v pre-commit >/dev/null 2>&1 && [[ "$MODE" == "install" ]]; then
    info "installing pre-commit hooks"
    pre-commit install && ok "pre-commit hooks installed"
fi

printf "\n%s[done]%s Mac dev environment ready for POSEIDON MVP backbone work.\n" "$GREEN" "$RESET"
printf "Next: docker compose -f deploy/compose/docker-compose.yml --profile core up\n"
