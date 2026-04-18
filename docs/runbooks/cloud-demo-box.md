# Shared cloud demo box (Linux + NVIDIA GPU)

The team runs Stonefish, Unreal at demo fidelity, CUDA AI inference, and the
determinism regression suite on a shared Linux host with an NVIDIA GPU.
Every team member keeps dev work local (Mac / Linux / WSL2), then SSHes
into this box for heavy work and demos.

This runbook covers provisioning, bringing up the POSEIDON stack, managing
cost, and day-to-day SSH workflow.

---

## What the box is for

| Task | Runs on the cloud box? | Why |
| --- | --- | --- |
| Stonefish physics + sensor sim | Yes | Linux-only, no ARM64 build |
| Demo-fidelity Unreal (water, terrain, lighting) | Yes | Needs NVIDIA GPU |
| CUDA-accelerated AI inference (Layer 3 runtime) | Yes | CoreML on Mac is a different path |
| Determinism regression suite | Yes | Release gate per `SYSTEM_DESIGN.md` Section 17.3 |
| Multi-seed sweep runs | Yes | Parallel scenarios, CPU + GPU heavy |
| Writing code, reviewing PRs, CI authoring | No | Local Mac / Linux is faster |
| Helm chart edits, docker compose on placeholders | No | Works on Mac |
| Foxglove review of a local MCAP | No | Mac Foxglove is fine |

Rule of thumb: **if the task runs Stonefish or uses a GPU, use the cloud box.**

---

## Recommended provider and spec

### Primary recommendation: Lambda Cloud

- On-demand `1x RTX 4090` instance, Ubuntu 24.04.
- Hourly price (as of provisioning date): ~$0.60/hr on-demand.
- Persistent storage: 200 GB block volume attached to the instance,
  persists when the instance is stopped.
- Console: <https://lambdalabs.com/cloud>

Why Lambda: pre-baked NVIDIA drivers + CUDA + Docker, no GPU quota
approval needed, simple billing.

### Secondary options

- **Vast.ai** - cheaper (~$0.30-0.50/hr for RTX 4090) but community hosts
  vary in reliability.
- **AWS g5.xlarge** (A10G) or `g6.xlarge` (L4) - ~$1.00/hr, but requires
  vCPU quota increase request on new AWS accounts.
- **Paperspace Core RTX A5000** - ~$0.76/hr, good UI for snapshots.

We do not recommend Google Colab or Kaggle - they are notebooks, not
persistent SSH-accessible VMs.

### Minimum spec

- GPU: RTX 4090 (24 GB VRAM) or RTX A5000 / L4 / A10G as fallback.
- CPU: 16+ vCPU.
- RAM: 64 GB (Stonefish + Unreal + multiple services).
- Disk: 200 GB NVMe + 200 GB attached volume for MCAP archive.
- Network: >= 1 Gbps for image pulls and MCAP upload.

### Cost budget

Target: **$200/month ceiling**. At $0.60/hr that is ~333 hours/month,
which comfortably covers the 4-person team running the box ~3 hours/day.
Key discipline: **stop the instance when nobody is using it.**

---

## One-time provisioning

### Step 1: create the instance

Log into Lambda Cloud. Launch `1x RTX 4090` on Ubuntu 24.04. Attach a
200 GB persistent block volume and mount it at `/srv/poseidon`. Upload
your public SSH key during launch.

Record the public IP and note the instance name (e.g. `poseidon-demo`).

### Step 2: connect and harden

```bash
# From your Mac (replace with your instance IP)
ssh ubuntu@<instance-ip>

# On the instance
sudo apt-get update && sudo apt-get -y upgrade
sudo apt-get -y install fail2ban ufw
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
sudo ufw --force enable
```

### Step 3: install Docker + NVIDIA Container Toolkit

The POSEIDON repo ships a provisioning script:

```bash
# On the instance
git clone https://github.com/Yonatand21/poseidon-mvp.git
cd poseidon-mvp
bash tools/setup-linux.sh
bash docs/runbooks/cloud-demo-box.provision.sh   # installs NVIDIA toolkit
```

