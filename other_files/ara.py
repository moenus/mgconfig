from pathlib import Path

a = Path(r'/dir/a.txt')
print(a)
print(str(a))
print(f'a.__repr__() {a.__repr__()}')
print(repr(a))

import platform

os_name = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
print(f"OS: {os_name}")

os_full = platform.platform()  # Full version info
print(f"Full: {os_full}")