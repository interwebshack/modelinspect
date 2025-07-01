# conftest.py

import pytest
from pathlib import Path

@pytest.fixture
def model_dir() -> Path:
    return Path(__file__).parent / "models"

@pytest.fixture
def dummy_pth(model_dir: Path) -> Path:
    return model_dir / "dummy.pth"

@pytest.fixture
def dummy_gguf(model_dir: Path) -> Path:
    return model_dir / "dummy.gguf"

@pytest.fixture
def dummy_safetensors(model_dir: Path) -> Path:
    return model_dir / "dummy.safetensors"
