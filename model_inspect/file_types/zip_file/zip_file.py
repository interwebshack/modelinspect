"""
Most of this code was duplicated from the cpython zipfile library.
https://github.com/python/cpython/blob/ef172521a9e9dfadebe57d590bfb53a0e9ac3a0b/Lib/zipfile/__init__.py

Only the read functions have been added to this file - the modelinspect
project only needs to read and identify zip files.  Type hints and other code
quality improvements have been added to the file.
"""

import binascii
import io
import os
import shutil
import stat
import struct
import sys
import threading
import time
import warnings
from typing import IO, Any, BinaryIO, Callable, ClassVar, Dict, List, Optional, Tuple, Union

try:
    import zlib  # We may need its compression method

    ZLIB_AVAILABLE = True
    crc32: Callable[[bytes], int] = zlib.crc32
except ImportError:
    ZLIB_AVAILABLE = False
    crc32 = binascii.crc32

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


class BadZipFile(Exception):
    """Raised when a ZIP file is found to be corrupt."""


# Below are some formats and associated data for reading headers using
# the struct module.  The names and structures of headers/records are those used
# in the PKWARE description of the ZIP file format:
#     http://www.pkware.com/documents/casestudies/APPNOTE.TXT
# (URL valid as of January 2008)

# The "end of central directory" structure, magic number, size, and indices
# (section V.I in the format document)
structEndArchive = b"<4s4H2LH"
stringEndArchive = b"PK\005\006"
sizeEndCentDir = struct.calcsize(structEndArchive)

# The "central directory" structure, magic number, size, and indices
# of entries in the structure (section V.F in the format document)
structCentralDir = "<4s4B4HL2L5H2L"
stringCentralDir = b"PK\001\002"
sizeCentralDir = struct.calcsize(structCentralDir)

# The "local file header" structure, magic number, size, and indices
# (section V.A in the format document)
structFileHeader = "<4s2B4HL2L2H"
stringFileHeader = b"PK\003\004"
sizeFileHeader = struct.calcsize(structFileHeader)


# The "Zip64 end of central directory locator" structure, magic number, and size
structEndArchive64Locator = "<4sLQL"
stringEndArchive64Locator = b"PK\x06\x07"
sizeEndCentDir64Locator = struct.calcsize(structEndArchive64Locator)

# The "Zip64 end of central directory" record, magic number, size, and indices
# (section V.G in the format document)
structEndArchive64 = "<4sQ2H2L4Q"
stringEndArchive64 = b"PK\x06\x06"
sizeEndCentDir64 = struct.calcsize(structEndArchive64)


def _check_zipfile(fp: BinaryIO) -> bool:
    """Check if a file-like object is a valid ZIP file.

    This function attempts to validate a file by checking for a correct
    magic number at the end of the file using the _end_rec_data function.

    Args:
        fp (BinaryIO): A file-like object opened in binary mode.

    Returns:
        bool: True if the file has the correct magic number, indicating
        it is a valid ZIP file; otherwise, False.
    """
    try:
        if _end_rec_data(fp):
            return True  # file has correct magic number
    except OSError:
        pass
    return False


def is_zipfile(filename: Union[str, BinaryIO]) -> bool:
    """Check if a file is a ZIP file by verifying the magic number.

    This function quickly checks if a file or file-like object is a ZIP file
    by reading its "End of Central Directory" record's magic number.

    Args:
        filename (Union[str, BinaryIO]): The path to the file or a file-like object.

    Returns:
        bool: True if the file is a ZIP file, otherwise False.

    Raises:
        TypeError: If filename is not a string or a file-like object with a 'read' method.
    """
    result = False
    try:
        if isinstance(filename, str):
            with open(filename, "rb") as fp:  # Open as BinaryIO if filename is a string
                result = _check_zipfile(fp)
        elif hasattr(filename, "read"):
            result = _check_zipfile(filename)  # Directly pass if already a BinaryIO
        else:
            raise TypeError(
                "filename must be a path (str) or a file-like object with a 'read' method."
            )
    except OSError:
        pass
    return result


def _end_rec_data_64(
    fpin: BinaryIO, offset: int, endrec: Dict[Union[int, str], int]
) -> Dict[Union[int, str], int]:
    """
    Reads the ZIP64 end-of-archive records from the provided file pointer and uses that data
    to update the end-of-central-directory (endrec) dictionary.

    This function seeks to specific offsets within the ZIP64 file structure, validates
    file signatures, and updates `endrec` if the file is determined to contain a valid
    ZIP64 end-of-archive record.

    Args:
        fpin (BinaryIO): The binary file pointer to the ZIP file.
        offset (int): The offset to seek to for reading the end-of-central-directory locator.
        endrec (Dict[Union[int, str], int]): A dictionary containing details about the
                end-of-central-directory.

    Returns:
        Dict[Union[int, str], int]: Updated end-of-central-directory dictionary with
                ZIP64 data if valid.

    Raises:
        BadZipFile: If the file spans multiple disks, which is not supported.
    """
    try:
        fpin.seek(offset - sizeEndCentDir64Locator, 2)
    except OSError:
        # If the seek fails, the file is not large enough to contain a ZIP64
        # end-of-archive record, so just return the end record we were given.
        return endrec

    data = fpin.read(sizeEndCentDir64Locator)
    if len(data) != sizeEndCentDir64Locator:
        return endrec
    sig, diskno, reloff, disks = struct.unpack(structEndArchive64Locator, data)

    # The relative offset of the ZIP64 end-of-central-directory record
    # The function assumes that the ZIP64 End of Central Directory (EOCD) record is located
    # immediately before the End of Central Directory Locator in the file. Therefore, it
    # seeks to offset - sizeEndCentDir64Locator - sizeEndCentDir64 rather than using reloff.
    # This approach skips the need to go back and forth in the file, assuming a fixed structure
    # instead.  We are deleting the variable to satisfy pylint Unused variable 'reloff' issue.
    del reloff

    if sig != stringEndArchive64Locator:
        return endrec

    if diskno != 0 or disks > 1:
        raise BadZipFile("zipfiles that span multiple disks are not supported")

    # Assume no 'zip64 extensible data'
    fpin.seek(offset - sizeEndCentDir64Locator - sizeEndCentDir64, 2)
    data = fpin.read(sizeEndCentDir64)
    if len(data) != sizeEndCentDir64:
        return endrec
    (
        sig,  # "signature" field in the ZIP64 End of Central Directory (EOCD)
        sz,  # size of the ZIP64 End of Central Directory (EOCD) record in bytes.
        create_version,  # "version made by" field in the ZIP64 EOCD record.
        read_version,  # "version needed to extract" field in the ZIP64 EOCD record.
        disk_num,
        disk_dir,
        dircount,
        dircount2,
        dirsize,
        diroffset,
    ) = struct.unpack(structEndArchive64, data)
    if sig != stringEndArchive64:
        return endrec

    # Although sz is extracted here, it’s not used further in the function. In a more detailed
    # implementation, sz could be checked against the actual data read to ensure consistency or
    # to confirm that the ZIP64 EOCD record has been read correctly.
    # We are deleting the variable to satisfy pylint Unused variable 'sz' issue.
    del sz

    # In this function, `create_version`` is extracted but not used further. In more detailed
    # implementations, it could help handle compatibility checks, determine specific features
    # within the ZIP file, or adjust processing based on the creation platform.
    # We are deleting the variable to satisfy pylint Unused variable 'create_version' issue.
    del create_version

    # In this function, `read_version`` is extracted but not utilized further. It could,
    # however, be used in a more detailed implementation to verify that the ZIP file’s
    # format requirements match the capabilities of the reading software or library.
    # We are deleting the variable to satisfy pylint Unused variable 'read_version' issue.
    del read_version

    # Update the original endrec using data from the ZIP64 record
    endrec[_ZIP64_SIGNATURE] = sig
    endrec[_ZIP64_DISK_NUMBER] = disk_num
    endrec[_ZIP64_DISK_START] = disk_dir
    endrec[_ZIP64_ENTRIES_THIS_DISK] = dircount
    endrec[_ZIP64_ENTRIES_TOTAL] = dircount2
    endrec[_ZIP64_SIZE] = dirsize
    endrec[_ZIP64_OFFSET] = diroffset
    return endrec


