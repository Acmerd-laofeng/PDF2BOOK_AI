# -*- coding: utf-8 -*-
"""首页 - 拖拽上传 + PDF分析卡片 + 最近任务"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, QHBoxLayout
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    TitleLabel, SubtitleLabel, BodyLabel, PushButton, CardWidget,
    FluentIcon as FIF, InfoBar, InfoBarPosition,
)

from ui.widgets.pdf_drop_area import PDFDropArea
from ui.widgets.analysis_card import AnalysisCard
from ui.widgets.progress_card import ProgressCard
from PySide6.QtWidgets import QFileDialog


class HomePage(QWidget):
    """首页"""

    file_selected = Signal(str)
    start_convert = Signal()
    navigate_requested = Signal(str)  # 页面名

    def __init__(self):
        super().__init__()
        self._recent_cards = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)

        # 标题区
        title = TitleLabel("📘 PDF2BOOK AI")
        layout.addWidget(title)

        subtitle = BodyLabel("AI智能电子书重构平台 · 将 PDF 转换为精美 EPUB")
        subtitle.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(subtitle)

        # 拖拽区域
        self.drop_area = PDFDropArea()
        self.drop_area.file_dropped.connect(self._on_file_dropped)
        self.drop_area.files_dropped.connect(self._on_files_dropped)
        layout.addWidget(self.drop_area)

        # 快捷功能入口
        entry_row = QHBoxLayout()
        entry_row.setSpacing(12)

        entries = [
            ("📄", "转换", "PDF → EPUB", "convert"),
            ("🔄", "格式转换", "多格式互转", "format_convert"),
            ("📚", "书库", "已转换书籍", "library"),
            ("⚙️", "设置", "配置参数", "setting"),
        ]
        for emoji, title, desc, page in entries:
            entry_card = CardWidget()
            entry_card.setFixedHeight(70)
            entry_card.setCursor(Qt.PointingHandCursor)
            entry_layout = QHBoxLayout(entry_card)
            entry_layout.setContentsMargins(16, 10, 16, 10)
            entry_layout.setSpacing(10)

            lbl_emoji = QLabel(emoji)
            lbl_emoji.setStyleSheet("font-size: 24px;")
            lbl_emoji.setFixedWidth(32)
            entry_layout.addWidget(lbl_emoji)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            lbl_title = BodyLabel(title)
            lbl_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #fff;")
            text_col.addWidget(lbl_title)
            lbl_desc = BodyLabel(desc)
            lbl_desc.setStyleSheet("font-size: 11px; color: #888;")
            text_col.addWidget(lbl_desc)
            entry_layout.addLayout(text_col)
            entry_layout.addStretch()

            # 点击跳转
            entry_card.mousePressEvent = lambda e, p=page: self._navigate_to(p)

            entry_row.addWidget(entry_card)

        layout.addLayout(entry_row)

        # 分析卡片 + 开始按钮放一行
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # 分析卡片
        self.analysis_card = AnalysisCard()
        self.analysis_card.setVisible(False)
        content_row.addWidget(self.analysis_card, 1)

        # 开始转换按钮（垂直居中）
        btn_layout = QVBoxLayout()
        btn_layout.addStretch()
        self.btn_convert = PushButton("开始转换")
        self.btn_convert.setFixedHeight(48)
        self.btn_convert.setFixedWidth(200)
        self.btn_convert.setEnabled(False)
        self.btn_convert.setIcon(FIF.PLAY)
        self.btn_convert.clicked.connect(self.start_convert.emit)
        btn_layout.addWidget(self.btn_convert)
        btn_layout.addStretch()
        content_row.addLayout(btn_layout)

        layout.addLayout(content_row)

        # 分隔线
        layout.addWidget(SubtitleLabel("最近转换"))

        # 最近任务列表
        self.recent_container = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_container)
        self.recent_layout.setSpacing(8)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)

        # 空状态提示
        self.lbl_empty = BodyLabel("暂无转换记录\n\n💡 拖入 PDF 到上方区域即可开始")
        self.lbl_empty.setStyleSheet("color: #666; padding: 20px; font-size: 14px;")
        self.lbl_empty.setAlignment(Qt.AlignCenter)
        self.recent_layout.addWidget(self.lbl_empty)

        layout.addWidget(self.recent_container)

        layout.addItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def _on_file_dropped(self, file_path: str):
        """拖入单文件回调"""
        self.file_selected.emit(file_path)
        self.btn_convert.setEnabled(True)

    def _on_files_dropped(self, file_paths: list):
        """拖入多文件回调 — 批量添加到最近任务"""
        if not file_paths:
            return
        # 第一个文件作为当前选中文件
        self.file_selected.emit(file_paths[0])
        self.btn_convert.setEnabled(True)
        # 多文件提示
        from qfluentwidgets import InfoBar, InfoBarPosition
        InfoBar.success(
            "批量选择",
            f"已选择 {len(file_paths)} 个文件，第一个已加载到转换区",
            parent=self, duration=4000
        )

    def show_analysis(self, info: dict):
        """显示 PDF 分析结果"""
        self.analysis_card.update_info(info)
        self.analysis_card.setVisible(True)

    def add_recent_task(self, name: str, progress: int = 0):
        """添加最近任务卡片"""
        if self.lbl_empty.isVisible():
            self.lbl_empty.setVisible(False)

        card = ProgressCard(name)
        card.set_progress(progress)
        self.recent_layout.insertWidget(0, card)
        self._recent_cards.append(card)

        # 只保留最近 3 个
        if len(self._recent_cards) > 3:
            old = self._recent_cards.pop(0)
            old.deleteLater()

    def _navigate_to(self, page: str):
        """触发导航信号"""
        self.navigate_requested.emit(page)

    def update_recent_progress(self, name: str, progress: int):
        """更新最近任务进度"""
        for card in self._recent_cards:
            if card.name == name:
                card.set_progress(progress)
                break
