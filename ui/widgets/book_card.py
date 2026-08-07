# -*- coding: utf-8 -*-
"""书库书籍卡片组件"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QMenu
from PySide6.QtCore import Qt, Signal, QPoint
from qfluentwidgets import Action, FluentIcon as FIF


class BookCard(QFrame):
    """书籍卡片

    显示封面 emoji、书名、作者。
    左键点击 → 预览；右键菜单 → 删除/重新导出。
    """

    clicked = Signal(str)            # 书名（左键点击）
    delete_requested = Signal(str)   # 书名（右键删除）

    def __init__(self, title: str, author: str = "未知"):
        super().__init__()
        self.title = title
        self.author = author
        self.epub_path = ""
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(160, 220)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        self._apply_style(False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(8)
        layout.setContentsMargins(12, 16, 12, 16)

        # 封面区域
        cover = QLabel("📘")
        cover.setObjectName("cover")
        cover.setAlignment(Qt.AlignCenter)
        cover.setFixedHeight(80)
        cover.setStyleSheet("font-size: 48px;")
        layout.addWidget(cover)

        # 书名
        lbl_title = QLabel(self.title)
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
        layout.addWidget(lbl_title)

        # 作者
        lbl_author = QLabel(self.author)
        lbl_author.setObjectName("author")
        lbl_author.setAlignment(Qt.AlignCenter)
        lbl_author.setStyleSheet("font-size: 12px; color: #888;")
        layout.addWidget(lbl_author)

    def _apply_style(self, hover: bool):
        if hover:
            self.setStyleSheet("""
                BookCard, QFrame {
                    background: rgba(0, 120, 212, 0.1);
                    border: 1px solid #0078d4;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                BookCard, QFrame {
                    background: rgba(255, 255, 255, 0.05);
                    border: 1px solid #333;
                    border-radius: 12px;
                }
            """)

    def enterEvent(self, event):
        self._apply_style(True)

    def leaveEvent(self, event):
        self._apply_style(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title)

    def _show_menu(self, pos: QPoint):
        """右键菜单"""
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background: #2b2b2b;
                border: 1px solid #444;
                border-radius: 6px;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 24px;
                color: #ddd;
            }
            QMenu::item:selected {
                background: #0078d4;
                border-radius: 4px;
            }
        """)

        action_open = Action(FIF.VIEW, "预览", menu)
        action_open.triggered.connect(lambda: self.clicked.emit(self.title))
        menu.addAction(action_open)

        menu.addSeparator()

        action_delete = Action(FIF.DELETE, "删除", menu)
        action_delete.triggered.connect(lambda: self.delete_requested.emit(self.title))
        menu.addAction(action_delete)

        menu.exec(self.mapToGlobal(pos))
