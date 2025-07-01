#!/usr/bin/env python3

# ✅ Usage (Offline or CI)
# docker pull yourdockerhubuser/ai-forensics:v1.2.0
# python3 tools/sbom_verify.py yourdockerhubuser/ai-forensics:v1.2.0 release/sbom.spdx.json
#
# This script can be extended to validate:
# - SBOM component versions vs dpkg -l or rpm -qa inside image (via container runtime)
# - File hashes inside container image against SBOM claims
# - Vulnerability scan comparison to SBOM inventory

import subprocess
import json
import sys
from typing import List
from pathlib import Path


def extract_image_layers(image: str) -> List[str]:
    result = subprocess.run(["docker", "inspect", image], stdout=subprocess.PIPE, check=True)
    inspect_data = json.loads(result.stdout)
    return inspect_data[0]["RootFS"]["Layers"]


def load_sbom(sbom_path: Path) -> List[str]:
    sbom = json.loads(sbom_path.read_text())
    packages = [p["name"] for p in sbom.get("packages", [])]
    return packages


def main():
    image = sys.argv[1]
    sbom_path = Path(sys.argv[2])
    print(f"🔍 Verifying image: {image}")
    print(f"📄 SBOM file: {sbom_path}")

    layers = extract_image_layers(image)
    packages = load_sbom(sbom_path)

    print(f"🧱 Layers found: {len(layers)}")
    print(f"📦 Packages listed in SBOM: {len(packages)}")

    # Placeholder: deeper matching logic
    if len(packages) < len(layers):
        print("⚠️  Fewer packages than layers — may be missing info")
    else:
        print("✅ SBOM package count is sufficient")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: sbom_verify.py <image> <sbom.json>")
        sys.exit(1)
    main()
