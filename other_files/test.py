# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT

import keyring

# Set a password
keyring.set_password("my_app", "my_username", "my_password123")

# Get a password
password = keyring.get_password("my_app", "my_username1")
print(password)