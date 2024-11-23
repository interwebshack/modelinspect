"""
Decompression utilities for ZIP file handling.

This module contains classes and functions to handle various decompression
methods used in ZIP files, including LZMA, BZ2, and deflate.
"""

import binascii
import bz2
import lzma
import struct
import zlib
from typing import Any, Callable, Optional, Union

try:
    import bz2  # We may need its compression method

    BZ2_AVAILABLE = True
except ImportError:
    BZ2_AVAILABLE = False

try:
    import lzma  # We may need its compression method

    LZMA_AVAILABLE = True
except ImportError:
    LZMA_AVAILABLE = False

try:
    import zlib  # We may need its compression method

    ZLIB_AVAILABLE = True
    crc32: Callable[[bytes], int] = zlib.crc32
except ImportError:
    ZLIB_AVAILABLE = False
    crc32 = binascii.crc32

from model_inspect.file_types.zip_file.constants import (
    ZIP_BZIP2,
    ZIP_DEFLATED,
    ZIP_LZMA,
    ZIP_STORED,
    compressor_names,
)


class LZMADecompressor:
    """
    A custom LZMA decompressor class for decompressing data in chunks with support
    for raw LZMA format.

    Attributes:
        eof (bool): Indicates if the end of the file has been reached during decompression.
    """

    def __init__(self) -> None:
        """
        Initializes the LZMADecompressor with internal states for decompression.

        Raises:
            RuntimeError: If lzma module is not available.
        """
        if not LZMA_AVAILABLE:
            raise RuntimeError("LZMA module is not available. Ensure lzma is installed.")

        self._decomp: Optional[lzma.LZMADecompressor] = None
        self._unconsumed: bytes = b""
        self.eof: bool = False

    def decompress(self, data: bytes) -> bytes:
        """
        Decompresses the provided LZMA compressed data.

        Args:
            data (bytes): The data to be decompressed.

        Returns:
            bytes: The decompressed data.

        Notes:
            This method initializes the decompressor on the first call by reading
            filter properties from the initial bytes of data. It continues to
            decompress data in chunks until the end of the file.

        Raises:
            RuntimeError: If decompression is attempted when lzma is not available.
        """
        if not LZMA_AVAILABLE:
            raise RuntimeError("LZMA module is not available. Decompression cannot proceed.")

        if self._decomp is None:
            self._unconsumed += data
            if len(self._unconsumed) <= 4:
                return b""
            (psize,) = struct.unpack("<H", self._unconsumed[2:4])
            if len(self._unconsumed) <= 4 + psize:
                return b""

            filter_props = self._unconsumed[4 : 4 + psize]
            self._decomp = lzma.LZMADecompressor(
                lzma.FORMAT_RAW,
                filters=[{"id": lzma.FILTER_LZMA1, "props": filter_props}],
            )
            data = self._unconsumed[4 + psize :]
            del self._unconsumed

        result = self._decomp.decompress(data)
        self.eof = self._decomp.eof
        return result


def _check_compression(compression: int) -> None:
    """
    Checks if the required compression module is available for the given compression type.

    Args:
        compression (int): The compression type identifier.

    Raises:
        RuntimeError: If the required compression module is missing.
        NotImplementedError: If the compression type is not supported.
    """
    if compression == ZIP_STORED:
        pass
    elif compression == ZIP_DEFLATED:
        if not zlib:
            raise RuntimeError("Compression requires the (missing) zlib module")
    elif compression == ZIP_BZIP2:
        if not bz2:
            raise RuntimeError("Compression requires the (missing) bz2 module")
    elif compression == ZIP_LZMA:
        if not lzma:
            raise RuntimeError("Compression requires the (missing) lzma module")
    else:
        raise NotImplementedError("That compression method is not supported")


# Use `Any` as a fallback for the zlib decompressor type to support fallback to binascii
DecompressorType = Optional[Union[Any, bz2.BZ2Decompressor, LZMADecompressor]]


def _get_decompressor(compress_type: int) -> DecompressorType:
    """
    Returns a decompressor object based on the specified compression type.

    Args:
        compress_type (int): The compression type identifier.

    Returns:
        DecompressorType:
            The decompressor object for the specified compression type,
            or None if no decompression is needed.

    Raises:
        NotImplementedError: If the compression type is not supported.
        RuntimeError: If the required compression module (e.g., zlib for ZIP_DEFLATED) is
        not available.
    """
    _check_compression(compress_type)

    if compress_type == ZIP_STORED:
        return None
    elif compress_type == ZIP_DEFLATED:
        if not ZLIB_AVAILABLE:
            raise RuntimeError(
                "Compression type ZIP_DEFLATED requires the zlib module, which is not available."
            )
        return zlib.decompressobj(-15)
    elif compress_type == ZIP_BZIP2:
        return bz2.BZ2Decompressor()
    elif compress_type == ZIP_LZMA:
        return LZMADecompressor()
    else:
        descr = compressor_names.get(compress_type)
        if descr:
            raise NotImplementedError(f"compression type {compress_type} ({descr})")
        else:
            raise NotImplementedError(f"compression type {compress_type}")