def _end_rec_data(fpin: BinaryIO) -> Optional[List[Union[bytes, int]]]:
    """Return data from the 'End of Central Directory' record, or None.

    This function reads and interprets the "End of Central Directory" record in
    a ZIP file, verifying its structure and content. If the record is found, it
    returns a list of nine items from the record followed by a blank comment
    and the file seek offset of the record. If the record includes a ZIP64 end
    of central directory structure, additional data may be included.

    Args:
        fpin (BinaryIO): A file-like object opened in binary mode to read the ZIP data.

    Returns:
        Optional[List[Union[bytes, int]]]: A list of values from the "End of Central Directory"
        record, or None if the record is not found or cannot be read correctly.
    """
    # Determine file size
    fpin.seek(0, 2)
    filesize = fpin.tell()

    # Check to see if this is ZIP file with no archive comment (the
    # "end of central directory" structure should be the last item in the
    # file if this is the case).
    try:
        fpin.seek(-sizeEndCentDir, 2)
    except OSError:
        return None
    data = fpin.read()
    if len(data) == sizeEndCentDir and data[0:4] == stringEndArchive and data[-2:] == b"\000\000":
        # the signature is correct and there's no comment, unpack structure
        endrec = list(struct.unpack(structEndArchive, data))

        # Append a blank comment and record start offset
        endrec.append(b"")
        endrec.append(filesize - sizeEndCentDir)

        # Try to read the "Zip64 end of central directory" structure
        # Convert `endrec` to dictionary with integer keys and pass to `_end_rec_data_64`
        zip64_data = _end_rec_data_64(fpin, -sizeEndCentDir, {i: v for i, v in enumerate(endrec)})
        if isinstance(zip64_data, dict):
            return list(zip64_data.values())
        return zip64_data

    # Either this is not a ZIP file, or it is a ZIP file with an archive
    # comment.  Search the end of the file for the "end of central directory"
    # record signature. The comment is the last item in the ZIP file and may be
    # up to 64K long.  It is assumed that the "end of central directory" magic
    # number does not appear in the comment.
    max_comment_start = max(filesize - (1 << 16) - sizeEndCentDir, 0)
    fpin.seek(max_comment_start, 0)
    data = fpin.read()
    start = data.rfind(stringEndArchive)
    if start >= 0:
        # found the magic number; attempt to unpack and interpret
        rec_data = data[start : start + sizeEndCentDir]
        if len(rec_data) != sizeEndCentDir:
            # Zip file is corrupted.
            return None
        endrec = list(struct.unpack(structEndArchive, rec_data))
        comment_size = endrec[_ECD_COMMENT_SIZE]  # as claimed by the zip file
        comment = data[start + sizeEndCentDir : start + sizeEndCentDir + comment_size]
        endrec.append(comment)
        endrec.append(max_comment_start + start)

        # Try to read the "Zip64 end of central directory" structure
        zip64_data = _end_rec_data_64(
            fpin, max_comment_start + start - filesize, {i: v for i, v in enumerate(endrec)}
        )
        if isinstance(zip64_data, dict):
            return list(zip64_data.values())
        return zip64_data

    # Unable to find a valid end of central directory structure
    return None


def _sanitize_filename(filename: str) -> str:
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
        filename = _sanitize_filename(filename)

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
                            self.filename = _sanitize_filename(up_unicode_name)
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


