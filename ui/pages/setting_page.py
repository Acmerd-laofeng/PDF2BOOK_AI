# -*- coding: utf-8 -*-
"""设置中心 - 转换质量、主题、OCR参数、AI配置"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    ComboBox, SpinBox, SwitchButton, LineEdit, PushButton,
    TitleLabel, BodyLabel, CardWidget,
    FluentIcon as FIF,
)

from app.constants import EPUB_THEMES, GEMINI_MODELS
from app.config import Config


class SettingPage(QWidget):
    """设置中心"""

    settings_changed = Signal(dict)

    def __init__(self):
        super().__init__()
        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        # 外层布局：只放一个 ScrollArea
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ScrollArea 包裹所有内容
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        # 内容容器
        container = QWidget()
        layout = QVBoxLayout(container)
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
        self.quality.addItems(["快速", "推荐", "极致", "AI增强"])
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

        # 开关 — 用固定高度避免挤压
        switch_row = QHBoxLayout()
        switch_row.setSpacing(24)

        col1 = QVBoxLayout()
        col1.setSpacing(4)
        col1.addWidget(BodyLabel("章节标题检测"))
        self.detect_chapters = SwitchButton()
        self.detect_chapters.setChecked(True)
        col1.addWidget(self.detect_chapters)
        switch_row.addLayout(col1)

        col2 = QVBoxLayout()
        col2.setSpacing(4)
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

        epub_layout.addWidget(BodyLabel("默认导出目录"))
        self.output_dir = LineEdit()
        self.output_dir.setPlaceholderText("留空则导出到 PDF 同级目录")
        self.output_dir.setText(Config.get_output_dir())
        epub_layout.addWidget(self.output_dir)

        layout.addWidget(epub_card)

        # === AI 配置 ===
        ai_card = CardWidget()
        ai_layout = QVBoxLayout(ai_card)
        ai_layout.setContentsMargins(20, 16, 20, 16)
        ai_layout.setSpacing(12)

        ai_title = BodyLabel("AI 纠错配置")
        ai_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #0078d4;")
        ai_layout.addWidget(ai_title)

        # API 服务 + 模型 横排
        ai_row1 = QHBoxLayout()
        ai_row1.setSpacing(16)

        col_provider = QVBoxLayout()
        col_provider.setSpacing(4)
        col_provider.addWidget(BodyLabel("AI 服务"))
        self.api_provider = ComboBox()
        self.api_provider.addItems(["不启用", "Google Gemini"])
        col_provider.addWidget(self.api_provider)
        ai_row1.addLayout(col_provider)

        col_model = QVBoxLayout()
        col_model.setSpacing(4)
        col_model.addWidget(BodyLabel("Gemini 模型"))
        self.ai_model = ComboBox()
        for key, name in GEMINI_MODELS.items():
            self.ai_model.addItem(name)
        col_model.addWidget(self.ai_model)
        ai_row1.addLayout(col_model)

        ai_layout.addLayout(ai_row1)

        # API Key + 测试连接 横排
        ai_row2 = QHBoxLayout()
        ai_row2.setSpacing(12)

        col_key = QVBoxLayout()
        col_key.setSpacing(4)
        col_key.addWidget(BodyLabel("API Key"))
        self.api_key = LineEdit()
        self.api_key.setPlaceholderText("输入 Gemini API Key")
        self.api_key.setEchoMode(LineEdit.Password)
        col_key.addWidget(self.api_key)
        ai_row2.addLayout(col_key, stretch=1)

        col_btn = QVBoxLayout()
        col_btn.setSpacing(4)
        col_btn.addWidget(BodyLabel(""))  # 对齐占位
        self.btn_test_ai = PushButton("测试连接")
        self.btn_test_ai.setFixedHeight(33)
        self.btn_test_ai.setFixedWidth(100)
        self.btn_test_ai.clicked.connect(self._test_ai_connection)
        col_btn.addWidget(self.btn_test_ai)
        ai_row2.addLayout(col_btn)

        ai_layout.addLayout(ai_row2)

        # AI 开关横排
        ai_switch_row = QHBoxLayout()
        ai_switch_row.setSpacing(24)

        col_a = QVBoxLayout()
        col_a.setSpacing(4)
        col_a.addWidget(BodyLabel("OCR AI 纠错"))
        self.ocr_correction = SwitchButton()
        col_a.addWidget(self.ocr_correction)
        ai_switch_row.addLayout(col_a)

        col_b = QVBoxLayout()
        col_b.setSpacing(4)
        col_b.addWidget(BodyLabel("章节摘要"))
        self.chapter_summary = SwitchButton()
        col_b.addWidget(self.chapter_summary)
        ai_switch_row.addLayout(col_b)
        ai_layout.addLayout(ai_switch_row)

        layout.addWidget(ai_card)

        # === 关于 ===
        about_card = CardWidget()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(20, 16, 20, 16)
        about_layout.setSpacing(12)

        about_title = BodyLabel("关于")
        about_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        about_layout.addWidget(about_title)

        from app.constants import APP_NAME, APP_VERSION
        about_info = BodyLabel(f"{APP_NAME}  v{APP_VERSION}")
        about_info.setStyleSheet("font-size: 15px; color: #60cdff; font-weight: bold;")
        about_layout.addWidget(about_info)

        about_desc = BodyLabel("AI 智能电子书重构平台 · PDF→EPUB 转换")
        about_desc.setStyleSheet("color: #888; font-size: 13px;")
        about_layout.addWidget(about_desc)

        about_btn_row = QHBoxLayout()
        about_btn_row.setSpacing(12)

        self.btn_check_update = PushButton("检查更新")
        self.btn_check_update.setIcon(FIF.SYNC)
        self.btn_check_update.clicked.connect(self._check_update)
        about_btn_row.addWidget(self.btn_check_update)

        self.btn_open_github = PushButton("项目主页")
        self.btn_open_github.setIcon(FIF.LINK)
        self.btn_open_github.clicked.connect(self._open_github)
        about_btn_row.addWidget(self.btn_open_github)

        about_btn_row.addStretch()
        about_layout.addLayout(about_btn_row)

        layout.addWidget(about_card)

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

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _load_settings(self):
        """从配置加载到 UI"""
        quality = Config.get_quality_mode()
        quality_map = {"quick": 0, "standard": 1, "precise": 2, "ai": 3}
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

        # AI 配置
        provider = Config.get_ai_provider()
        provider_map = {"none": 0, "gemini": 1}
        if provider in provider_map:
            self.api_provider.setCurrentIndex(provider_map[provider])

        model = Config.get_ai_model()
        model_keys = list(GEMINI_MODELS.keys())
        for i, k in enumerate(model_keys):
            if k == model:
                self.ai_model.setCurrentIndex(i)
                break

        key = Config.get_ai_api_key()
        if key:
            self.api_key.setText(key)

        self.ocr_correction.setChecked(Config.get_ai_correct_enabled())

    def _test_ai_connection(self):
        """测试 Gemini API 连接"""
        key = self.api_key.text().strip()
        if not key:
            from qfluentwidgets import InfoBar
            InfoBar.warning("提示", "请先输入 API Key", parent=self, duration=3000)
            return

        from app.constants import GEMINI_MODELS
        model_keys = list(GEMINI_MODELS.keys())
        model = model_keys[self.ai_model.currentIndex()]

        from engines.ai.llm_client import LLMClient
        client = LLMClient(api_key=key, model=model)

        from qfluentwidgets import InfoBar
        success, msg = client.test_connection()
        if success:
            InfoBar.success("连接成功", msg, parent=self, duration=5000)
        else:
            InfoBar.error("连接失败", msg, parent=self, duration=8000)

    def _on_save(self):
        """保存设置"""
        from app.config import Config
        from app.constants import GEMINI_MODELS

        # quality 用英文 key（与 pipeline quality_dpi_map 对齐）
        quality_keys = ["quick", "standard", "precise", "ai"]
        quality_key = quality_keys[self.quality.currentIndex()] if self.quality.currentIndex() < len(quality_keys) else "standard"
        settings = {
            "quality": quality_key,
            "dpi": self.dpi.value(),
            "parallel": self.parallel.value(),
            "indent_threshold": self.indent_threshold.value(),
            "gap_ratio": self.gap_ratio.text(),
            "detect_chapters": self.detect_chapters.isChecked(),
            "merge_cross_page": self.merge_cross_page.isChecked(),
            "epub_theme": self._theme_keys[self.default_theme.currentIndex()],
            "export_format": self.default_format.currentText(),
            "output_dir": self.output_dir.text().strip(),
        }

        Config.set_output_dir(self.output_dir.text().strip())

        # AI 配置持久化
        provider_map = {0: "none", 1: "gemini"}
        Config.set_ai_provider(provider_map.get(self.api_provider.currentIndex(), "none"))

        model_keys = list(GEMINI_MODELS.keys())
        Config.set_ai_model(model_keys[self.ai_model.currentIndex()])
        Config.set_ai_api_key(self.api_key.text().strip())
        Config.set_ai_correct_enabled(self.ocr_correction.isChecked())

        self.settings_changed.emit(settings)

    def _check_update(self):
        """手动检查更新"""
        from qfluentwidgets import InfoBar
        from PySide6.QtCore import QThread, Signal as QSignal

        class CheckThread(QThread):
            result = QSignal(object)

            def run(self):
                from core.updater import check_update
                info = check_update(timeout=10)
                self.result.emit(info)

        InfoBar.info("正在检查更新...", "", parent=self, duration=3000)
        self._update_thread = CheckThread()
        self._update_thread.result.connect(self._on_update_checked)
        self._update_thread.start()

    def _on_update_checked(self, info):
        from qfluentwidgets import InfoBar
        if info is None:
            InfoBar.warning("检查失败", "网络请求失败，请稍后重试", parent=self, duration=5000)
            return
        if not info.has_update:
            from app.constants import APP_VERSION
            InfoBar.success("已是最新版本", f"当前版本 v{APP_VERSION}", parent=self, duration=4000)
            return
        from ui.dialogs.update_dialog import UpdateDialog
        dialog = UpdateDialog(info, self)
        dialog.exec()

    def _open_github(self):
        """打开项目主页"""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        QDesktopServices.openUrl(QUrl("https://github.com/Acmerd-laofeng/PDF2BOOK_AI"))
