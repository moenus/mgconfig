# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import json
import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives import hashes, hmac
from cryptography.hazmat.backends import default_backend
from pathlib import Path
from mgconfig.helpers import logger
from mgconfig.key_provider import KeyProvider
from cryptography.exceptions import InvalidTag


# === Crypto Constants ===
AES_KEY_SIZE = 32          # 32 bytes = 256 bits for AES-256
AES_GCM_NONCE_SIZE = 12    # 12 bytes = recommended nonce size for AES-GCM
HKDF_KEY_SIZE = 64         # total derived bytes (we're using 32 for AES key)

# hash of current master key encrypted with current master key
CURRENT_MK_HASH = '_cmk_hash'
# current master key encrypted with the new master key
AEMK_OLD_MK_KEY = '_aemk_old_k'
# hash of current master key encrypted with the new master key
AEMK_OLD_MK_HASH = '_aemk_old_h'
AEMK_NEW_MK_HASH = '_aemk_new_h'

ITEMNAME_NONCE = 'nonce'
ITEMNAME_CIPHERTEXT = 'ciphertext'
ITEMNAME_TAG = 'tag'


INDENT = ' ' * 5


def bytes_to_b64str(value_bytes: bytes) -> str:
    """Convert bytes to a Base64-encoded UTF-8 string.

    Args:
        value_bytes (bytes): The input bytes.

    Returns:
        str: The Base64-encoded string.
    """
    return base64.b64encode(value_bytes).decode('utf-8')


def b64str_to_bytes(value_str: str) -> bytes:
    """Convert a Base64-encoded string to bytes.

    Args:
        value_str (str): The Base64-encoded string.

    Returns:
        bytes: The decoded bytes.
    """
    return base64.b64decode(value_str)


# def _get_msg(operation, name, value, key):
#     return f'{operation.ljust(10)} {name.ljust(15)} {str(value)[:20].ljust(25)} {str(key)[:20].ljust(25)}'


def generate_key_str():
    """Generate a new AES-256 key encoded in Base64.

    Returns:
        str: A randomly generated 32-byte AES key encoded as a Base64 string.
    """
    return bytes_to_b64str(os.urandom(AES_KEY_SIZE))  # AES-256 requires a 32-byte key


