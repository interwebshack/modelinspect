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
- **Enforce source code integrity verification**
- **Prevent execution if tampered**
- **Ensure immutability and provenance in air-gapped systems**
- **Harden the runtime environment with container security controls**
- **Use Cosign for container image signing and Rekor transparency**

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
```
ai-forensics/
├── ai_forensics/ # Source code
├── integrity/
│ ├── manifest.json # SHA256 hashes of all .py files
│ ├── manifest.sig # Signature of manifest.json
│ ├── public.pem # Public key used for verification
│ ├── verifier.py # Runtime enforcement logic
│ ├── fingerprint.py # Optional SHA256 fingerprint lock
│ └── entrypoint.sh # Container startup guard
├── Dockerfile # Hardened build
```

---

## 🧱 Runtime Workflow (Container & Standalone)

```text
Startup → [verify_all()]
       → Manifest verified? ── No → Abort
                       │
                      Yes
                       ↓
          → [compare SHA256 fingerprint]
               → Match? ── No → Abort
                       │
                      Yes
                       ↓
            → Launch actual AI Forensics tool
```

---

## 🐳 Dockerfile (Hardened Container)

```dockerfile
FROM python:3.10-slim

# Copy application code and integrity metadata
COPY ai_forensics/ /ai_forensics/
COPY integrity/ /integrity/

# Set working directory and install dependencies
WORKDIR /ai_forensics
RUN pip install .

# Lock down filesystem and permissions
RUN useradd -r forensic && \
    chmod -R 555 /ai_forensics /integrity

USER forensic
ENTRYPOINT ["/bin/sh", "/integrity/entrypoint.sh"]
```

---

## 🔐 entrypoint.sh – Secure Bootstrap Script

```bash
#!/bin/sh
echo "🔐 Verifying source integrity..."
python3 /integrity/verifier.py
if [ $? -ne 0 ]; then
  echo "❌ Source verification failed. Aborting container startup."
  exit 1
fi

echo "✅ Verified. Starting AI Forensics Tool..."
exec python3 /ai_forensics/cli.py "$@"
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

## 🧪 Local Test (Podman)

```bash
podman build -t ai-forensics:secure .
podman run --rm \
  -v $(pwd)/models:/input:ro \
  ai-forensics:secure scan /input/model.pth
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

---

## 🧾 Notes

- **Manifest-based verification** ensures the actual Python source matches a signed SHA256 hash list
- **Fingerprint check** provides offline immutability by locking the entire tool to a specific digest
- **Cosign signature** ensures container was built and signed by an authorized party (see SECURITY.md)
