"""
Generates .safetensors files containing NumPy arrays with varied shapes
for use in testing shape handling in downstream tools like `ai-forensics`.

This module is intended to create a suite of test files that include:
    - Standard 1D and 2D shapes
    - Edge cases like zero-sized dimensions
    - Higher-dimensional shapes
    - Large tensors

Files are saved under the output/numpy_dtypes directory.
"""

import os
from typing import Tuple

import numpy as np
import pytest
from safetensors.numpy import save_file

OUTPUT_DIR = "output/safetensors_numpy"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SHAPES = [(1,), (2, 2), (0, 5), (1, 1, 1), (1000, 1000)]


@pytest.mark.parametrize("shape", SHAPES)
def test_generate_numpy_varied_shapes(shape: Tuple[int, ...]) -> None:
    """
    Generates a .safetensors file with a NumPy array of a specific shape.

    This function creates a tensor filled with ones using the specified shape
    and saves it to disk in the SafeTensors format. The output files are
    named according to their shape for traceability.

    Args:
        shape (Tuple[int, ...]): The shape of the NumPy array to generate.

    Side Effects:
        Writes a .safetensors file to the output/numpy_dtypes directory.
    """
    arr = np.ones(shape, dtype=np.float32)
    fname = f"numpy_shape_{'_'.join(map(str, shape))}.safetensors"

    save_file({"tensor": arr}, os.path.join(OUTPUT_DIR, fname))
