"""
Generates .safetensors files containing PyTorch tensors with varied shapes
for use in testing shape handling in downstream tools like `ai-forensics`.

This module is intended to create a suite of test files that include:
    - Standard 1D and 2D shapes
    - Edge cases like zero-sized dimensions
    - Higher-dimensional shapes
    - Large tensors

Files are saved under the output/safetensors_torch directory.
"""

import os
from typing import Tuple

import pytest
import torch
from safetensors.torch import save_file

OUTPUT_DIR = "output/safetensors_torch"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SHAPES = [
    (1,),  # 1D vector
    (2, 2),  # Standard 2D matrix
    (0, 5),  # Edge case: zero-size dimension
    (1, 1, 1),  # 3D tensor
    (1000, 1000),  # Large tensor
]


@pytest.mark.parametrize("shape", SHAPES)
def test_generate_torch_varied_shapes(shape: Tuple[int, ...]) -> None:
    """
    Generates a .safetensors file with a PyTorch tensor of a specific shape.

    This function creates a tensor filled with ones using the specified shape
    and saves it to disk in the SafeTensors format. The output files are
    named according to their shape for traceability.

    Args:
        shape (Tuple[int, ...]): The shape of the PyTorch tensor to generate.

    Side Effects:
        Writes a .safetensors file to the output/safetensors_torch directory.
    """
    tensor = torch.ones(shape, dtype=torch.float32)
    fname = f"torch_shape_{'_'.join(map(str, shape))}.safetensors"
    save_file({"tensor": tensor}, os.path.join(OUTPUT_DIR, fname))
