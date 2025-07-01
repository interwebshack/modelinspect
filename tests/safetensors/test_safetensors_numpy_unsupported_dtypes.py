"""
Tests for generating deliberately malformed .safetensors files with unsupported dtypes
for use in testing the robustness of the `ai-forensics` tool.

This module creates valid safetensors files using NumPy and then corrupts the header
to simulate unsupported or invalid dtypes (e.g., complex numbers, non-standard types).

Output:
- File saved to tests/models/numpy_dtypes directory.
"""

import json
import os
import struct

import numpy as np
from safetensors.numpy import save_file

OUTPUT_DIR = "tests/models/safetensors_numpy"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_generate_numpy_corrupted_dtype_file() -> None:
    """
    Generates a valid .safetensors file and corrupts its header to simulate an unsupported dtype.

    The process:
        1. Saves a NumPy tensor with a supported dtype (float32).
        2. Reads the binary file and decodes the header.
        3. Replaces the dtype in the header with an unsupported value ('complex64').
        4. Rewrites the file with the tampered header.

    This file can then be used to test how the `ai-forensics` tool handles invalid metadata.

    Raises:
        IOError: If there are issues reading or writing the file.
    """
    fname = os.path.join(OUTPUT_DIR, "corrupted_complex64.safetensors")

    # Step 1: Create valid file
    arr = np.ones((2, 2), dtype=np.float32)
    save_file({"tensor": arr}, fname)

    # Step 2: Read binary and decode header
    with open(fname, "rb") as f:
        header_len = struct.unpack("<Q", f.read(8))[0]
        header = json.loads(f.read(header_len))
        rest = f.read()

    # Step 3: Tamper with dtype in header
    header["tensor"]["dtype"] = "complex64"

    # Step 4: Re-encode header and write new file
    new_header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    new_len_bytes = struct.pack("<Q", len(new_header_bytes))

    with open(fname, "wb") as f:
        f.write(new_len_bytes)
        f.write(new_header_bytes)
        f.write(rest)
