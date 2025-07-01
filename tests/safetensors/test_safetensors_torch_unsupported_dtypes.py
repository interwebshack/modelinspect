"""
Tests for generating deliberately malformed .safetensors files with unsupported dtypes
for use in testing the robustness of the `ai-forensics` tool.

This module creates valid safetensors files using PyTorch and then corrupts the header
to simulate unsupported or invalid dtypes (e.g., complex numbers, non-standard types).

Output:
    - File saved to tests/models/safetensors_torch directory.
"""

import json
import os
import struct

import torch
from safetensors.torch import save_file

OUTPUT_DIR = "tests/models/safetensors_torch"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_generate_torch_corrupted_dtype_file() -> None:
    """
    Generates a valid .safetensors file and corrupts its header to simulate an unsupported dtype.

    The process:
        1. Saves a PyTorch tensor with a supported dtype (float32).
        2. Reads the binary file and decodes the header.
        3. Replaces the dtype in the header with an unsupported value ('complex64').
        4. Rewrites the file with the tampered header.

    This file can then be used to test how the `ai-forensics` tool handles invalid metadata.

    Raises:
        IOError: If there are issues reading or writing the file.
    """
    fname = os.path.join(OUTPUT_DIR, "corrupted_complex64_torch.safetensors")

    # Step 1: Create valid file
    tensor = torch.ones((2, 2), dtype=torch.float32)
    save_file({"tensor": tensor}, fname)

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
