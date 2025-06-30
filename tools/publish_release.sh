#!/bin/bash

# Make executable:
# chmod +x tools/publish_release.sh
#
# Usage (after building artifacts):
# ./publish_release.sh v1.2.0
# 
# When offline, ensure gh is pre-installed and authenticated using a saved token.

set -e

TAG=$1
if [[ -z "$TAG" ]]; then
  echo "Usage: $0 <version-tag>"
  exit 1
fi

# Validate required tools
command -v gh >/dev/null || { echo "gh CLI not found"; exit 1; }

# Confirm required artifacts exist
for f in release.md release.html release.html.asc sbom.cyclonedx.json sbom.spdx.json; do
  [[ -f "release-artifacts/$f" ]] || { echo "Missing $f"; exit 1; }
done

# Prepare release body
RELEASE_BODY=$(sed "s/vX.Y.Z/$TAG/g" .github/RELEASE_TEMPLATE.md)

# Create release (dry-run: remove --draft to publish)
gh release create "$TAG" \
  --title "AI Forensics $TAG" \
  --notes "$RELEASE_BODY" \
  --draft \
  release-artifacts/release.md \
  release-artifacts/release.html \
  release-artifacts/release.html.asc \
  release-artifacts/sbom.cyclonedx.json \
  release-artifacts/sbom.spdx.json
