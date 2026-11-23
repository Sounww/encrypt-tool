"""RSA 混合加密：随机 AES-256 密钥加密正文，再用 RSA-OAEP(SHA-256) 包装该密钥。

密文布局（Base64 前）：wrapped_key(key_size/8) ‖ nonce(12) ‖ ciphertext+tag
"""

import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from . import keys
from .common import (
    NONCE_SIZE,
    TAG_SIZE,
    CryptoError,
    b64_decode,
    b64_encode,
    decode_utf8,
    gcm_open,
    gcm_seal,
    require_text,
)

NAME = "RSA"
KEY_OPTIONS = ["2048", "3072", "4096"]
DEFAULT_OPTION = "2048"
_DECRYPT_FAILED = "解密失败：私钥不匹配或密文已损坏"


def _oaep() -> padding.OAEP:
    return padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)


def generate_keypair(option: str = DEFAULT_OPTION) -> tuple[str, str]:
    if str(option) not in KEY_OPTIONS:
        raise CryptoError(f"不支持的密钥长度：{option}")
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=int(option))
    return keys.private_to_pem(private_key), keys.public_to_pem(private_key.public_key())


def encrypt(plaintext: str, public_pem: str) -> str:
    require_text(plaintext, "要加密的内容")
    public_key = keys.load_public_key(public_pem, NAME)
    session_key = os.urandom(32)
    wrapped = public_key.encrypt(session_key, _oaep())
    return b64_encode(wrapped + gcm_seal(session_key, plaintext.encode("utf-8")))


def decrypt(token: str, private_pem: str, password: str | None = None) -> str:
    raw = b64_decode(token)
    private_key = keys.load_private_key(private_pem, password, NAME)
    wrapped_size = (private_key.key_size + 7) // 8
    if len(raw) < wrapped_size + NONCE_SIZE + TAG_SIZE:
        raise CryptoError("密文长度不正确，可能不完整或与私钥不匹配")
    try:
        session_key = private_key.decrypt(raw[:wrapped_size], _oaep())
    except ValueError:
        raise CryptoError(_DECRYPT_FAILED) from None
    return decode_utf8(gcm_open(session_key, raw[wrapped_size:], _DECRYPT_FAILED))
