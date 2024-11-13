"""
file_types.base_file.binary_file_base

This module defines the BinaryFileBase class, a foundational class for representing 
and analyzing common characteristics of binary files.

Classes:
    BinaryFileBase: A base class that defines basic properties and methods for analyzing
        binary files, such as start and end addresses, file size, checksum, permissions,
        and timestamps.

This module is intended to be extended by file-type-specific subclasses that add
methods and attributes for detailed analysis of specific binary file formats.
"""

import datetime
import hashlib
from pathlib import Path
from typing import Optional


class BinaryFileBase:
    """Base class representing a binary file with common characteristics.

    Attributes:
        file_path (Path): Path to the binary file.
        start_address (int): The starting address of the file in bytes.
        end_address (int): The ending address of the file in bytes.
        file_size (int): The size of the file in bytes.
        magic_number (Optional[str]): The magic number or identifier for the file type.
        checksum (Optional[str]): The checksum (e.g., SHA-256) for verifying file integrity.
        permissions (Optional[str]): Permissions of the file in string format.
        timestamp (datetime.datetime): Timestamp for file creation or modification.
        file_type (Optional[str]): The type or format of the binary file.
        endianness (Optional[str]): Endianness for multibyte numbers ("big" or "little").
    """

    def __init__(self, file_path: Path):
        """Initializes the BinaryFileBase class with a given file path.

        Args:
            file_path (Path): The path to the binary file.
        """
        self.file_path = file_path
        self.start_address = 0
        self.end_address = self.get_file_size()
        self.file_size = self.end_address
        self.magic_number = self.read_magic_number()
        self.checksum = self.calculate_checksum()
        self.permissions = self.get_permissions()
        self.timestamp = self.get_timestamp()
        self.file_type = None  # This would be determined by specific implementations.
        self.endianness = "big"  # Default; can be overridden by specific file types.

    def get_file_size(self) -> int:
        """Calculates the size of the file in bytes.

        Returns:
            int: Size of the file in bytes.
        """
        return self.file_path.stat().st_size

    def read_magic_number(self) -> Optional[str]:
        """Reads the magic number or identifier from the binary file.

        Returns:
            Optional[str]: The magic number or identifier as a string.
        """
        with self.file_path.open("rb") as f:
            return f.read(4).hex()  # Example: reading the first 4 bytes.

    def calculate_checksum(self) -> Optional[str]:
        """Calculates the SHA-256 checksum of the file.

        Returns:
            Optional[str]: The SHA-256 checksum as a hexadecimal string.
        """
        sha256 = hashlib.sha256()
        with self.file_path.open("rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_permissions(self) -> Optional[str]:
        """Retrieves the permissions of the file as a string.

        Returns:
            Optional[str]: File permissions as a string (e.g., "rw-r--r--").
        """
        return oct(self.file_path.stat().st_mode)[-3:]

    def get_timestamp(self) -> datetime.datetime:
        """Gets the last modified timestamp of the file.

        Returns:
            datetime.datetime: The last modified timestamp.
        """
        return datetime.datetime.fromtimestamp(self.file_path.stat().st_mtime)
