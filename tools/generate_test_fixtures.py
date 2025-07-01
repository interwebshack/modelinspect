#!/usr/bin/env python3
"""
generate_test_fixtures.py

Creates dummy model files for testing AI Forensics format parsers.
These files are synthetic and should NOT be used in production.
"""

# Usage: python tools/generate_test_fixtures.py

import os
from pathlib import Path
import zipfile

FIXTURE_DIR = Path("tests/models")
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

def create_dummy_pth():
    dummy_pkl = FIXTURE_DIR / "dummy.pkl"
    dummy_pkl.write_text('{"model": "test"}')

    dummy_pth = FIXTURE_DIR / "dummy.pth"
    with zipfile.ZipFile(dummy_pth, "w") as zipf:
        zipf.write(dummy_pkl, arcname="model.pkl")

    dummy_pkl.unlink()

def create_dummy_gguf():
    gguf = FIXTURE_DIR / "dummy.gguf"
    with gguf.open("wb") as f:
        f.write(b"GGUFv1")
        f.write(os.urandom(4096))

def create_dummy_safetensors():
    st = FIXTURE_DIR / "dummy.safetensors"
    st.write_bytes(
        b'{"__metadata__": {"format": "safetensors", "version": "1"}}\n' + os.urandom(2048)
    )

if __name__ == "__main__":
    print("🧪 Generating test fixtures in:", FIXTURE_DIR)
    create_dummy_pth()
    create_dummy_gguf()
    create_dummy_safetensors()
    print("✅ Dummy test fixtures created.")
