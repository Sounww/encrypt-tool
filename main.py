"""CipherBox 加密工具箱 —— 程序入口。"""

import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import QApplication


def _enable_high_dpi() -> None:
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(QGuiApplication, "setHighDpiScaleFactorRoundingPolicy"):
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )


def _set_windows_app_id() -> None:
    """让 Windows 任务栏显示本程序的图标，而不是 python.exe 的图标。"""
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("CipherBox.EncryptTool")
        except (AttributeError, OSError):
            pass


def main() -> int:
    _enable_high_dpi()
    _set_windows_app_id()
    app = QApplication(sys.argv)

    from gui.main_window import MainWindow
    from gui.theme import apply_theme

    apply_theme(app)
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
