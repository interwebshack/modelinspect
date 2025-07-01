"""
Generates .safetensors files containing PyTorch tensors of various supported dtypes
to test downstream handling of data types in tools like `ai-forensics`.

This module produces one file per supported dtype. Each file contains a 2x2 tensor
of ones, serialized in SafeTensors format. These files are intended for validating
type inference and parsing behavior in post-processing tools.

Output:
    Files are saved in the tests/models/safetensors_torch directory and named as:
    test_torch_<dtype>.safetensors (e.g., test_torch_float32.safetensors)

Output:
    - File saved to tests/models/safetensors_torch directory.
"""

import os
from typing import List

import pytest
import torch
from safetensors.torch import save_file

OUTPUT_DIR = "tests/models/safetensors_torch"
os.makedirs(OUTPUT_DIR, exist_ok=True)

SUPPORTED_DTYPES: List[torch.dtype] = [
    torch.float16,
    torch.float32,
    torch.float64,
    torch.int8,
    torch.int16,
    torch.int32,
    torch.int64,
    torch.uint8,
    torch.bool,
]


@pytest.mark.parametrize("dtype", SUPPORTED_DTYPES)
def test_generate_torch_dtype_files(dtype: torch.dtype) -> None:
    """
    Generates a .safetensors file with a PyTorch tensor of the specified dtype.

    Each file contains a (2, 2) tensor filled with ones. The file is saved with a name
    that reflects the dtype being tested.

    Args:
        dtype (torch.dtype): The PyTorch data type (e.g., torch.float32).

    Side Effects:
        Writes a .safetensors file to the output/safetensors_torch directory.
    """
    t: torch.Tensor = torch.ones((2, 2), dtype=dtype)
    dtype_name: str = str(dtype).split(".")[-1]
    fname: str = os.path.join(OUTPUT_DIR, f"test_torch_{dtype_name}.safetensors")
    save_file({"tensor": t}, fname)
