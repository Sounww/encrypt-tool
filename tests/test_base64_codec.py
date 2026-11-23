import base64

import pytest

from crypto_core import base64_codec
from crypto_core.common import CryptoError


def test_encode_matches_known_value():
    assert base64_codec.encode("hello") == "aGVsbG8="


def test_encode_uses_utf8_by_default():
    assert base64_codec.encode("中文") == base64.b64encode("中文".encode("utf-8")).decode()


def test_encode_url_safe_replaces_plus_and_slash():
    assert base64_codec.encode("~~~") == "fn5+"
    assert base64_codec.encode("~~~", url_safe=True) == "fn5-"
    assert base64_codec.encode("???", url_safe=True) == "Pz8_"


def test_encode_gbk():
    assert base64_codec.encode("中文", charset="GBK") == "1tDOxA=="


def test_encode_reports_characters_charset_cannot_represent():
    with pytest.raises(CryptoError, match="GBK"):
        base64_codec.encode("🔐", charset="GBK")


def test_encode_rejects_empty_input():
    with pytest.raises(CryptoError, match="内容"):
        base64_codec.encode("")


def test_decode_round_trip():
    assert base64_codec.decode(base64_codec.encode("你好, Base64!")) == "你好, Base64!"


def test_decode_accepts_url_safe_alphabet():
    assert base64_codec.decode("Pz8_") == "???"


def test_decode_accepts_missing_padding():
    assert base64_codec.decode("aGVsbG8") == "hello"


def test_decode_ignores_whitespace_and_newlines():
    assert base64_codec.decode("  aGVs\r\nbG8=\n") == "hello"


def test_decode_gbk():
    assert base64_codec.decode("1tDOxA==", charset="GBK") == "中文"


@pytest.mark.parametrize("bad", ["abc$", "aGVsb", "a=bc"])
def test_decode_rejects_invalid_base64(bad):
    with pytest.raises(CryptoError, match="Base64"):
        base64_codec.decode(bad)


def test_decode_reports_non_text_result():
    with pytest.raises(CryptoError, match="UTF-8"):
        base64_codec.decode("//4=")  # 0xFF 0xFE


def test_decode_rejects_empty_input():
    with pytest.raises(CryptoError):
        base64_codec.decode("   ")


def test_charsets_offered():
    assert base64_codec.CHARSETS == ["UTF-8", "GBK"]
