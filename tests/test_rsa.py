import base64

import pytest

from crypto_core import ecc_cipher, keys, rsa_cipher
from crypto_core.common import CryptoError, PasswordRequired


@pytest.fixture(scope="module")
def keypair():
    return rsa_cipher.generate_keypair("2048")


def test_generate_keypair_returns_pem_strings(keypair):
    private_pem, public_pem = keypair
    assert private_pem.startswith("-----BEGIN PRIVATE KEY-----")
    assert public_pem.startswith("-----BEGIN PUBLIC KEY-----")


def test_unsupported_key_size_rejected():
    with pytest.raises(CryptoError, match="密钥长度"):
        rsa_cipher.generate_keypair("1024")


def test_round_trip_handles_text_longer_than_rsa_block(keypair):
    private_pem, public_pem = keypair
    message = "长文本-long text " * 500
    token = rsa_cipher.encrypt(message, public_pem)
    assert rsa_cipher.decrypt(token, private_pem) == message


def test_decrypt_with_other_private_key_raises(keypair):
    _, public_pem = keypair
    other_private, _ = rsa_cipher.generate_keypair("2048")
    token = rsa_cipher.encrypt("secret", public_pem)
    with pytest.raises(CryptoError, match="解密失败"):
        rsa_cipher.decrypt(token, other_private)


def test_tampered_ciphertext_raises(keypair):
    private_pem, public_pem = keypair
    raw = bytearray(base64.b64decode(rsa_cipher.encrypt("secret", public_pem)))
    raw[-1] ^= 0x01
    with pytest.raises(CryptoError, match="解密失败"):
        rsa_cipher.decrypt(base64.b64encode(bytes(raw)).decode(), private_pem)


def test_ecc_public_key_rejected(keypair):
    _, ecc_public = ecc_cipher.generate_keypair("P-256")
    with pytest.raises(CryptoError, match="RSA"):
        rsa_cipher.encrypt("hi", ecc_public)


def test_garbage_pem_rejected():
    with pytest.raises(CryptoError, match="公钥"):
        rsa_cipher.encrypt("hi", "not a pem")


def test_missing_public_key_rejected():
    with pytest.raises(CryptoError, match="公钥"):
        rsa_cipher.encrypt("hi", "   ")


def test_encrypted_private_key_requires_password(keypair):
    private_pem, public_pem = keypair
    protected = keys.protect_private_pem(private_pem, "kp", "RSA")
    assert keys.is_encrypted_pem(protected)
    token = rsa_cipher.encrypt("hi", public_pem)
    with pytest.raises(PasswordRequired):
        rsa_cipher.decrypt(token, protected)
    assert rsa_cipher.decrypt(token, protected, "kp") == "hi"


def test_wrong_private_key_password_raises(keypair):
    private_pem, public_pem = keypair
    protected = keys.protect_private_pem(private_pem, "kp", "RSA")
    token = rsa_cipher.encrypt("hi", public_pem)
    with pytest.raises(CryptoError, match="私钥密码错误") as info:
        rsa_cipher.decrypt(token, protected, "nope")
    assert not isinstance(info.value, PasswordRequired)


def test_unlock_private_pem_returns_plain_pem(keypair):
    private_pem, _ = keypair
    protected = keys.protect_private_pem(private_pem, "kp", "RSA")
    unlocked = keys.unlock_private_pem(protected, "kp", "RSA")
    assert not keys.is_encrypted_pem(unlocked)
    assert unlocked.startswith("-----BEGIN PRIVATE KEY-----")


def test_protect_without_password_keeps_key_unencrypted(keypair):
    private_pem, _ = keypair
    assert not keys.is_encrypted_pem(keys.protect_private_pem(private_pem, "", "RSA"))
