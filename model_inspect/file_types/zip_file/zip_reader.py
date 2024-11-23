from model_inspect.file_types.zip_file.constants import ZIP_DEFLATED, ZIP_STORED, compressor_names
from model_inspect.file_types.zip_file.exceptions import BadZipFile


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
