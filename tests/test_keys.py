"""keys 模块：多种公钥 / 私钥格式的识别，以及由私钥生成公钥。"""

import base64
import datetime

import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.x509.oid import NameOID

from crypto_core import ecc_cipher, keys, rsa_cipher
from crypto_core.common import CryptoError, PasswordRequired, PrivateKeyGiven

Encoding, PublicFormat, PrivateFormat = (
    serialization.Encoding,
    serialization.PublicFormat,
    serialization.PrivateFormat,
)


@pytest.fixture(scope="module")
def rsa_pair():
    return rsa_cipher.generate_keypair("2048")


@pytest.fixture(scope="module")
def rsa_key(rsa_pair):
    return serialization.load_pem_private_key(rsa_pair[0].encode(), None)


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode()


def _self_signed_cert(private_key) -> x509.Certificate:
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "test")])
    now = datetime.datetime.now(datetime.timezone.utc)
    return (
        x509.CertificateBuilder()
        .subject_name(name)
        .issuer_name(name)
        .public_key(private_key.public_key())
        .serial_number(1)
        .not_valid_before(now)
        .not_valid_after(now + datetime.timedelta(days=1))
        .sign(private_key, hashes.SHA256())
    )


# ---------- 公钥格式识别 ----------

def test_standard_pem_is_unchanged(rsa_pair):
    assert keys.normalize_public_pem(rsa_pair[1], "RSA").strip() == rsa_pair[1].strip()


def test_openssh_public_key_is_accepted(rsa_pair, rsa_key):
    ssh = rsa_key.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    assert keys.normalize_public_pem(ssh + " user@host", "RSA").strip() == rsa_pair[1].strip()


def test_certificate_public_key_is_extracted(rsa_pair, rsa_key):
    cert_pem = _self_signed_cert(rsa_key).public_bytes(Encoding.PEM).decode()
    assert keys.normalize_public_pem(cert_pem, "RSA").strip() == rsa_pair[1].strip()


def test_bare_base64_spki_is_accepted(rsa_pair, rsa_key):
    body = _b64(rsa_key.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo))
    assert keys.normalize_public_pem(body, "RSA").strip() == rsa_pair[1].strip()


def test_bare_base64_pkcs1_is_accepted(rsa_pair, rsa_key):
    body = _b64(rsa_key.public_key().public_bytes(Encoding.DER, PublicFormat.PKCS1))
    assert keys.normalize_public_pem(body, "RSA").strip() == rsa_pair[1].strip()


def test_bare_base64_certificate_is_accepted(rsa_pair, rsa_key):
    body = _b64(_self_signed_cert(rsa_key).public_bytes(Encoding.DER))
    assert keys.normalize_public_pem(body, "RSA").strip() == rsa_pair[1].strip()


def test_ecc_openssh_public_key_is_accepted():
    private_pem, public_pem = ecc_cipher.generate_keypair("P-256")
    key = serialization.load_pem_private_key(private_pem.encode(), None)
    ssh = key.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    assert keys.normalize_public_pem(ssh, "ECC").strip() == public_pem.strip()


def test_encrypt_accepts_openssh_public_key(rsa_pair, rsa_key):
    ssh = rsa_key.public_key().public_bytes(Encoding.OpenSSH, PublicFormat.OpenSSH).decode()
    token = rsa_cipher.encrypt("hi", ssh)
    assert rsa_cipher.decrypt(token, rsa_pair[0]) == "hi"


def test_private_pem_in_public_slot_explains_mistake(rsa_pair):
    with pytest.raises(PrivateKeyGiven, match="这是私钥"):
        keys.normalize_public_pem(rsa_pair[0], "RSA")


def test_bare_base64_private_key_in_public_slot_explains_mistake(rsa_key):
    body = _b64(rsa_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, serialization.NoEncryption()))
    with pytest.raises(PrivateKeyGiven, match="这是私钥"):
        keys.normalize_public_pem(body, "RSA")


def test_public_key_in_private_slot_explains_mistake(rsa_pair):
    with pytest.raises(CryptoError, match="这是公钥"):
        keys.unlock_private_pem(rsa_pair[1], None, "RSA")


def test_wrong_key_type_still_rejected():
    _, ecc_public = ecc_cipher.generate_keypair("P-256")
    with pytest.raises(CryptoError, match="这不是 RSA 公钥"):
        keys.normalize_public_pem(ecc_public, "RSA")


def test_unrecognized_text_lists_supported_formats():
    with pytest.raises(CryptoError, match="OpenSSH"):
        keys.normalize_public_pem("hello world", "RSA")


# ---------- 私钥格式识别 ----------

def test_bare_base64_private_key_is_accepted(rsa_pair, rsa_key):
    body = _b64(rsa_key.private_bytes(Encoding.DER, PrivateFormat.PKCS8, serialization.NoEncryption()))
    assert keys.unlock_private_pem(body, None, "RSA").strip() == rsa_pair[0].strip()


def test_openssh_private_key_is_accepted(rsa_pair, rsa_key):
    ssh = rsa_key.private_bytes(Encoding.PEM, PrivateFormat.OpenSSH, serialization.NoEncryption()).decode()
    assert keys.unlock_private_pem(ssh, None, "RSA").strip() == rsa_pair[0].strip()


def test_encrypted_openssh_private_key_requires_password(rsa_pair, rsa_key):
    ssh = rsa_key.private_bytes(
        Encoding.PEM, PrivateFormat.OpenSSH, serialization.BestAvailableEncryption(b"kp")
    ).decode()
    with pytest.raises(PasswordRequired):
        keys.unlock_private_pem(ssh, None, "RSA")
    assert keys.unlock_private_pem(ssh, "kp", "RSA").strip() == rsa_pair[0].strip()


def test_unrecognized_private_text_rejected():
    with pytest.raises(CryptoError, match="私钥"):
        keys.unlock_private_pem("hello world", None, "RSA")


# ---------- 由私钥生成公钥 ----------

def test_public_pem_from_private(rsa_pair):
    assert keys.public_pem_from_private(rsa_pair[0], None, "RSA").strip() == rsa_pair[1].strip()


def test_public_pem_from_encrypted_private_requires_password(rsa_pair):
    protected = keys.protect_private_pem(rsa_pair[0], "kp", "RSA")
    with pytest.raises(PasswordRequired):
        keys.public_pem_from_private(protected, None, "RSA")
    assert keys.public_pem_from_private(protected, "kp", "RSA").strip() == rsa_pair[1].strip()


def test_public_pem_from_ecc_private():
    private_pem, public_pem = ecc_cipher.generate_keypair("P-384")
    assert keys.public_pem_from_private(private_pem, None, "ECC").strip() == public_pem.strip()


def test_public_pem_from_wrong_kind_private_rejected():
    ecc_private, _ = ecc_cipher.generate_keypair("P-256")
    with pytest.raises(CryptoError, match="这不是 RSA 私钥"):
        keys.public_pem_from_private(ecc_private, None, "RSA")
