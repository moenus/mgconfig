# Copyright (c) 2025 moenus
# SPDX-License-Identifier: MIT


import time
from dataclasses import dataclass, fields
from typing import Optional, Dict, Tuple
VERSION_STR = "v1"  # is used in file header and info parameter
from .sec_store_crypt import ITEMS_MAC_ALG, KDF_ALG, generate_salt_str, CryptoContextMAC, VERSION_STR, b64str_to_bytes, bytes_to_b64str


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

    @property
    def salt(self):
        return b64str_to_bytes(self.salt_b64)

    def update_items_mac(self, items: Dict[str, Dict[str, str]], master_key: bytes) -> None:
        self.items_mac_alg = ITEMS_MAC_ALG
        mac_context = CryptoContextMAC(self.salt, master_key)
        self.items_mac_b64 = mac_context.compute_items_mac(items)

    def verify_items_mac(self, items: Dict[str, Dict[str, str]], master_key: bytes) -> None:
        if self.items_mac_alg != ITEMS_MAC_ALG:
            raise ValueError(
                "SecureStore integrity check failed (MAC algorithm mismatch)")
        try:
            mac_context = CryptoContextMAC(self.salt, master_key)            
            mac_context.verify_items_mac(items,self.items_mac_b64)
        except Exception as e:
            raise ValueError(
                "SecureStore integrity check failed (items MAC mismatch)") from e

    @classmethod
    def create_new(cls, master_key_hash: bytes) -> "SecurityHeader":
        return cls(
            version=VERSION_STR,
            kdf=KDF_ALG,
            salt_b64=generate_salt_str(),  # public, random, per-store
            created_at=int(time.time()),
            mk_hash=master_key_hash,
            items_mac_b64=None,
            items_mac_alg=None
        )

    @classmethod
    def prepare(cls, header_dict: dict) -> "SecurityHeader":
        for field in fields(cls):
            if field.name not in header_dict:
                raise ValueError(f"SecureStore header missing '{field.name}'")
        return cls(**header_dict)
