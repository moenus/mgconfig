import re

_INVALID_CHARS = r'<>:"/\\|?*'
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *[f"COM{i}" for i in range(1, 10)],
    *[f"LPT{i}" for i in range(1, 10)]
}

_invalid_chars_pattern = re.compile(f"[{re.escape(_INVALID_CHARS)}]")


def is_valid_windows_filename(name: str) -> bool:
    if not name or name.strip(" .") == "":
        return False  # empty or only dots/spaces
    if _invalid_chars_pattern.search(name):
        return False
    if name.endswith(" ") or name.endswith("."):
        return False
    base = name.split(".", 1)[0]  # name before first dot
    if base.upper() in _RESERVED_NAMES:
        return False
    return True
