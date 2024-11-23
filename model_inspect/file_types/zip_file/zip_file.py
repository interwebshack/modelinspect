"""
Most of this code was duplicated from the cpython zipfile library.
https://github.com/python/cpython/blob/ef172521a9e9dfadebe57d590bfb53a0e9ac3a0b/Lib/zipfile/__init__.py

Only the read functions have been added to this file - the modelinspect
project only needs to read and identify zip files.  Type hints and other code
quality improvements have been added to the file.
"""

import io
import os
import shutil
import struct
import threading
from typing import IO, BinaryIO, Callable, Dict, List, Optional, Union

from model_inspect.file_types.zip_file.constants import (
    _ZIP64_DISK_NUMBER,
    _ZIP64_DISK_START,
    _ZIP64_ENTRIES_THIS_DISK,
    _ZIP64_ENTRIES_TOTAL,
    _ZIP64_OFFSET,
    _ZIP64_SIGNATURE,
    _ZIP64_SIZE,
)
from model_inspect.file_types.zip_file.exceptions import BadZipFile

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
