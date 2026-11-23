import pytest

from crypto_core import hashing
from crypto_core.common import CryptoError

ABC_SHA256 = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_sha256_matches_known_vector():
    assert hashing.sha256_hex("abc") == ABC_SHA256


def test_sha256_uppercase_option():
    assert hashing.sha256_hex("abc", upper=True) == ABC_SHA256.upper()


def test_sha256_encodes_text_as_utf8():
    import hashlib

    assert hashing.sha256_hex("中文") == hashlib.sha256("中文".encode("utf-8")).hexdigest()


def test_bcrypt_hash_uses_requested_cost():
    assert hashing.bcrypt_hash("pw", rounds=4).startswith("$2b$04$")


def test_bcrypt_verify_accepts_correct_password():
    hashed = hashing.bcrypt_hash("correct horse", rounds=4)
    assert hashing.bcrypt_verify("correct horse", hashed) is True


def test_bcrypt_verify_rejects_wrong_password():
    hashed = hashing.bcrypt_hash("correct horse", rounds=4)
    assert hashing.bcrypt_verify("battery staple", hashed) is False


def test_bcrypt_verify_tolerates_surrounding_whitespace_in_hash():
    hashed = hashing.bcrypt_hash("pw", rounds=4)
    assert hashing.bcrypt_verify("pw", f"  {hashed}\n") is True


def test_bcrypt_rejects_password_over_72_bytes():
    with pytest.raises(CryptoError, match="72"):
        hashing.bcrypt_hash("密" * 25, rounds=4)  # 75 bytes in UTF-8


def test_bcrypt_verify_rejects_password_over_72_bytes():
    hashed = hashing.bcrypt_hash("pw", rounds=4)
    with pytest.raises(CryptoError, match="72"):
        hashing.bcrypt_verify("a" * 73, hashed)


def test_bcrypt_rejects_cost_out_of_range():
    with pytest.raises(CryptoError, match="cost"):
        hashing.bcrypt_hash("pw", rounds=3)


def test_bcrypt_rejects_empty_password():
    with pytest.raises(CryptoError, match="密码"):
        hashing.bcrypt_hash("", rounds=4)


def test_bcrypt_verify_rejects_malformed_hash():
    with pytest.raises(CryptoError, match="哈希格式"):
        hashing.bcrypt_verify("pw", "not-a-bcrypt-hash")
