import os
from pathlib import Path
from enum import Enum
import sys
import yaml
import json
import tempfile
from types import MappingProxyType
from typing import Dict, Any, Optional, IO

import logging
logger = logging.getLogger(__name__)


class FileFormat(Enum):
    """Supported file formats for FileCache.

    Attributes:
        JSON (str): JSON format.
        YAML (str): YAML format.
    """
    JSON = 'json'
    YAML = 'yaml'


class FileMode(Enum):
    """Supported file write modes.

    Attributes:
        READONLY (str): Read-only mode (no writes allowed).
        STANDARD_WRITE (str): Standard write.
        ATOMIC_WRITE (str): Atomic write using a temporary file.
        SECURE_WRITE (str): Secure write with restricted permissions.
    """
    READONLY = 'ro'    # Read-only mode
    STANDARD_WRITE = 'std'  # Standard write
    ATOMIC_WRITE = 'tmp'  # Atomic write using a temporary file
    SECURE_WRITE = "sec"  # Secure write with restricted permissions


class FileCache:
    """Cache for reading and writing structured data (JSON/YAML).

    Provides transparent caching, automatic format detection, and multiple
    write strategies (atomic, secure, standard, read-only).

    Attributes:
        filepath (Path): Path to the target file.
        file_format (FileFormat): File format (JSON/YAML).
        write_mode (WriteMode): Mode used when writing.
        _data (Any): Cached data.
        _ready (bool): Indicates whether the cache has been initialized.
    """

    def __init__(self, filepath: Path, file_format: Optional[FileFormat] = None, file_mode: FileMode = FileMode.STANDARD_WRITE) -> None:
        """Initialize FileCache.

        Args:
            filepath (Path): Path to the target file.
            file_format (Optional[FileFormat], optional): File format. If None,
                it will be inferred from the file suffix. Defaults to None.
            write_mode (WriteMode, optional): Write mode (TMP, SEC, STD, RO).
                Defaults to WriteMode.STD.

        Raises:
            ValueError: If `filepath` is not a Path instance.
            ValueError: If the file format cannot be determined.
        """
        if not isinstance(filepath, Path):
            raise ValueError(f'Parameter filepath is not a PATH instance.')

        if file_format is None:
            file_format = get_file_format(filepath)

        self._filepath: Path = filepath
        self._file_format: FileFormat = file_format
        self._file_mode: FileMode = file_mode
        self._data: Any = {}
        self._ready: bool = False
        logger.debug(f'Initialized: {self.__repr__()}')

    def __repr__(self) -> str:
        return f'File Cache for "{self._filepath}", file format = {self._file_format.value}, write_mode = {self._file_mode.value}'

    @property
    def data(self) -> Any:
        """Return cached data, reading from file if not already loaded.

        If the cache was opened in read-only mode (`WriteMode.RO`), an immutable
        view is returned:

        - dict -> `MappingProxyType(dict)`
        - list/tuple -> `tuple(list_or_tuple)`
        - other types -> returned as-is

        Returns:
            Any: Parsed file content (usually `dict` or `list`). May be wrapped
                to enforce immutability in RO mode.

        Raises:
            ValueError: If the file cannot be read.
        """
        if not self._ready:
            self._read_file()

        if self._file_mode == FileMode.READONLY and isinstance(self._data, dict):
            return MappingProxyType(self._data)

        return self._data

    def clear(self) -> None:
        """Clear the cached data and mark the cache as not ready.

        This resets the internal cache to an empty dict and forces a fresh read
        from disk on next access to `.data`.
        """
        # Reassign to a new empty dict to avoid errors if _data is a non-mutable
        # or a type without a .clear() method.
        self._data = {}
        self._ready = False

    def save(self) -> None:
        """Save cached data to file.

        Raises:
            ValueError: If cache is not ready.
        """
        if not self._ready:
            raise ValueError(f'Cannot save because file cache was not properly initialized.')
        try:
            self._write_file()
        except Exception as e:
            logger.debug(
                f'Cannot save data to file "{self._filepath}": {e}.')
            raise 


    def _read_file(self) -> None:
        """Read file contents into the cache.

        Raises:
            ValueError: If reading or parsing fails.
        """
        if not self._filepath.exists():
            logger.info(f'File "{self._filepath}" not found.')
            self._ready = True
            return

        logger.debug(f'Read: {self.__repr__()}')

        try:
            with open(self._filepath, "r", encoding="utf-8") as file:
                if self._file_format == FileFormat.JSON:
                    self._data = json.load(file) or {}
                elif self._file_format == FileFormat.YAML:
                    # Use safe_load to prevent code execution
                    self._data = yaml.safe_load(file) or {}
            self._ready = True

        except json.JSONDecodeError as e:
            raise RuntimeError(
                f'Invalid JSON in file "{self._filepath}"": {e}') from e

        except Exception as e:
            raise RuntimeError(
                f'Cannot read values from file "{self._filepath}"') from e

    def _write_file(self) -> bool:
        """Write cached data to file according to the configured write mode.

        Returns:
            bool: True if file was written successfully.

        Raises:
            IOError: If write mode is RO.
            Exception: If file writing fails.
        """
        logger.debug(f'Write: {self.__repr__()}')

        if self._file_mode == FileMode.READONLY:
            raise RuntimeError('File cannot be overwritten.')

        folder = self._filepath.parent
        folder.mkdir(parents=True, exist_ok=True)

        if self._file_mode == FileMode.STANDARD_WRITE:
            try:
                with open(self._filepath, "w", encoding="utf-8") as file:
                    self._dump_data_to_file(file)
            except Exception as exc:
                raise RuntimeError(
                    f'Failed to write file "{self._filepath}": {exc}') from exc

        elif self._file_mode == FileMode.ATOMIC_WRITE:
            try:
                with tempfile.NamedTemporaryFile("w", dir=folder, delete=False, encoding="utf-8") as file:
                    self._dump_data_to_file(file)
                    temp_name = file.name

                # Atomically replace the target file with the temp file
                Path(temp_name).replace(self._filepath)
            except Exception as exc:
                # Add context while preserving original traceback
                raise RuntimeError(
                    f'Failed to write temporary file for "{self._filepath}": {exc}') from exc
            finally:
                # If temp file still exists (on failure), try to clean up
                try:
                    if "temp_name" in locals():
                        temp_path = Path(temp_name)
                        if temp_path.exists():
                            temp_path.unlink()
                except Exception:
                    # Best-effort cleanup; swallow to avoid hiding earlier exceptions
                    pass

        elif self._file_mode == FileMode.SECURE_WRITE:
            try:
                with open_secure_file(self._filepath) as file:
                    self._dump_data_to_file(file)
            except Exception as exc:
                raise RuntimeError(
                    f'Failed to write secure file "{self._filepath}": {exc}') from exc

    def _dump_data_to_file(self, file) -> None:
        """Serialize the cached data to an open text file and flush to disk.

        This writes either JSON or YAML to the provided, already-open text file
        object. The file is flushed and `os.fsync` is called to ensure data hits
        the storage device.

        Args:
            file (IO[str]): An open text-mode file-like object (writable).

        Raises:
            TypeError: If the data cannot be serialized to the requested format.
            OSError: If flushing or syncing the file descriptor fails.
        """
        if self._file_format == FileFormat.JSON:
            json.dump(self._data, file,
                      ensure_ascii=False,
                      indent=2)
        elif self._file_format == FileFormat.YAML:
            yaml.safe_dump(self._data, file,
                           default_flow_style=False,  # block style (readable)
                           sort_keys=False,           # preserve dict insertion order
                           allow_unicode=True,
                           width=None)
        file.flush()
        os.fsync(file.fileno())  # Ensure data is flushed to disk

    def __enter__(self):
        """Enter a context for the FileCache.

        Returns:
            FileCache: The cache instance (self).
        """
        return self

    def __exit__(self, exc_type, exc, tb):
        """Exit the context manager.

        If no exception occurred within the context block, the cache is saved to
        disk. Exceptions are propagated (this method does not suppress them).

        Args:
            exc_type: Exception class (or None).
            exc: Exception instance (or None).
            tb: Traceback (or None).
        """
        if exc_type is None:
            self.save()


