# 🧪 Release Verification Guide for AI Forensics

This document outlines how to verify the integrity and authenticity of a release of **AI Forensics**, including container image, SBOMs, and artifact bundle.

---

## 📦 What’s in a Release Bundle

Each release includes the following:

| File | Description |
|------|-------------|
| `release.tar.gz` | All release metadata and security artifacts |
| `release.tar.gz.sig` | Detached GPG signature of the bundle |
| `manifest.yaml` | Hash manifest for each artifact |
| `sbom.cyclonedx.json` / `sbom.spdx.json` | Bill of Materials for runtime & dependencies |
| `image-signature.txt` | Cosign output from signing the container |
| `signature-verify.log` | Output from `cosign verify` |
| `release.md` / `release.html` | Human-readable changelog and links |

---

## 🔐 Prerequisites

Install:

- [Cosign](https://docs.sigstore.dev/cosign/)
- [GPG](https://gnupg.org)
- [Python 3.10+](https://python.org)
- Dependencies: `pip install -r requirements.txt` (or use `poetry`)

---

## ✅ Verification Steps

### 1. Verify GPG Signature

```bash
gpg --import cosign.pub.gpg
gpg --verify release.tar.gz.sig release.tar.gz
```

### 2. Extract Bundle

```bash
tar -xzf release.tar.gz
cd release/
```

### 3. Validate Manifest Hashes

```bash
python3 tools/verify_release.py release/
```

### 4. Validate Container Signature

```bash
cosign verify --key cosign.pub ghcr.io/interwebshack/ai-forensics:vX.Y.Z
```

---

## ✅ 2. Container Layer & SBOM Verification

### 🔍 Objective

Validate that:

- Each SBOM entry corresponds to an actual image layer
- There are no unknown layers or packages not accounted for in SBOM

---

