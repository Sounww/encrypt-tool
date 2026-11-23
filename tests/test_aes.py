import base64

import pytest

from crypto_core import aes_cipher
from crypto_core.common import CryptoError


def test_round_trip_restores_plaintext():
    token = aes_cipher.encrypt("你好, world! 🔐", "s3cret")
    assert aes_cipher.decrypt(token, "s3cret") == "你好, world! 🔐"


def test_encrypting_twice_gives_different_ciphertext():
    assert aes_cipher.encrypt("hi", "pw") != aes_cipher.encrypt("hi", "pw")


def test_decrypt_tolerates_whitespace_in_pasted_token():
    token = aes_cipher.encrypt("hello", "pw")
    pasted = f"  {token[:10]}\n{token[10:]}\n"
    assert aes_cipher.decrypt(pasted, "pw") == "hello"


def test_wrong_password_raises():
    token = aes_cipher.encrypt("hi", "pw")
    with pytest.raises(CryptoError, match="密码错误"):
        aes_cipher.decrypt(token, "other")


def test_tampered_ciphertext_raises():
    raw = bytearray(base64.b64decode(aes_cipher.encrypt("hello", "pw")))
    raw[-1] ^= 0x01
    with pytest.raises(CryptoError, match="篡改"):
        aes_cipher.decrypt(base64.b64encode(bytes(raw)).decode(), "pw")


def test_invalid_base64_raises():
    with pytest.raises(CryptoError, match="Base64"):
        aes_cipher.decrypt("!!!not base64!!!", "pw")


def test_too_short_ciphertext_raises():
    with pytest.raises(CryptoError, match="长度"):
        aes_cipher.decrypt(base64.b64encode(b"short").decode(), "pw")


def test_empty_password_rejected():
    with pytest.raises(CryptoError, match="密码"):
        aes_cipher.encrypt("hi", "")


def test_empty_plaintext_rejected():
    with pytest.raises(CryptoError, match="内容"):
        aes_cipher.encrypt("", "pw")
