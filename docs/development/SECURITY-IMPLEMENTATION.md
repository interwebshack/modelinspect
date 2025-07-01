
---

### ✅ `SECURITY.md` – *Code Signing & Supply Chain Security*

```markdown
# 🔐 AI Forensics Security & Signing Policy

This document outlines how the AI Forensics tool enforces software and artifact integrity using code signing, SBOM attestation, and integration with transparency logs such as Sigstore's Rekor.

---

## 🎯 Goals

- Prevent unauthorized code modification
- Ensure all distributed artifacts are tamper-evident
- Integrate with reproducible builds and transparency logs
- Comply with NIST 800-190, 800-53, and DISA container hardening guidance

---

## 🧾 Signed Artifacts

| Artifact Type          | Signing Method   | Notes                                    |
|------------------------|------------------|------------------------------------------|
| Source Code Release    | `cosign sign-blob` | SHA256 hash of tarball or `.zip` source |
| Container Image        | `cosign sign`     | OCI image signed and pushed to registry |
| HTML Report            | `cosign sign-blob` | Optional, signed user-facing report     |
| SBOM File              | `cosign sign-blob` | SPDX or CycloneDX attested with key     |
| Attestation Bundle     | `cosign attest`   | DSSE signed metadata for artifact trace |

---

## 🧩 Security Strategy Layers

| Layer               | Enforcement Method                     | Mandatory |
|--------------------|-----------------------------------------|-----------|
| Signed Manifest    | SHA256 hashes + digital signature       | ✅ Yes     |
| Runtime Verifier   | Python script validates all source files| ✅ Yes     |
| Fingerprint Lock   | SHA256 digest of all source files       | ✅ Yes     |
| Entrypoint Guard   | Container startup aborts if check fails | ✅ Yes     |
| Cosign Signatures  | Image signing & Rekor transparency log  | ✅ Yes     |

---

## 📜 Signed Manifest Strategy

1. `manifest.json` includes SHA256 hashes of all `.py` files.
2. `manifest.sig` is a digital signature of that file.
3. `public.pem` is the public key embedded in the verifier.
4. At runtime, the verifier:
   - Validates signature of `manifest.json`
   - Recalculates each file hash
   - Compares to manifest
   - Verifies a fixed fingerprint hash of the complete source tree

---

## 🔍 Fingerprint Lock (Optional but Recommended)

```python
EXPECTED_DIGEST = "9acb314..."

def calc_digest():
    import hashlib, os
    h = hashlib.sha256()
    for root, _, files in os.walk("ai_forensics"):
        for f in sorted(files):
            with open(os.path.join(root, f), "rb") as file:
                h.update(file.read())
    return h.hexdigest()

if calc_digest() != EXPECTED_DIGEST:
    print("❌ Fingerprint mismatch. Abort.")
    exit(1)
```
> Prevents substitution even if manifest is bypassed or compromised.

---

## 🐳 Container Image Signing (Cosign)

```bash
# Build and tag container
docker build -t ghcr.io/your-org/ai-forensics:secure .

# Sign it using your key
cosign sign --key cosign.key ghcr.io/your-org/ai-forensics:secure
```

---

## 🔍 Verification at Deploy Time

```bash
cosign verify --key cosign.pub ghcr.io/your-org/ai-forensics:secure
```
Optional Rekor logging:
```bash
cosign sign --key cosign.key --rekor-url https://rekor.sigstore.dev ghcr.io/your-org/ai-forensics:secure
```

---
## 🧾 Cosign Setup

### 🔑 Key Generation

```bash
cosign generate-key-pair
# Produces cosign.key and cosign.pub
```
Store cosign.key securely. Optionally use a KMS or YubiKey.

---

### 🔍 Signing Example

```bash
# Sign the ZIP bundle of analysis outputs
cosign sign-blob --key cosign.key --output-signature sigmodel.zip.sig sigmodel.zip
```

### 🔒 Rekor Transparency Log

```bash
cosign sign-blob \
  --key cosign.key \
  --rekor-url https://rekor.sigstore.dev \
  --output-signature sigmodel.zip.sig sigmodel.zip