def get_file_format(filepath: Path):
    """Infer the file format from a file path suffix.

    Recognizes `.json`, `.yaml`, and `.yml`. Case-insensitive.

    Args:
        filepath (Path): The path whose suffix will be used to detect format.

    Returns:
        FileFormat: The detected file format.

    Raises:
        ValueError: If the suffix is unsupported.
    """
    suffix = filepath.suffix[1:].lower()
    if suffix == "yml":
        suffix = "yaml"
    for file_fmt in FileFormat:
        if suffix == file_fmt.value:
            return file_fmt

    raise ValueError(
        f'File format could not be determined. Unsupported file extension "{filepath.suffix}"')


if sys.platform == "win32":
    try:
        import win32api
        import win32con
        import win32file
        import win32security
        import msvcrt
        import pywintypes
    except ImportError:
        raise RuntimeError("Secure file mode requires pywin32 on Windows.")


def open_secure_file(path: Path, mode: str = "w") -> IO[str]:
    """Open a file with permissions restricted to the current user only.

    On POSIX systems, the file is created with mode `0o600` (rw-------). On
    Windows, an ACL is applied to restrict access to the current user.

    Args:
        path (Path): Target file path.
        mode (str, optional): Open mode (text mode). Defaults to "w".

    Returns:
        IO[str]: An open text-mode file object with restricted permissions.

    Raises:
        RuntimeError: If secure mode is requested on Windows but pywin32 is not
            available (the import check is performed earlier).
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
        return os.fdopen(fd, mode, encoding='utf-8')

    else:  # POSIX
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        return os.fdopen(fd, mode, encoding='utf-8')
