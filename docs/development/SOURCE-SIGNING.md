# Source Signing

>This should be moved into its own repository and referenced from this project.

## ✅ Overview
1. Generate a cryptographic signature of your source code (e.g., a .zip, .tar.gz, or individual files).
2. Bundle the public key with your tool (or embed a trusted hash).
3. Verify the signature at runtime before executing sensitive logic.
4. Fail securely if the source code or binary has been tampered with.

## 🔑 1. Generate a Signing Key (Cosign or OpenSSL)
**Option A: Using Cosign (Sigstore)**
```bash
cosign generate-key-pair
# Creates cosign.key and cosign.pub
```
**Option B: Using OpenSSL (RSA)**
```bash
openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:4096
openssl rsa -pubout -in private.pem -out public.pem
```

## 📦 2. Sign the Source Code Bundle
```bash
# Example: tar the src folder
tar czf ai_forensics_src.tar.gz ai_forensics/

# Sign it using Cosign
cosign sign-blob --key cosign.key --output-signature ai_forensics.sig ai_forensics_src.tar.gz
```
Or with OpenSSL:
```bash
openssl dgst -sha256 -sign private.pem -out ai_forensics.sig ai_forensics_src.tar.gz
```

---

## 🧪 3. Runtime Integrity Verification in Python

```python
"""verifier.py - Runtime source integrity checker"""
import os
import hashlib
import subprocess
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

class SourceIntegrityVerifier:
    def __init__(self, public_key_path: str, signature_path: str, archive_path: str):
        self.public_key_path = Path(public_key_path)
        self.signature_path = Path(signature_path)
        self.archive_path = Path(archive_path)

    def verify(self) -> bool:
        with open(self.archive_path, "rb") as f:
            data = f.read()

        with open(self.signature_path, "rb") as f:
            signature = f.read()

        with open(self.public_key_path, "rb") as f:
            public_key = serialization.load_pem_public_key(f.read())

        try:
            public_key.verify(
                signature,
                data,
                padding.PKCS1v15(),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
```

---

## 🚫 4. Use It at Tool Startup

```python
from verifier import SourceIntegrityVerifier

def main():
    verifier = SourceIntegrityVerifier(
        public_key_path="cosign.pub",
        signature_path="ai_forensics.sig",
        archive_path="ai_forensics_src.tar.gz"
    )

    if not verifier.verify():
        print("❌ Source code integrity verification failed!")
        exit(1)

    print("✅ Source code verified. Running AI Forensics Tool...")
    # Proceed with actual execution

if __name__ == "__main__":
    main()
```

---

## 📁 5. Directory Layout Example

```
ai-forensics/
├── ai_forensics/         # Actual source code
├── ai_forensics_src.tar.gz  # Archived source
├── ai_forensics.sig         # Signature over the archive
├── cosign.pub / public.pem  # Public key
├── verifier.py              # Signature checker
└── main.py                  # Entrypoint, calls verifier
```

---

## 🔐 Optional: Deep Verification Strategies
- 🔁 **Re-hash and compare live files** (`hashlib` file-by-file) against signed hash manifest (like `sha256sums.txt` signed).
- 🔐 **Compile-time signature** if packaging as .pyz or .pex, and verify before unpacking.
- 🚫 **Fail fast** and lock functionality (e.g., disable parsing) if tampering is detected.

---

## 🔒 Security Notes

| Threat                | Mitigation                                                    |
| --------------------- | ------------------------------------------------------------- |
| File modification     | Signature fails if tarball is altered                         |
| Signature replacement | Public key is hardcoded or bundled securely                   |
| Key compromise        | Rotate key pair regularly                                     |
| Source not checked    | Require successful `verifier.verify()` before main logic runs |

---

## ✅ 1. Manifest-Based Signing Strategy

Instead of signing a tarball, you'll:
- Generate a manifest.json containing SHA256 hashes of each source file.
- Sign the manifest using your private key.
- Verify each file at runtime by hashing and comparing to the manifest.

---

## 📁 Project Layout