```
Rekor entry ensures immutable logging of signature.

---

### 📦 Container Image Signing

```bash
cosign sign --key cosign.key ghcr.io/your-org/ai-forensics:latest
```

### 🔐 Verification

```bash
cosign verify --key cosign.pub ghcr.io/your-org/ai-forensics:latest
```

## 🔄 Supply Chain (Planned)

| Capability                  | Status     |
| --------------------------- | ---------- |
| In-toto Provenance Chains   | 🔜 Planned |
| Git commit signing (GPG)    | 🔜 Planned |
| Signed Policy Files         | ✅ Done     |
| CI/CD Provenance Export     | 🔜 Planned |
| SBOM Reference in Container | ✅ Done     |

## 🛡️ Secure Build Recommendations

- Enforce signed commits and releases
- Scan containers with Trivy/Grype
- Use reproducible builds where possible
- Restrict CI runners to signed artifacts only
- Verify all Cosign signatures in pipeline

---

## ⚙️ CI/CD Workflow Enforcement
Include this in `.github/workflows/sign-verify.yml`:
```yaml
- name: 🔐 Verify manifest + fingerprint
  run: python3 integrity/verifier.py
```
Require this passes on all merge requests, releases, and deployments.

---

## 🧭 Security Goals Achieved

| Goal                          | Achieved By                        |
| ----------------------------- | ---------------------------------- |
| Tamper-evident source         | Manifest + signature + fingerprint |
| Immutable container execution | Entrypoint + read-only container   |
| Verifiable provenance         | Cosign + Rekor                     |
| Enforcement even offline      | Hardcoded digest                   |
| Defense in depth              | Multiple independent checks        |

---

## 📄 References

- [Sigstore](https://www.sigstore.dev/)
- [Cosign](https://github.com/sigstore/cosign)
- [Rekor Transparency Log](https://rekor.sigstore.dev/)
- [NIST 800-190](https://csrc.nist.gov/publications/detail/sp/800-190/final)
- [SLSA Framework](https://slsa.dev/)

---

## ✅ 1. Makefile – Automate Sign & Verify Workflows

```makefile
# Makefile for AI Forensics integrity operations

# Paths
SOURCE_DIR=ai_forensics
INTEGRITY_DIR=integrity
ARCHIVE=source.tar.gz
PRIVATE_KEY=$(INTEGRITY_DIR)/private.pem
PUBLIC_KEY=$(INTEGRITY_DIR)/public.pem
MANIFEST=$(INTEGRITY_DIR)/manifest.json
SIGNATURE=$(INTEGRITY_DIR)/manifest.sig

.PHONY: all sign verify fingerprint container

all: sign verify fingerprint

sign:
	@echo "🔐 Generating manifest and signing..."
	python3 $(INTEGRITY_DIR)/signer.py

verify:
	@echo "🔍 Verifying source integrity..."
	python3 $(INTEGRITY_DIR)/verifier.py

fingerprint:
	@echo "🔑 Calculating fingerprint..."
	python3 $(INTEGRITY_DIR)/fingerprint.py

container:
	@echo "🐳 Building container with secure entrypoint..."
	podman build -t ai-forensics:secure .

```

---

## ✅ 2. fingerprint.py – Fingerprint Digest Calculator

```python
"""fingerprint.py - Generate SHA256 fingerprint of source tree."""

import hashlib
import os
from pathlib import Path

SOURCE_DIR = Path("../ai_forensics")
EXPECTED_DIGEST_PATH = Path("fingerprint.lock")

def calculate_digest() -> str:
    h = hashlib.sha256()
    for path in sorted(SOURCE_DIR.rglob("*.py")):
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
    return h.hexdigest()

if __name__ == "__main__":
    digest = calculate_digest()
    EXPECTED_DIGEST_PATH.write_text(digest + "\n")
    print(f"✅ Digest written to {EXPECTED_DIGEST_PATH}:")
    print(digest)

```
> 🔒 This creates fingerprint.lock used by the verifier to enforce fixed digest matching.

---

## ✅ 3. gitlab-ci.yml – GitLab Pipeline with Enforcement

```yaml
stages:
  - integrity

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

integrity_check:
  stage: integrity
  image: python:3.10-slim
  before_script:
    - pip install cryptography
  script:
    - echo "🔐 Verifying AI Forensics source integrity..."
    - python3 integrity/verifier.py
  only:
    refs:
      - main
      - merge_requests

```
> You can expand this pipeline to also sign containers using Cosign and enforce merge request policies using [GitLab compliance frameworks](https://docs.gitlab.com/ee/user/compliance/).

---

## ✅ 1. Signed fingerprint.lock using Cosign

🔑 **Fingerprint Signing Step (add to GitHub Actions workflow)**
Update your `sign-verify.yml` (or `release.yml`) to include:
```yaml
- name: 🧬 Generate fingerprint
  run: |
    python3 integrity/fingerprint.py

