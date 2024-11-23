"""
constants.py

This module defines a set of constants used throughout the ZIP file handling package.
The constants are organized by category, covering various aspects of ZIP file processing,
including compression types, file format identifiers, buffer sizes, encryption settings,
error messages, ZIP version requirements, and structural fields.

These constants serve as fixed reference points, helping ensure consistency and
readability across modules that rely on them for handling ZIP file operations.

Sections:
    - Compression Types: Identifiers for different ZIP compression methods.
    - File Format Identifiers: Signatures for ZIP file headers and directories.
    - Buffer Sizes: Recommended buffer sizes for reading and processing data.
    - Encryption/Decryption: Constants for ZIP file encryption and CRC-32.
    - Error Messages: Standardized error messages for common operations.
    - ZIP Version Constants: Minimum and default ZIP version requirements.
    - Data Descriptor Flags: Flags for ZIP data descriptors.
    - ZIP File Limits: Constraints on ZIP file entry limits and filename length.
    - Compression Levels: Suggested compression levels for supported methods.
    - ZIP64-Specific Constants: Definitions for ZIP64 directory fields.
    - Central Directory Structure Fields: Indexes for central directory records.
    - Central Directory 64 (CD64) Structure Fields: Fields for ZIP64 directory records.
    - General Purpose Bit Flags: Flags for ZIP compression and encryption settings.
    - Field Header Constants: Field header indexes for ZIP file entries.
    - End of Central Directory Constants: Structure for end-of-directory records.
    - Data Descriptor Signature: Signature for ZIP file data descriptors.

Usage:
    Import this module to access constants in other ZIP file processing modules:

    from model_inspect.analyzers.zipfile.constants import ZIP_DEFLATED, MAX_READ_SIZE
"""
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

# Compression Types
ZIP_STORED = 0  # No compression
ZIP_DEFLATED = 8  # Standard deflate compression
ZIP_BZIP2 = 12  # BZIP2 compression
ZIP_LZMA = 14  # LZMA compression
# Other ZIP compression methods not supported

# File Format Identifiers
# Signature identifiers in ZIP files for different sections.
ZIP_FILE_MAGIC = b"PK\x03\x04"  # Local file header signature
ZIP_CENTRAL_DIR_MAGIC = b"PK\x01\x02"  # Central directory header signature
ZIP_END_CENTRAL_DIR_MAGIC = b"PK\x05\x06"  # End of central directory signature

# Buffer Sizes
# Buffer sizes for reading and processing ZIP files.
READ_BUFFER_SIZE = 4096  # Buffer size for reading compressed data
MIN_READ_SIZE = 512  # Minimum read size to reduce allocation overhead
MAX_READ_SIZE = 1 << 24  # Max chunk size for seek reads (16 MB)
MAX_N = (1 << 31) - 1  # Maximum size supported by decompressor
ZIP64_LIMIT = (1 << 31) - 1  # ZIP64 format limit for large files (2GB+)
ZIP_FILECOUNT_LIMIT = (1 << 16) - 1  # Max number of files in standard ZIP
ZIP_MAX_COMMENT = (1 << 16) - 1  # Max comment length in ZIP files

# Encryption/Decryption
ENCRYPTION_HEADER_SIZE = 12  # Size of the encryption header in bytes
CRC_POLYNOMIAL = 0xEDB88320  # Polynomial used for CRC-32 checksums

# Error Messages
# Common error messages for ZIP file operations.
ERROR_MSG_FILE_CLOSED = "I/O operation on closed file."
ERROR_MSG_BAD_PASSWORD = "Bad password for file {filename}"
ERROR_MSG_UNSUPPORTED_COMPRESSION = "Unsupported compression type: {compression_type}"

# ZIP Version Constants
# ZIP format version requirements for different features.
DEFAULT_CREATE_VERSION = (
    20  # Default ZIP specification version (2.0) used when creating standard ZIP files.
)
DEFAULT_EXTRACT_VERSION = (
    20  # Minimum ZIP version (2.0) required for extracting most standard ZIP files.
)
DEFAULT_VERSION = 20  # Generic default version for general ZIP operations if not specified.
ZIP64_VERSION = 45  # Version (4.5) required to read/write ZIP64 extensions for larger files.
BZIP2_VERSION = 46  # Version (4.6) required to use BZIP2 compression in ZIP files.
LZMA_VERSION = 63  # Version (6.3) required to use LZMA compression in ZIP files.
MAX_EXTRACT_VERSION = (
    63  # Maximum ZIP version (6.3) supported for reading features, even if not all are implemented.
)

# Data Descriptor Flags
# Flags for ZIP data descriptors.
FLAG_USE_DATA_DESCRIPTOR = 0x08  # Indicates the presence of a data descriptor

# ZIP File Limits
# Constraints on ZIP file entries.
MAX_FILENAME_LENGTH = 255  # Maximum length of a filename in ZIP archives

# Compression Levels (for flexible configuration)
# Suggested default compression levels for different compression methods.
COMPRESSION_LEVELS = {
    ZIP_STORED: None,  # No compression level needed for stored files
    ZIP_DEFLATED: 6,  # Default compression level for deflate
    ZIP_BZIP2: 9,  # Highest compression for BZIP2
    ZIP_LZMA: 9,  # Highest compression for LZMA
}