# ZIP supports a password-based form of encryption. Even though known
# plaintext attacks have been found against it, it is still useful
# to be able to get data out of such a file.
#
# Usage:
#     password = b'my_password'
#     encrypted_data = b'\x9a\xdc\xff...'  # Encrypted bytes from a ZIP file
#     zd = ZipDecrypter(password)
#     plain_bytes = zd.decrypt(encrypted_data)
class ZipDecrypter:
    """ZIP file decrypter using legacy password-based encryption with custom CRC32 implementation.

    This class implements the ZIP legacy encryption algorithm, which updates
    internal keys with each byte processed. It provides a method to decrypt
    encrypted data using these keys.
    """

    # Generate the CRC32 table once at the class level
    _crctable: ClassVar[List[int]] = []

    # ZIP encryption uses the CRC32 one-byte primitive for scrambling some
    # internal keys. We noticed that a direct implementation is faster than
    # relying on binascii.crc32().
    @staticmethod
    def _gen_crc(crc: int) -> int:
        """
        Generate a CRC-32 checksum for one byte.

        This function performs bitwise operations to compute the CRC-32
        checksum using the polynomial 0xEDB88320.

        Args:
            crc (int): The initial CRC value.

        Returns:
            int: The updated CRC-32 checksum.
        """
        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xEDB88320
            else:
                crc >>= 1
        return crc & 0xFFFFFFFF

    @classmethod
    def _init_crctable(cls) -> None:
        """Initialize the CRC table if it hasn't been initialized yet."""
        if not cls._crctable:
            cls._crctable = [cls._gen_crc(i) for i in range(256)]

    def __init__(self, password: bytes):
        """Initialize the decrypter with the given password.

        Args:
            password (bytes): The password used to initialize decryption keys.
        """
        # Initialize the CRC table
        self._init_crctable()

        # Initialize keys
        self.key0: int = 0x12345678
        self.key1: int = 0x23456789
        self.key2: int = 0x34567890

        # Update keys with the password
        for char in password:
            self._update_keys(char)

    def _compute_crc32_byte(self, ch: int, crc: int) -> int:
        """Compute the CRC32 primitive on one byte.

        Args:
            ch (int): The byte to apply CRC on.
            crc (int): The current CRC value.

        Returns:
            int: The updated CRC value after applying the byte.
        """
        return (crc >> 8) ^ self._crctable[(crc ^ ch) & 0xFF]

    def _update_keys(self, byte_value: int) -> None:
        """Update internal keys based on the provided byte.

        Args:
            byte_value (int): The byte used to update the decryption keys.
        """
        self.key0 = self._compute_crc32_byte(byte_value, self.key0)
        self.key1 = (self.key1 + (self.key0 & 0xFF)) & 0xFFFFFFFF
        self.key1 = (self.key1 * 134775813 + 1) & 0xFFFFFFFF
        self.key2 = self._compute_crc32_byte((self.key1 >> 24) & 0xFF, self.key2)

    def decrypt(self, data: bytes) -> bytes:
        """Decrypt a bytes object using the initialized keys.

        Args:
            data (bytes): The encrypted data to decrypt.

        Returns:
            bytes: The decrypted data.
        """
        result = bytearray()
        for byte in data:
            temp = self.key2 | 2
            decrypted_byte = byte ^ ((temp * (temp ^ 1)) >> 8) & 0xFF
            self._update_keys(decrypted_byte)
            result.append(decrypted_byte)
        return bytes(result)


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


compressor_names = {
    0: "store",
    1: "shrink",
    2: "reduce",
    3: "reduce",
    4: "reduce",
    5: "reduce",
    6: "implode",
    7: "tokenize",
    8: "deflate",
    9: "deflate64",
    10: "implode",
    12: "bzip2",
    14: "lzma",
    18: "terse",
    19: "lz77",
    97: "wavpack",
    98: "ppmd",
}


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


class _SharedFile:
    """
    A class for managing shared, thread-safe access to a file with controlled read and write
    operations.

    This class provides methods for reading, seeking, and closing the file with lock-based
    thread safety.  It ensures that reading and seeking operations are blocked if a writing
    handle is open on the file.

    Attributes:
        seekable (Callable[[], bool]): A method to check if the file supports seeking.
    """

    def __init__(
        self,
        file: IO[bytes],
        pos: int,
        close: Callable[[IO[bytes]], None],
        lock: threading.Lock,
        writing: Callable[[], bool],
    ) -> None:
        """
        Initializes a _SharedFile instance.

        Args:
            file (IO[bytes]): The binary file object to manage.
            pos (int): The current position in the file.
            close (Callable[[IO[bytes]], None]): A callable to close the file.
            lock (threading.Lock): A lock to ensure thread-safe access to the file.
            writing (Callable[[], bool]): A function that returns True if a writing handle is open
            on the file.
        """
        self._file: Optional[IO[bytes]] = file
        self._pos: int = pos
        self._close: Callable[[IO[bytes]], None] = close
        self._lock: threading.Lock = lock
        self._writing: Callable[[], bool] = writing
        self.seekable: Callable[[], bool] = file.seekable

    def tell(self) -> int:
        """
        Returns the current file position.

        Returns:
            int: The current position in the file.
        """
        return self._pos

    def seek(self, offset: int, whence: int = 0) -> int:
        """
        Repositions the file cursor.

        Args:
            offset (int): The offset to move to, relative to `whence`.
            whence (int): The reference point for the offset
                          (default is 0, i.e., the start of the file).

        Returns:
            int: The new position in the file.

        Raises:
            ValueError: If attempting to reposition while a writing handle is open.
            RuntimeError: If the file is already closed.
        """
        if self._file is None:
            raise RuntimeError("File is closed.")

        with self._lock:
            if self._writing():
                raise ValueError(
                    "Can't reposition in the ZIP file while "
                    "there is an open writing handle on it. "
                    "Close the writing handle before trying to read."
                )
            self._file.seek(offset, whence)
            self._pos = self._file.tell()
            return self._pos

    def read(self, n: int = -1) -> bytes:
        """
        Reads data from the file.

        Args:
            n (int): The number of bytes to read
                     (default is -1, which reads until the end of the file).

        Returns:
            bytes: The data read from the file.

        Raises:
            ValueError: If attempting to read while a writing handle is open.
            RuntimeError: If the file is already closed.
        """
        if self._file is None:
            raise RuntimeError("File is closed.")

        with self._lock:
            if self._writing():
                raise ValueError(
                    "Can't read from the ZIP file while there "
                    "is an open writing handle on it. "
                    "Close the writing handle before trying to read."
                )
            self._file.seek(self._pos)
            data = self._file.read(n)
            self._pos = self._file.tell()
            return data

    def close(self) -> None:
        """
        Closes the file if it is open by calling the provided close function.
        """
        if self._file is not None:
            fileobj = self._file
            self._file = None
            self._close(fileobj)


# Provide the tell method for unseekable stream
class _Tellable:
    """
    A wrapper class that adds tell functionality to unseekable file-like objects.

    This class maintains an internal offset that tracks the write position, providing a
    `tell` method to get the current position. It can be used with file-like objects that
    do not natively support seeking or position tracking.

    Attributes:
        fp (BinaryIO): The underlying file-like object being wrapped.
        offset (int): The current write position in the file-like object.
    """

    def __init__(self, fp: BinaryIO) -> None:
        """
        Initializes a _Tellable instance.

        Args:
            fp (BinaryIO): The underlying file-like object to wrap.
        """
        self.fp: BinaryIO = fp
        self.offset: int = 0

    def write(self, data: bytes) -> int:
        """
        Writes data to the file-like object and updates the current position.

        Args:
            data (bytes): The data to write.

        Returns:
            int: The number of bytes written.
        """
        n = self.fp.write(data)
        self.offset += n
        return n

    def tell(self) -> int:
        """
        Returns the current position in the file-like object.

        Returns:
            int: The current write position, tracked by the offset.
        """
        return self.offset

    def flush(self) -> None:
        """Flushes the underlying file-like object."""
        self.fp.flush()

    def close(self) -> None:
        """Closes the underlying file-like object."""
        self.fp.close()


