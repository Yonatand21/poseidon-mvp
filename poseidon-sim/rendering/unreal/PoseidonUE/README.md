# PoseidonUE - Unreal Engine 5 project

UE5 scene and rendering consumer for POSEIDON MVP. Subscribes to ROS 2
topics (via the bridge in [`../../bridge/`](../../bridge/)) and renders
the AUV, SSV, archetype terrain, ocean surface, and camera presets.

**Design reference:** `SYSTEM_DESIGN.md` Section 14 (Unreal visual layer),
Section 18.1 (Yonatan deliverables).

## Engine version

Unreal Engine 5.4. On macOS Apple Silicon the editor runs natively. On
Linux we use the precompiled binary release.

## Opening for the first time

1. Install Unreal Engine 5.4 via Epic Games Launcher (or the Linux
   binary on the cloud demo box).
2. Double-click `PoseidonUE.uproject` (or right-click -> `Generate
   project files` on Windows / Linux, `Services -> Generate Xcode Project`
   on Mac).
3. UE will prompt "Missing PoseidonUE Modules. Would you like to rebuild
   now?" - click Yes.
4. After compile, the editor opens with a blank Open World level.

First open takes 10-20 minutes depending on the machine. Subsequent
opens are under 30 seconds.

## Directory layout (committed)

```text
PoseidonUE/
  PoseidonUE.uproject
  .gitignore
  Config/
    DefaultEngine.ini
    DefaultGame.ini
    DefaultInput.ini
  Source/
    PoseidonUE.Target.cs
    PoseidonUEEditor.Target.cs
    PoseidonUE/
      PoseidonUE.Build.cs
      PoseidonUE.h
      PoseidonUE.cpp
  Content/
    (committed content assets go here; see below)
```

## Directory layout (generated, gitignored)

UE5 generates the following on first open. They are all in `.gitignore`:

```text
Binaries/             compiled C++
Build/                per-platform build artifacts
DerivedDataCache/     shader / asset cache (can be many GB)
Intermediate/         build scratch
Saved/                per-user logs, crash reports, autosaves
*.xcodeproj/ *.sln    IDE project files
```

## Content policy

`Content/` contains UE5 binary `.uasset` / `.umap` files. Rules:

- Maps (`*.umap`): committed. These define levels.
- Blueprints (`*.uasset`) authored by us: committed.
- Auto-imported meshes from `vehicles/*/meshes/visual.gltf`: NOT
  committed here; the import pipeline pulls them at build time.
- Auto-imported heightfields from `world_generator/output/to_unreal/`:
  NOT committed here; same rule.
- Epic Marketplace / plugin content: NOT committed (adds GB).

Any `.uasset` over 10 MB should go through Git LFS (it falls under the
`**/*.uasset` LFS rule in `.gitattributes` once we add it).

## Bridge

See [`../../bridge/`](../../bridge/) for the ROS 2 <-> UE bridge. ADR at
[`../../../../docs/architecture/0001-unreal-ros2-bridge.md`](../../../../docs/architecture/0001-unreal-ros2-bridge.md).

## Build on the cloud box (headless)

Once the project is initialized, a headless Linux build runs as:

```bash
/opt/UnrealEngine/Engine/Build/BatchFiles/Linux/Build.sh \
  PoseidonUEEditor Linux Development \
  -project="$PWD/PoseidonUE.uproject" -waitmutex
```

This is wired into CI as a Tier 3 job (not yet enabled; pending Unreal
binary install on a self-hosted runner).

## Status

- [x] `.uproject` + `Source/` + `Config/` committed.
- [ ] First `Generate project files` run on a machine with UE5 installed.
- [ ] Rotating-cube bridge demo (Days 7-8 of Yonatan plan).
- [ ] choke_point heightfield + water (Days 9-10).
- [ ] Camera Blueprints (Days 11-12).