```
ai-forensics/
├── ai_forensics/                 # Source code
├── integrity/
│   ├── manifest.json             # SHA256 of all .py files
│   ├── manifest.sig              # Signature over the manifest
│   ├── public.pem                # Public key
│   └── signer.py                 # Script to sign manifest
│   └── verifier.py              # Runtime verification
├── .github/
│   └── workflows/
│       └── sign-verify.yml       # GitHub Actions
```

## 🔐 `signer.py` – Manifest Signer

```python
"""signer.py - Generate manifest and signature."""
import json
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

SOURCE_DIR = Path("../ai_forensics")  # Adjust as needed
MANIFEST_PATH = Path("manifest.json")
SIGNATURE_PATH = Path("manifest.sig")
PRIVATE_KEY_PATH = Path("private.pem")

def compute_file_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def generate_manifest() -> dict:
    file_hashes = {}
    for file in SOURCE_DIR.rglob("*.py"):
        file_hashes[str(file.relative_to(SOURCE_DIR.parent))] = compute_file_hash(file)
    return file_hashes

def sign_manifest(manifest: dict) -> None:
    with PRIVATE_KEY_PATH.open("rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)
    payload = json.dumps(manifest, indent=2).encode("utf-8")
    signature = private_key.sign(
        payload,
        padding.PKCS1v15(),
        hashes.SHA256()
    )
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2))
    SIGNATURE_PATH.write_bytes(signature)

if __name__ == "__main__":
    manifest = generate_manifest()
    sign_manifest(manifest)
    print("✅ Manifest signed and saved.")

```

---

## 🔍 `verifier.py` – Runtime File Verification

```python
"""verifier.py - Runtime manifest verification."""
import json
import hashlib
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

MANIFEST_PATH = Path("integrity/manifest.json")
SIGNATURE_PATH = Path("integrity/manifest.sig")
PUBLIC_KEY_PATH = Path("integrity/public.pem")

def compute_file_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def verify_signature() -> bool:
    with MANIFEST_PATH.open("rb") as f:
        manifest_data = f.read()
    with SIGNATURE_PATH.open("rb") as f:
        signature = f.read()
    with PUBLIC_KEY_PATH.open("rb") as f:
        public_key = serialization.load_pem_public_key(f.read())

    try:
        public_key.verify(
            signature,
            manifest_data,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

def verify_files(manifest: dict) -> list[str]:
    mismatches = []
    for path_str, expected_hash in manifest.items():
        file_path = Path(path_str)
        if not file_path.exists() or compute_file_hash(file_path) != expected_hash:
            mismatches.append(path_str)
    return mismatches

def verify_all() -> bool:
    if not verify_signature():
        print("❌ Signature verification failed.")
        return False
    manifest = json.loads(MANIFEST_PATH.read_text())
    mismatches = verify_files(manifest)
    if mismatches:
        print("❌ File mismatch detected:")
        for m in mismatches:
            print(f" - {m}")
        return False
    print("✅ Source code verified.")
    return True

if __name__ == "__main__":
    verified = verify_all()
    exit(0 if verified else 1)

```

---

## 🚀 2. GitHub Actions Workflow – sign-verify.yml

```yaml
name: Sign & Verify Source

on:
  push:
    branches: [main]
  pull_request:

jobs:
  sign-and-verify:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: integrity

    steps:
      - name: Checkout source
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install cryptography
        run: pip install cryptography

      - name: Generate RSA key (for demo)
        run: |
          openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:4096
          openssl rsa -in private.pem -pubout -out public.pem

      - name: Sign source manifest
        run: python signer.py

      - name: Verify source manifest
        run: python verifier.py
```
---

## 🔒 Result
- Every push signs the current source structure.
- Every commit verifies integrity via signature and SHA256 hashes.
- This can be extended to **require signed source** before release or deploy jobs.

---

## ✅ Enforcement Strategy Overview

To **ensure AI Forensics always runs with verified, signed source** and cannot be bypassed or tampered with, you must enforce runtime integrity enforcement. Below is a hardened, multi-layer approach:

| Layer                            | Description                                                                  |
| -------------------------------- | ---------------------------------------------------------------------------- |
| 🧠 **Runtime Self-Verification** | Verify source hashes and manifest before executing any logic                 |
| 🧱 **Entrypoint Hardening**      | All entry points (CLI, API, GUI) call `verify()` first and `exit(1)` on fail |
| 🔐 **Container Lockdown**        | Container image is signed, read-only, and all source is pre-hashed           |
| 🧬 **Single Entrypoint**         | Prevent module-level execution (e.g., `python ai_forensics/parser.py`)       |
| 🧾 **Release Pipeline Signing**  | Enforce signed Git commits/tags and CI verification                          |

---

## 1️⃣ Entrypoint Self-Verification Pattern

In your `cli.py` and any other entrypoint:

```python
# cli.py
from integrity.verifier import verify_all

def main():
    if not verify_all():
        print("❌ Code verification failed. Exiting.")
        exit(1)

    # Safe to run
    print("✅ AI Forensics started.")
    ...

if __name__ == "__main__":
    main()
```
> 🔒 This ensures no logic executes without verified manifest + signatures.

---

## 2️⃣ Single Entrypoint Only (No Module Execution)
Add this to each `.py` module:

```python
# Prevent module from being run directly
if __name__ == "__main__":
    print("🚫 This module must be run via cli.py. Exiting.")
    exit(1)
```
>❌ Blocks: `python ai_forensics/parser.py`

---

## 3️⃣ Lock Down the Container (Production Use)

In the final container build:
- Copy only signed files + verifier
- Run `verify_all()` inside `entrypoint.sh`

**Example `entrypoint.sh`**:

```bash
#!/bin/sh
echo "🔐 Verifying source before launch..."
python3 /integrity/verifier.py
if [ $? -ne 0 ]; then
  echo "❌ Integrity check failed. Aborting container start."
  exit 1
fi

exec python3 /ai_forensics/cli.py "$@"
```

**Dockerfile Hardened Block**:

```dockerfile
FROM python:3.10-slim

COPY ai_forensics/ /ai_forensics/
COPY integrity/ /integrity/
WORKDIR /ai_forensics

# Drop permissions, enable read-only FS
RUN useradd -r forensic && \
    chmod -R 555 /ai_forensics /integrity

USER forensic
ENTRYPOINT ["/bin/sh", "/integrity/entrypoint.sh"]
```
>🛑 Prevents bypass even inside container

---

## 4️⃣ Enforce in CI/CD
- Require `verifier.py` passes in all GitHub Actions and GitLab CI jobs
- Require signed commits or tag verification before publishing
- Sign manifest with your Cosign or OpenSSL key in GitHub

```yaml
# In your pipeline
- name: 🔐 Verify source
  run: python3 integrity/verifier.py
```

---

## 5️⃣ Advanced (Optional): Hardcoded Fingerprint

For extremely high assurance, store a fingerprint in `__init__.py` and compare it.

```python
EXPECTED_HASH = "9b16f..."

import hashlib
def current_hash() -> str:
    import os
    h = hashlib.sha256()
    for root, _, files in os.walk("ai_forensics"):
        for f in sorted(files):
            with open(os.path.join(root, f), "rb") as file:
                h.update(file.read())
    return h.hexdigest()

if current_hash() != EXPECTED_HASH:
    print("🔐 Code hash mismatch. Exiting.")
    exit(1)
```
> This locks the tool to one known-good fingerprint, suitable for **classified or regulatory use**.

---

## 🚨 Summary: Can't Bypass If You Do All of These

| Control                    | Description                    | Required?             |
| -------------------------- | ------------------------------ | --------------------- |
| Manifest Verification      | Hash + signature check         | ✅ Yes                 |
| Entrypoint Check           | Fail early if invalid          | ✅ Yes                 |
| Container Entrypoint Guard | Block container startup        | ✅ Yes                 |
| Module Execution Lock      | Prevent direct file execution  | ✅ Yes                 |
| CI Signature Enforcement   | Signed commits/tags            | 🔒 Highly recommended |
| Fingerprint Lock           | Optional for offline/airgapped | 🧱 Advanced           |
