"""
Generates .safetensors files containing NumPy arrays with various supported dtypes
for use in testing how tools like `ai-forensics` handle different data types.

Each test case creates a tensor of shape (2, 3) filled with ones, using a specific
supported NumPy dtype. The output files are saved in the 'output/numpy_dtypes'
directory and named according to their dtype (e.g., numpy_float32.safetensors).

Supported dtypes include:
    - Floating point: float16, float32, float64
    - Signed integers: int8, int16, int32, int64
    - Unsigned integers: uint8
    - Boolean: bool_

Output:
- File saved to tests/models/numpy_dtypes directory.
"""

import os
from typing import Type

import numpy as np
import pytest
from safetensors.numpy import save_file

OUTPUT_DIR = "tests/models/safetensors_numpy"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUPPORTED_DTYPES = [
    np.float16,
    np.float32,
    np.float64,
    np.int8,
    np.int16,
    np.int32,
    np.int64,
    np.uint8,
    np.bool_,
]


@pytest.mark.parametrize("dtype", SUPPORTED_DTYPES)
def test_generate_numpy_dtype_files(dtype: Type[np.generic]) -> None:
    """
    Generates a .safetensors file with a NumPy tensor of the specified dtype.

    This function creates a (2, 3) NumPy array filled with ones using the
    provided dtype, and saves it as a .safetensors file. The purpose is to
    generate test cases for dtype-specific handling in downstream tools.

    Args:
        dtype (Type[np.generic]): A supported NumPy data type for the tensor.

    Side Effects:
        Writes a .safetensors file to the output/numpy_dtypes directory.
    """
    arr = np.ones((2, 3), dtype=dtype)
    file_name = f"numpy_{dtype.__name__}.safetensors"
    save_file({"tensor": arr}, os.path.join(OUTPUT_DIR, file_name))
