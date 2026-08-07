# -*- coding: utf-8 -*-
"""EPUB 主题选择卡片"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Signal, Qt


class ThemeCard(QFrame):
    """EPUB 主题选择卡片（单选模式）"""

    selected = Signal(str)  # theme_key

    # 主题预览色
    THEME_COLORS = {
        "classic": ("#f5f0e8", "#333333"),   # 米色底 + 深灰字
        "kindle": ("#e6e6e6", "#1a1a1a"),    # 灰白底 + 黑字
        "modern": ("#ffffff", "#2c3e50"),     # 白底 + 深蓝字
        "eye_care": ("#c7edcc", "#333333"),   # 护眼绿底 + 深灰字
    }

    def __init__(self, name: str, theme_key: str):
        super().__init__()
        self.name = name
        self.theme_key = theme_key
        self._selected = False
        self._init_ui()

    def _init_ui(self):
        self.setFixedSize(130, 100)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style()

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setSpacing(4)
        layout.setContentsMargins(8, 8, 8, 8)

        # 主题预览色块
        bg_color, text_color = self.THEME_COLORS.get(
            self.theme_key, ("#333", "#fff")
        )
        preview = QLabel("Aa 文字")
        preview.setAlignment(Qt.AlignCenter)
        preview.setFixedHeight(40)
        preview.setStyleSheet(f"""
            background: {bg_color};
            color: {text_color};
            border-radius: 6px;
            font-size: 14px;
            font-weight: bold;
        """)
        layout.addWidget(preview)

        lbl_name = QLabel(self.name)
        lbl_name.setAlignment(Qt.AlignCenter)
        lbl_name.setStyleSheet("font-size: 13px; color: #ccc;")
        layout.addWidget(lbl_name)

    def _apply_style(self):
        if self._selected:
            border = "#0078d4"
            bg = "rgba(0, 120, 212, 0.15)"
        else:
            border = "#444"
            bg = "rgba(255, 255, 255, 0.03)"
        self.setStyleSheet(f"""
            ThemeCard, QFrame {{
                background: {bg};
                border: 2px solid {border};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: #5599ff;
            }}
        """)

    def is_selected(self) -> bool:
        return self._selected

    def set_selected(self, selected: bool):
        self._selected = selected
        self._apply_style()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._selected = True
            self._apply_style()
            self.selected.emit(self.theme_key)
