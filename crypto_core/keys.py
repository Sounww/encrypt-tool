"""RSA / ECC 共用的 PEM 密钥加载与序列化。"""

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from .common import CryptoError, PasswordRequired

# kind -> (公钥类型, 私钥类型)
_KINDS = {
    "RSA": (rsa.RSAPublicKey, rsa.RSAPrivateKey),
    "ECC": (ec.EllipticCurvePublicKey, ec.EllipticCurvePrivateKey),
}


def is_encrypted_pem(pem: str) -> bool:
    return "ENCRYPTED" in pem


def load_public_key(pem: str, kind: str):
    if not pem.strip():
        raise CryptoError("请先提供公钥（生成、导入或粘贴 PEM）")
    try:
        key = serialization.load_pem_public_key(pem.strip().encode())
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise CryptoError("无法解析公钥，请检查 PEM 格式") from None
    if not isinstance(key, _KINDS[kind][0]):
        raise CryptoError(f"这不是 {kind} 公钥，请确认密钥类型")
    return key


def load_private_key(pem: str, password: str | None, kind: str):
    if not pem.strip():
        raise CryptoError("请先提供私钥（生成、导入或粘贴 PEM）")
    data = pem.strip().encode()
    secret = password.encode() if password else None
    try:
        key = serialization.load_pem_private_key(data, secret)
    except TypeError:
        # 两种情况：密钥已加密但没给密码；或者给了密码但密钥没加密
        if secret is None:
            raise PasswordRequired("私钥已加密，需要输入私钥密码") from None
        key = _load_unencrypted(data)
    except (ValueError, UnsupportedAlgorithm):
        if secret is not None and is_encrypted_pem(pem):
            raise CryptoError("私钥密码错误，或私钥已损坏") from None
        raise CryptoError("无法解析私钥，请检查 PEM 格式") from None
    if not isinstance(key, _KINDS[kind][1]):
        raise CryptoError(f"这不是 {kind} 私钥，请确认密钥类型")
    return key


def _load_unencrypted(data: bytes):
    try:
        return serialization.load_pem_private_key(data, None)
    except (ValueError, TypeError, UnsupportedAlgorithm):
        raise CryptoError("无法解析私钥，请检查 PEM 格式") from None


def private_to_pem(key, password: str | None = None) -> str:
    encryption = (
        serialization.BestAvailableEncryption(password.encode())
        if password
        else serialization.NoEncryption()
    )
    return key.private_bytes(
        serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, encryption
    ).decode("ascii")


def public_to_pem(key) -> str:
    return key.public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("ascii")


def protect_private_pem(pem: str, password: str | None, kind: str) -> str:
    """把未加密的私钥重新序列化；password 为空时保持不加密。"""
    return private_to_pem(load_private_key(pem, None, kind), password or None)


def unlock_private_pem(pem: str, password: str, kind: str) -> str:
    """用密码解开加密私钥，返回未加密的 PKCS8 PEM。"""
    return private_to_pem(load_private_key(pem, password, kind))
