# constants.py

# Compression Types
ZIP_STORED = 0  # No compression
ZIP_DEFLATED = 8  # Standard deflate compression
ZIP_BZIP2 = 12  # BZIP2 compression
ZIP_LZMA = 14  # LZMA compression

# File Format Identifiers
ZIP_FILE_MAGIC = b"PK\x03\x04"  # Standard ZIP file magic number for local file header
ZIP_CENTRAL_DIR_MAGIC = b"PK\x01\x02"  # Magic number for central directory
ZIP_END_CENTRAL_DIR_MAGIC = b"PK\x05\x06"  # End of central directory

# Buffer Sizes
READ_BUFFER_SIZE = 4096  # Buffer size for reading compressed data
MIN_READ_SIZE = 512  # Minimum read size to reduce allocation overhead
MAX_READ_SIZE = 1 << 24  # Max chunk size for seek reads (16 MB)
MAX_N = (1 << 31) - 1  # Maximum size supported by decompressor

# Encryption/Decryption
ENCRYPTION_HEADER_SIZE = 12  # Size of the encryption header in bytes
CRC_POLYNOMIAL = 0xEDB88320  # Polynomial used for CRC-32

# Error Messages
ERROR_MSG_FILE_CLOSED = "I/O operation on closed file."
ERROR_MSG_BAD_PASSWORD = "Bad password for file {filename}"
ERROR_MSG_UNSUPPORTED_COMPRESSION = "Unsupported compression type: {compression_type}"

# ZIP Version Constants
DEFAULT_CREATE_VERSION = 20  # Version used for creating standard ZIP files
DEFAULT_EXTRACT_VERSION = 20  # Minimum version required for extracting standard ZIP files

# Data Descriptor Flags
FLAG_USE_DATA_DESCRIPTOR = 0x08  # Indicates the presence of a data descriptor

# ZIP File Limits
MAX_FILENAME_LENGTH = 255  # Maximum length of a filename in ZIP archives

# Compression Levels (for flexible configuration)
COMPRESSION_LEVELS = {
    ZIP_STORED: None,  # No compression level needed for stored files
    ZIP_DEFLATED: 6,  # Default compression level for deflate
    ZIP_BZIP2: 9,  # Highest compression for BZIP2
    ZIP_LZMA: 9,  # Highest compression for LZMA
}
