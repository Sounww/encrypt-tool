from crypto_core import aes_cipher

from ..widgets import Card, PasswordInput, TextPanel, button_row, make_button
from .base import BasePage


class AesPage(BasePage):
    def __init__(self):
        super().__init__(
            "AES 对称加密",
            "加密和解密使用同一个密码。密码经 Scrypt 强化后生成 256 位密钥，密文自带防篡改校验。",
            ["AES-256-GCM", "Scrypt", "对称加密"],
        )

        key_card = Card("密码", "解密时必须输入同一个密码")
        self.password = PasswordInput("输入加密 / 解密密码")
        key_card.body.addWidget(self.password)
        self.add(key_card)

        work = Card("加解密")
        self.input_panel = TextPanel("输入", "输入要加密的明文，或粘贴要解密的 Base64 密文", min_height=120)
        self.output_panel = TextPanel(
            "输出", "结果会显示在这里", mono=True, read_only=True, copyable=True, min_height=120
        )
        self.encrypt_btn = make_button("加密")
        self.decrypt_btn = make_button("解密", "secondary")
        self.swap_btn = make_button("⇅  输出转为输入", "ghost")
        self.clear_btn = make_button("清空", "ghost")
        work.body.addWidget(self.input_panel, 1)
        work.body.addLayout(button_row(self.encrypt_btn, self.decrypt_btn, None, self.swap_btn, self.clear_btn))
        work.body.addWidget(self.output_panel, 1)
        self.add(work, 1)

        self.encrypt_btn.clicked.connect(self._encrypt)
        self.decrypt_btn.clicked.connect(self._decrypt)
        self.swap_btn.clicked.connect(self._swap)
        self.clear_btn.clicked.connect(self._clear)

    def _buttons(self, first):
        others = [b for b in (self.encrypt_btn, self.decrypt_btn, self.swap_btn, self.clear_btn) if b is not first]
        return (first, *others)

    def _show_result(self, message):
        def handler(text):
            self.output_panel.set_text(text)
            self.success(message)
        return handler

    def _encrypt(self):
        self.run(
            aes_cipher.encrypt, self.input_panel.text(), self.password.text(),
            on_success=self._show_result("加密完成"), busy=self._buttons(self.encrypt_btn),
        )

    def _decrypt(self):
        self.run(
            aes_cipher.decrypt, self.input_panel.text(), self.password.text(),
            on_success=self._show_result("解密完成"), busy=self._buttons(self.decrypt_btn),
        )

    def _swap(self):
        self.input_panel.set_text(self.output_panel.text())
        self.output_panel.clear()

    def _clear(self):
        self.input_panel.clear()
        self.output_panel.clear()