- name: 🔐 Sign fingerprint.lock with Cosign
  run: |
    cosign sign-blob \
      --key integrity/private.pem \
      --output-signature integrity/fingerprint.lock.sig \
      integrity/fingerprint.lock

```
>This produces:
> - "`integrity/fingerprint.lock`"
> - "`integrity/fingerprint.lock.sig`"

Store `public.pem` in the repo or use GitHub Secrets with KMS for production.

---

## ✅ 2. Combined Manifest + Fingerprint Verification Logic

Update `verifier.py` to include fingerprint locking:

```python
from integrity.fingerprint import calculate_digest
from pathlib import Path

FINGERPRINT_PATH = Path("integrity/fingerprint.lock")
FINGERPRINT_SIG = Path("integrity/fingerprint.lock.sig")

def verify_fingerprint_signature() -> bool:
    from cryptography.hazmat.primitives import serialization, hashes
    from cryptography.hazmat.primitives.asymmetric import padding

    digest = FINGERPRINT_PATH.read_text().strip().encode()
    signature = FINGERPRINT_SIG.read_bytes()
    pub_key = serialization.load_pem_public_key(PUBLIC_KEY_PATH.read_bytes())

    try:
        pub_key.verify(
            signature,
            digest,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def verify_fingerprint() -> bool:
    expected = FINGERPRINT_PATH.read_text().strip()
    actual = calculate_digest()
    return expected == actual

def verify_all() -> bool:
    if not verify_signature():
        print("❌ Manifest signature invalid.")
        return False
    manifest = json.loads(MANIFEST_PATH.read_text())
    if mismatches := verify_files(manifest):
        print("❌ File mismatches detected:")
        for path in mismatches:
            print(f" - {path}")
        return False
    if not verify_fingerprint_signature():
        print("❌ Fingerprint signature invalid.")
        return False
    if not verify_fingerprint():
        print("❌ Fingerprint digest mismatch.")
        return False
    print("✅ Manifest, signature, and fingerprint verified.")
    return True
```

---

## ✅ 3. Auto-regeneration during GitHub Releases
Create a GitHub Actions workflow in `.github/workflows/tag-release.yml`:

```yaml
name: Tag & Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  integrity-release:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: integrity

    steps:
      - name: Checkout
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: pip install cryptography

      - name: Generate Manifest & Fingerprint
        run: |
          python signer.py
          python fingerprint.py

      - name: Sign Fingerprint and Manifest
        run: |
          cosign sign-blob --key private.pem \
            --output-signature manifest.sig manifest.json
          cosign sign-blob --key private.pem \
            --output-signature fingerprint.lock.sig fingerprint.lock

      - name: Upload release assets
        uses: softprops/action-gh-release@v2
        with:
          files: |
            manifest.json
            manifest.sig
            fingerprint.lock
            fingerprint.lock.sig
```
>🔐 Uploads signed manifest + fingerprint automatically to the release.

---

## 📦 Summary of File Outputs per Tag

| File                   | Description                        |
| ---------------------- | ---------------------------------- |
| `manifest.json`        | SHA256 hashes of all source files  |
| `manifest.sig`         | Signature of manifest using Cosign |
| `fingerprint.lock`     | SHA256 of entire source tree       |
| `fingerprint.lock.sig` | Signature of fingerprint           |

---

## 🧭 AI Forensics – GitHub Workflows Overview

Here’s a complete breakdown of **GitHub workflows** you should implement for the AI Forensics project, aligned with your security and provenance goals. Each workflow is tied to specific GitHub **trigger events** (`push`, `pull_request`, `tag`, etc.) and serves a unique purpose in the trusted software supply chain.

| Workflow Name         | Trigger Event           | Purpose                                                         |
| --------------------- | ----------------------- | --------------------------------------------------------------- |
| `sign-verify.yml`     | `push`, `pull_request`  | Verify manifest + fingerprint on every commit and PR            |
| `tag-release.yml`     | `push` to `v*.*.*` tag  | Generate, sign, and upload integrity artifacts at release       |
| `build-container.yml` | `push` to `main`, `tag` | Build and sign container image, verify at runtime               |
| `cosign-verify.yml`   | `deployment`, `manual`  | Verify container/image signatures with Cosign before deployment |