Verify GPU visibility:

```bash
nvidia-smi
docker run --rm --gpus all nvidia/cuda:12.4.1-base-ubuntu22.04 nvidia-smi
```

Both should list the RTX 4090.

### Step 4: authenticate to GHCR and pull images

```bash
gh auth login          # follow the device-flow prompt
gh auth token | docker login ghcr.io -u USERNAME --password-stdin

docker pull --platform linux/amd64 \
  ghcr.io/yonatand21/poseidon-mvp/poseidon-base-dev:dev
docker pull --platform linux/amd64 \
  ghcr.io/yonatand21/poseidon-mvp/poseidon-sim:dev
```

### Step 5: onboard the team

Add each teammate's SSH public key to `~/.ssh/authorized_keys`:

```bash
# Paste each teammate's pub key on its own line, prefixed with a comment:
# From: john@john-laptop
ssh-ed25519 AAAA... john@john-laptop
# From: robert@robert-mbp
ssh-ed25519 AAAA... robert@robert-mbp
# From: robbie@robbie-linux
ssh-ed25519 AAAA... robbie@robbie-linux
```

Test by having each teammate SSH in and run `docker ps`.

### Step 6: cost alerting

Set up a billing alert in Lambda / AWS / Paperspace at **80% of $200**
($160). Recipients: Yonatan + one backup. Document the alert config
inline in this file when it is set.

---

## Daily usage

### Starting the box

Log into the cloud provider console, click Start on the instance. Wait
~60 seconds for boot. SSH in:

```bash
ssh poseidon@<instance-ip>     # poseidon user created by setup-linux.sh
```

### Bringing up the stack

```bash
cd ~/src/poseidon-mvp
git pull
docker compose \
  -f deploy/compose/docker-compose.yml \
  -f deploy/compose/docker-compose.gpu.yml \
  --profile core up
```

Foxglove at `http://<instance-ip>:8080` once the `viz` profile is added.

### Stopping the box

**Always stop the instance when done.** Running = billed, stopped = cheap
storage cost only (~$5/month for 200 GB).

```bash
# On the instance
docker compose -f deploy/compose/docker-compose.yml down
exit

# In the cloud provider console: click Stop
```

Optional: add a `~/stop-when-idle.sh` cron job that checks `who` and
stops the instance if no users have been active for 60 minutes.

---

## VS Code Remote-SSH setup

On the Mac / Linux workstation:

```bash
# Add to ~/.ssh/config
Host poseidon-demo
    HostName <instance-ip>
    User poseidon
    ServerAliveInterval 60
    ControlMaster auto
    ControlPath ~/.ssh/cm-%r@%h:%p
    ControlPersist 10m
```

Then in VS Code: `Remote-SSH: Connect to Host... -> poseidon-demo`.

The SSH multiplexing config above keeps a single connection alive so
multiple VS Code windows and terminal sessions share one SSH tunnel. This
is much faster than re-authenticating each time.

---

## When the RTX 4090 is unavailable

Lambda Cloud's RTX 4090 tier is sometimes at capacity. Fallbacks in
order of preference:

1. RTX A6000 (48 GB VRAM, also on Lambda) - same process, higher cost.
2. Vast.ai RTX 4090 - cheaper, community hosts.
3. AWS `g6.2xlarge` (L4 GPU) - request vCPU quota in advance.

Record the provider/spec actually in use at the top of this file under
the "Current deployment" header once provisioning is done.

---

## Current deployment

Status: **not yet provisioned** (planning only).

When provisioned, update this section with:

- Provider and instance type.
- Public IP / DNS name.
- SSH config snippet for the team to paste in.
- Start date and monthly budget ceiling.
- On-call rotation for restarts / cost alerts.

---

## Related

- [`dev-setup.md`](dev-setup.md) - local dev environment setup for Mac /
  Linux / Windows.
- [`../architecture/`](../architecture/) - ADRs on the runtime choices.
- `INFRASTRUCTURE_DESIGN.md` Section 2.3 (GPU and compute) and Section
  16.2 (partner single-node appliance reference topology).
