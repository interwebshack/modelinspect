"""
Generates a .safetensors file containing a PyTorch tensor with metadata
for testing metadata extraction and validation in downstream tools like aiforensics.

This test ensures that a .safetensors file can include arbitrary metadata
and be successfully saved and read for analysis.

The generated file includes:
    - A tensor of shape (2, 2)
    - Metadata such as versioning and source tags

Output:
    - File saved to output/safetensors_torch/torch_with_metadata.safetensors
"""

import os
from typing import Dict

import torch
from safetensors.torch import save_file

OUTPUT_DIR = "output/safetensors_torch"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_generate_torch_metadata() -> None:
    """
    Creates a .safetensors file with a PyTorch tensor and custom metadata.

    This test generates a 2x2 tensor and attaches example metadata
    fields to simulate versioning and provenance. The resulting file
    can be used to test downstream metadata handling.

    Side Effects:
        Writes a .safetensors file to the output/safetensors_torch directory.
    """
    tensor: torch.Tensor = torch.ones((2, 2), dtype=torch.float32)
    metadata: Dict[str, str] = {"source": "test_case", "version": "1.0"}
    fname: str = os.path.join(OUTPUT_DIR, "torch_with_metadata.safetensors")
    save_file({"tensor": tensor}, fname, metadata=metadata)
