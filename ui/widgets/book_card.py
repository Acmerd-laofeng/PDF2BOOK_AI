# -*- coding: utf-8 -*-
"""书库书籍卡片组件"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QMenu
from PySide6.QtCore import Qt, Signal, QPoint
from qfluentwidgets import Action, FluentIcon as FIF


class BookCard(QFrame):
    """书籍卡片

    显示封面渐变色、书名、作者、格式标签。
    左键点击 → 预览；右键菜单 → 打开目录/删除。
    """

    clicked = Signal(str)            # 书名（左键点击）
    delete_requested = Signal(str)   # 书名（右键删除）
    open_dir_requested = Signal(str)  # 书名（打开目录）

    # 根据书名首字生成不同的封面渐变色
    COVER_GRADIENTS = [
        ("#667eea", "#764ba2"),  # 紫蓝
        ("#f093fb", "#f5576c"),  # 粉红
        ("#4facfe", "#00f2fe"),  # 青蓝
        ("#43e97b", "#38f9d7"),  # 翠绿
        ("#fa709a", "#fee140"),  # 橙粉
        ("#30cfd0", "#330867"),  # 深蓝紫
        ("#a8edea", "#fed6e3"),  # 浅粉绿
        ("#ff9a9e", "#fecfef"),  # 暖粉
    ]

    def __init__(self, title: str, author: str = "未知", epub_path: str = ""):
        super().__init__()
        self.title = title
        self.author = author
        self.epub_path = epub_path
        self._init_ui()

    def _get_cover_colors(self) -> tuple:
        """根据书名 hash 选择封面色"""
        idx = hash(self.title) % len(self.COVER_GRADIENTS)
        return self.COVER_GRADIENTS[idx]

    def _get_format_tag(self) -> str:
        """从文件路径推断格式标签"""
        if not self.epub_path:
            return ""
        ext = self.epub_path.rsplit(".", 1)[-1].upper() if "." in self.epub_path else ""
        return ext

    def _init_ui(self):
        self.setFixedSize(160, 240)
        self.setCursor(Qt.PointingHandCursor)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_menu)

        self._apply_style(False)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(6)
        layout.setContentsMargins(10, 14, 10, 14)

        # 封面区域 — 渐变色背景 + 首字
        c1, c2 = self._get_cover_colors()
        cover = QLabel(self.title[0] if self.title else "📖")
        cover.setObjectName("cover")
        cover.setAlignment(Qt.AlignCenter)
        cover.setFixedHeight(90)
        cover.setStyleSheet(f"""
            font-size: 42px;
            font-weight: bold;
            color: white;
            border-radius: 8px;
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {c1}, stop:1 {c2});
        """)
        layout.addWidget(cover)

        # 书名
        lbl_title = QLabel(self.title)
        lbl_title.setObjectName("title")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setWordWrap(True)
        lbl_title.setMaximumHeight(40)
        lbl_title.setStyleSheet("font-size: 13px; font-weight: bold; color: #fff;")
        layout.addWidget(lbl_title)

        # 作者
        lbl_author = QLabel(self.author)
        lbl_author.setObjectName("author")
        lbl_author.setAlignment(Qt.AlignCenter)
        lbl_author.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(lbl_author)

        # 格式标签
        fmt = self._get_format_tag()
        if fmt:
            lbl_fmt = QLabel(fmt)
            lbl_fmt.setAlignment(Qt.AlignCenter)
            lbl_fmt.setFixedHeight(18)
            lbl_fmt.setStyleSheet("""
                font-size: 10px;
                color: #0078d4;
                background: rgba(0, 120, 212, 0.15);
                border-radius: 4px;
                padding: 1px 6px;
            """)
            layout.addWidget(lbl_fmt)

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

        action_dir = Action(FIF.FOLDER, "打开所在目录", menu)
        action_dir.triggered.connect(lambda: self.open_dir_requested.emit(self.title))
        menu.addAction(action_dir)

        menu.addSeparator()

        action_delete = Action(FIF.DELETE, "从书库删除", menu)
        action_delete.triggered.connect(lambda: self.delete_requested.emit(self.title))
        menu.addAction(action_delete)

        menu.exec(self.mapToGlobal(pos))
