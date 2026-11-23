"""RSA 与 ECC 共用的公钥加密页面。cipher 模块需要提供：
NAME, KEY_OPTIONS, DEFAULT_OPTION, generate_keypair(option), encrypt(text, pub), decrypt(token, priv, password)。
"""

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFileDialog, QHBoxLayout

from crypto_core import keys
from crypto_core.common import CryptoError, PasswordRequired

from ..widgets import (
    Card,
    TextPanel,
    ask_password,
    button_row,
    field_label,
    make_button,
    mini_button,
)
from .base import BasePage

_PEM_FILTER = "PEM 密钥 (*.pem *.key *.pub);;所有文件 (*)"


class AsymmetricPage(BasePage):
    def __init__(self, cipher, title: str, subtitle: str, tags, option_label: str):
        super().__init__(title, subtitle, tags)
        self.cipher = cipher
        self.kind = cipher.NAME

        # ---------- 密钥卡片 ----------
        self.option_combo = QComboBox()
        self.option_combo.addItems(cipher.KEY_OPTIONS)
        self.option_combo.setCurrentText(cipher.DEFAULT_OPTION)
        self.option_combo.setCursor(Qt.PointingHandCursor)
        self.generate_btn = make_button("生成密钥对")
        key_card = Card(
            "密钥对", "公钥可公开，私钥请保管好",
            header_widgets=(field_label(option_label), self.option_combo, self.generate_btn),
        )

        self.import_pub_btn, self.export_pub_btn = mini_button("导入"), mini_button("导出")
        self.import_priv_btn, self.export_priv_btn = mini_button("导入"), mini_button("导出")
        self.public_panel = TextPanel(
            "公钥 PEM", "生成、导入或粘贴公钥", mono=True, pem=True, copyable=True,
            min_height=130, actions=(self.import_pub_btn, self.export_pub_btn),
        )
        self.private_panel = TextPanel(
            "私钥 PEM", "生成、导入或粘贴私钥", mono=True, pem=True, copyable=True,
            min_height=130, actions=(self.import_priv_btn, self.export_priv_btn),
        )
        pems = QHBoxLayout()
        pems.setSpacing(14)
        pems.addWidget(self.public_panel)
        pems.addWidget(self.private_panel)
        key_card.body.addLayout(pems)
        self.add(key_card)

        # ---------- 加解密卡片 ----------
        work = Card("加解密", "使用公钥加密，使用私钥解密")
        self.input_panel = TextPanel("输入", "输入要加密的明文，或粘贴要解密的 Base64 密文", min_height=84)
        self.output_panel = TextPanel(
            "输出", "结果会显示在这里", mono=True, read_only=True, copyable=True, min_height=84
        )
        self.encrypt_btn = make_button("公钥加密")
        self.decrypt_btn = make_button("私钥解密", "secondary")
        self.swap_btn = make_button("⇅  输出转为输入", "ghost")
        self.clear_btn = make_button("清空", "ghost")
        work.body.addWidget(self.input_panel, 1)
        work.body.addLayout(button_row(self.encrypt_btn, self.decrypt_btn, None, self.swap_btn, self.clear_btn))
        work.body.addWidget(self.output_panel, 1)
        self.add(work, 1)

        self.generate_btn.clicked.connect(self._generate)
        self.import_pub_btn.clicked.connect(self._import_public)
        self.export_pub_btn.clicked.connect(self._export_public)
        self.import_priv_btn.clicked.connect(self._import_private)
        self.export_priv_btn.clicked.connect(self._export_private)
        self.encrypt_btn.clicked.connect(self._encrypt)
        self.decrypt_btn.clicked.connect(lambda: self._decrypt())
        self.swap_btn.clicked.connect(self._swap)
        self.clear_btn.clicked.connect(self._clear)

    # ---------- 密钥 ----------
    def _generate(self):
        self.run(
            self.cipher.generate_keypair, self.option_combo.currentText(),
            on_success=self._on_keys, busy=(self.generate_btn,), busy_text="生成中…",
        )

    def _on_keys(self, pair):
        private_pem, public_pem = pair
        self.private_panel.set_text(private_pem.strip())
        self.public_panel.set_text(public_pem.strip())
        self.success(f"{self.kind} 密钥对已生成（{self.option_combo.currentText()}）")

    def _import_public(self):
        text = self._read_pem_file("导入公钥")
        if text is None:
            return
        try:
            keys.load_public_key(text, self.kind)
        except CryptoError as exc:
            self.show_error(exc)
            return
        self.public_panel.set_text(text.strip())
        self.success("公钥已导入")

    def _import_private(self):
        text = self._read_pem_file("导入私钥")
        if text is None:
            return
        try:
            if keys.is_encrypted_pem(text):
                password = ask_password(self, "私钥已加密", "请输入私钥密码：")
                if password is None:
                    self.private_panel.set_text(text.strip())
                    self.info("已导入加密私钥，解密时需要输入密码")
                    return
                text = keys.unlock_private_pem(text, password, self.kind)
            else:
                keys.load_private_key(text, None, self.kind)
        except CryptoError as exc:
            self.show_error(exc)
            return
        self.private_panel.set_text(text.strip())
        self.success("私钥已导入")

    def _export_public(self):
        pem = self.public_panel.text().strip()
        try:
            keys.load_public_key(pem, self.kind)
        except CryptoError as exc:
            self.show_error(exc)
            return
        self._save_pem_file("导出公钥", f"{self.kind.lower()}_public.pem", pem, "公钥已保存")

    def _export_private(self):
        pem = self.private_panel.text().strip()
        if not pem:
            self.show_error(CryptoError("没有可导出的私钥，请先生成或导入"))
            return
        if not keys.is_encrypted_pem(pem):
            password = ask_password(self, "保护私钥", "设置私钥保护密码（留空则不加密）：")
            if password is None:
                return
            if password:
                confirm = ask_password(self, "保护私钥", "再次输入密码确认：")
                if confirm is None:
                    return
                if confirm != password:
                    self.show_error(CryptoError("两次输入的密码不一致"))
                    return
            try:
                pem = keys.protect_private_pem(pem, password, self.kind).strip()
            except CryptoError as exc:
                self.show_error(exc)
                return
        self._save_pem_file("导出私钥", f"{self.kind.lower()}_private.pem", pem, "私钥已保存")

    def _read_pem_file(self, title: str) -> str | None:
        path, _ = QFileDialog.getOpenFileName(self, title, "", _PEM_FILTER)
        if not path:
            return None
        try:
            return Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            self.show_error(CryptoError(f"读取文件失败：{exc}"))
            return None

    def _save_pem_file(self, title: str, default_name: str, pem: str, message: str) -> None:
        path, _ = QFileDialog.getSaveFileName(self, title, default_name, "PEM 密钥 (*.pem);;所有文件 (*)")
        if not path:
            return
        try:
            Path(path).write_text(pem + "\n", encoding="utf-8")
        except OSError as exc:
            self.show_error(CryptoError(f"保存文件失败：{exc}"))
            return
        self.success(f"{message}：{Path(path).name}")

    # ---------- 加解密 ----------
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
            self.cipher.encrypt, self.input_panel.text(), self.public_panel.text(),
            on_success=self._show_result("加密完成"), busy=self._buttons(self.encrypt_btn),
        )

    def _decrypt(self, password: str | None = None):
        self.run(
            self.cipher.decrypt, self.input_panel.text(), self.private_panel.text(), password,
            on_success=self._show_result("解密完成"),
            on_error=self._on_decrypt_error,
            busy=self._buttons(self.decrypt_btn),
        )

    def _on_decrypt_error(self, exc):
        if isinstance(exc, PasswordRequired):
            password = ask_password(self, "私钥已加密", "请输入私钥密码：")
            if password:
                self._decrypt(password)
            return
        self.show_error(exc)

    def _swap(self):
        self.input_panel.set_text(self.output_panel.text())
        self.output_panel.clear()

    def _clear(self):
        self.input_panel.clear()
        self.output_panel.clear()