class ZipExtFile(io.BufferedIOBase):
    """
    File-like object for reading a file entry within a ZIP archive.
    Is returned by ZipFile.open().

    This class enables reading data from compressed ZIP archive members,
    managing decompression, CRC checking, optional decryption, and
    seeking within the compressed data if supported by the underlying file object.

    Attributes:
        MAX_N (int): Maximum size supported by decompressor.
        MIN_READ_SIZE (int): Block size for reading compressed data.
        MAX_SEEK_READ (int): Chunk size for reading during seek operations.
        mode (str): Mode in which the file is opened.
        name (str): The filename of the archive member.
        newlines (Optional[str]): Line separator used if text mode is specified.
    """

    # Max size supported by decompressor.
    MAX_N = 1 << 31 - 1

    # Read from compressed files in 4k blocks.
    MIN_READ_SIZE = 4096

    # Chunk size to read during seek
    MAX_SEEK_READ = 1 << 24

    def __init__(
        self,
        fileobj: io.BufferedIOBase,
        mode: str,
        zipinfo: ZipInfo,
        pwd: Optional[bytes] = None,
        close_fileobj: bool = False,
    ) -> None:
        """
        Initializes a ZipExtFile instance for reading a compressed archive member.

        Args:
            fileobj (io.BufferedIOBase): The file object for reading the ZIP file.
            mode (str): The mode in which the file is opened ('r' for reading).
            zipinfo: The ZipInfo object with details about the archive member.
            pwd (Optional[bytes]): The password for decrypting the archive member (if needed).
            close_fileobj (bool): If True, closes the file object when the instance is closed.
        """
        self._fileobj = fileobj
        self._pwd = pwd
        self._close_fileobj = close_fileobj

        self._compress_type = zipinfo.compress_type
        self._compress_left = zipinfo.compress_size
        self._left = zipinfo.file_size

        # Initialize decompressor based on compression type
        self._decompressor = _get_decompressor(self._compress_type)

        self._eof = False
        self._readbuffer = b""
        self._offset = 0

        self.newlines: Optional[str] = None

        self.mode: str = mode
        self.name: str = zipinfo.filename

        # Declare _expected_crc as Optional[int] to allow None
        self._expected_crc: Optional[int] = None
        self._running_crc: int = crc32(b"")

        # Check for CRC and set initial value
        if hasattr(zipinfo, "crc_value"):
            self._expected_crc = zipinfo.crc_value
        else:
            self._expected_crc = None

        # Attempt to determine if the file object supports seeking
        self._seekable = False
        try:
            if fileobj.seekable():
                self._orig_compress_start = fileobj.tell()
                self._orig_compress_size = zipinfo.compress_size
                self._orig_file_size = zipinfo.file_size
                self._orig_start_crc = self._running_crc
                self._orig_crc = self._expected_crc
                self._seekable = True
        except AttributeError:
            pass

        # Initialize decrypter if password-protected
        # Define _decrypter as Optional[ZipDecrypter] to accommodate both None
        # and ZipDecrypter instances
        self._decrypter: Optional[ZipDecrypter] = None

        if pwd:
            if zipinfo.flag_bits & _MASK_USE_DATA_DESCRIPTOR:
                # Use extended local headers for decryption check
                # Ensure that _raw_time is not None before using it
                if zipinfo._raw_time is not None:
                    check_byte = (zipinfo._raw_time >> 8) & 0xFF
                else:
                    raise ValueError(
                        "Missing _raw_time value in ZipInfo; cannot perform decryption check."
                    )
            else:
                # Use CRC for decryption check otherwise
                check_byte = (zipinfo.crc_value >> 24) & 0xFF
            h = self._init_decrypter()
            if h != check_byte:
                raise RuntimeError(f"Bad password for file {zipinfo.orig_filename!r}")

    def _init_decrypter(self) -> Optional[int]:
        """
        Initializes the decrypter for encrypted ZIP files.

        This method sets up the decryption mechanism if a password (`_pwd`) is provided.
        It reads the encryption header, which consists of the first 12 bytes in the
        cipher stream. The first 11 bytes are random, while the 12th byte contains
        a value used to check password correctness (either the MSB of the CRC or the
        MSB of the file time, depending on the ZIP header type).

        Returns:
            int: The 12th byte of the decrypted header, used to check password correctness.

        Raises:
            RuntimeError: If `_pwd` or `_fileobj` is not set, and decryption is attempted.
        """
        if not self._pwd:
            raise RuntimeError("Password is required for decryption.")
        if not self._fileobj:
            raise RuntimeError("File object is required for reading encrypted data.")

        # Initialize decrypter with the provided password
        self._decrypter = ZipDecrypter(self._pwd)

        # Read the first 12 bytes from the file object as the encryption header
        # The first 12 bytes in the cypher stream is an encryption header
        #  used to strengthen the algorithm. The first 11 bytes are
        #  completely random, while the 12th contains the MSB of the CRC,
        #  or the MSB of the file time depending on the header type
        #  and is used to check the correctness of the password.
        header = self._fileobj.read(12)
        self._compress_left -= 12

        # Decrypt the header and return the 12th byte, used for password verification
        decrypted_header = self._decrypter.decrypt(header)
        return decrypted_header[11]

    def __repr__(self) -> str:
        """
        Generates a string representation of the ZipExtFile instance.

        This representation includes the class module, name, file name,
        and compression type if the file is open. If the file is closed,
        the representation indicates that.

        Returns:
            str: A string representation of the ZipExtFile instance.
        """
        result: List[str] = [f"<{self.__class__.__module__}.{self.__class__.__qualname__}"]
        if not self.closed:
            result.append(f" name={self.name!r}")
            if self._compress_type != ZIP_STORED:
                result.append(
                    f" compress_type="
                    f"{compressor_names.get(self._compress_type, self._compress_type)}"
                )
        else:
            result.append(" [closed]")
        result.append(">")
        return "".join(result)

    def readline(self, limit: Optional[int] = -1) -> bytes:
        """
        Read and return a line from the stream.

        This method reads bytes from the stream until a newline byte is found
        or until `limit` bytes have been read, whichever comes first.

        Args:
            limit (Optional[int]): The maximum number of bytes to read. If negative,
                reads until a newline is encountered or the end of the buffer.

        Returns:
            bytes: The line read from the stream, including the newline character if found.
        """

        if limit is not None and limit < 0:
            # Shortcut common case - newline found in buffer.
            i = self._readbuffer.find(b"\n", self._offset) + 1
            if i > 0:
                line = self._readbuffer[self._offset : i]
                self._offset = i
                return line

        return super().readline(limit)

    def peek(self, n: int = 1) -> bytes:
        """
        Return up to `n` bytes from the buffer without advancing the position.

        This method attempts to return buffered bytes up to a maximum of 512 bytes,
        reducing allocation overhead in tight loops. If there aren’t enough bytes in
        the buffer, it reads more data into the buffer without moving the file position.

        Args:
            n (int): The number of bytes to attempt to peek from the buffer. Defaults to 1.

        Returns:
            bytes: The bytes read from the buffer without changing the current offset.
        """

        if n > len(self._readbuffer) - self._offset:
            chunk = self.read(n)
            if len(chunk) > self._offset:
                # Extend the buffer with new data and reset the offset
                self._readbuffer = chunk + self._readbuffer[self._offset :]
                self._offset = 0
            else:
                # Adjust the offset if fewer bytes were read than requested
                self._offset -= len(chunk)

        # Return up to 512 bytes to reduce allocation overhead for tight loops.
        return self._readbuffer[self._offset : self._offset + 512]

    def readable(self) -> bool:
        """
        Check if the file is open and readable.

        Raises:
            ValueError: If the file is closed.

        Returns:
            bool: `True` if the file is open and readable, otherwise raises an exception.
        """
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError("I/O operation on closed file.")
        return True

    def read(self, n: Optional[int] = -1) -> bytes:
        """Read and return up to `n` bytes from the stream.

        If `n` is omitted, `None`, or negative, reads until EOF is reached.
        If the file is closed, raises a `ValueError`.

        Args:
            n (Optional[int]): The number of bytes to read. If `None` or negative,
                reads until the end of the file.

        Returns:
            bytes: The data read from the stream.

        Raises:
            ValueError: If an attempt is made to read from a closed file.
        """
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError("Read from closed file.")

        if n is None or n < 0:
            # Read until EOF if n is None or negative
            buf = self._readbuffer[self._offset :]
            self._readbuffer = b""
            self._offset = 0
            while not self._eof:
                buf += self._read1(self.MAX_N)
            return buf

        end = n + self._offset
        if end < len(self._readbuffer):
            # Return the data directly from the buffer if it’s already available
            buf = self._readbuffer[self._offset : end]
            self._offset = end
            return buf

        # Otherwise, read the remaining data needed
        n = end - len(self._readbuffer)
        buf = self._readbuffer[self._offset :]
        self._readbuffer = b""
        self._offset = 0
        while n > 0 and not self._eof:
            data = self._read1(n)
            if n < len(data):
                # If more data was read than needed, store the excess
                self._readbuffer = data
                self._offset = n
                buf += data[:n]
                break
            buf += data
            n -= len(data)

        return buf

    def _update_crc(self, newdata):
        # Update the CRC using the given data.
        if self._expected_crc is None:
            # No need to compute the CRC if we don't have a reference value
            return
        self._running_crc = crc32(newdata, self._running_crc)
        # Check the CRC if we're at the end of the file
        if self._eof and self._running_crc != self._expected_crc:
            raise BadZipFile("Bad CRC-32 for file %r" % self.name)

    def read1(self, n):
        """Read up to n bytes with at most one read() system call."""

        if n is None or n < 0:
            buf = self._readbuffer[self._offset :]
            self._readbuffer = b""
            self._offset = 0
            while not self._eof:
                data = self._read1(self.MAX_N)
                if data:
                    buf += data
                    break
            return buf

        end = n + self._offset
        if end < len(self._readbuffer):
            buf = self._readbuffer[self._offset : end]
            self._offset = end
            return buf

        n = end - len(self._readbuffer)
        buf = self._readbuffer[self._offset :]
        self._readbuffer = b""
        self._offset = 0
        if n > 0:
            while not self._eof:
                data = self._read1(n)
                if n < len(data):
                    self._readbuffer = data
                    self._offset = n
                    buf += data[:n]
                    break
                if data:
                    buf += data
                    break
        return buf

    def _read1(self, n: int) -> bytes:
        """Read up to `n` compressed bytes with at most one `read()` system call,
        decrypt and decompress them as needed.

        This method handles unconsumed data for compressed streams and manages EOF status.
        It also updates the CRC (Cyclic Redundancy Check) for data integrity verification.

        Args:
            n (int): The maximum number of compressed bytes to read.

        Returns:
            bytes: The decompressed and decrypted data, up to `n` bytes or until EOF.

        Raises:
            ValueError: If an unsupported compression type is encountered.
        """
        if self._eof or n <= 0:
            return b""

        # Read from file based on compression type.
        if self._compress_type == ZIP_DEFLATED:
            # Handle unconsumed data.
            data = self._decompressor.unconsumed_tail
            if n > len(data):
                data += self._read2(n - len(data))
        else:
            data = self._read2(n)

        # Process data based on compression type.
        if self._compress_type == ZIP_STORED:
            self._eof = self._compress_left <= 0
        elif self._compress_type == ZIP_DEFLATED:
            n = max(n, self.MIN_READ_SIZE)
            data = self._decompressor.decompress(data, n)
            self._eof = self._decompressor.eof or (
                self._compress_left <= 0 and not self._decompressor.unconsumed_tail
            )
            if self._eof:
                data += self._decompressor.flush()
        else:
            data = self._decompressor.decompress(data)
            self._eof = self._decompressor.eof or self._compress_left <= 0

        # Adjust data length and update internal state.
        data = data[: self._left]
        self._left -= len(data)
        if self._left <= 0:
            self._eof = True

        # Update CRC for the data.
        self._update_crc(data)
        return data

    def _read2(self, n):
        if self._compress_left <= 0:
            return b""

        n = max(n, self.MIN_READ_SIZE)
        n = min(n, self._compress_left)

        data = self._fileobj.read(n)
        self._compress_left -= len(data)
        if not data:
            raise EOFError

        if self._decrypter is not None:
            data = self._decrypter(data)
        return data

    def close(self):
        try:
            if self._close_fileobj:
                self._fileobj.close()
        finally:
            super().close()

    def seekable(self):
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError("I/O operation on closed file.")
        return self._seekable

    def seek(self, offset, whence=os.SEEK_SET):
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError("seek on closed file.")
        if not self._seekable:
            raise io.UnsupportedOperation("underlying stream is not seekable")
        curr_pos = self.tell()
        if whence == os.SEEK_SET:
            new_pos = offset
        elif whence == os.SEEK_CUR:
            new_pos = curr_pos + offset
        elif whence == os.SEEK_END:
            new_pos = self._orig_file_size + offset
        else:
            raise ValueError(
                "whence must be os.SEEK_SET (0), " "os.SEEK_CUR (1), or os.SEEK_END (2)"
            )

        if new_pos > self._orig_file_size:
            new_pos = self._orig_file_size

        if new_pos < 0:
            new_pos = 0

        read_offset = new_pos - curr_pos
        buff_offset = read_offset + self._offset

        if buff_offset >= 0 and buff_offset < len(self._readbuffer):
            # Just move the _offset index if the new position is in the _readbuffer
            self._offset = buff_offset
            read_offset = 0
        # Fast seek uncompressed unencrypted file
        elif self._compress_type == ZIP_STORED and self._decrypter is None and read_offset > 0:
            # disable CRC checking after first seeking - it would be invalid
            self._expected_crc = None
            # seek actual file taking already buffered data into account
            read_offset -= len(self._readbuffer) - self._offset
            self._fileobj.seek(read_offset, os.SEEK_CUR)
            self._left -= read_offset
            read_offset = 0
            # flush read buffer
            self._readbuffer = b""
            self._offset = 0
        elif read_offset < 0:
            # Position is before the current position. Reset the ZipExtFile
            self._fileobj.seek(self._orig_compress_start)
            self._running_crc = self._orig_start_crc
            self._expected_crc = self._orig_crc
            self._compress_left = self._orig_compress_size
            self._left = self._orig_file_size
            self._readbuffer = b""
            self._offset = 0
            self._decompressor = _get_decompressor(self._compress_type)
            self._eof = False
            read_offset = new_pos
            if self._decrypter is not None:
                self._init_decrypter()

        while read_offset > 0:
            read_len = min(self.MAX_SEEK_READ, read_offset)
            self.read(read_len)
            read_offset -= read_len

        return self.tell()

    def tell(self):
        if self.closed:  # pylint: disable=using-constant-test
            raise ValueError("tell on closed file.")
        if not self._seekable:
            raise io.UnsupportedOperation("underlying stream is not seekable")
        filepos = self._orig_file_size - self._left - len(self._readbuffer) + self._offset
        return filepos


