"""AES-256-GCM 口令加密：Scrypt 从密码派生密钥。

密文布局（Base64 前）：salt(16) ‖ nonce(12) ‖ ciphertext+tag
"""

import os

from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from .common import (
    CryptoError,
    b64_decode,
    b64_encode,
    decode_utf8,
    gcm_open,
    gcm_seal,
    require_text,
)

SALT_SIZE = 16
_WRONG_PASSWORD = "解密失败：密码错误或密文已被篡改"


def _derive_key(password: str, salt: bytes) -> bytes:
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(password.encode("utf-8"))


def encrypt(plaintext: str, password: str) -> str:
    require_text(plaintext, "要加密的内容")
    require_text(password, "密码")
    salt = os.urandom(SALT_SIZE)
    blob = gcm_seal(_derive_key(password, salt), plaintext.encode("utf-8"))
    return b64_encode(salt + blob)


def decrypt(token: str, password: str) -> str:
    require_text(password, "密码")
    raw = b64_decode(token)
    if len(raw) <= SALT_SIZE:
        raise CryptoError("密文长度不正确，可能不完整")
    salt, blob = raw[:SALT_SIZE], raw[SALT_SIZE:]
    return decode_utf8(gcm_open(_derive_key(password, salt), blob, _WRONG_PASSWORD))
