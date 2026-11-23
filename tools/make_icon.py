"""生成 exe 用的多尺寸 .ico 图标，复用界面里的 Logo 绘制代码，不依赖 Pillow。

用法：python tools/make_icon.py [输出路径，默认 build/app.ico]
"""

import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtCore import QBuffer, QByteArray, QIODevice, Qt  # noqa: E402
from PyQt5.QtGui import QGuiApplication, QImage, QPainter  # noqa: E402

from gui.widgets import paint_logo  # noqa: E402

SIZES = (16, 24, 32, 48, 64, 128, 256)


def render_png(size: int) -> bytes:
    image = QImage(size, size, QImage.Format_ARGB32)
    image.fill(Qt.transparent)
    painter = QPainter(image)
    paint_logo(painter, size)
    painter.end()
    data = QByteArray()
    buffer = QBuffer(data)
    buffer.open(QIODevice.WriteOnly)
    image.save(buffer, "PNG")
    buffer.close()
    return bytes(data)


def build_ico(images: dict[int, bytes]) -> bytes:
    """images: {边长: PNG 数据}。ICO = 文件头 + 每张图 16 字节目录项 + 图像数据。"""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    entries, blobs = b"", b""
    for size, png in images.items():
        dim = 0 if size >= 256 else size
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    return header + entries + blobs


def main(argv=None) -> None:
    argv = sys.argv[1:] if argv is None else argv
    target = Path(argv[0]) if argv else Path("build/app.ico")
    _app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])  # noqa: F841
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(build_ico({size: render_png(size) for size in SIZES}))
    print(f"图标已生成：{target}")


if __name__ == "__main__":
    main()
