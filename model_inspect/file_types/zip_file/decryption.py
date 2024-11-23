from typing import ClassVar, List


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
