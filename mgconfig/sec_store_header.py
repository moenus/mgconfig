# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


import time
from dataclasses import dataclass, fields
from typing import Optional, Dict, Tuple
from .sec_store_crypt import verify_items_mac, compute_items_mac, ITEMS_MAC_ALG, KDF_ALG, hash_bytes, generate_salt_str


__version__ = 1  # is used in file header and info parameter


# --------------------------------------------------------------------------------
# security header
# --------------------------------------------------------------------------------


@dataclass
class SecurityHeader:
    version: int
    kdf: str
    salt_b64: str
    created_at: int
    mk_hash: str
    items_mac_b64: Optional[str] = None     # Base64(HMAC(items))
    items_mac_alg: Optional[str] = None

    def update_items_mac(self, items: Dict[str, Dict[str, str]], master_key: bytes) -> None:
        self.items_mac_alg = ITEMS_MAC_ALG
        self.items_mac_b64 = compute_items_mac(items, master_key, self.salt_b64)

    def verify_items_mac(self, items: Dict[str, Dict[str, str]], master_key: bytes) -> None:
        if self.items_mac_alg != ITEMS_MAC_ALG:
            raise ValueError(
                "SecureStore integrity check failed (MAC algorithm mismatch)")
        if not verify_items_mac(items, self.items_mac_b64, master_key, self.salt_b64):
            raise ValueError(
                "SecureStore integrity check failed (items MAC mismatch)")


def new_header(master_key: bytes) -> SecurityHeader:
    return SecurityHeader(
        version=__version__,
        kdf=KDF_ALG,
        salt_b64=generate_salt_str(),  # public, random, per-store
        created_at=int(time.time()),
        mk_hash=hash_bytes(master_key),
        items_mac_b64=None,
        items_mac_alg=None
    )


def create_header(header_dict: dict) -> SecurityHeader:
    for field in fields(SecurityHeader):
        if field.name not in header_dict:
            raise ValueError(f"SecureStore header missing '{field.name}'")
    return SecurityHeader(**header_dict)
