from PyQt5.QtWidgets import QCheckBox, QHBoxLayout, QLabel

from crypto_core import hashing

from ..widgets import Card, OutputLine, TextPanel, field_label
from .base import BasePage


class Sha256Page(BasePage):
    def __init__(self):
        super().__init__(
            "SHA-256 哈希",
            "单向摘要：相同输入永远得到相同结果，但无法从哈希值还原原文。常用于校验数据是否被改动。",
            ["SHA-256", "256 位摘要", "不可逆"],
        )

        card = Card("计算摘要", "输入内容后实时更新")
        self.input_panel = TextPanel("输入", "输入任意文本，哈希值会实时更新", min_height=200)

        out_header = QHBoxLayout()
        out_header.setContentsMargins(2, 0, 0, 0)
        out_header.addWidget(field_label("SHA-256（十六进制）"))
        out_header.addStretch(1)
        self.upper_check = QCheckBox("大写")
        out_header.addWidget(self.upper_check)

        self.output = OutputLine("哈希值会显示在这里")
        self.meta = QLabel()
        self.meta.setObjectName("metaText")

        card.body.addWidget(self.input_panel, 1)
        card.body.addSpacing(4)
        card.body.addLayout(out_header)
        card.body.addWidget(self.output)
        card.body.addWidget(self.meta)
        self.add(card, 1)

        tip = Card("说明")
        tip_text = QLabel(
            "SHA-256 不能「解密」。要验证一段文本是否和原文一致，"
            "对它重新计算哈希，再和原来的哈希值比对即可。\n"
            "注意：不要直接用 SHA-256 存储用户密码，存储密码请使用 bcrypt。"
        )
        tip_text.setObjectName("cardHint")
        tip_text.setWordWrap(True)
        tip.body.addWidget(tip_text)
        self.add(tip)

        self.input_panel.edit.textChanged.connect(self._update)
        self.upper_check.toggled.connect(self._update)
        self._update()

    def _update(self):
        text = self.input_panel.text()
        self.output.set_text(hashing.sha256_hex(text, self.upper_check.isChecked()) if text else "")
        self.meta.setText(f"{len(text)} 个字符 · {len(text.encode('utf-8'))} 字节（UTF-8）")
