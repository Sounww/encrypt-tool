from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QMainWindow, QScrollArea, QStackedWidget, QWidget

from crypto_core import ecc_cipher, rsa_cipher

from .pages.aes_page import AesPage
from .pages.asymmetric_page import AsymmetricPage
from .pages.base64_page import Base64Page
from .pages.bcrypt_page import BcryptPage
from .pages.sha256_page import Sha256Page
from .sidebar import Sidebar
from .widgets import Toast, make_app_icon

NAV_GROUPS = [
    ("可逆加密", [
        ("A", "AES", "对称加密 · 口令"),
        ("R", "RSA", "非对称 · 公钥 / 私钥"),
        ("E", "ECC", "非对称 · 椭圆曲线"),
    ]),
    ("单向哈希", [
        ("#", "SHA-256", "数据摘要 · 不可逆"),
        ("B", "bcrypt", "密码存储 · 可验证"),
    ]),
    ("编码转换", [
        ("64", "Base64", "文本编码 · 可还原"),
    ]),
]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CipherBox · 加密工具箱")
        self.setWindowIcon(make_app_icon())
        self.resize(1100, 760)
        self.setMinimumSize(960, 680)

        self.pages = {
            "aes": AesPage(),
            "rsa": AsymmetricPage(
                rsa_cipher,
                "RSA 公钥加密",
                "公钥加密、私钥解密。公钥可以分享给任何人，私钥务必妥善保管。支持任意长度文本（混合加密）。",
                ["RSA-OAEP", "SHA-256", "混合加密"],
                "密钥长度（位）",
            ),
            "ecc": AsymmetricPage(
                ecc_cipher,
                "ECC 椭圆曲线加密",
                "基于椭圆曲线的公钥加密（ECIES）：同等安全强度下密钥更短、运算更快。",
                ["ECIES", "ECDH + HKDF", "AES-256-GCM"],
                "曲线",
            ),
            "sha256": Sha256Page(),
            "bcrypt": BcryptPage(),
            "base64": Base64Page(),
        }

        root = QWidget()
        root.setObjectName("root")
        root.setAttribute(Qt.WA_StyledBackground)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.sidebar = Sidebar(NAV_GROUPS)
        self.stack = QStackedWidget()
        self.stack.setObjectName("content")
        for page in self.pages.values():
            scroll = QScrollArea()
            scroll.setObjectName("pageScroll")
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(page)
            self.stack.addWidget(scroll)

        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)

        self.toast = Toast(root)
        for page in self.pages.values():
            page.notify.connect(self.toast.show_message)
        self.sidebar.currentChanged.connect(self.stack.setCurrentIndex)
        self.sidebar.select(0)
