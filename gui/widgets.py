"""可复用的界面组件。样式全部在 theme.build_qss() 里，这里只设置 objectName / 属性。"""

from PyQt5.QtCore import QEasingCurve, QEvent, QPointF, QPropertyAnimation, QRectF, QSize, Qt, QTimer
from PyQt5.QtGui import QColor, QIcon, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QTextOption
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from . import theme


def set_prop(widget: QWidget, name: str, value) -> None:
    """修改动态属性后重新套用样式，让 QSS 里的 [prop="..."] 选择器生效。"""
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def make_button(text: str, variant: str = "primary") -> QPushButton:
    button = QPushButton(text)
    button.setProperty("variant", variant)
    button.setCursor(Qt.PointingHandCursor)
    return button


def button_row(*items) -> QHBoxLayout:
    """None 表示在该位置插入弹性空白。"""
    row = QHBoxLayout()
    row.setSpacing(10)
    for item in items:
        if item is None:
            row.addStretch(1)
        else:
            row.addWidget(item)
    return row


def field_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("fieldLabel")
    return label


def labeled(text: str, widget: QWidget) -> QWidget:
    box = QWidget()
    layout = QVBoxLayout(box)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(6)
    layout.addWidget(field_label(text))
    layout.addWidget(widget)
    return box


def ask_password(parent: QWidget, title: str, label: str) -> str | None:
    text, ok = QInputDialog.getText(parent, title, label, QLineEdit.Password)
    return text if ok else None


class Card(QFrame):
    def __init__(self, title: str = "", hint: str = "", header_widgets=()):
        """header_widgets 会放在标题行右侧。"""
        super().__init__()
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(22, 18, 22, 20)
        self.body.setSpacing(12)
        if title:
            header = QHBoxLayout()
            header.setSpacing(10)
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            header.addWidget(title_label)
            if hint:
                hint_label = QLabel(hint)
                hint_label.setObjectName("cardHint")
                header.addWidget(hint_label)
            header.addStretch(1)
            for widget in header_widgets:
                header.addWidget(widget)
            self.body.addLayout(header)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(30, 36, 51, 18))
        self.setGraphicsEffect(shadow)


class PageHeader(QWidget):
    def __init__(self, title: str, subtitle: str, tags=()):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 0, 0, 2)
        layout.setSpacing(6)

        row = QHBoxLayout()
        row.setSpacing(8)
        title_label = QLabel(title)
        title_label.setObjectName("pageTitle")
        row.addWidget(title_label)
        row.addSpacing(6)
        for tag in tags:
            tag_label = QLabel(tag)
            tag_label.setProperty("role", "tag")
            row.addWidget(tag_label, 0, Qt.AlignVCenter)
        row.addStretch(1)
        layout.addLayout(row)

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("pageSubtitle")
        subtitle_label.setWordWrap(True)
        layout.addWidget(subtitle_label)


class PasswordInput(QLineEdit):
    """密码框，右侧内嵌「显示 / 隐藏」切换按钮。"""

    def __init__(self, placeholder: str = ""):
        super().__init__()
        self.setEchoMode(QLineEdit.Password)
        self.setPlaceholderText(placeholder)
        self._toggle = QPushButton(self)
        self._toggle.setObjectName("pwToggle")
        self._toggle.setText("显示")
        self._toggle.setCursor(Qt.PointingHandCursor)
        self._toggle.setFocusPolicy(Qt.NoFocus)
        self._toggle.clicked.connect(self._toggle_echo)
        self.setTextMargins(0, 0, 44, 0)

    def _toggle_echo(self):
        hidden = self.echoMode() == QLineEdit.Password
        self.setEchoMode(QLineEdit.Normal if hidden else QLineEdit.Password)
        self._toggle.setText("隐藏" if hidden else "显示")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        size = self._toggle.sizeHint()
        self._toggle.setGeometry(
            self.width() - size.width() - 8,
            (self.height() - size.height()) // 2,
            size.width(),
            size.height(),
        )


class CopyButton(QPushButton):
    def __init__(self, getter):
        super().__init__("复制")
        self.setProperty("variant", "mini")
        self.setCursor(Qt.PointingHandCursor)
        self._getter = getter
        self._reset_timer = QTimer(self)
        self._reset_timer.setSingleShot(True)
        self._reset_timer.setInterval(1200)
        self._reset_timer.timeout.connect(lambda: self.setText("复制"))
        self.clicked.connect(self._copy)

    def _copy(self):
        text = self._getter()
        if text:
            QApplication.clipboard().setText(text)
            self.setText("已复制")
        else:
            self.setText("无内容")
        self._reset_timer.start()


def mini_button(text: str) -> QPushButton:
    return make_button(text, "mini")


class _CompactTextEdit(QPlainTextEdit):
    """建议高度等于最小高度。否则 QScrollArea 会按默认 192px 的建议高度排版，导致多余的滚动条。"""

    def sizeHint(self):
        return QSize(super().sizeHint().width(), self.minimumHeight())


