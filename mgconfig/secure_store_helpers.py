# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import os
import base64
from cryptography.hazmat.primitives import hashes


KEY_SIZE = 32


def bytes_to_b64str(value_bytes: bytes) -> str:
    """Convert bytes to a Base64-encoded UTF-8 string.

    Args:
        value_bytes (bytes): Arbitrary bytes.

    Returns:
        str: Base64-encoded string.
    """
    return base64.b64encode(value_bytes).decode('utf-8')


def b64str_to_bytes(value_str: str) -> bytes:
    """Convert a Base64-encoded string to bytes.

    Args:
        value_str (str): Base64-encoded string.

    Returns:
        bytes: Decoded bytes.
    """
    return base64.b64decode(value_str)    



def hash_bytes(value: bytes) -> str:
    """Compute a SHA-256 hash of input bytes, Base64-encoded.

    Args:
        value (bytes): Data to hash.

    Returns:
        str: Base64 SHA-256 digest.
    """
    digest = hashes.Hash(hashes.SHA256())
    digest.update(value)
    return bytes_to_b64str(digest.finalize())


def generate_key_str() -> str:
    """Generate a random AES-256 key, Base64-encoded.

    Returns:
        str: A randomly generated AES key encoded as a Base64 string.
    """
    return bytes_to_b64str(os.urandom(KEY_SIZE))