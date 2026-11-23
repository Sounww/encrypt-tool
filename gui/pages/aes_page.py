from crypto_core import aes_cipher

from ..widgets import Card, IOPanel, PasswordInput
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
        self.io = IOPanel("加密", "解密", "输入要加密的明文，或粘贴要解密的 Base64 密文", min_height=120)
        work.body.addWidget(self.io, 1)
        self.add(work, 1)

        self.input_panel, self.output_panel = self.io.input_panel, self.io.output_panel
        self.encrypt_btn, self.decrypt_btn = self.io.primary_btn, self.io.secondary_btn
        self.swap_btn, self.clear_btn = self.io.swap_btn, self.io.clear_btn

        self.encrypt_btn.clicked.connect(self._encrypt)
        self.decrypt_btn.clicked.connect(self._decrypt)

    def _show_result(self, message):
        def handler(text):
            self.output_panel.set_text(text)
            self.success(message)
        return handler

    def _encrypt(self):
        self.run(
            aes_cipher.encrypt, self.input_panel.text(), self.password.text(),
            on_success=self._show_result("加密完成"), busy=self.io.busy_buttons(self.encrypt_btn),
        )

    def _decrypt(self):
        self.run(
            aes_cipher.decrypt, self.input_panel.text(), self.password.text(),
            on_success=self._show_result("解密完成"), busy=self.io.busy_buttons(self.decrypt_btn),
        )
