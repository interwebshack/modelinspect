from abc import ABC, abstractmethod


class ModelScanner(ABC):
    """Abstract base class for model scanners."""

    @abstractmethod
    def scan(self, file_path: str) -> bool:
        """Scans the given file for malware.

        Args:
            file_path: The path to the model file.

        Returns:
            True if the file is clean, False if malware is detected.
        """
        pass
