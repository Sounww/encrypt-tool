"""Base64 编解码（RFC 4648）。注意：这是编码而不是加密，任何人都能还原。

解码比较宽松：同时接受标准和 URL 安全字母表，允许缺少末尾的 = 以及夹杂空白和换行。
"""

import base64
import binascii

from .common import CryptoError, require_text

CHARSETS = ["UTF-8", "GBK"]
_INVALID = "不是有效的 Base64 字符串"


def encode(text: str, url_safe: bool = False, charset: str = "UTF-8") -> str:
    require_text(text, "要编码的内容")
    try:
        data = text.encode(charset)
    except UnicodeEncodeError:
        raise CryptoError(f"文本中有 {charset} 无法表示的字符，请改用 UTF-8") from None
    encoded = base64.urlsafe_b64encode(data) if url_safe else base64.b64encode(data)
    return encoded.decode("ascii")


def decode(token: str, charset: str = "UTF-8") -> str:
    compact = "".join(token.split())
    require_text(compact, "要解码的 Base64 内容")
    compact = compact.replace("-", "+").replace("_", "/")
    if len(compact) % 4 == 1:
        raise CryptoError(f"{_INVALID}（长度不正确）")
    compact += "=" * (-len(compact) % 4)
    try:
        data = base64.b64decode(compact, validate=True)
    except (binascii.Error, ValueError):
        raise CryptoError(_INVALID) from None
    try:
        return data.decode(charset)
    except UnicodeDecodeError:
        raise CryptoError(f"解码结果不是有效的 {charset} 文本，可以尝试切换字符编码") from None
