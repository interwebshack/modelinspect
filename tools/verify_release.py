#!/usr/bin/env python3

# ✅ Usage (Offline Mode)
# cd downloaded-release-bundle/
# python3 tools/verify_release.py .

import hashlib
import json
import subprocess
import sys
from pathlib import Path
import yaml

def sha256sum(file_path: Path) -> str:
    return hashlib.sha256(file_path.read_bytes()).hexdigest()

def verify_hashes(manifest_path: Path):
    with open(manifest_path, 'r') as f:
        manifest = yaml.safe_load(f)

    failed = False
    for file in manifest.get("hashes", {}):
        expected = manifest["hashes"][file]
        actual = sha256sum(Path(file))
        if actual != expected:
            print(f"[FAIL] {file}: hash mismatch")
            failed = True
        else:
            print(f"[PASS] {file}")
    return not failed

def verify_cosign(image: str, key: str):
    try:
        subprocess.run(
            ["cosign", "verify", "--key", key, image],
            check=True,
        )
        print("[PASS] Cosign signature verified")
        return True
    except subprocess.CalledProcessError:
        print("[FAIL] Cosign signature invalid")
        return False

def verify_gpg_signature(bundle_path: Path):
    sig_path = Path(str(bundle_path) + ".sig")
    try:
        subprocess.run(["gpg", "--verify", str(sig_path), str(bundle_path)], check=True)
        print("[PASS] GPG signature valid")
        return True
    except subprocess.CalledProcessError:
        print("[FAIL] GPG signature invalid")
        return False

def check_layers_against_sbom(layers_file: Path, sbom_file: Path):
    import json
    layers = json.loads(layers_file.read_text())
    sbom = json.loads(sbom_file.read_text())
    # Simplified comparison logic
    print(f"🔍 Image has {len(layers)} layers")
    print(f"🧾 SBOM lists {len(sbom.get('packages', []))} packages")
    # In practice: compare known files or hashes
    
if __name__ == "__main__":
    release_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("release")
    manifest = release_dir / "manifest.yaml"
    pubkey = release_dir / "cosign.pub"
    image = yaml.safe_load(manifest.read_text())["image"]["name"]

    print(f"Verifying bundle: {release_dir}")
    all_passed = verify_hashes(manifest) and verify_cosign(image, str(pubkey))

    if not verify_gpg_signature(release_dir.parent / f"release-{version}.tar.gz"):
    sys.exit(1)
    
    if not all_passed:
        sys.exit(1)
