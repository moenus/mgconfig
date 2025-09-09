import pytest
import time
from unittest.mock import patch
from dataclasses import asdict

from mgconfig.sec_store_header import (
    SecurityHeader, new_header, create_header,
    VERSION_STR, KDF_ALG, ITEMS_MAC_ALG
)
from mgconfig.sec_store_helpers import bytes_to_b64str, b64str_to_bytes

# -----------------------------
# Fixtures
# -----------------------------
@pytest.fixture
def sample_header_dict():
    """Provide sample header dictionary."""
    return {
        "version": VERSION_STR,
        "kdf": KDF_ALG,
        "salt_b64": bytes_to_b64str(b"test_salt"),
        "created_at": 1234567890,
        "mk_hash": "test_hash",
        "items_mac_b64": None,
        "items_mac_alg": None
    }

@pytest.fixture
def sample_items():
    """Provide sample items dictionary."""
    return {
        "secret1": {"n": "nonce1", "ct": "ciphertext1"},
        "secret2": {"n": "nonce2", "ct": "ciphertext2"}
    }

# -----------------------------
# SecurityHeader Tests
# -----------------------------
def test_security_header_creation(sample_header_dict):
    """Test SecurityHeader creation from dictionary."""
    header = SecurityHeader(**sample_header_dict)
    assert header.version == VERSION_STR
    assert header.kdf == KDF_ALG
    assert header.salt_b64 == sample_header_dict["salt_b64"]
    assert header.created_at == sample_header_dict["created_at"]
    assert header.mk_hash == sample_header_dict["mk_hash"]
    assert header.items_mac_b64 is None
    assert header.items_mac_alg is None

def test_security_header_salt_property(sample_header_dict):
    """Test salt property conversion."""
    header = SecurityHeader(**sample_header_dict)
    assert header.salt == b"test_salt"

def test_update_items_mac(sample_header_dict, sample_items):
    """Test updating items MAC."""
    header = SecurityHeader(**sample_header_dict)
    master_key = b"test_master_key"
    
    header.update_items_mac(sample_items, master_key)
    
    assert header.items_mac_alg == ITEMS_MAC_ALG
    assert isinstance(header.items_mac_b64, str)
    # MAC value depends on items and master key
    assert len(b64str_to_bytes(header.items_mac_b64)) == 32  # SHA-256 length

def test_verify_items_mac(sample_header_dict, sample_items):
    """Test items MAC verification."""
    header = SecurityHeader(**sample_header_dict)
    master_key = b"test_master_key"
    
    # First update MAC
    header.update_items_mac(sample_items, master_key)
    
    # Verify with same items - should not raise
    header.verify_items_mac(sample_items, master_key)
    
    # Verify with modified items - should raise
    modified_items = sample_items.copy()
    modified_items["secret1"]["ct"] = "tampered"
    with pytest.raises(ValueError, match="integrity check failed"):
        header.verify_items_mac(modified_items, master_key)

def test_verify_items_mac_algorithm_mismatch(sample_header_dict, sample_items):
    """Test MAC algorithm mismatch detection."""
    header = SecurityHeader(**sample_header_dict)
    master_key = b"test_master_key"
    
    header.update_items_mac(sample_items, master_key)
    header.items_mac_alg = "wrong_algorithm"
    
    with pytest.raises(ValueError, match="algorithm mismatch"):
        header.verify_items_mac(sample_items, master_key)

# -----------------------------
# Header Creation Tests
# -----------------------------
def test_new_header():
    """Test new header creation."""
    master_key_hash = "test_hash"
    current_time = 1234567890
    
    with patch('time.time', return_value=current_time):
        header = new_header(master_key_hash)
    
    assert header.version == VERSION_STR
    assert header.kdf == KDF_ALG
    assert header.created_at == current_time
    assert header.mk_hash == master_key_hash
    assert header.items_mac_b64 is None
    assert header.items_mac_alg is None
    # Verify salt is generated and valid base64
    assert b64str_to_bytes(header.salt_b64)  # Should not raise

def test_create_header_from_dict(sample_header_dict):
    """Test header creation from dictionary."""
    header = create_header(sample_header_dict)
    assert isinstance(header, SecurityHeader)
    for key, value in sample_header_dict.items():
        assert getattr(header, key) == value

def test_create_header_missing_field():
    """Test header creation with missing field."""
    incomplete_dict = {
        "version": VERSION_STR,
        "kdf": KDF_ALG,
        # missing salt_b64
        "created_at": 1234567890,
        "mk_hash": "test_hash"
    }
    
    with pytest.raises(ValueError, match="header missing 'salt_b64'"):
        create_header(incomplete_dict)

def test_security_header_to_dict(sample_header_dict):
    """Test converting SecurityHeader to dictionary."""
    header = SecurityHeader(**sample_header_dict)
    header_dict = asdict(header)
    
    assert header_dict == sample_header_dict