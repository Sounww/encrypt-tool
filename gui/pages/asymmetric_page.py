"""RSA 与 ECC 共用的公钥加密页面。cipher 模块需要提供：
NAME, KEY_OPTIONS, DEFAULT_OPTION, generate_keypair(option), encrypt(text, pub), decrypt(token, priv, password)。
"""

import base64
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFileDialog, QHBoxLayout

from crypto_core import keys
from crypto_core.common import CryptoError, PasswordRequired, PrivateKeyGiven

from ..widgets import (
    Card,
    IOPanel,
    TextPanel,
    ask_password,
    field_label,
    make_button,
    mini_button,
)
from .base import BasePage

_KEY_FILTER = "密钥 / 证书 (*.pem *.key *.pub *.der *.cer *.crt *.txt);;所有文件 (*)"


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

        self.derive_pub_btn = mini_button("由私钥生成")
        self.derive_pub_btn.setToolTip("根据右侧私钥计算出对应的公钥")
        self.import_pub_btn, self.export_pub_btn = mini_button("导入"), mini_button("导出")
        self.import_priv_btn, self.export_priv_btn = mini_button("导入"), mini_button("导出")
        self.public_panel = TextPanel(
            "公钥 PEM", "生成、导入或粘贴公钥", mono=True, pem=True, copyable=True,
            min_height=130, actions=(self.derive_pub_btn, self.import_pub_btn, self.export_pub_btn),
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
        self.io = IOPanel("公钥加密", "私钥解密", "输入要加密的明文，或粘贴要解密的 Base64 密文", min_height=84)
        work.body.addWidget(self.io, 1)
        self.add(work, 1)

        self.input_panel, self.output_panel = self.io.input_panel, self.io.output_panel
        self.encrypt_btn, self.decrypt_btn = self.io.primary_btn, self.io.secondary_btn
        self.swap_btn, self.clear_btn = self.io.swap_btn, self.io.clear_btn

        self.generate_btn.clicked.connect(self._generate)
        self.derive_pub_btn.clicked.connect(self._derive_public)
        self.import_pub_btn.clicked.connect(self._import_public)
        self.export_pub_btn.clicked.connect(self._export_public)
        self.import_priv_btn.clicked.connect(self._import_private)
        self.export_priv_btn.clicked.connect(self._export_private)
        self.encrypt_btn.clicked.connect(self._encrypt)
        self.decrypt_btn.clicked.connect(lambda: self._decrypt())

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

    def _with_private_password(self, fn):
        """调用 fn(password)；私钥加密时弹框要密码。用户取消返回 None，其余错误照常抛出。"""
        try:
            return fn(None)
        except PasswordRequired:
            password = ask_password(self, "私钥已加密", "请输入私钥密码：")
            if password is None:
                return None
            return fn(password)

    def _derive_public(self):
        private_text = self.private_panel.text()
        try:
            pem = self._with_private_password(
                lambda pw: keys.public_pem_from_private(private_text, pw, self.kind)
            )
        except CryptoError as exc:
            self.show_error(exc)
            return
        if pem is not None:
            self.public_panel.set_text(pem.strip())
            self.success("已根据私钥生成公钥")

    def _import_public(self):
        text = self._read_key_file("导入公钥")
        if text is None:
            return
        try:
            pem = keys.normalize_public_pem(text, self.kind)
            message = "公钥已导入"
        except PrivateKeyGiven:
            # 选中的是私钥文件：直接从私钥中提取公钥
            try:
                pem = self._with_private_password(
                    lambda pw: keys.public_pem_from_private(text, pw, self.kind)
                )
            except CryptoError as exc:
                self.show_error(exc)
                return
            if pem is None:
                return
            message = "选中的是私钥文件，已从中提取公钥"
        except CryptoError as exc:
            self.show_error(exc)
            return
        self.public_panel.set_text(pem.strip())
        self.success(message)

    def _import_private(self):
        text = self._read_key_file("导入私钥")
        if text is None:
            return
        try:
            pem = keys.unlock_private_pem(text, None, self.kind)
        except PasswordRequired:
            password = ask_password(self, "私钥已加密", "请输入私钥密码：")
            if password is None:
                self.private_panel.set_text(text.strip())
                self.info("已导入加密私钥，解密时需要输入密码")
                return
            try:
                pem = keys.unlock_private_pem(text, password, self.kind)
            except CryptoError as exc:
                self.show_error(exc)
                return
        except CryptoError as exc:
            self.show_error(exc)
            return
        self.private_panel.set_text(pem.strip())
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

    def _read_key_file(self, title: str) -> str | None:
        """读取密钥文件。文本文件按 UTF-8 读（自动去掉 BOM）；二进制 DER 文件转成 Base64 文本交给 keys 识别。"""
        path, _ = QFileDialog.getOpenFileName(self, title, "", _KEY_FILTER)
        if not path:
            return None
        try:
            raw = Path(path).read_bytes()
        except OSError as exc:
            self.show_error(CryptoError(f"读取文件失败：{exc}"))
            return None
        try:
            return raw.decode("utf-8-sig")
        except UnicodeDecodeError:
            return base64.b64encode(raw).decode("ascii")

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
    def _show_result(self, message):
        def handler(text):
            self.output_panel.set_text(text)
            self.success(message)
        return handler

    def _encrypt(self):
        self.run(
            self.cipher.encrypt, self.input_panel.text(), self.public_panel.text(),
            on_success=self._show_result("加密完成"), busy=self.io.busy_buttons(self.encrypt_btn),
        )

    def _decrypt(self, password: str | None = None):
        self.run(
            self.cipher.decrypt, self.input_panel.text(), self.private_panel.text(), password,
            on_success=self._show_result("解密完成"),
            on_error=self._on_decrypt_error,
            busy=self.io.busy_buttons(self.decrypt_btn),
        )

    def _on_decrypt_error(self, exc):
        if isinstance(exc, PasswordRequired):
            password = ask_password(self, "私钥已加密", "请输入私钥密码：")
            if password:
                self._decrypt(password)
            return
        self.show_error(exc)
