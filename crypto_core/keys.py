"""RSA / ECC 共用的密钥识别、加载与序列化。

公钥支持：PEM（SPKI / PKCS#1）、OpenSSH 单行格式、X.509 证书（PEM / DER）、无头尾的 Base64（DER）。
私钥支持：PEM（PKCS#8 / 传统格式，可加密）、OpenSSH 私钥（可加密）、无头尾的 Base64（DER）。
"""

import base64
import binascii
import re

from cryptography import x509
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from .common import CryptoError, PasswordRequired, PrivateKeyGiven

# kind -> (公钥类型, 私钥类型)
_KINDS = {
    "RSA": (rsa.RSAPublicKey, rsa.RSAPrivateKey),
    "ECC": (ec.EllipticCurvePublicKey, ec.EllipticCurvePrivateKey),
}
_PARSE_ERRORS = (ValueError, TypeError, UnsupportedAlgorithm)
_SSH_PUBLIC_PREFIX = re.compile(r"^(ssh-|ecdsa-sha2-|sk-)")
_PUBLIC_FORMATS = "支持 PEM、OpenSSH、X.509 证书或 Base64 格式"
_PRIVATE_FORMATS = "支持 PEM、OpenSSH 私钥或 Base64 格式"
_PRIVATE_NOT_PUBLIC = "这是私钥而不是公钥，请使用「由私钥生成」获取公钥"


def is_encrypted_pem(pem: str) -> bool:
    return "ENCRYPTED" in pem


def _clean(text: str) -> str:
    return text.replace("﻿", "").strip()


def _b64_or_none(text: str) -> bytes | None:
    compact = "".join(text.split())
    if not compact:
        return None
    try:
        return base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        return None


def _is_der_private_key(der: bytes) -> bool:
    try:
        serialization.load_der_private_key(der, None)
    except TypeError:
        return True  # 已加密的私钥
    except (ValueError, UnsupportedAlgorithm):
        return False
    return True


# ---------- 公钥 ----------

def _parse_public(text: str):
    if "PRIVATE KEY" in text:
        raise PrivateKeyGiven(_PRIVATE_NOT_PUBLIC)
    try:
        if "BEGIN CERTIFICATE" in text:
            return x509.load_pem_x509_certificate(text.encode()).public_key()
        if "-----BEGIN" in text:
            return serialization.load_pem_public_key(text.encode())
        if _SSH_PUBLIC_PREFIX.match(text):
            return serialization.load_ssh_public_key(text.encode())
    except _PARSE_ERRORS:
        raise CryptoError(f"无法解析公钥，{_PUBLIC_FORMATS}") from None

    der = _b64_or_none(text)
    if der is not None:
        try:
            return serialization.load_der_public_key(der)
        except _PARSE_ERRORS:
            pass
        try:
            return x509.load_der_x509_certificate(der).public_key()
        except _PARSE_ERRORS:
            pass
        if _is_der_private_key(der):
            raise PrivateKeyGiven(_PRIVATE_NOT_PUBLIC)
    raise CryptoError(f"无法识别的公钥格式，{_PUBLIC_FORMATS}")


def load_public_key(text: str, kind: str):
    cleaned = _clean(text)
    if not cleaned:
        raise CryptoError("请先提供公钥（生成、导入或粘贴）")
    key = _parse_public(cleaned)
    if not isinstance(key, _KINDS[kind][0]):
        raise CryptoError(f"这不是 {kind} 公钥，请确认密钥类型")
    return key


def normalize_public_pem(text: str, kind: str) -> str:
    """识别任意支持的公钥格式，转换成标准 PEM（SubjectPublicKeyInfo）。"""
    return public_to_pem(load_public_key(text, kind))


# ---------- 私钥 ----------

def _private_source(text: str):
    """返回 (加载函数, 数据)。"""
    if "OPENSSH PRIVATE KEY" in text:
        return serialization.load_ssh_private_key, text.encode()
    if "PRIVATE KEY" in text:
        return serialization.load_pem_private_key, text.encode()
    if "PUBLIC KEY" in text or "BEGIN CERTIFICATE" in text or _SSH_PUBLIC_PREFIX.match(text):
        raise CryptoError("这是公钥而不是私钥，解密需要私钥")
    if "-----BEGIN" in text:
        raise CryptoError(f"无法解析私钥，{_PRIVATE_FORMATS}")
    der = _b64_or_none(text)
    if der is None:
        raise CryptoError(f"无法识别的私钥格式，{_PRIVATE_FORMATS}")
    return serialization.load_der_private_key, der


def load_private_key(text: str, password: str | None, kind: str):
    cleaned = _clean(text)
    if not cleaned:
        raise CryptoError("请先提供私钥（生成、导入或粘贴）")
    loader, data = _private_source(cleaned)
    secret = password.encode() if password else None
    try:
        key = loader(data, secret)
    except TypeError:
        # 两种情况：私钥已加密但没给密码；或者给了密码但私钥没加密
        if secret is None:
            raise PasswordRequired("私钥已加密，需要输入私钥密码") from None
        key = _load_without_password(loader, data)
    except (ValueError, UnsupportedAlgorithm):
        if secret is not None:
            raise CryptoError("私钥密码错误，或私钥已损坏") from None
        raise CryptoError(f"无法解析私钥，{_PRIVATE_FORMATS}") from None
    if not isinstance(key, _KINDS[kind][1]):
        raise CryptoError(f"这不是 {kind} 私钥，请确认密钥类型")
    return key


def _load_without_password(loader, data: bytes):
    try:
        return loader(data, None)
    except _PARSE_ERRORS:
        raise CryptoError(f"无法解析私钥，{_PRIVATE_FORMATS}") from None


# ---------- 序列化 ----------

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


def unlock_private_pem(text: str, password: str | None, kind: str) -> str:
    """识别任意支持的私钥格式（必要时用密码解开），返回未加密的 PKCS#8 PEM。"""
    return private_to_pem(load_private_key(text, password, kind))


def public_pem_from_private(text: str, password: str | None, kind: str) -> str:
    """由私钥推导出对应的公钥（标准 PEM）。"""
    return public_to_pem(load_private_key(text, password, kind).public_key())
