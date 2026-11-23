import base64

import pytest

from crypto_core import ecc_cipher, rsa_cipher
from crypto_core.common import CryptoError


@pytest.mark.parametrize("curve", ecc_cipher.KEY_OPTIONS)
def test_round_trip_on_every_curve(curve):
    private_pem, public_pem = ecc_cipher.generate_keypair(curve)
    token = ecc_cipher.encrypt("椭圆曲线 ECC ✓", public_pem)
    assert ecc_cipher.decrypt(token, private_pem) == "椭圆曲线 ECC ✓"


def test_key_options_cover_expected_curves():
    assert ecc_cipher.KEY_OPTIONS == ["P-256", "P-384", "P-521", "secp256k1"]


def test_unknown_curve_rejected():
    with pytest.raises(CryptoError, match="曲线"):
        ecc_cipher.generate_keypair("P-999")


def test_decrypt_with_other_private_key_raises():
    _, public_pem = ecc_cipher.generate_keypair("P-256")
    other_private, _ = ecc_cipher.generate_keypair("P-256")
    token = ecc_cipher.encrypt("secret", public_pem)
    with pytest.raises(CryptoError, match="解密失败"):
        ecc_cipher.decrypt(token, other_private)


def test_tampered_ciphertext_raises():
    private_pem, public_pem = ecc_cipher.generate_keypair("P-256")
    raw = bytearray(base64.b64decode(ecc_cipher.encrypt("secret", public_pem)))
    raw[-1] ^= 0x01
    with pytest.raises(CryptoError, match="解密失败"):
        ecc_cipher.decrypt(base64.b64encode(bytes(raw)).decode(), private_pem)


def test_corrupted_ephemeral_point_raises():
    private_pem, public_pem = ecc_cipher.generate_keypair("P-256")
    raw = bytearray(base64.b64decode(ecc_cipher.encrypt("secret", public_pem)))
    raw[0] = 0x07  # not a valid point prefix
    with pytest.raises(CryptoError):
        ecc_cipher.decrypt(base64.b64encode(bytes(raw)).decode(), private_pem)


def test_rsa_public_key_rejected():
    _, rsa_public = rsa_cipher.generate_keypair("2048")
    with pytest.raises(CryptoError, match="ECC"):
        ecc_cipher.encrypt("hi", rsa_public)


def test_too_short_ciphertext_raises():
    private_pem, _ = ecc_cipher.generate_keypair("P-256")
    with pytest.raises(CryptoError, match="长度"):
        ecc_cipher.decrypt(base64.b64encode(b"x" * 20).decode(), private_pem)
