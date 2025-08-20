import os, sys
from pathlib import Path
import base64
from cryptography.hazmat.primitives import hashes

if sys.platform == "win32":
    import win32api
    import win32con
    import win32file
    import win32security
    import msvcrt
    import pywintypes

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

def open_secure_file(path: Path, mode: str = "w+b"):
    """
    Open a file with permissions restricted to the current user only.

    Cross-platform:
    - On POSIX: mode 0o600 (rw-------).
    - On Windows: creates a file with an ACL allowing only the current user.

    Args:
        path (Path): Target file path.
        mode (str): Open mode (default "w+b").

    Returns:
        file object: Open file handle.
    """
    if os.name == "nt":
        # Get current user SID
        user_sid, _, _ = win32security.LookupAccountName(
            None, win32api.GetUserName())

        # Create security descriptor
        sd = win32security.SECURITY_DESCRIPTOR()
        dacl = win32security.ACL()
        dacl.AddAccessAllowedAce(
            win32security.ACL_REVISION, win32con.GENERIC_ALL, user_sid)
        sd.SetSecurityDescriptorDacl(1, dacl, 0)

        # Wrap into SECURITY_ATTRIBUTES
        sa = pywintypes.SECURITY_ATTRIBUTES()
        sa.SECURITY_DESCRIPTOR = sd

        # Create secure file
        handle = win32file.CreateFile(
            str(path),
            win32con.GENERIC_READ | win32con.GENERIC_WRITE,
            0,  # no sharing
            sa,  # SECURITY_ATTRIBUTES
            win32con.CREATE_ALWAYS,
            win32con.FILE_ATTRIBUTE_NORMAL,
            None,
        )

        # Convert raw handle into Python file object
        fd = msvcrt.open_osfhandle(handle.Detach(), os.O_RDWR)
        return os.fdopen(fd, mode)

    else:  # POSIX
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        return os.fdopen(fd, mode)


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