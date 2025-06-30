# 🧱 Containerized Execution for AI Forensics

This document describes the containerization strategy for the AI Forensics tool to support secure, reproducible, and isolated model scanning in environments with strict security and provenance requirements.

---

## 📦 Purpose

Containerizing the AI Forensics engine provides:

- **Isolation:** Prevents inspected artifacts from accessing the host system
- **Reproducibility:** Ensures consistent environments across deployments
- **Auditability:** Enables traceability of scanner actions via provenance metadata
- **Portability:** Supports execution in air-gapped or hardened systems
- **Policy Enforcement:** Containers can be configured with SELinux, AppArmor, seccomp

---

## 🧰 Container Layout

```
ai-forensics/
├── container/
│ ├── Dockerfile # Hardened base container
│ ├── entrypoint.sh # Launch script for CLI
│ ├── sandbox_profile.json # (Optional) seccomp/apparmor profile
│ └── run_scan.sh # Example: bind-mount binary and run scanner
```

---

## 🛠️ Build Instructions

```bash
# From root of the repository
docker build -t ai-forensics:latest -f container/Dockerfile .
```

Example Podman (rootless):

```bash
podman build -t ai-forensics:latest -f container/Dockerfile
```

---

## 🚀 Usage Example

```bash
docker run --rm \
  -v $(pwd)/models:/input:ro \
  -v $(pwd)/output:/output \
  ai-forensics:latest \
  scan /input/model.pth --output-dir /output
```
- `/input`: Read-only bind mount of the model to scan
- `/output`: Where reports (HTML, JSON, SBOM) are written
- `scan`: Entrypoint to cli.py inside the container

---

## 🔐 Security Recommendations
- Run with `--read-only` and `--cap-drop=ALL`
- Use SELinux/AppArmor profiles
- Enable seccomp filtering (`--security-opt seccomp=...`)
- Consider using systemd-nspawn or gVisor for further isolation
- Sign and verify the container image using Cosign (see `SECURITY.md`)

---

## 🧪 Testing Inside Container

```bash
podman run --rm \
  -v ./examples:/input:ro \
  -v ./out:/output \
  localhost/ai-forensics:latest \
  scan /input/example_model.gguf --policy /input/policy.yaml --output-dir /output
```

---

## 📜 Provenance Support

- Container images are signed with Cosign  
- Execution produces signed SBOM and attestation bundle  
- Optional support for in-toto attestations (planned)  

