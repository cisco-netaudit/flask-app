"""
PasswordCipher Module

This module provides secure encryption and decryption of strings using a Fernet symmetric key 
stored in the system keyring. It can be utilized in any Python project requiring secure storage 
of credentials.
"""

import getpass
import keyring
from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = "PasswordCipherService"
USERNAME = getpass.getuser()


class PasswordCipher:
    """
    Manages encryption and decryption of sensitive data using a symmetric Fernet key.
    The key is securely stored and retrieved from the operating system's keyring.

    - Generates a new encryption key if it doesn't exist.
    - Stores the key securely using the `keyring` module.
    - Encrypts and decrypts strings via Fernet (symmetric authenticated encryption).
    - Allows the reset or regeneration of the encryption key.

    WARNING:
        Resetting or regenerating the key will render any previously encrypted data unreadable.
    """

    def __init__(self, service_name: str = SERVICE_NAME, username: str = USERNAME):
        self.service_name = service_name
        self.username = username
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key.encode())

    def _get_or_create_key(self) -> str:
        """Retrieve or generate the encryption key, storing it securely if new."""
        key = keyring.get_password(self.service_name, self.username)
        if key:
            return key

        key = Fernet.generate_key().decode()
        keyring.set_password(self.service_name, self.username, key)
        return key

    def encrypt(self, plain_text: str) -> str:
        """
        Encrypt plain text.
        
        Args:
            plain_text (str): The text to encrypt.
        
        Returns:
            str: The encrypted text, or an empty string if the input is empty.
        """
        if not plain_text:
            return ""
        return self.fernet.encrypt(plain_text.encode()).decode()

    def decrypt(self, cipher_text: str) -> str:
        """
        Decrypt cipher text.
        
        Args:
            cipher_text (str): The text to decrypt.
        
        Returns:
            str: The decrypted text, or an empty string if the input is empty.
        
        Raises:
            ValueError: If decryption fails due to invalid key or corrupted data.
        """
        if not cipher_text:
            return ""
        try:
            return self.fernet.decrypt(cipher_text.encode()).decode()
        except InvalidToken:
            raise ValueError("Decryption failed: invalid key or corrupted data.")

    def reset_key(self):
        """
        Delete the stored key from the keyring.
        
        WARNING: This makes all previously encrypted data unrecoverable.
        """
        try:
            keyring.delete_password(self.service_name, self.username)
        except keyring.errors.PasswordDeleteError:
            pass

    def regenerate_key(self):
        """
        Deletes the current key and generates a new one.
        
        WARNING: Makes existing encrypted data unrecoverable.
        """
        self.reset_key()
        self.key = self._get_or_create_key()
        self.fernet = Fernet(self.key.encode())