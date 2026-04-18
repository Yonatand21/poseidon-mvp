# models

Pinned AI model artifacts. Every model is versioned, hashed, and referenced
by scenario YAML via a `model_ref` path.

**Design reference:** `SYSTEM_DESIGN.md` Section 10.7 (AI scenario controls),
Section 17.3 (Versioning and provenance), `INFRASTRUCTURE_DESIGN.md`
Section 5.2 (Model registry).

## Storage

- Small reference models (< 100 MB) live here via Git LFS
  (see `.gitattributes`).
- Larger artifacts live in MinIO / S3 and are pulled by hash at install.
- MLflow is the authoritative model registry in multi-tenant and on-prem
  deployments.

## Naming

`models/<task>/<model>_<version>.<ext>` with a sibling
`<model>_<version>.sha256` recording the hash.

Examples:

```text
models/perception/yolo_v8_surface_contacts_v3.onnx
models/perception/yolo_v8_surface_contacts_v3.sha256
models/anomaly/gnss_spoof_rf_v1.joblib
models/anomaly/gnss_spoof_rf_v1.sha256
```

## Offline-first

No component may pull model artifacts from public model hubs at runtime
(`AGENTS.md` Section 3, `SYSTEM_DESIGN.md` Section 17.3). Every release
bundle includes the models it references.
