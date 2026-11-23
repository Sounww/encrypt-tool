"""单向哈希：SHA-256 摘要，以及用于密码存储的 bcrypt。"""

import hashlib

import bcrypt

from .common import CryptoError, require_text

BCRYPT_MIN_COST = 4
BCRYPT_MAX_COST = 16
BCRYPT_DEFAULT_COST = 12
BCRYPT_MAX_BYTES = 72


def sha256_hex(text: str, upper: bool = False) -> str:
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return digest.upper() if upper else digest


def _password_bytes(password: str) -> bytes:
    require_text(password, "密码")
    data = password.encode("utf-8")
    if len(data) > BCRYPT_MAX_BYTES:
        raise CryptoError(
            f"bcrypt 只支持不超过 {BCRYPT_MAX_BYTES} 字节的密码（当前 {len(data)} 字节，中文每字 3 字节）"
        )
    return data


def bcrypt_hash(password: str, rounds: int = BCRYPT_DEFAULT_COST) -> str:
    data = _password_bytes(password)
    if not BCRYPT_MIN_COST <= rounds <= BCRYPT_MAX_COST:
        raise CryptoError(f"cost 必须在 {BCRYPT_MIN_COST} 到 {BCRYPT_MAX_COST} 之间")
    return bcrypt.hashpw(data, bcrypt.gensalt(rounds)).decode("ascii")


def bcrypt_verify(password: str, hashed: str) -> bool:
    data = _password_bytes(password)
    cleaned = require_text(hashed.strip(), "bcrypt 哈希值")
    try:
        return bcrypt.checkpw(data, cleaned.encode("ascii"))
    except (ValueError, UnicodeEncodeError):
        raise CryptoError("bcrypt 哈希格式不正确，应形如 $2b$12$...") from None