class SecureStore:
    def __init__(self, securestore_file: str, key_provider: KeyProvider):
        """Initialize the secure store.

        Args:
            securestore_file (str): Path to the JSON secure store file.
            key_provider (KeyProvider): Object providing the 'master_key' and 'salt'.
        """
        self.securestore_file = securestore_file
        self.securestore = {}
        self._master_key = b64str_to_bytes(key_provider.get('master_key'))
        self._salt = b64str_to_bytes(key_provider.get('salt'))
        self._read_securestore_file()
        if self.securestore == {}:
            self.store_secret(CURRENT_MK_HASH, self.master_key_hash)

    def _derive_keys(self) -> bytes:
        """Derive the AES encryption key from the master key and salt key.

        Uses HMAC-SHA256 with the salt key, followed by HKDF-SHA256.

        Returns:
            bytes: The derived AES key of length AES_KEY_SIZE.
        """
        h = hmac.HMAC(self._salt, hashes.SHA256(),
                      backend=default_backend())
        h.update(self._master_key)
        salt = h.finalize()
        hkdf = HKDF(
            algorithm=SHA256(),
            length=HKDF_KEY_SIZE,
            salt=salt,
            info=None,
            backend=default_backend(),
        )
        derived_keys = hkdf.derive(self._master_key)
        return derived_keys[:AES_KEY_SIZE]

    def validate_master_key(self) -> bool:
        """Validate the current master key against the stored hash.

        If the master key matches the new master key hash, triggers automatic key exchange.

        Returns:
            bool: True if the master key is valid or successfully exchanged, False otherwise.
        """
        masterkey_hash = self.master_key_hash
        logger.debug(
            f'validate_master_key: {self.master_key_str} {masterkey_hash}')
        retrieved_masterkey_hash = self.retrieve_secret(CURRENT_MK_HASH)
        if retrieved_masterkey_hash == masterkey_hash:
            return True
        new_master_key_hash = self.retrieve_secret(AEMK_NEW_MK_HASH)
        if new_master_key_hash == masterkey_hash:
            return self._auto_key_exchange()
        return False

    def _auto_key_exchange(self) -> bool:
        """Perform automatic master key exchange.

        Decrypts all secrets with the old key, re-encrypts them with the new key, and updates the store.

        Returns:
            bool: True if successful, False otherwise.
        """
        logger.debug('auto_key_exchange ...')
        old_master_key_str = self.retrieve_secret(AEMK_OLD_MK_KEY)
        if not old_master_key_str:
            logger.debug(f'{INDENT}cannot retrieve {AEMK_OLD_MK_KEY}')
            return False
        old_master_key_hash = self.retrieve_secret(AEMK_OLD_MK_HASH)
        if old_master_key_hash != self.hash(old_master_key_str):
            logger.debug(f'{INDENT}cannot retrieve valid {AEMK_OLD_MK_HASH}')
            return False
        new_master_key_str = self.master_key_str
        logger.debug(f'{INDENT}new master key = {new_master_key_str}')
        self._set_master_key(old_master_key_str)
        logger.debug(f'{INDENT}old master key = {old_master_key_str}')
        unencrypted_values = self.retrieve_all_secrets()
        self._set_master_key(new_master_key_str)
        self.store_all_secrets(unencrypted_values)
        self.store_secret(CURRENT_MK_HASH, self.master_key_hash)
        self.save_securestore()
        logger.debug('auto_key_exchange successful')
        return True

    def prepare_auto_key_exchange(self) -> str:
        """Prepare the secure store for an automatic key exchange.

        Generates a new master key, stores the old master key encrypted in the secure store along with hashes of the old and the new key.

        Returns:
            str: The new master key (Base64 encoded).
        """
        logger.debug(f'prepare_auto_key_exchange ...')
        logger.debug(
            f'{INDENT}Current key: master_key: {self.master_key_str} hash: {self.master_key_hash}')
        current_mk_str = self.master_key_str
        current_mk_hash = self.master_key_hash
        new_master_key_str = generate_key_str()
        self._set_master_key(new_master_key_str)
        logger.debug(
            f'{INDENT}Replacement: master_key: {self.master_key_str} hash: {self.master_key_hash}')
        self.store_secret(AEMK_NEW_MK_HASH, self.master_key_hash)
        self.store_secret(AEMK_OLD_MK_KEY, current_mk_str)
        self.store_secret(AEMK_OLD_MK_HASH, current_mk_hash)
        self.save_securestore()
        self._set_master_key(current_mk_str)
        logger.debug(f'prepare_auto_key_exchange done.')
        return new_master_key_str

    def _set_master_key(self, keystring: str):
        """Set the master key from a Base64-encoded string.

        Args:
            keystring (str): Base64-encoded master key.
        """
        self._master_key = b64str_to_bytes(keystring)

    def _read_securestore_file(self) -> None:
        """Read the secure store JSON file into memory."""
        self.securestore = {}
        if os.path.exists(self.securestore_file):
            with open(self.securestore_file, "r") as f:
                self.securestore = json.load(f)

    def delete_securestore_file(self) -> None:
        """Delete the secure store file from disk and clear memory."""
        self.securestore = {}
        if os.path.exists(self.securestore_file):
            os.remove(self.securestore_file)

    def save_securestore(self) -> None:
        """Save the in-memory secure store to disk in JSON format."""
        path = Path(self.securestore_file).parent
        path.mkdir(parents=True, exist_ok=True)
        with open(self.securestore_file, "w") as f:
            json.dump(self.securestore, f)

    def retrieve_secret(self, secret_name: str) -> str:
        """Retrieve and decrypt (with AES-GCM) a secret from the secure store.

        Args:
            secret_name (str): Name of the secret.

        Returns:
            str: The decrypted secret value, or None if not found or decryption fails.
        """
        if secret_name not in self.securestore:
            return None
        encrypted_data = self.securestore[secret_name]
        if type(encrypted_data) != dict:
            raise TypeError(f'Encrypted data for secret name {secret_name} is not a dict')
        try:
            enc_key = self._derive_keys()
            nonce = b64str_to_bytes(encrypted_data[ITEMNAME_NONCE])
            ciphertext = b64str_to_bytes(encrypted_data[ITEMNAME_CIPHERTEXT])
            tag = b64str_to_bytes(encrypted_data[ITEMNAME_TAG])
            cipher = Cipher(
                algorithms.AES(enc_key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            )
            decryptor = cipher.decryptor()
            decrypted_data = decryptor.update(
                ciphertext) + decryptor.finalize()
            secret_value = decrypted_data.decode()
            return secret_value
        except InvalidTag:
            logger.warning(
                f"Decryption failed for {secret_name}: authentication tag mismatch (tampering suspected)")
            return None

        except Exception as e:
            logger.warning(f"Decryption failed for {secret_name}: {e}")
            return None
        # logger.debug(_get_msg('retrieve', secret_name,
        #                         secret_value, self.master_key_str))
        # return secret_value

    def retrieve_all_secrets(self) -> dict:
        """Retrieve and decrypt all secrets in the secure store.

        Returns:
            dict: Mapping of secret names to decrypted values.
        """
        logger.debug('retrieve all secrets')
        unencrypted = {}
        for key in self.securestore:
            unencrypted[key] = self.retrieve_secret(key)
        return unencrypted

    def store_secret(self, secret_name: str, secret_value: str) -> None:
        """Encrypt (with AES-GCM) and store a secret in the secure store.

        Args:
            secret_name (str): Name of the secret.
            secret_value (str): Secret value in plaintext.
        """
        secret_value = str(secret_value)
        enc_key = self._derive_keys()
        nonce = os.urandom(AES_GCM_NONCE_SIZE)  # nonce for AES-GCM
        cipher = Cipher(algorithms.AES(enc_key), modes.GCM(
            nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        ciphertext = encryptor.update(
            secret_value.encode()) + encryptor.finalize()
        encrypted_data = {
            ITEMNAME_NONCE: bytes_to_b64str(nonce),
            ITEMNAME_CIPHERTEXT: bytes_to_b64str(ciphertext),
            ITEMNAME_TAG: bytes_to_b64str(encryptor.tag),
        }
        self.securestore[secret_name] = encrypted_data
        # logger.debug(_get_msg('store', secret_name,
        #              secret_value, self.master_key_str))

    def store_all_secrets(self, unencrypted_values: dict) -> None:
        """Encrypt and store multiple secrets in the secure store.

        Args:
            unencrypted_values (dict): Mapping of secret names to plaintext values.
        """
        logger.debug('store all secrets')
        for key in unencrypted_values:
            if type(unencrypted_values[key]) == str:
                self.store_secret(key, unencrypted_values[key])

    @property
    def master_key_str(self) -> str:
        """Get the master key as a Base64-encoded string.

        Returns:
            str: The Base64-encoded master key.
        """
        return bytes_to_b64str(self._master_key)

    @property
    def master_key_hash(self) -> str:
        """Get the SHA-256 hash of the Base64-encoded master key.

        Returns:
            str: Hexadecimal hash string.
        """
        return self.hash(self.master_key_str)

    def hash(self, value: str) -> str:
        """Compute the SHA-256 hash of a string.

        Args:
            value (str): Input string.

        Returns:
            str: Hexadecimal hash string.
        """
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        digest.update(value.encode())
        return digest.finalize().hex()
