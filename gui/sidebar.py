"""左侧导航栏。"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from .widgets import make_logo_pixmap, set_prop


class NavItem(QFrame):
    clicked = pyqtSignal()

    def __init__(self, icon_text: str, title: str, desc: str):
        super().__init__()
        self.setObjectName("navItem")
        self.setAttribute(Qt.WA_Hover)
        self.setAttribute(Qt.WA_StyledBackground)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(58)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 12, 0)
        layout.setSpacing(10)

        self._bar = QFrame()
        self._bar.setObjectName("navBar")
        self._bar.setFixedSize(3, 26)
        self._icon = QLabel(icon_text)
        self._icon.setObjectName("navIcon")
        self._icon.setAlignment(Qt.AlignCenter)
        self._icon.setFixedSize(34, 34)

        texts = QVBoxLayout()
        texts.setSpacing(1)
        self._title = QLabel(title)
        self._title.setObjectName("navTitle")
        self._desc = QLabel(desc)
        self._desc.setObjectName("navDesc")
        texts.addStretch(1)
        texts.addWidget(self._title)
        texts.addWidget(self._desc)
        texts.addStretch(1)

        layout.addWidget(self._bar)
        layout.addWidget(self._icon)
        layout.addLayout(texts, 1)
        self.set_active(False)

    def set_active(self, active: bool) -> None:
        for widget in (self, self._bar, self._icon, self._title, self._desc):
            set_prop(widget, "active", active)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class Sidebar(QFrame):
    currentChanged = pyqtSignal(int)

    def __init__(self, groups):
        """groups: [(分组名, [(图标文字, 标题, 说明), ...]), ...]"""
        super().__init__()
        self.setObjectName("sidebar")
        self.setAttribute(Qt.WA_StyledBackground)
        self.setFixedWidth(232)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 22, 14, 18)
        layout.setSpacing(4)

        brand = QHBoxLayout()
        brand.setContentsMargins(8, 0, 0, 0)
        brand.setSpacing(12)
        logo = QLabel()
        logo.setPixmap(make_logo_pixmap(40))
        logo.setFixedSize(40, 40)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(0)
        title = QLabel("CipherBox")
        title.setObjectName("brandTitle")
        subtitle = QLabel("加密工具箱")
        subtitle.setObjectName("brandSubtitle")
        brand_text.addWidget(title)
        brand_text.addWidget(subtitle)
        brand.addWidget(logo)
        brand.addLayout(brand_text, 1)
        layout.addLayout(brand)
        layout.addSpacing(24)

        self._items: list[NavItem] = []
        for group_name, entries in groups:
            group_label = QLabel(group_name)
            group_label.setObjectName("navGroup")
            layout.addWidget(group_label)
            layout.addSpacing(4)
            for icon_text, item_title, desc in entries:
                item = NavItem(icon_text, item_title, desc)
                index = len(self._items)
                item.clicked.connect(lambda i=index: self.select(i))
                self._items.append(item)
                layout.addWidget(item)
            layout.addSpacing(16)

        layout.addStretch(1)
        footer = QLabel("所有运算均在本地完成\n不会上传任何数据")
        footer.setObjectName("sidebarFooter")
        layout.addWidget(footer)

        self._current = -1

    def select(self, index: int) -> None:
        if index == self._current:
            return
        for i, item in enumerate(self._items):
            item.set_active(i == index)
        self._current = index
        self.currentChanged.emit(index)