class ZipFile:
    """Class with methods to open, read, close, list zip files.

    z = ZipFile(file, mode="r", compression=ZIP_STORED, allowZip64=True,
                compresslevel=None)

    file: Either the path to the file, or a file-like object.
          If it is a path, the file will be opened and closed by ZipFile.
    mode: The mode can be read 'r'.
    compression: ZIP_STORED (no compression), ZIP_DEFLATED (requires zlib),
                 ZIP_BZIP2 (requires bz2) or ZIP_LZMA (requires lzma).
    allowZip64: if True ZipFile will create files with ZIP64 extensions when
                needed, otherwise it will raise an exception when this would
                be necessary.
    compresslevel: None (default for the given compression type) or an integer
                   specifying the level to pass to the compressor.
                   When using ZIP_STORED or ZIP_LZMA this keyword has no effect.
                   When using ZIP_DEFLATED integers 0 through 9 are accepted.
                   When using ZIP_BZIP2 integers 1 through 9 are accepted.

    """

    fp = None  # Set here since __del__ checks it
    _windows_illegal_name_trans_table = None

    def __init__(
        self,
        file,
        mode="r",
        compression=ZIP_STORED,
        allowZip64=True,
        compresslevel=None,
        *,
        strict_timestamps=True,
        metadata_encoding=None,
    ):
        """Open the ZIP file with mode read 'r'."""
        if mode not in ("r"):
            raise ValueError("ZipFile requires mode 'r'")

        _check_compression(compression)

        self._allowZip64 = allowZip64
        self._didModify = False
        self.debug = 0  # Level of printing: 0 through 3
        self.NameToInfo = {}  # Find file info given name
        self.filelist = []  # List of ZipInfo instances for archive
        self.compression = compression  # Method of compression
        self.compresslevel = compresslevel
        self.mode = mode
        self.pwd = None
        self._comment = b""
        self._strict_timestamps = strict_timestamps
        self.metadata_encoding = metadata_encoding

        # Check that we don't try to write with nonconforming codecs
        if self.metadata_encoding and mode != "r":
            raise ValueError("metadata_encoding is only supported for reading files")

        # Check if we were passed a file-like object
        if isinstance(file, os.PathLike):
            file = os.fspath(file)
        if isinstance(file, str):
            # No, it's a filename
            self._filePassed = 0
            self.filename = file
            modeDict = {
                "r": "rb",
                "r+b": "w+b",
            }
            filemode = modeDict[mode]
            while True:
                try:
                    self.fp = io.open(file, filemode)
                except OSError:
                    if filemode in modeDict:
                        filemode = modeDict[filemode]
                        continue
                    raise
                break
        else:
            self._filePassed = 1
            self.fp = file
            self.filename = getattr(file, "name", None)
        self._fileRefCnt = 1
        self._lock = threading.RLock()
        self._seekable = True
        self._writing = False

        try:
            if mode == "r":
                self._RealGetContents()
            else:
                raise ValueError("Mode must be 'r'")
        except:
            fp = self.fp
            self.fp = None
            self._fpclose(fp)
            raise

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def __repr__(self):
        result = ["<%s.%s" % (self.__class__.__module__, self.__class__.__qualname__)]
        if self.fp is not None:
            if self._filePassed:
                result.append(" file=%r" % self.fp)
            elif self.filename is not None:
                result.append(" filename=%r" % self.filename)
            result.append(" mode=%r" % self.mode)
        else:
            result.append(" [closed]")
        result.append(">")
        return "".join(result)

    def _RealGetContents(self):
        """Read in the table of contents for the ZIP file."""
        fp = self.fp
        try:
            endrec = _end_rec_data(fp)
        except OSError:
            raise BadZipFile("File is not a zip file")
        if not endrec:
            raise BadZipFile("File is not a zip file")
        if self.debug > 1:
            print(endrec)
        size_cd = endrec[_ECD_SIZE]  # bytes in central directory
        offset_cd = endrec[_ECD_OFFSET]  # offset of central directory
        self._comment = endrec[_ECD_COMMENT]  # archive comment

        # "concat" is zero, unless zip was concatenated to another file
        concat = endrec[_ECD_LOCATION] - size_cd - offset_cd
        if endrec[_ECD_SIGNATURE] == stringEndArchive64:
            # If Zip64 extension structures are present, account for them
            concat -= sizeEndCentDir64 + sizeEndCentDir64Locator

        if self.debug > 2:
            inferred = concat + offset_cd
            print("given, inferred, offset", offset_cd, inferred, concat)
        # self.start_dir:  Position of start of central directory
        self.start_dir = offset_cd + concat
        if self.start_dir < 0:
            raise BadZipFile("Bad offset for central directory")
        fp.seek(self.start_dir, 0)
        data = fp.read(size_cd)
        fp = io.BytesIO(data)
        total = 0
        while total < size_cd:
            centdir = fp.read(sizeCentralDir)
            if len(centdir) != sizeCentralDir:
                raise BadZipFile("Truncated central directory")
            centdir = struct.unpack(structCentralDir, centdir)
            if centdir[_CD_SIGNATURE] != stringCentralDir:
                raise BadZipFile("Bad magic number for central directory")
            if self.debug > 2:
                print(centdir)
            filename = fp.read(centdir[_CD_FILENAME_LENGTH])
            orig_filename_crc = crc32(filename)
            flags = centdir[_CD_FLAG_BITS]
            if flags & _MASK_UTF_FILENAME:
                # UTF-8 file names extension
                filename = filename.decode("utf-8")
            else:
                # Historical ZIP filename encoding
                filename = filename.decode(self.metadata_encoding or "cp437")
            # Create ZipInfo instance to store file information
            x = ZipInfo(filename)
            x.extra = fp.read(centdir[_CD_EXTRA_FIELD_LENGTH])
            x.comment = fp.read(centdir[_CD_COMMENT_LENGTH])
            x.header_offset = centdir[_CD_LOCAL_HEADER_OFFSET]
            (
                x.create_version,
                x.create_system,
                x.extract_version,
                x.reserved,
                x.flag_bits,
                x.compress_type,
                t,
                d,
                x.CRC,
                x.compress_size,
                x.file_size,
            ) = centdir[1:12]
            if x.extract_version > MAX_EXTRACT_VERSION:
                raise NotImplementedError("zip file version %.1f" % (x.extract_version / 10))
            x.volume, x.internal_attr, x.external_attr = centdir[15:18]
            # Convert date/time code to (year, month, day, hour, min, sec)
            x._raw_time = t
            x.date_time = (
                (d >> 9) + 1980,
                (d >> 5) & 0xF,
                d & 0x1F,
                t >> 11,
                (t >> 5) & 0x3F,
                (t & 0x1F) * 2,
            )
            x._decode_extra(orig_filename_crc)
            x.header_offset = x.header_offset + concat
            self.filelist.append(x)
            self.NameToInfo[x.filename] = x

            # update total bytes read from central directory
            total = (
                total
                + sizeCentralDir
                + centdir[_CD_FILENAME_LENGTH]
                + centdir[_CD_EXTRA_FIELD_LENGTH]
                + centdir[_CD_COMMENT_LENGTH]
            )

            if self.debug > 2:
                print("total", total)

        end_offset = self.start_dir
        for zinfo in sorted(self.filelist, key=lambda zinfo: zinfo.header_offset, reverse=True):
            zinfo._end_offset = end_offset
            end_offset = zinfo.header_offset

    def namelist(self):
        """Return a list of file names in the archive."""
        return [data.filename for data in self.filelist]

    def infolist(self):
        """Return a list of class ZipInfo instances for files in the
        archive."""
        return self.filelist

    def printdir(self, file=None):
        """Print a table of contents for the zip file."""
        print("%-46s %19s %12s" % ("File Name", "Modified    ", "Size"), file=file)
        for zinfo in self.filelist:
            date = "%d-%02d-%02d %02d:%02d:%02d" % zinfo.date_time[:6]
            print("%-46s %s %12d" % (zinfo.filename, date, zinfo.file_size), file=file)

    def testzip(self):
        """Read all the files and check the CRC.

        Return None if all files could be read successfully, or the name
        of the offending file otherwise."""
        chunk_size = 2**20
        for zinfo in self.filelist:
            try:
                # Read by chunks, to avoid an OverflowError or a
                # MemoryError with very large embedded files.
                with self.open(zinfo.filename, "r") as f:
                    while f.read(chunk_size):  # Check CRC-32
                        pass
            except BadZipFile:
                return zinfo.filename

    def getinfo(self, name):
        """Return the instance of ZipInfo given 'name'."""
        info = self.NameToInfo.get(name)
        if info is None:
            raise KeyError("There is no item named %r in the archive" % name)

        return info

    def setpassword(self, pwd):
        """Set default password for encrypted files."""
        if pwd and not isinstance(pwd, bytes):
            raise TypeError("pwd: expected bytes, got %s" % type(pwd).__name__)
        if pwd:
            self.pwd = pwd
        else:
            self.pwd = None

    @property
    def comment(self):
        """The comment text associated with the ZIP file."""
        return self._comment

    @comment.setter
    def comment(self, comment):
        if not isinstance(comment, bytes):
            raise TypeError("comment: expected bytes, got %s" % type(comment).__name__)
        # check for valid comment length
        if len(comment) > ZIP_MAX_COMMENT:
            import warnings

            warnings.warn(
                "Archive comment is too long; truncating to %d bytes" % ZIP_MAX_COMMENT,
                stacklevel=2,
            )
            comment = comment[:ZIP_MAX_COMMENT]
        self._comment = comment
        self._didModify = True

    def read(self, name, pwd=None):
        """Return file bytes for name. 'pwd' is the password to decrypt
        encrypted files."""
        with self.open(name, "r", pwd) as fp:
            return fp.read()

    def open(self, name, mode="r", pwd=None, *, force_zip64=False):
        """Return file-like object for 'name'.

        name is a string for the file name within the ZIP file, or a ZipInfo
        object.

        mode should be 'r' to read a file already in the ZIP file.

        pwd is the password to decrypt files (only used for reading).
        """
        if mode not in {"r"}:
            raise ValueError('open() requires mode "r"')
        if not self.fp:
            raise ValueError("Attempt to use ZIP archive that was already closed")

        # Make sure we have an info object
        if isinstance(name, ZipInfo):
            # 'name' is already an info object
            zinfo = name
        else:
            # Get info object for name
            zinfo = self.getinfo(name)

        # Open for reading:
        self._fileRefCnt += 1
        zef_file = _SharedFile(
            self.fp, zinfo.header_offset, self._fpclose, self._lock, lambda: self._writing
        )
        try:
            # Skip the file header:
            fheader = zef_file.read(sizeFileHeader)
            if len(fheader) != sizeFileHeader:
                raise BadZipFile("Truncated file header")
            fheader = struct.unpack(structFileHeader, fheader)
            if fheader[_FH_SIGNATURE] != stringFileHeader:
                raise BadZipFile("Bad magic number for file header")

            fname = zef_file.read(fheader[_FH_FILENAME_LENGTH])
            if fheader[_FH_EXTRA_FIELD_LENGTH]:
                zef_file.seek(fheader[_FH_EXTRA_FIELD_LENGTH], whence=1)

            if zinfo.flag_bits & _MASK_COMPRESSED_PATCH:
                # Zip 2.7: compressed patched data
                raise NotImplementedError("compressed patched data (flag bit 5)")

            if zinfo.flag_bits & _MASK_STRONG_ENCRYPTION:
                # strong encryption
                raise NotImplementedError("strong encryption (flag bit 6)")

            if fheader[_FH_GENERAL_PURPOSE_FLAG_BITS] & _MASK_UTF_FILENAME:
                # UTF-8 filename
                fname_str = fname.decode("utf-8")
            else:
                fname_str = fname.decode(self.metadata_encoding or "cp437")

            if fname_str != zinfo.orig_filename:
                raise BadZipFile(
                    "File name in directory %r and header %r differ." % (zinfo.orig_filename, fname)
                )

            if (
                zinfo._end_offset is not None
                and zef_file.tell() + zinfo.compress_size > zinfo._end_offset
            ):
                raise BadZipFile(f"Overlapped entries: {zinfo.orig_filename!r} (possible zip bomb)")

            # check for encrypted flag & handle password
            is_encrypted = zinfo.flag_bits & _MASK_ENCRYPTED
            if is_encrypted:
                if not pwd:
                    pwd = self.pwd
                if pwd and not isinstance(pwd, bytes):
                    raise TypeError("pwd: expected bytes, got %s" % type(pwd).__name__)
                if not pwd:
                    raise RuntimeError(
                        "File %r is encrypted, password " "required for extraction" % name
                    )
            else:
                pwd = None

            return ZipExtFile(zef_file, mode + "b", zinfo, pwd, True)
        except:
            zef_file.close()
            raise

    def extract(self, member, path=None, pwd=None):
        """Extract a member from the archive to the current working directory,
        using its full name. Its file information is extracted as accurately
        as possible. 'member' may be a filename or a ZipInfo object. You can
        specify a different directory using 'path'. You can specify the
        password to decrypt the file using 'pwd'.
        """
        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        return self._extract_member(member, path, pwd)

    def extractall(self, path=None, members=None, pwd=None):
        """Extract all members from the archive to the current working
        directory. 'path' specifies a different directory to extract to.
        'members' is optional and must be a subset of the list returned
        by namelist(). You can specify the password to decrypt all files
        using 'pwd'.
        """
        if members is None:
            members = self.namelist()

        if path is None:
            path = os.getcwd()
        else:
            path = os.fspath(path)

        for zipinfo in members:
            self._extract_member(zipinfo, path, pwd)

    @classmethod
    def _sanitize_windows_name(cls, arcname, pathsep):
        """Replace bad characters and remove trailing dots from parts."""
        table = cls._windows_illegal_name_trans_table
        if not table:
            illegal = ':<>|"?*'
            table = str.maketrans(illegal, "_" * len(illegal))
            cls._windows_illegal_name_trans_table = table
        arcname = arcname.translate(table)
        # remove trailing dots and spaces
        arcname = (x.rstrip(" .") for x in arcname.split(pathsep))
        # rejoin, removing empty parts.
        arcname = pathsep.join(x for x in arcname if x)
        return arcname

    def _extract_member(self, member, targetpath, pwd):
        """Extract the ZipInfo object 'member' to a physical
        file on the path targetpath.
        """
        if not isinstance(member, ZipInfo):
            member = self.getinfo(member)

        # build the destination pathname, replacing
        # forward slashes to platform specific separators.
        arcname = member.filename.replace("/", os.path.sep)

        if os.path.altsep:
            arcname = arcname.replace(os.path.altsep, os.path.sep)
        # interpret absolute pathname as relative, remove drive letter or
        # UNC path, redundant separators, "." and ".." components.
        arcname = os.path.splitdrive(arcname)[1]
        invalid_path_parts = ("", os.path.curdir, os.path.pardir)
        arcname = os.path.sep.join(
            x for x in arcname.split(os.path.sep) if x not in invalid_path_parts
        )
        if os.path.sep == "\\":
            # filter illegal characters on Windows
            arcname = self._sanitize_windows_name(arcname, os.path.sep)

        if not arcname and not member.is_dir():
            raise ValueError("Empty filename.")

        targetpath = os.path.join(targetpath, arcname)
        targetpath = os.path.normpath(targetpath)

        # Create all upper directories if necessary.
        upperdirs = os.path.dirname(targetpath)
        if upperdirs and not os.path.exists(upperdirs):
            os.makedirs(upperdirs, exist_ok=True)

        if member.is_dir():
            if not os.path.isdir(targetpath):
                try:
                    os.mkdir(targetpath)
                except FileExistsError:
                    if not os.path.isdir(targetpath):
                        raise
            return targetpath

        with self.open(member, pwd=pwd) as source, open(targetpath, "wb") as target:
            shutil.copyfileobj(source, target)

        return targetpath

    def __del__(self):
        """Call the "close()" method in case the user forgot."""
        self.close()

    def close(self):
        """Close the file"""
        if self.fp is None:
            return

        fp = self.fp
        self.fp = None
        self._fpclose(fp)

    def _fpclose(self, fp):
        assert self._fileRefCnt > 0
        self._fileRefCnt -= 1
        if not self._fileRefCnt and not self._filePassed:
            fp.close()
