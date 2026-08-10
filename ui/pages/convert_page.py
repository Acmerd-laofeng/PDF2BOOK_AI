# -*- coding: utf-8 -*-
"""转换中心 - 模式选择 + 高级设置 + 进度 + 日志"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit, QScrollArea
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import (
    ComboBox, ProgressBar, PushButton, SpinBox, SwitchButton, LineEdit,
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

        # 转换模式可视化卡片
        mode_cards_row = QHBoxLayout()
        mode_cards_row.setSpacing(8)

        self._mode_cards = []
        mode_descs = [
            ("quick", "⚡", "快速", "150 DPI\n纯文字 PDF"),
            ("standard", "✅", "推荐", "300 DPI\n大多数扫描版"),
            ("precise", "🎯", "极致", "400 DPI\n小字/古籍"),
            ("ai", "🤖", "AI增强", "300 DPI + AI\n需联网"),
        ]
        for key, emoji, name, desc in mode_descs:
            card = CardWidget()
            card.setFixedHeight(80)
            card.setCursor(Qt.PointingHandCursor)
            card._mode_key = key
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(12, 8, 12, 8)
            card_layout.setSpacing(2)
            card_layout.setAlignment(Qt.AlignCenter)

            lbl_emoji = QLabel(emoji)
            lbl_emoji.setAlignment(Qt.AlignCenter)
            lbl_emoji.setStyleSheet("font-size: 20px;")
            card_layout.addWidget(lbl_emoji)

            lbl_name = QLabel(name)
            lbl_name.setAlignment(Qt.AlignCenter)
            lbl_name.setStyleSheet("font-size: 13px; font-weight: bold; color: #fff;")
            card_layout.addWidget(lbl_name)

            lbl_desc = QLabel(desc)
            lbl_desc.setAlignment(Qt.AlignCenter)
            lbl_desc.setStyleSheet("font-size: 10px; color: #888;")
            card_layout.addWidget(lbl_desc)

            card.mousePressEvent = lambda e, k=key: self._select_mode_card(k)
            self._mode_cards.append(card)
            mode_cards_row.addWidget(card)

        mode_layout.addLayout(mode_cards_row)

        # 隐藏旧的 combo（保留逻辑兼容）
        self.mode_combo = ComboBox()
        self.mode_combo.setVisible(False)

        # 模式说明
        self.lbl_mode_desc = BodyLabel("")
        self.lbl_mode_desc.setStyleSheet("color: #888; font-size: 13px;")
        mode_layout.addWidget(self.lbl_mode_desc)
        self._selected_mode = "standard"
        self._select_mode_card("standard")

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
        chapter_col.setSpacing(4)
        chapter_col.addWidget(BodyLabel("章节标题检测"))
        self.chapter_switch = SwitchButton()
        self.chapter_switch.setChecked(True)
        chapter_col.addWidget(self.chapter_switch)
        switch_layout.addLayout(chapter_col)

        cross_col = QVBoxLayout()
        cross_col.setSpacing(4)
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

        # === 导出路径 ===
        output_card = CardWidget()
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(20, 16, 20, 16)
        output_layout.setSpacing(10)

        output_title = BodyLabel("导出路径")
        output_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        output_layout.addWidget(output_title)

        output_row = QHBoxLayout()
        output_row.setSpacing(8)

        self.output_path_edit = LineEdit()
        self.output_path_edit.setPlaceholderText("留空则导出到 PDF 同级目录")
        self.output_path_edit.setText(self._load_default_output_dir())
        output_row.addWidget(self.output_path_edit, stretch=1)

        self.btn_browse = PushButton("浏览")
        self.btn_browse.setFixedHeight(33)
        self.btn_browse.setFixedWidth(80)
        self.btn_browse.setIcon(FIF.FOLDER)
        self.btn_browse.clicked.connect(self._on_browse_output)
        output_row.addWidget(self.btn_browse)

        output_layout.addLayout(output_row)

        # 提示
        lbl_output_hint = BodyLabel("默认导出到输入文件的同一层级")
        lbl_output_hint.setStyleSheet("color: #888; font-size: 13px;")
        output_layout.addWidget(lbl_output_hint)

        layout.addWidget(output_card)

        # === 进度 + 日志 ===
        progress_card = CardWidget()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(20, 16, 20, 16)
        progress_layout.setSpacing(10)

        progress_title = BodyLabel("转换进度")
        progress_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fff;")
        progress_layout.addWidget(progress_title)

        # 完成后自动打开目录开关
        auto_open_row = QHBoxLayout()
        auto_open_col = QVBoxLayout()
        auto_open_col.setSpacing(4)
        auto_open_col.addWidget(BodyLabel("转换完成后自动打开目录"))
        self.auto_open_switch = SwitchButton()
        self.auto_open_switch.setChecked(False)
        auto_open_col.addWidget(self.auto_open_switch)
        auto_open_row.addLayout(auto_open_col)
        auto_open_row.addStretch()
        progress_layout.addLayout(auto_open_row)

        self.progress_bar = ProgressBar()
        progress_layout.addWidget(self.progress_bar)

        # 进度大字 + 预估剩余
        progress_info_row = QHBoxLayout()
        progress_info_row.setSpacing(16)

        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setStyleSheet("font-size: 32px; font-weight: bold; color: #0078d4;")
        progress_info_row.addWidget(self.lbl_progress_pct)

        self.lbl_eta = QLabel("")
        self.lbl_eta.setStyleSheet("color: #888; font-size: 13px;")
        progress_info_row.addWidget(self.lbl_eta)

        progress_info_row.addStretch()
        progress_layout.addLayout(progress_info_row)

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

        # 状态指示器
        self.lbl_status = BodyLabel("● 空闲")
        self.lbl_status.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.lbl_status)

        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _load_default_output_dir(self) -> str:
        """从配置加载默认导出目录"""
        from app.config import Config
        return Config.get_output_dir()

    def _on_browse_output(self):
        """选择导出目录"""
        from PySide6.QtWidgets import QFileDialog
        dir_path = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if dir_path:
            self.output_path_edit.setText(dir_path)

    def _select_mode_card(self, key: str):
        """可视化模式卡片选择"""
        self._selected_mode = key
        for card in self._mode_cards:
            is_selected = card._mode_key == key
            if is_selected:
                card.setStyleSheet("""
                    CardWidget {
                        background: rgba(0, 120, 212, 0.15);
                        border: 2px solid #0078d4;
                        border-radius: 8px;
                    }
                """)
            else:
                card.setStyleSheet("""
                    CardWidget {
                        background: rgba(255, 255, 255, 0.05);
                        border: 2px solid transparent;
                        border-radius: 8px;
                    }
                    CardWidget:hover {
                        border: 2px solid #3399ff;
                    }
                """)

        # 更新说明
        descs = {
            "quick": "⚡ 速度快 · 适合纯文字 PDF",
            "standard": "✅ 推荐 · 适合大多数扫描版",
            "precise": "🎯 高精度 · 适合小字/古籍",
            "ai": "🤖 AI 纠错 · 需联网 · 质量最佳",
        }
        self.lbl_mode_desc.setText(descs.get(key, ""))

        # 同步 combo 索引（逻辑兼容）
        keys = list(CONVERT_MODES.keys())
        if key in keys:
            self.mode_combo.setCurrentIndex(keys.index(key))

    def _on_mode_changed(self):
        """combo 变化时同步可视化卡片"""
        idx = self.mode_combo.currentIndex()
        keys = list(CONVERT_MODES.keys())
        if idx < len(keys):
            self._select_mode_card(keys[idx])

    def _on_theme_selected(self, theme_key: str):
        """主题单选：选中一个，取消其他"""
        self._selected_theme = theme_key
        for card in self.theme_cards:
            card.set_selected(card.theme_key == theme_key)

    def _on_start_clicked(self):
        settings = self.get_settings()
        self.append_log(f"开始转换 · 模式={settings['quality']} · DPI={settings['dpi']}")
        # 保存导出路径到配置
        from app.config import Config
        Config.set_output_dir(settings['output_dir'])
        self.lbl_status.setText("● 转换中...")
        self.lbl_status.setStyleSheet("color: #60cdff; font-size: 12px;")
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
        quality = getattr(self, '_selected_mode', 'standard')
        return {
            "quality": quality,
            "dpi": self.dpi_spin.value(),
            "indent_threshold": self.indent_spin.value(),
            "detect_chapters": self.chapter_switch.isChecked(),
            "merge_cross_page": self.cross_page_switch.isChecked(),
            "epub_theme": self._selected_theme,
            "output_dir": self.output_path_edit.text().strip(),
            "auto_open_dir": self.auto_open_switch.isChecked(),
        }

    def update_progress(self, value: int):
        """更新进度条"""
        self.progress_bar.setValue(value)
        self.lbl_progress_pct.setText(f"{value}%")
        self.lbl_progress_text.setText(f"{value}%")

        if value >= 100:
            self.lbl_status.setText("● 已完成")
            self.lbl_status.setStyleSheet("color: #43e97b; font-size: 12px;")
        elif value > 0:
            self.lbl_status.setText("● 转换中...")
            self.lbl_status.setStyleSheet("color: #60cdff; font-size: 12px;")

        # 预估剩余时间
        if value > 0 and not hasattr(self, '_progress_start'):
            from time import time
            self._progress_start = time()
        if value > 3 and hasattr(self, '_progress_start'):
            from time import time
            elapsed = time() - self._progress_start
            eta = elapsed / value * (100 - value)
            if eta < 60:
                self.lbl_eta.setText(f"预计剩余 {int(eta)} 秒")
            else:
                self.lbl_eta.setText(f"预计剩余 {int(eta / 60)} 分 {int(eta % 60)} 秒")
        elif value == 0:
            self.lbl_eta.setText("")
            if hasattr(self, '_progress_start'):
                del self._progress_start

    def append_log(self, msg: str):
        """追加日志（支持颜色分级）"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")

        # 根据内容着色
        if any(kw in msg for kw in ["错误", "失败", "异常", "Error", "error"]):
            color = "#f5576c"
        elif any(kw in msg for kw in ["完成", "成功", "Done", "success"]):
            color = "#43e97b"
        elif any(kw in msg for kw in ["警告", "Warning", "warn"]):
            color = "#fa709a"
        elif "开始" in msg or "启动" in msg:
            color = "#60cdff"
        else:
            color = "#ccc"

        self.log_text.append(f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">{msg}</span>')

        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.End)
        self.log_text.setTextCursor(cursor)

    def reset(self):
        """重置状态"""
        self.progress_bar.setValue(0)
        self.lbl_progress_pct.setText("0%")
        self.lbl_eta.setText("")
        self.lbl_progress_text.setText("就绪")
        self.log_text.clear()
        if hasattr(self, '_progress_start'):
            del self._progress_start
