"""
Generates a .safetensors file containing NumPy array metadata
for testing metadata extraction and validation in downstream tools like aiforensics.

This test ensures that a .safetensors file can include arbitrary metadata
and be successfully saved for later analysis.

The generated file includes:
    - A tensor of shape (2, 2)
    - Metadata such as versioning and source tags

Output:
    - File saved to output/numpy_dtypes/numpy_with_metadata.safetensors
"""

import os
from typing import Dict

import numpy as np
import numpy.typing as npt
from safetensors.numpy import save_file

OUTPUT_DIR = "output/safetensors_numpy"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_generate_numpy_metadata() -> None:
    """
    Creates a .safetensors file with NumPy tensor and custom metadata.

    This test generates a 2x2 tensor and attaches example metadata
    fields to simulate versioning and provenance. The resulting file
    can be used to test downstream metadata handling.

    Side Effects:
        Writes a .safetensors file to the output/numpy_dtypes directory.
    """
    arr: npt.NDArray[np.float32] = np.ones((2, 2), dtype=np.float32)
    metadata: Dict[str, str] = {"source": "test_case", "version": "1.0"}
    fname: str = os.path.join(OUTPUT_DIR, "numpy_with_metadata.safetensors")
    save_file({"tensor": arr}, fname, metadata=metadata)
