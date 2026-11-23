"""页面基类：统一的页头、边距、后台任务和提示信号。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget

from crypto_core.common import CryptoError

from ..widgets import PageHeader
from ..worker import TaskRunner


class BasePage(QWidget):
    notify = pyqtSignal(str, str)  # (文字, "success" | "error" | "info")

    def __init__(self, title: str, subtitle: str, tags=()):
        super().__init__()
        self.setObjectName("pageBody")
        self.setAttribute(Qt.WA_StyledBackground)
        self._runner = TaskRunner(self)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(36, 26, 36, 24)
        self._layout.setSpacing(16)
        self._layout.addWidget(PageHeader(title, subtitle, tags))

    def add(self, widget: QWidget, stretch: int = 0) -> None:
        self._layout.addWidget(widget, stretch)

    def run(self, fn, *args, on_success, busy=(), on_error=None, busy_text="处理中…"):
        self._runner.run(
            fn, *args,
            on_success=on_success,
            on_error=on_error or self.show_error,
            busy=busy,
            busy_text=busy_text,
        )

    def show_error(self, exc: Exception) -> None:
        message = str(exc) if isinstance(exc, CryptoError) else f"发生意外错误：{exc}"
        self.notify.emit(message, "error")

    def success(self, message: str) -> None:
        self.notify.emit(message, "success")

    def info(self, message: str) -> None:
        self.notify.emit(message, "info")