# ZIP64-Specific Constants
# Constants for ZIP64-specific end-of-central-directory fields
_ZIP64_SIGNATURE = "signature"
_ZIP64_DISK_NUMBER = "disk_number"
_ZIP64_DISK_START = "disk_start"
_ZIP64_ENTRIES_THIS_DISK = "entries_this_disk"
_ZIP64_ENTRIES_TOTAL = "entries_total"
_ZIP64_SIZE = "size"
_ZIP64_OFFSET = "offset"

# Central Directory Structure Fields
# Indexes for central directory fields in the ZIP file.
_CD_SIGNATURE = 0
_CD_CREATE_VERSION = 1
_CD_CREATE_SYSTEM = 2
_CD_EXTRACT_VERSION = 3
_CD_EXTRACT_SYSTEM = 4
_CD_FLAG_BITS = 5
_CD_COMPRESS_TYPE = 6
_CD_TIME = 7
_CD_DATE = 8
_CD_CRC = 9
_CD_COMPRESSED_SIZE = 10
_CD_UNCOMPRESSED_SIZE = 11
_CD_FILENAME_LENGTH = 12
_CD_EXTRA_FIELD_LENGTH = 13
_CD_COMMENT_LENGTH = 14
_CD_DISK_NUMBER_START = 15
_CD_INTERNAL_FILE_ATTRIBUTES = 16
_CD_EXTERNAL_FILE_ATTRIBUTES = 17
_CD_LOCAL_HEADER_OFFSET = 18

# Central Directory 64 (CD64) Structure Fields
_CD64_SIGNATURE = 0
_CD64_DIRECTORY_RECSIZE = 1
_CD64_CREATE_VERSION = 2
_CD64_EXTRACT_VERSION = 3
_CD64_DISK_NUMBER = 4
_CD64_DISK_NUMBER_START = 5
_CD64_NUMBER_ENTRIES_THIS_DISK = 6
_CD64_NUMBER_ENTRIES_TOTAL = 7
_CD64_DIRECTORY_SIZE = 8
_CD64_OFFSET_START_CENTDIR = 9

# General purpose bit flags
# Bit flags as per the ZIP specification for general purpose usage.
# Zip Appnote: 4.4.4 general purpose bit flag: (2 bytes)
_MASK_ENCRYPTED = 1 << 0
# Bits 1 and 2 have different meanings depending on the compression used.
_MASK_COMPRESS_OPTION_1 = 1 << 1
# _MASK_COMPRESS_OPTION_2 = 1 << 2
# _MASK_USE_DATA_DESCRIPTOR: If set, crc-32, compressed size and uncompressed
# size are zero in the local header and the real values are written in the data
# descriptor immediately following the compressed data.
_MASK_USE_DATA_DESCRIPTOR = 1 << 3
# Bit 4: Reserved for use with compression method 8, for enhanced deflating.
# _MASK_RESERVED_BIT_4 = 1 << 4
_MASK_COMPRESSED_PATCH = 1 << 5
_MASK_STRONG_ENCRYPTION = 1 << 6
# _MASK_UNUSED_BIT_7 = 1 << 7
# _MASK_UNUSED_BIT_8 = 1 << 8
# _MASK_UNUSED_BIT_9 = 1 << 9
# _MASK_UNUSED_BIT_10 = 1 << 10
_MASK_UTF_FILENAME = 1 << 11
# Bit 12: Reserved by PKWARE for enhanced compression.
# _MASK_RESERVED_BIT_12 = 1 << 12
# _MASK_ENCRYPTED_CENTRAL_DIR = 1 << 13
# Bit 14, 15: Reserved by PKWARE
# _MASK_RESERVED_BIT_14 = 1 << 14
# _MASK_RESERVED_BIT_15 = 1 << 15

# Field Header Constants
# Field header indexes in ZIP file entries.
_FH_SIGNATURE = 0
_FH_EXTRACT_VERSION = 1
_FH_EXTRACT_SYSTEM = 2
_FH_GENERAL_PURPOSE_FLAG_BITS = 3
_FH_COMPRESSION_METHOD = 4
_FH_LAST_MOD_TIME = 5
_FH_LAST_MOD_DATE = 6
_FH_CRC = 7
_FH_COMPRESSED_SIZE = 8
_FH_UNCOMPRESSED_SIZE = 9
_FH_FILENAME_LENGTH = 10
_FH_EXTRA_FIELD_LENGTH = 11

# End of Central Directory Constants
# Constants for the End of Central Directory (EOCD) record structure.
_ECD_SIGNATURE = 0
_ECD_DISK_NUMBER = 1
_ECD_DISK_START = 2
_ECD_ENTRIES_THIS_DISK = 3
_ECD_ENTRIES_TOTAL = 4
_ECD_SIZE = 5
_ECD_OFFSET = 6
_ECD_COMMENT_SIZE = 7
# These last two indices are not part of the structure as defined in the
# spec, but they are used internally by this module as a convenience
_ECD_COMMENT = 8
_ECD_LOCATION = 9

# Data Descriptor Signature
_DD_SIGNATURE = 0x08074B50