class TextPanel(QWidget):
    """带标题的多行文本框；标题行右侧可放操作按钮和复制按钮。"""

    def __init__(
        self,
        label: str,
        placeholder: str = "",
        *,
        mono: bool = False,
        read_only: bool = False,
        copyable: bool = False,
        pem: bool = False,
        min_height: int = 110,
        actions=(),
    ):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 0, 0)
        header.setSpacing(2)
        header.addWidget(field_label(label))
        header.addStretch(1)
        for action in actions:
            header.addWidget(action)

        self.edit = _CompactTextEdit()
        self.edit.setPlaceholderText(placeholder)
        self.edit.setReadOnly(read_only)
        self.edit.setTabChangesFocus(True)
        self.edit.setMinimumHeight(min_height)
        self.edit.setProperty("mono", mono)
        self.edit.setProperty("pem", pem)
        if mono:
            self.edit.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        if copyable:
            header.addWidget(CopyButton(self.text))

        layout.addLayout(header)
        layout.addWidget(self.edit, 1)

    def text(self) -> str:
        return self.edit.toPlainText()

    def set_text(self, text: str) -> None:
        self.edit.setPlainText(text)

    def clear(self) -> None:
        self.edit.clear()


class OutputLine(QWidget):
    """单行只读等宽输出框 + 复制按钮。"""

    def __init__(self, placeholder: str = ""):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self.edit = QLineEdit()
        self.edit.setReadOnly(True)
        self.edit.setProperty("mono", True)
        self.edit.setPlaceholderText(placeholder)
        layout.addWidget(self.edit, 1)
        layout.addWidget(CopyButton(self.text))

    def text(self) -> str:
        return self.edit.text()

    def set_text(self, text: str) -> None:
        self.edit.setText(text)
        self.edit.setCursorPosition(0)


class Toast(QLabel):
    """父窗口右上角的浮动提示，自动淡出。"""

    _ICONS = {"success": "✓", "error": "✕", "info": "•"}

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.hide()
        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(0.0)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)
        self._anim.finished.connect(self._on_anim_finished)
        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)
        parent.installEventFilter(self)

    def show_message(self, text: str, kind: str = "info") -> None:
        if len(text) > 80:
            text = text[:77] + "…"
        self.setText(f"{self._ICONS.get(kind, '•')}  {text}")
        set_prop(self, "kind", kind)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()
        self._animate_to(1.0)
        self._hide_timer.start(4000 if kind == "error" else 2600)

    def reposition(self) -> None:
        parent = self.parentWidget()
        self.move(parent.width() - self.width() - 24, 20)

    def eventFilter(self, obj, event):
        if obj is self.parentWidget() and event.type() == QEvent.Resize and self.isVisible():
            self.reposition()
        return False

    def _animate_to(self, value: float) -> None:
        self._anim.stop()
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(value)
        self._anim.start()

    def _fade_out(self) -> None:
        self._animate_to(0.0)

    def _on_anim_finished(self) -> None:
        if self._effect.opacity() < 0.01:
            self.hide()


def paint_logo(painter: QPainter, size: float) -> None:
    painter.setRenderHint(QPainter.Antialiasing)
    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0, QColor("#5C7CFA"))
    gradient.setColorAt(1, QColor(theme.PRIMARY_PRESSED))
    painter.setPen(Qt.NoPen)
    painter.setBrush(gradient)
    painter.drawRoundedRect(QRectF(0, 0, size, size), size * 0.28, size * 0.28)

    # 锁梁
    pen = QPen(QColor("white"))
    pen.setWidthF(size * 0.085)
    pen.setCapStyle(Qt.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    shackle_w = size * 0.30
    shackle_x = (size - shackle_w) / 2
    shackle_y = size * 0.20
    path = QPainterPath()
    path.moveTo(shackle_x, size * 0.48)
    path.lineTo(shackle_x, shackle_y + shackle_w / 2)
    path.arcTo(QRectF(shackle_x, shackle_y, shackle_w, shackle_w), 180, -180)
    path.lineTo(shackle_x + shackle_w, size * 0.48)
    painter.drawPath(path)

    # 锁身 + 锁孔
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor("white"))
    body_w, body_h, body_y = size * 0.48, size * 0.34, size * 0.44
    painter.drawRoundedRect(QRectF((size - body_w) / 2, body_y, body_w, body_h), size * 0.07, size * 0.07)
    painter.setBrush(QColor(theme.PRIMARY))
    painter.drawEllipse(QPointF(size / 2, body_y + body_h * 0.45), size * 0.05, size * 0.05)


def make_logo_pixmap(size: int, device_ratio: float = 3.0) -> QPixmap:
    pixmap = QPixmap(int(size * device_ratio), int(size * device_ratio))
    pixmap.setDevicePixelRatio(device_ratio)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    paint_logo(painter, size)
    painter.end()
    return pixmap


def make_app_icon() -> QIcon:
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        paint_logo(painter, size)
        painter.end()
        icon.addPixmap(pixmap)
    return icon
