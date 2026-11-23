import time

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSlider

from crypto_core import hashing

from ..widgets import (
    Card,
    OutputLine,
    PasswordInput,
    button_row,
    field_label,
    labeled,
    make_button,
    set_prop,
)
from .base import BasePage

_IDLE_TEXT = "输入密码和哈希后点击「验证」"


def _timed_hash(password: str, rounds: int):
    start = time.perf_counter()
    hashed = hashing.bcrypt_hash(password, rounds)
    return hashed, time.perf_counter() - start


class BcryptPage(BasePage):
    def __init__(self):
        super().__init__(
            "bcrypt 密码哈希",
            "专为存储密码设计的慢哈希：自带随机盐，同一密码每次结果都不同；cost 越高，暴力破解越困难。",
            ["bcrypt", "$2b$", "自动加盐"],
        )

        # ---------- 生成 ----------
        gen = Card("生成哈希", "同一密码每次生成的哈希都不同，这是正常的")
        self.hash_password = PasswordInput("输入要哈希的密码（最多 72 字节）")
        gen.body.addWidget(labeled("密码", self.hash_password))

        self.cost_slider = QSlider(Qt.Horizontal)
        self.cost_slider.setRange(hashing.BCRYPT_MIN_COST, hashing.BCRYPT_MAX_COST)
        self.cost_slider.setValue(hashing.BCRYPT_DEFAULT_COST)
        self.cost_slider.setFixedWidth(240)
        self.cost_slider.setCursor(Qt.PointingHandCursor)
        self.cost_label = QLabel()
        self.cost_label.setObjectName("metaText")
        self.cost_label.setMinimumWidth(170)
        self.hash_btn = make_button("生成哈希")
        cost_row = QHBoxLayout()
        cost_row.setSpacing(12)
        cost_row.addWidget(field_label("计算强度 cost"))
        cost_row.addWidget(self.cost_slider)
        cost_row.addWidget(self.cost_label)
        cost_row.addStretch(1)
        cost_row.addWidget(self.hash_btn)
        gen.body.addLayout(cost_row)

        self.hash_output = OutputLine("$2b$12$…")
        gen.body.addWidget(labeled("哈希结果", self.hash_output))
        self.hash_meta = QLabel()
        self.hash_meta.setObjectName("metaText")
        gen.body.addWidget(self.hash_meta)
        self.add(gen)

        # ---------- 验证 ----------
        verify = Card("验证密码", "检查密码与 bcrypt 哈希是否匹配")
        self.verify_password = PasswordInput("输入要验证的密码")
        verify.body.addWidget(labeled("密码", self.verify_password))

        self.verify_hash = QLineEdit()
        self.verify_hash.setProperty("mono", True)
        self.verify_hash.setPlaceholderText("粘贴 bcrypt 哈希，例如 $2b$12$…")
        self.use_hash_btn = make_button("使用上方结果", "ghost")
        hash_row = QHBoxLayout()
        hash_row.setSpacing(8)
        hash_row.addWidget(self.verify_hash, 1)
        hash_row.addWidget(self.use_hash_btn)
        verify.body.addWidget(field_label("bcrypt 哈希"))
        verify.body.addLayout(hash_row)

        self.verify_btn = make_button("验证")
        self.result_badge = QLabel()
        self.result_badge.setObjectName("resultBadge")
        self.result_badge.setAlignment(Qt.AlignCenter)
        self.result_badge.setMinimumHeight(48)
        verify.body.addLayout(button_row(self.verify_btn, None))
        verify.body.addWidget(self.result_badge)
        self.add(verify)
        self._layout.addStretch(1)

        self.cost_slider.valueChanged.connect(self._update_cost_label)
        self.hash_btn.clicked.connect(self._hash)
        self.use_hash_btn.clicked.connect(self._use_generated_hash)
        self.verify_btn.clicked.connect(self._verify)
        self.verify_password.textChanged.connect(self._reset_badge)
        self.verify_hash.textChanged.connect(self._reset_badge)
        self._update_cost_label(self.cost_slider.value())
        self._reset_badge()

    def _update_cost_label(self, cost: int):
        self.cost_label.setText(f"{cost}   ·   2^{cost} = {2 ** cost:,} 轮")

    def _hash(self):
        rounds = self.cost_slider.value()
        self.run(
            _timed_hash, self.hash_password.text(), rounds,
            on_success=lambda result: self._on_hashed(result, rounds),
            busy=(self.hash_btn,), busy_text="计算中…",
        )

    def _on_hashed(self, result, rounds: int):
        hashed, elapsed = result
        self.hash_output.set_text(hashed)
        self.hash_meta.setText(f"耗时 {elapsed:.2f} 秒 · cost {rounds}")
        self.success("bcrypt 哈希已生成")

    def _use_generated_hash(self):
        self.verify_hash.setText(self.hash_output.text())

    def _verify(self):
        self.run(
            hashing.bcrypt_verify, self.verify_password.text(), self.verify_hash.text(),
            on_success=self._on_verified, on_error=self._on_verify_error,
            busy=(self.verify_btn, self.use_hash_btn), busy_text="验证中…",
        )

    def _on_verified(self, matched: bool):
        self.result_badge.setText("✓  密码匹配" if matched else "✗  密码不匹配")
        set_prop(self.result_badge, "state", "match" if matched else "mismatch")

    def _on_verify_error(self, exc):
        self._reset_badge()
        self.show_error(exc)

    def _reset_badge(self):
        self.result_badge.setText(_IDLE_TEXT)
        set_prop(self.result_badge, "state", "idle")
