"""ECC 加密（ECIES）：临时 EC 密钥 + ECDH → HKDF-SHA256 → AES-256-GCM。

密文布局（Base64 前）：临时公钥点(未压缩) ‖ nonce(12) ‖ ciphertext+tag
"""

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

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

NAME = "ECC"
CURVES = {
    "P-256": ec.SECP256R1,
    "P-384": ec.SECP384R1,
    "P-521": ec.SECP521R1,
    "secp256k1": ec.SECP256K1,
}
KEY_OPTIONS = list(CURVES)
DEFAULT_OPTION = "P-256"
_HKDF_INFO = b"CipherBox-ECIES-v1"
_DECRYPT_FAILED = "解密失败：私钥不匹配或密文已损坏"


def _point_size(curve: ec.EllipticCurve) -> int:
    return 1 + 2 * ((curve.key_size + 7) // 8)


def _derive_key(shared_secret: bytes, ephemeral_point: bytes) -> bytes:
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=_HKDF_INFO + ephemeral_point)
    return hkdf.derive(shared_secret)


def generate_keypair(option: str = DEFAULT_OPTION) -> tuple[str, str]:
    if option not in CURVES:
        raise CryptoError(f"不支持的曲线：{option}")
    private_key = ec.generate_private_key(CURVES[option]())
    return keys.private_to_pem(private_key), keys.public_to_pem(private_key.public_key())


def encrypt(plaintext: str, public_pem: str) -> str:
    require_text(plaintext, "要加密的内容")
    public_key = keys.load_public_key(public_pem, NAME)
    ephemeral = ec.generate_private_key(public_key.curve)
    point = ephemeral.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    key = _derive_key(ephemeral.exchange(ec.ECDH(), public_key), point)
    return b64_encode(point + gcm_seal(key, plaintext.encode("utf-8"), aad=point))


def decrypt(token: str, private_pem: str, password: str | None = None) -> str:
    raw = b64_decode(token)
    private_key = keys.load_private_key(private_pem, password, NAME)
    point_size = _point_size(private_key.curve)
    if len(raw) < point_size + NONCE_SIZE + TAG_SIZE:
        raise CryptoError("密文长度不正确，可能不完整或与私钥不匹配")
    point, blob = raw[:point_size], raw[point_size:]
    try:
        ephemeral_public = ec.EllipticCurvePublicKey.from_encoded_point(private_key.curve, point)
    except ValueError:
        raise CryptoError(_DECRYPT_FAILED) from None
    key = _derive_key(private_key.exchange(ec.ECDH(), ephemeral_public), point)
    return decode_utf8(gcm_open(key, blob, _DECRYPT_FAILED, aad=point))
