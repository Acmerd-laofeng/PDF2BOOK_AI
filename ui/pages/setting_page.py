# -*- coding: utf-8 -*-
"""设置中心 - 转换质量、主题、OCR参数、AI配置"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout
)
from PySide6.QtCore import Signal
from qfluentwidgets import (
    ComboBox, SpinBox, SwitchButton, LineEdit, PushButton,
    TitleLabel, BodyLabel, CardWidget,
    FluentIcon as FIF,
)

from app.constants import EPUB_THEMES


class SettingPage(QWidget):
    """设置中心"""

    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(16)

        layout.addWidget(TitleLabel("设置中心"))

        # === 转换设置 ===
        convert_card = CardWidget()
        convert_layout = QVBoxLayout(convert_card)
        convert_layout.setContentsMargins(20, 16, 20, 16)
        convert_layout.setSpacing(12)

        convert_title = BodyLabel("转换设置")
        convert_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        convert_layout.addWidget(convert_title)

        # 转换质量
        convert_layout.addWidget(BodyLabel("转换质量"))
        self.quality = ComboBox()
        self.quality.addItems(["快速", "推荐", "极致"])
        self.quality.setCurrentIndex(1)
        convert_layout.addWidget(self.quality)

        # DPI
        convert_layout.addWidget(BodyLabel("默认渲染 DPI"))
        self.dpi = SpinBox()
        self.dpi.setRange(150, 600)
        self.dpi.setValue(300)
        self.dpi.setSingleStep(50)
        convert_layout.addWidget(self.dpi)

        # OCR 并行
        convert_layout.addWidget(BodyLabel("OCR 并行线程数"))
        self.parallel = SpinBox()
        self.parallel.setRange(1, 8)
        self.parallel.setValue(4)
        convert_layout.addWidget(self.parallel)

        layout.addWidget(convert_card)

        # === 段落检测 ===
        layout_card = CardWidget()
        layout_inner = QVBoxLayout(layout_card)
        layout_inner.setContentsMargins(20, 16, 20, 16)
        layout_inner.setSpacing(12)

        layout_title = BodyLabel("段落检测")
        layout_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        layout_inner.addWidget(layout_title)

        layout_inner.addWidget(BodyLabel("首行缩进阈值（像素）"))
        self.indent_threshold = SpinBox()
        self.indent_threshold.setRange(10, 100)
        self.indent_threshold.setValue(30)
        layout_inner.addWidget(self.indent_threshold)

        layout_inner.addWidget(BodyLabel("行间距倍数"))
        self.gap_ratio = LineEdit()
        self.gap_ratio.setText("1.8")
        layout_inner.addWidget(self.gap_ratio)

        # 开关
        switch_row = QHBoxLayout()
        col1 = QVBoxLayout()
        col1.addWidget(BodyLabel("章节标题检测"))
        self.detect_chapters = SwitchButton()
        self.detect_chapters.setChecked(True)
        col1.addWidget(self.detect_chapters)
        switch_row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.addWidget(BodyLabel("跨页断行合并"))
        self.merge_cross_page = SwitchButton()
        self.merge_cross_page.setChecked(True)
        col2.addWidget(self.merge_cross_page)
        switch_row.addLayout(col2)
        layout_inner.addLayout(switch_row)

        layout.addWidget(layout_card)

        # === EPUB 导出 ===
        epub_card = CardWidget()
        epub_layout = QVBoxLayout(epub_card)
        epub_layout.setContentsMargins(20, 16, 20, 16)
        epub_layout.setSpacing(12)

        epub_title = BodyLabel("EPUB 导出")
        epub_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        epub_layout.addWidget(epub_title)

        epub_layout.addWidget(BodyLabel("默认主题"))
        self.default_theme = ComboBox()
        self._theme_keys = list(EPUB_THEMES.keys())
        for key, name in EPUB_THEMES.items():
            self.default_theme.addItem(name)
        epub_layout.addWidget(self.default_theme)

        epub_layout.addWidget(BodyLabel("默认导出格式"))
        self.default_format = ComboBox()
        self.default_format.addItems(["EPUB", "EPUB3", "MOBI", "HTML", "Markdown", "TXT"])
        epub_layout.addWidget(self.default_format)

        layout.addWidget(epub_card)

        # === AI 配置（预留）===
        ai_card = CardWidget()
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(20, 16, 20, 16)
        ai_layout.setSpacing(12)

        ai_title = BodyLabel("AI 配置（预留 · v4 启用）")
        ai_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #888;")
        ai_layout.addWidget(ai_title)

        ai_layout.addWidget(BodyLabel("AI 服务"))
        self.api_provider = ComboBox()
        self.api_provider.addItems(["不启用", "DeepSeek", "OpenAI", "本地模型"])
        ai_layout.addWidget(self.api_provider)

        ai_layout.addWidget(BodyLabel("API Key"))
        self.api_key = LineEdit()
        self.api_key.setPlaceholderText("输入 API Key（留空则不启用 AI 功能）")
        self.api_key.setEchoMode(LineEdit.Password)
        ai_layout.addWidget(self.api_key)

        ai_switch_row = QHBoxLayout()
        col_a = QVBoxLayout()
        col_a.addWidget(BodyLabel("OCR 纠错"))
        self.ocr_correction = SwitchButton()
        col_a.addWidget(self.ocr_correction)
        ai_switch_row.addLayout(col_a)

        col_b = QVBoxLayout()
        col_b.addWidget(BodyLabel("章节摘要"))
        self.chapter_summary = SwitchButton()
        col_b.addWidget(self.chapter_summary)
        ai_switch_row.addLayout(col_b)
        ai_layout.addLayout(ai_switch_row)

        layout.addWidget(ai_card)

        # === 保存按钮 ===
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_save = PushButton("保存设置")
        self.btn_save.setFixedHeight(40)
        self.btn_save.setFixedWidth(160)
        self.btn_save.setIcon(FIF.ACCEPT)
        self.btn_save.clicked.connect(self._on_save)
        btn_row.addWidget(self.btn_save)
        layout.addLayout(btn_row)

        layout.addStretch()

    def _load_settings(self):
        """从配置加载到 UI"""
        from app.config import Config
        quality = Config.get_quality_mode()
        quality_map = {"fast": 0, "recommended": 1, "extreme": 2}
        if quality in quality_map:
            self.quality.setCurrentIndex(quality_map[quality])

        self.dpi.setValue(Config.get_dpi())
        self.indent_threshold.setValue(Config.get_indent_threshold())
        self.gap_ratio.setText(str(Config.get_gap_ratio()))

        theme = Config.get_theme()
        for i, k in enumerate(self._theme_keys):
            if k == theme:
                self.default_theme.setCurrentIndex(i)
                break

    def _on_save(self):
        """保存设置"""
        settings = {
            "quality": self.quality.currentText(),
            "dpi": self.dpi.value(),
            "parallel": self.parallel.value(),
            "indent_threshold": self.indent_threshold.value(),
            "gap_ratio": self.gap_ratio.text(),
            "detect_chapters": self.detect_chapters.isChecked(),
            "merge_cross_page": self.merge_cross_page.isChecked(),
            "epub_theme": self._theme_keys[self.default_theme.currentIndex()],
            "export_format": self.default_format.currentText(),
        }
        self.settings_changed.emit(settings)
