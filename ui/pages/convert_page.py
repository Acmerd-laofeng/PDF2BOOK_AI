# -*- coding: utf-8 -*-
"""转换中心 - 模式选择 + 高级设置 + 进度 + 日志"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit
)
from PySide6.QtCore import Signal
from qfluentwidgets import (
    ComboBox, ProgressBar, PushButton, SpinBox, SwitchButton,
    TitleLabel, SubtitleLabel, BodyLabel, CardWidget,
    FluentIcon as FIF,
)

from app.constants import CONVERT_MODES, EPUB_THEMES, DEFAULT_DPI, MIN_DPI, MAX_DPI
from ui.widgets.theme_card import ThemeCard


class ConvertPage(QWidget):
    """转换中心"""

    start_conversion = Signal(dict)

    def __init__(self):
        super().__init__()
        self._selected_theme = "classic"
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 30)

        # 标题
        layout.addWidget(TitleLabel("转换中心"))

        # 当前文件信息
        self.lbl_file = BodyLabel("未选择文件")
        self.lbl_file.setStyleSheet("color: #888; font-size: 14px;")
        layout.addWidget(self.lbl_file)

        # === 转换模式 ===
        mode_card = CardWidget()
        mode_layout = QVBoxLayout(mode_card)
        mode_layout.setContentsMargins(20, 16, 20, 16)
        mode_layout.setSpacing(10)

        mode_title = BodyLabel("转换模式")
        mode_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        mode_layout.addWidget(mode_title)

        self.mode_combo = ComboBox()
        self._mode_keys = list(CONVERT_MODES.keys())
        for key, name in CONVERT_MODES.items():
            self.mode_combo.addItem(name)
        self.mode_combo.setCurrentIndex(1)  # 默认推荐模式
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_layout.addWidget(self.mode_combo)

        # 模式说明
        self.lbl_mode_desc = BodyLabel("")
        self.lbl_mode_desc.setStyleSheet("color: #888; font-size: 13px;")
        mode_layout.addWidget(self.lbl_mode_desc)
        self._update_mode_desc()

        layout.addWidget(mode_card)

        # === 高级设置 ===
        advanced_card = CardWidget()
        advanced_layout = QVBoxLayout(advanced_card)
        advanced_layout.setContentsMargins(20, 16, 20, 16)
        advanced_layout.setSpacing(10)

        adv_title = BodyLabel("⚙ 高级设置")
        adv_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        advanced_layout.addWidget(adv_title)

        # DPI
        advanced_layout.addWidget(BodyLabel("渲染 DPI（越高越精准但越慢）"))
        self.dpi_spin = SpinBox()
        self.dpi_spin.setRange(MIN_DPI, MAX_DPI)
        self.dpi_spin.setValue(DEFAULT_DPI)
        self.dpi_spin.setSingleStep(50)
        advanced_layout.addWidget(self.dpi_spin)

        # 缩进阈值
        advanced_layout.addWidget(BodyLabel("段落缩进阈值（像素）"))
        self.indent_spin = SpinBox()
        self.indent_spin.setRange(10, 100)
        self.indent_spin.setValue(30)
        advanced_layout.addWidget(self.indent_spin)

        # 开关
        switch_layout = QHBoxLayout()

        chapter_col = QVBoxLayout()
        chapter_col.addWidget(BodyLabel("章节标题检测"))
        self.chapter_switch = SwitchButton()
        self.chapter_switch.setChecked(True)
        chapter_col.addWidget(self.chapter_switch)
        switch_layout.addLayout(chapter_col)

        cross_col = QVBoxLayout()
        cross_col.addWidget(BodyLabel("跨页断行合并"))
        self.cross_page_switch = SwitchButton()
        self.cross_page_switch.setChecked(True)
        cross_col.addWidget(self.cross_page_switch)
        switch_layout.addLayout(cross_col)

        advanced_layout.addLayout(switch_layout)
        layout.addWidget(advanced_card)

        # === EPUB 主题选择 ===
        theme_card = CardWidget()
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 16, 20, 16)
        theme_layout.setSpacing(10)

        theme_title = BodyLabel("EPUB 主题")
        theme_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        theme_layout.addWidget(theme_title)

        theme_row = QHBoxLayout()
        theme_row.setSpacing(12)
        self.theme_cards = []
        for key, name in EPUB_THEMES.items():
            card = ThemeCard(name, key)
            card.selected.connect(self._on_theme_selected)
            if key == "classic":
                card.set_selected(True)
            self.theme_cards.append(card)
            theme_row.addWidget(card)
        theme_row.addStretch()
        theme_layout.addLayout(theme_row)

        layout.addWidget(theme_card)

        # === 进度 + 日志 ===
        progress_card = CardWidget()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(20, 16, 20, 16)
        progress_layout.setSpacing(10)

        progress_title = BodyLabel("转换进度")
        progress_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        progress_layout.addWidget(progress_title)

        self.progress_bar = ProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.lbl_progress_text = BodyLabel("就绪")
        self.lbl_progress_text.setStyleSheet("color: #888; font-size: 13px;")
        progress_layout.addWidget(self.lbl_progress_text)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(180)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: rgba(0, 0, 0, 0.3);
                color: #ccc;
                font-size: 13px;
                font-family: 'Consolas', 'Microsoft YaHei UI';
                border: 1px solid #333;
                border-radius: 6px;
                padding: 8px;
            }
        """)
        progress_layout.addWidget(self.log_text)

        layout.addWidget(progress_card)

        # 开始按钮
        self.btn_start = PushButton("开始转换")
        self.btn_start.setFixedHeight(48)
        self.btn_start.setIcon(FIF.PLAY)
        self.btn_start.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.btn_start)

        layout.addStretch()

    def _on_mode_changed(self):
        self._update_mode_desc()

    def _update_mode_desc(self):
        descs = {
            "quick": "150 DPI · 速度快 · 适合纯文字 PDF",
            "standard": "300 DPI · 推荐 · 适合大多数扫描版",
            "precise": "400 DPI · 高精度 · 适合小字/古籍",
            "ai": "300 DPI + AI 纠错 · 需联网 · 质量最佳",
        }
        idx = self.mode_combo.currentIndex()
        key = self._mode_keys[idx] if idx < len(self._mode_keys) else "standard"
        self.lbl_mode_desc.setText(descs.get(key, ""))

    def _on_theme_selected(self, theme_key: str):
        """主题单选：选中一个，取消其他"""
        self._selected_theme = theme_key
        for card in self.theme_cards:
            card.set_selected(card.theme_key == theme_key)

    def _on_start_clicked(self):
        settings = self.get_settings()
        self.append_log(f"开始转换 · 模式={settings['quality']} · DPI={settings['dpi']}")
        self.start_conversion.emit(settings)

    def set_pdf_info(self, pdf_path: str):
        """设置当前 PDF 信息"""
        import os
        filename = os.path.basename(pdf_path)
        size = os.path.getsize(pdf_path)
        if size < 1024 * 1024:
            size_str = f"{size / 1024:.0f} KB"
        else:
            size_str = f"{size / 1024 / 1024:.1f} MB"
        self.lbl_file.setText(f"📄 {filename}  ({size_str})")

    def get_settings(self) -> dict:
        """获取当前转换设置"""
        idx = self.mode_combo.currentIndex()
        quality = self._mode_keys[idx] if idx < len(self._mode_keys) else "standard"
        return {
            "quality": quality,
            "dpi": self.dpi_spin.value(),
            "indent_threshold": self.indent_spin.value(),
            "detect_chapters": self.chapter_switch.isChecked(),
            "merge_cross_page": self.cross_page_switch.isChecked(),
            "epub_theme": self._selected_theme,
        }

    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.lbl_progress_text.setText(f"{value}%")

    def append_log(self, msg: str):
        """追加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {msg}")

    def reset(self):
        """重置状态"""
        self.progress_bar.setValue(0)
        self.lbl_progress_text.setText("就绪")
        self.log_text.clear()
