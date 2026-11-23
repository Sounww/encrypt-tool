from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QCheckBox, QComboBox, QLabel

from crypto_core import base64_codec
from crypto_core.common import CryptoError

from ..widgets import Card, IOPanel, field_label
from .base import BasePage


class Base64Page(BasePage):
    def __init__(self):
        super().__init__(
            "Base64 编码",
            "把文本转换成只由字母、数字和 + / 组成的字符串，便于放进网址、配置文件或接口参数中传输。",
            ["Base64", "RFC 4648", "可逆编码"],
        )

        self.url_safe_check = QCheckBox("URL 安全（- _ 代替 + /）")
        self.url_safe_check.setCursor(Qt.PointingHandCursor)
        self.charset_combo = QComboBox()
        self.charset_combo.addItems(base64_codec.CHARSETS)
        self.charset_combo.setCursor(Qt.PointingHandCursor)

        work = Card(
            "编解码",
            header_widgets=(self.url_safe_check, field_label("字符编码"), self.charset_combo),
        )
        self.io = IOPanel("编码", "解码", "输入要编码的文本，或粘贴要解码的 Base64", min_height=120)
        work.body.addWidget(self.io, 1)
        self.add(work, 1)

        tip = Card("说明")
        tip_text = QLabel(
            "Base64 只是编码，不是加密：任何人都能把它还原成原文，不要用它保护密码或隐私数据，"
            "需要保密请使用 AES / RSA / ECC。\n"
            "解码时会自动识别标准和 URL 安全两种写法，缺少末尾的 = 或夹杂换行也能正常解码。"
        )
        tip_text.setObjectName("cardHint")
        tip_text.setWordWrap(True)
        tip.body.addWidget(tip_text)
        self.add(tip)

        self.input_panel, self.output_panel = self.io.input_panel, self.io.output_panel
        self.encode_btn, self.decode_btn = self.io.primary_btn, self.io.secondary_btn
        self.swap_btn, self.clear_btn = self.io.swap_btn, self.io.clear_btn

        self.encode_btn.clicked.connect(self._encode)
        self.decode_btn.clicked.connect(self._decode)

    def _encode(self):
        self._apply(
            lambda text: base64_codec.encode(
                text, self.url_safe_check.isChecked(), self.charset_combo.currentText()
            ),
            "编码完成",
        )

    def _decode(self):
        self._apply(lambda text: base64_codec.decode(text, self.charset_combo.currentText()), "解码完成")

    def _apply(self, fn, message: str) -> None:
        """Base64 运算很快，直接在界面线程执行。"""
        try:
            result = fn(self.input_panel.text())
        except CryptoError as exc:
            self.show_error(exc)
            return
        self.output_panel.set_text(result)
        self.success(message)
