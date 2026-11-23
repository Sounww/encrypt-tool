"""共享工具：统一异常、Base64 编解码、AES-GCM 封装。"""

import base64
import binascii
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

NONCE_SIZE = 12
TAG_SIZE = 16


class CryptoError(Exception):
    """带中文说明、可以直接展示给用户的错误。"""


class PasswordRequired(CryptoError):
    """私钥已加密，但调用方没有提供密码。"""


class PrivateKeyGiven(CryptoError):
    """需要公钥的地方给了私钥（可以改为从私钥提取公钥）。"""


def require_text(value: str, what: str) -> str:
    if not value:
        raise CryptoError(f"请输入{what}")
    return value


def b64_encode(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64_decode(text: str) -> bytes:
    cleaned = "".join(text.split())
    if not cleaned:
        raise CryptoError("请输入要解密的密文")
    try:
        return base64.b64decode(cleaned, validate=True)
    except (binascii.Error, ValueError):
        raise CryptoError("密文不是有效的 Base64 字符串") from None


def gcm_seal(key: bytes, plaintext: bytes, aad: bytes | None = None) -> bytes:
    nonce = os.urandom(NONCE_SIZE)
    return nonce + AESGCM(key).encrypt(nonce, plaintext, aad)


def gcm_open(key: bytes, blob: bytes, error_message: str, aad: bytes | None = None) -> bytes:
    if len(blob) < NONCE_SIZE + TAG_SIZE:
        raise CryptoError("密文长度不正确，可能不完整")
    nonce, body = blob[:NONCE_SIZE], blob[NONCE_SIZE:]
    try:
        return AESGCM(key).decrypt(nonce, body, aad)
    except InvalidTag:
        raise CryptoError(error_message) from None


def decode_utf8(data: bytes) -> str:
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        raise CryptoError("解密结果不是有效的 UTF-8 文本") from None
