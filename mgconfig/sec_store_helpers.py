# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import base64

# KEY_SIZE = 32


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

