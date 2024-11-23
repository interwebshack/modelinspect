import os
import stat
import struct
import sys
import time
import warnings
from typing import Optional, Tuple, Union

from model_inspect.file_types.zip_file.constants import (
    DEFAULT_VERSION,
    ZIP_BZIP2,
    ZIP_LZMA,
    ZIP_STORED,
    compressor_names,
)
from model_inspect.file_types.zip_file.utils import sanitize_filename


class ZipInfo:
    """Class with attributes describing each file in the ZIP archive.

    Attributes:
        orig_filename (str): Original file name in the archive.
        filename (str): Normalized file name (with sanitized path).
        date_time (Tuple[int, int, int, int, int, int]):
            Timestamp as (year, month, day, hour, min, sec).
        compress_type (int): Type of compression for the file (default is ZIP_STORED).
        compress_level (Optional[int]): Level for the compressor, if applicable.
        comment (bytes): Comment for the file in the ZIP archive.
        extra (bytes): Extra data field in the ZIP format.
        create_system (int): System that created the ZIP archive (0 for Windows, 3 for Unix).
        create_version (int): ZIP version that created the archive.
        extract_version (int): ZIP version required to extract the archive.
        reserved (int): Reserved field, must be zero.
        flag_bits (int): ZIP flag bits.
        volume (int): Volume number of the file header.
        internal_attr (int): Internal attributes for the file.
        external_attr (int): External attributes for the file.
        header_offset (Optional[int]): Byte offset to the file header (set externally).
        CRC (Optional[int]): CRC-32 of the uncompressed file (set externally).
        compress_size (int): Size of the compressed file.
        file_size (int): Size of the uncompressed file.
        _raw_time (Optional[int]): Raw time data (set externally).
        _end_offset (Optional[int]): Offset to the end of the file in the ZIP archive.
    """

    __slots__ = (
        "orig_filename",
        "filename",
        "date_time",
        "compress_type",
        "compress_level",
        "comment",
        "extra",
        "create_system",
        "create_version",
        "extract_version",
        "reserved",
        "flag_bits",
        "volume",
        "internal_attr",
        "external_attr",
        "header_offset",
        "crc_value",
        "compress_size",
        "file_size",
        "_raw_time",
        "_end_offset",
    )

    def __init__(
        self,
        filename: str = "NoName",
        date_time: Tuple[int, int, int, int, int, int] = (1980, 1, 1, 0, 0, 0),
    ):
        """Initialize the ZipInfo object with the provided filename and timestamp.

        Args:
            filename (str): Original file name in the archive (default is "NoName").
            date_time (Tuple[int, int, int, int, int, int]):
                Timestamp as (year, month, day, hour, min, sec).
                Raises ValueError if the year is before 1980.

        Raises:
            ValueError: If the date_time's year is before 1980
                        (ZIP does not support dates earlier than 1980).
        """
        self.orig_filename: str = filename  # Original file name in archive

        # Terminate the file name at the first null byte and
        # ensure paths always use forward slashes as the directory separator.
        filename = sanitize_filename(filename)

        self.filename: str = filename  # Normalized file name
        self.date_time: Tuple[int, int, int, int, int, int] = (
            date_time  # year, month, day, hour, min, sec
        )

        if date_time[0] < 1980:
            raise ValueError("ZIP does not support timestamps before 1980")

        # Standard values:
        self.compress_type: int = ZIP_STORED  # Type of compression for the file
        self.compress_level: Optional[int] = None  # Level for the compressor
        self.comment: bytes = b""  # Comment for each file
        self.extra: bytes = b""  # ZIP extra data
        # System which created ZIP archive
        self.create_system: int = (
            0 if sys.platform == "win32" else 3
        )  # Assume everything else is unix-y
        self.create_version: int = DEFAULT_VERSION  # Version which created ZIP archive
        self.extract_version: int = DEFAULT_VERSION  # Version needed to extract archive
        self.reserved: int = 0  # Must be zero
        self.flag_bits: int = 0  # ZIP flag bits
        self.volume: int = 0  # Volume number of file header
        self.internal_attr: int = 0  # Internal attributes
        self.external_attr: int = 0  # External file attributes
        self.compress_size: int = 0  # Size of the compressed file
        self.file_size: int = 0  # Size of the uncompressed file
        self.crc_value: int = 0  # CRC-32 of the uncompressed file
        self.header_offset: Optional[int] = None  # Byte offset to the file header
        self._raw_time: Optional[int] = None  # Raw time data, set externally
        self._end_offset: Optional[int] = (
            None  # Start of the next local header or central directory
        )

    # Maintain backward compatibility with the old protected attribute name.
    @property
    def _compresslevel(self) -> Optional[int]:
        """Get the compression level for backward compatibility.

        Returns:
            Optional[int]: The compression level, if set; otherwise, None.
        """
        return self.compress_level

    @_compresslevel.setter
    def _compresslevel(self, value: Optional[int]) -> None:
        """Set the compression level for backward compatibility.

        Args:
            value (Optional[int]): The compression level to set.
        """
        self.compress_level = value

    def __repr__(self) -> str:
        """Return a string representation of the ZipInfo object.

        The representation includes filename, compression type, file mode,
        external attributes, file size, and compression size.

        Returns:
            str: A string representation of the ZipInfo object.
        """
        result = [f"<{self.__class__.__name__} filename={self.filename!r}"]
        if self.compress_type != ZIP_STORED:
            result.append(
                f" compress_type={compressor_names.get(self.compress_type, self.compress_type)}"
            )
        hi = self.external_attr >> 16
        lo = self.external_attr & 0xFFFF
        if hi:
            result.append(f" filemode={stat.filemode(hi)!r}")
        if lo:
            result.append(f" external_attr={lo:#x}")
        isdir: bool = self.is_dir()
        if not isdir or self.file_size:
            result.append(f" file_size={self.file_size!r}")
        if (not isdir or self.compress_size) and (
            self.compress_type != ZIP_STORED or self.file_size != self.compress_size
        ):
            result.append(f" compress_size={self.compress_size!r}")
        result.append(">")
        return "".join(result)

    def file_header(self, zip64: Optional[bool] = None) -> bytes:
        """Generate the per-file header as a bytes object.

        Args:
            zip64 (Optional[bool]): Determines whether ZIP64 format should be used.
                If None, ZIP64 is used if file_size or compress_size exceeds ZIP64 limit.

        Returns:
            bytes: The file header in binary format.
        """
        dt = self.date_time
        dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
        dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)

        if self.flag_bits & _MASK_USE_DATA_DESCRIPTOR:
            # Set these to zero because they are written after file data
            crc_value = compress_size = file_size = 0
        else:
            crc_value = self.crc_value
            compress_size = self.compress_size
            file_size = self.file_size

        extra = self.extra

        min_version = 0
        if zip64 is None:
            # Default to ZIP64 if file or compression size exceeds the limit
            # We always explicitly pass zip64 within this module.... This
            # remains for anyone using ZipInfo.file_header as a public API.
            zip64 = file_size > ZIP64_LIMIT or compress_size > ZIP64_LIMIT
        if zip64:
            fmt = "<HHQQ"
            extra += struct.pack(fmt, 1, struct.calcsize(fmt) - 4, file_size, compress_size)
            file_size = 0xFFFFFFFF
            compress_size = 0xFFFFFFFF
            min_version = ZIP64_VERSION

        if self.compress_type == ZIP_BZIP2:
            min_version = max(BZIP2_VERSION, min_version)
        elif self.compress_type == ZIP_LZMA:
            min_version = max(LZMA_VERSION, min_version)

        self.extract_version = max(min_version, self.extract_version)
        self.create_version = max(min_version, self.create_version)

        filename, flag_bits = self._encode_filename_flags()
        header = struct.pack(
            structFileHeader,
            stringFileHeader,
            self.extract_version,
            self.reserved,
            flag_bits,
            self.compress_type,
            dostime,
            dosdate,
            crc_value,
            compress_size,
            file_size,
            len(filename),
            len(extra),
        )
        return header + filename + extra

    def _encode_filename_flags(self) -> Tuple[bytes, int]:
        """Encode the filename and determine the appropriate flag bits.

        Returns:
            Tuple[bytes, int]: A tuple containing the encoded filename as bytes and
            the flag bits, with UTF-8 encoding flag set if needed.
        """
        try:
            return self.filename.encode("ascii"), self.flag_bits
        except UnicodeEncodeError:
            return self.filename.encode("utf-8"), self.flag_bits | _MASK_UTF_FILENAME

    def _decode_extra(self, filename_crc: int) -> None:
        """Decode the extra field data for ZIP64 extensions and Unicode path handling.

        Args:
            filename_crc (int): The CRC-32 checksum of the filename used to validate
                the Unicode Path Extra Field.

        Raises:
            BadZipFile: If the extra field is corrupt, or if there are issues decoding
                the ZIP64 or Unicode path extra fields.
        """
        # Try to decode the extra field.
        extra = self.extra
        unpack = struct.unpack

        while len(extra) >= 4:
            tp, ln = unpack("<HH", extra[:4])
            if ln + 4 > len(extra):
                raise BadZipFile(f"Corrupt extra field {tp:04x} (size={ln})")

            if tp == 0x0001:
                data = extra[4 : ln + 4]
                # ZIP64 extension for large files and archives
                field = "Unknown field"  # Default value for field
                try:
                    if self.file_size in (0xFFFF_FFFF_FFFF_FFFF, 0xFFFF_FFFF):
                        field = "File size"
                        (self.file_size,) = unpack("<Q", data[:8])
                        data = data[8:]
                    if self.compress_size == 0xFFFF_FFFF:
                        field = "Compress size"
                        (self.compress_size,) = unpack("<Q", data[:8])
                        data = data[8:]
                    if self.header_offset == 0xFFFF_FFFF:
                        field = "Header offset"
                        (self.header_offset,) = unpack("<Q", data[:8])
                except struct.error:
                    raise BadZipFile(f"Corrupt zip64 extra field. {field} not found.") from None

            elif tp == 0x7075:
                data = extra[4 : ln + 4]
                # Unicode Path Extra Field
                try:
                    up_version, up_name_crc = unpack("<BL", data[:5])
                    if up_version == 1 and up_name_crc == filename_crc:
                        up_unicode_name = data[5:].decode("utf-8")
                        if up_unicode_name:
                            self.filename = sanitize_filename(up_unicode_name)
                        else:
                            warnings.warn("Empty unicode path extra field (0x7075)", stacklevel=2)
                except struct.error as e:
                    raise BadZipFile("Corrupt unicode path extra field (0x7075)") from e
                except UnicodeDecodeError as e:
                    raise BadZipFile(
                        "Corrupt unicode path extra field (0x7075): invalid utf-8 bytes"
                    ) from e

            extra = extra[ln + 4 :]

    @classmethod
    def from_file(
        cls,
        filename: Union[str, os.PathLike[str]],
        arcname: Optional[str] = None,
        *,
        strict_timestamps: bool = True,
    ) -> "ZipInfo":
        """Construct an appropriate ZipInfo instance for a file on the filesystem.

        Args:
            filename (Union[str, os.PathLike[str]]): The path to a file or directory on the
                filesystem.
            arcname (Optional[str]): The name which the file will have within the archive. Defaults
                to the same as `filename`, but without a drive letter and with leading path
                separators removed.
            strict_timestamps (bool): If True, restricts the timestamp range between 1980 and 2107
                (ZIP file specification limits). Defaults to True.

        Returns:
            ZipInfo: A ZipInfo instance containing file information.

        Raises:
            OSError: If there is an error accessing the file or directory.
        """

        if isinstance(filename, os.PathLike):
            filename = os.fspath(filename)
        st = os.stat(filename)
        isdir = stat.S_ISDIR(st.st_mode)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]

        # Enforce timestamp limits if strict_timestamps is False
        if not strict_timestamps:
            if date_time[0] < 1980:
                date_time = (1980, 1, 1, 0, 0, 0)
            elif date_time[0] > 2107:
                date_time = (2107, 12, 31, 23, 59, 59)

        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        if isdir:
            arcname += "/"

        # Create and populate ZipInfo instance
        zinfo = cls(arcname, date_time)
        zinfo.external_attr = (st.st_mode & 0xFFFF) << 16  # Unix attributes
        if isdir:
            zinfo.file_size = 0
            zinfo.external_attr |= 0x10  # MS-DOS directory flag
        else:
            zinfo.file_size = st.st_size

        return zinfo

    def is_dir(self) -> bool:
        """Check if this archive member represents a directory.

        Returns:
            bool: True if the member is a directory, False otherwise.
        """
        if self.filename.endswith("/"):
            return True
        # The ZIP format specification requires to use forward slashes
        # as the directory separator, but in practice some ZIP files
        # created on Windows can use backward slashes.  For compatibility
        # with the extraction code which already handles this:
        if os.path.altsep:
            return self.filename.endswith((os.path.sep, os.path.altsep))
        return False
