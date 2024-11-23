"""
utils.py

General-purpose utility functions for the ZIP file handling package.

This module provides helper functions for common operations like CRC-32
calculations, file path sanitization, byte conversions, and bit manipulation.
"""

import os
import zlib


def compute_crc32(data: bytes, crc: int = 0) -> int:
    """Compute the CRC-32 checksum of the given data."""
    return zlib.crc32(data, crc) & 0xFFFFFFFF


def int_to_bytes(value: int, length: int, byteorder: str = "little") -> bytes:
    """Convert an integer to a byte string of a given length."""
    return value.to_bytes(length, byteorder)


def bytes_to_int(data: bytes, byteorder: str = "little") -> int:
    """Convert a byte string to an integer."""
    return int.from_bytes(data, byteorder)


def is_bit_set(value: int, bit: int) -> bool:
    """Check if a specific bit is set in an integer."""
    return (value & (1 << bit)) != 0


def parse_local_file_header(data: bytes) -> dict:
    """Parse a ZIP file's local file header."""
    if len(data) < 30:
        raise ValueError("Invalid local file header data.")
    return {
        "signature": data[:4],
        "extract_version": int.from_bytes(data[4:6], "little"),
        "flag_bits": int.from_bytes(data[6:8], "little"),
        "compression_method": int.from_bytes(data[8:10], "little"),
        "mod_time": int.from_bytes(data[10:12], "little"),
        "mod_date": int.from_bytes(data[12:14], "little"),
        "crc": int.from_bytes(data[14:18], "little"),
        "compressed_size": int.from_bytes(data[18:22], "little"),
        "uncompressed_size": int.from_bytes(data[22:26], "little"),
        "filename_length": int.from_bytes(data[26:28], "little"),
        "extra_field_length": int.from_bytes(data[28:30], "little"),
    }


def sanitize_filename(filename: str) -> str:
    """Sanitizes the filename by terminating at the first null byte and
    ensuring paths use forward slashes as the directory separator.

    Args:
        filename (str): The input filename to sanitize.

    Returns:
        str: The sanitized filename, with null bytes removed and directory
             separators converted to forward slashes.
    """
    # Terminate the file name at the first null byte.  Null bytes in file
    # names are used as tricks by viruses in archives.
    null_byte = filename.find(chr(0))
    if null_byte >= 0:
        filename = filename[0:null_byte]

    # This is used to ensure paths in generated ZIP files always use
    # forward slashes as the directory separator, as required by the
    # ZIP format specification.
    if os.sep != "/" and os.sep in filename:
        filename = filename.replace(os.sep, "/")

    # Replace alternative separator if present and different from forward slash.
    if os.altsep and os.altsep != "/" and os.altsep in filename:
        filename = filename.replace(os.altsep, "/")

    return filename
