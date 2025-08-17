# Windows reserved names (case-insensitive), with or without extension
_WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

_INVALID_WIN_CHARS = r'<>:"/\\|?*'
_MAX_FILENAME_LEN = 255  # typical filesystem limit per component

def is_valid_filename(name: str, os: str = "windows") -> bool:
    if not name or name in (".", ".."):
        return False

    # POSIX: forbid null and slash
    if "\x00" in name or "/" in name:
        return False

    # Windows-specific checks
    if os == 'windows':
        # reserved names (ignore extension), e.g., "CON", "con.txt"
        base = name.split(".", 1)[0]
        if base.upper() in _WINDOWS_RESERVED:
            return False
        # invalid characters
        if any(c in _INVALID_WIN_CHARS for c in name):
            return False
        # names ending with space or dot are invalid
        if name.endswith(" ") or name.endswith("."):
            return False

    # length check (in bytes to be safer)
    try:
        if len(name.encode("utf-8")) > _MAX_FILENAME_LEN:
            return False
    except Exception:
        return False

    return True


def parse_filename(value):
    if is_valid_filename(value):
        return value