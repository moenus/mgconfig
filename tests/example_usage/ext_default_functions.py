import socket
from tzlocal import get_localzone_name


def default_hostname() -> str:
    """Return the current machine's hostname.

    Returns:
        str: The system's hostname.
    """
    return socket.gethostname()


def default_timezone(default: str = 'Etc/UTC') -> str:
    """Return the local timezone name, falling back to a provided default.

    The function first tries to get the local timezone using
    `get_localzone_name()`. If it returns ``Etc/UTC``, it attempts to
    read `/etc/timezone` for a more specific value. If that file does
    not exist, the provided default value is returned.

    Args:
        default (str, optional): Fallback timezone to use if the system
            timezone cannot be determined. Defaults to ``'Etc/UTC'``.

    Returns:
        str: The determined timezone name or the fallback default.
    """
    local_timezone_str = get_localzone_name()
    if local_timezone_str == 'Etc/UTC':
        try:
            with open('/etc/timezone', 'r') as tz_file:
                local_timezone_str = tz_file.read().strip()
        except FileNotFoundError:
            # Fallback to DEFAULT_TIMEZONE if timezone file is not available
            local_timezone_str = default
    return local_timezone_str


