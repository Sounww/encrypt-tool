import struct

from tools import make_icon

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_render_png_returns_png_bytes():
    assert make_icon.render_png(32).startswith(PNG_SIGNATURE)


def test_build_ico_writes_directory_pointing_at_each_image():
    images = {16: b"a" * 10, 256: b"b" * 20}
    ico = make_icon.build_ico(images)

    reserved, kind, count = struct.unpack_from("<HHH", ico, 0)
    assert (reserved, kind, count) == (0, 1, 2)

    entries = [struct.unpack_from("<BBBBHHII", ico, 6 + 16 * i) for i in range(count)]
    width16, _, _, _, _, bpp, size16, offset16 = entries[0]
    width256, _, _, _, _, _, size256, offset256 = entries[1]
    assert (width16, bpp, size16) == (16, 32, 10)
    assert width256 == 0  # ICO 规定 256 写成 0
    assert ico[offset16:offset16 + size16] == b"a" * 10
    assert ico[offset256:offset256 + size256] == b"b" * 20


def test_main_writes_ico_file(tmp_path):
    target = tmp_path / "nested" / "app.ico"
    make_icon.main([str(target)])
    data = target.read_bytes()
    assert struct.unpack_from("<HHH", data, 0) == (0, 1, len(make_icon.SIZES))
