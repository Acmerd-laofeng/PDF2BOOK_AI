# -*- coding: utf-8 -*-
"""格式转换页面 — 独立于 OCR 转换页

支持 PDF/EPUB/TXT/MOBI 互转。
拖入或选择文件 → 选择目标格式 → 开始转换 → 进度反馈。
"""
import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    TitleLabel, BodyLabel, PushButton, ComboBox, FluentIcon as FIF,
    InfoBar, InfoBarPosition, CardWidget, IconWidget, LineEdit,
    ProgressBar, StrongBodyLabel, CaptionLabel
)

from core.format_converter import FormatConverterService
from core.event_bus import event_bus
from app.format_constants import (
    SUPPORTED_FORMATS, FORMAT_CONVERSION_MATRIX, FORMAT_LABELS,
    FORMAT_DESCRIPTIONS, DEFAULT_EXPORT_OPTIONS
)


class FormatConvertPage(QWidget):
    """格式转换页面"""

    start_conversion = Signal(dict)  # 转换参数

    def __init__(self):
        super().__init__()
        self.setObjectName("format_convert_page")
        self._service = FormatConverterService()
        self._current_file = None
        self._init_ui()
        self._connect_events()

    def _init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(16)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # 标题
        header = QHBoxLayout()
        header.addWidget(TitleLabel("格式转换"))
        header.addStretch()

        self.btn_help = PushButton("使用说明")
        self.btn_help.setIcon(FIF.QUESTION)
        header.addWidget(self.btn_help)
        content_layout.addLayout(header)

        # 说明文字
        desc = BodyLabel(
            "支持 PDF、EPUB、TXT、MOBI 格式互转。\n"
            "无需 OCR，直接提取文本并转换格式。"
        )
        desc.setStyleSheet("color: #888; font-size: 14px;")
        content_layout.addWidget(desc)

        # === 文件选择卡片 ===
        file_card = CardWidget()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(24, 20, 24, 20)
        file_layout.setSpacing(12)

        file_title = StrongBodyLabel("选择文件")
        file_layout.addWidget(file_title)

        file_row = QHBoxLayout()
        self.input_file = LineEdit()
        self.input_file.setPlaceholderText("点击下方按钮选择，或直接拖入文件")
        self.input_file.setReadOnly(True)
        file_row.addWidget(self.input_file)

        self.btn_browse = PushButton("浏览")
        self.btn_browse.setIcon(FIF.FOLDER)
        file_row.addWidget(self.btn_browse)
        file_layout.addLayout(file_row)

        # 拖放提示
        self.lbl_drop = CaptionLabel("💡 支持拖放文件到此处")
        self.lbl_drop.setStyleSheet("color: #666;")
        file_layout.addWidget(self.lbl_drop)

        # 文件信息
        self.lbl_file_info = BodyLabel("")
        self.lbl_file_info.setStyleSheet("color: #0078d4; font-size: 13px;")
        self.lbl_file_info.setVisible(False)
        file_layout.addWidget(self.lbl_file_info)

        content_layout.addWidget(file_card)

        # === 转换设置卡片 ===
        settings_card = CardWidget()
        settings_layout = QVBoxLayout(settings_card)
        settings_layout.setContentsMargins(24, 20, 24, 20)
        settings_layout.setSpacing(12)

        settings_title = StrongBodyLabel("转换设置")
        settings_layout.addWidget(settings_title)

        # 目标格式
        format_row = QHBoxLayout()
        format_row.addWidget(BodyLabel("目标格式:"))

        self.combo_target = ComboBox()
        self.combo_target.setMinimumWidth(200)
        format_row.addWidget(self.combo_target)
        format_row.addStretch()
        settings_layout.addLayout(format_row)

        # EPUB 主题选项（仅 EPUB 目标时显示）
        self.theme_row = QHBoxLayout()
        self.theme_row.addWidget(BodyLabel("EPUB 主题:"))
        self.combo_theme = ComboBox()
        self.combo_theme.addItems(["经典阅读", "Kindle 风格", "现代简洁", "护眼模式"])
        self.theme_row.addWidget(self.combo_theme)
        self.theme_row.addStretch()
        self.theme_widget = QWidget()
        self.theme_widget.setLayout(self.theme_row)
        self.theme_widget.setVisible(False)
        settings_layout.addWidget(self.theme_widget)

        # 输出路径
        output_row = QHBoxLayout()
        output_row.addWidget(BodyLabel("输出路径:"))
        self.input_output = LineEdit()
        self.input_output.setPlaceholderText("留空则与源文件同目录")
        output_row.addWidget(self.input_output)

        self.btn_output_browse = PushButton("浏览")
        self.btn_output_browse.setIcon(FIF.FOLDER)
        output_row.addWidget(self.btn_output_browse)
        settings_layout.addLayout(output_row)

        content_layout.addWidget(settings_card)

        # === 操作按钮 ===
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_convert = PushButton("开始转换")
        self.btn_convert.setIcon(FIF.ACCEPT)
        self.btn_convert.setEnabled(False)
        btn_row.addWidget(self.btn_convert)

        content_layout.addLayout(btn_row)

        # === 进度区 ===
        self.progress_card = CardWidget()
        progress_layout = QVBoxLayout(self.progress_card)
        progress_layout.setContentsMargins(24, 20, 24, 20)
        progress_layout.setSpacing(8)

        self.lbl_progress_title = StrongBodyLabel("转换进度")
        progress_layout.addWidget(self.lbl_progress_title)

        self.progress_bar = ProgressBar()
        progress_layout.addWidget(self.progress_bar)

        self.lbl_progress_status = BodyLabel("等待开始...")
        self.lbl_progress_status.setStyleSheet("color: #888; font-size: 13px;")
        progress_layout.addWidget(self.lbl_progress_status)

        self.progress_card.setVisible(False)
        content_layout.addWidget(self.progress_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # 设置拖放
        self.setAcceptDrops(True)

    def _connect_events(self):
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_output_browse.clicked.connect(self._on_output_browse)
        self.btn_convert.clicked.connect(self._on_convert)
        self.combo_target.currentIndexChanged.connect(self._on_target_changed)

        # EventBus
        event_bus.progress.connect(self._on_progress)
        event_bus.finished.connect(self._on_finished)
        event_bus.error.connect(self._on_error)

    def _on_browse(self):
        """选择源文件"""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "选择文件",
            "",
            "支持的格式 (*.pdf *.epub *.txt *.mobi);;所有文件 (*.*)"
        )
        if path:
            self._set_file(path)

    def _on_output_browse(self):
        """选择输出路径"""
        target = self.combo_target.currentData() or self.combo_target.currentText().lower()
        path, _ = QFileDialog.getSaveFileName(
            self,
            "选择输出路径",
            "",
            f"{target.upper()} 文件 (*.{target})"
        )
        if path:
            self.input_output.setText(path)

    def _set_file(self, file_path: str):
        """设置源文件"""
        self._current_file = file_path
        self.input_file.setText(file_path)

        # 检测格式
        ext = os.path.splitext(file_path)[1].lower().lstrip(".")
        if ext not in SUPPORTED_FORMATS:
            InfoBar.warning(
                "不支持的格式",
                f".{ext} 暂不支持，支持: {', '.join(SUPPORTED_FORMATS)}",
                parent=self, duration=5000
            )
            self._current_file = None
            self.input_file.clear()
            self.btn_convert.setEnabled(False)
            return

        # 更新目标格式选项
        targets = FORMAT_CONVERSION_MATRIX.get(ext, [])
        self.combo_target.clear()
        for t in targets:
            self.combo_target.addItem(FORMAT_LABELS.get(t, t), userData=t)

        # 文件信息
        size = os.path.getsize(file_path)
        if size < 1024:
            size_str = f"{size} B"
        elif size < 1024 * 1024:
            size_str = f"{size / 1024:.1f} KB"
        else:
            size_str = f"{size / 1024 / 1024:.1f} MB"

        self.lbl_file_info.setText(
            f"📄 {os.path.basename(file_path)}  |  "
            f"格式: {ext.upper()}  |  大小: {size_str}  |  "
            f"可转换为: {', '.join(FORMAT_LABELS.get(t, t) for t in targets)}"
        )
        self.lbl_file_info.setVisible(True)

        self.btn_convert.setEnabled(bool(targets))

    def _on_target_changed(self):
        """目标格式变化"""
        target = self.combo_target.currentData() or ""
        # EPUB 目标时显示主题选项
        self.theme_widget.setVisible(target == "epub")

    def _on_convert(self):
        """开始转换"""
        if not self._current_file:
            InfoBar.warning("提示", "请先选择文件", parent=self)
            return

        target = self.combo_target.currentData()
        if not target:
            InfoBar.warning("提示", "请选择目标格式", parent=self)
            return

        output_path = self.input_output.text().strip()
        options = {}

        # EPUB 主题
        if target == "epub":
            theme_keys = ["classic", "kindle", "modern", "eye_care"]
            idx = self.combo_theme.currentIndex()
            if 0 <= idx < len(theme_keys):
                options["theme"] = theme_keys[idx]

        # 创建任务
        task_id = self._service.create_task(
            source_path=self._current_file,
            target_format=target,
            output_path=output_path,
            options=options,
        )

        # 显示进度区
        self.progress_card.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("正在转换...")
        self.btn_convert.setEnabled(False)

        # 启动转换
        self._service.start_task(task_id)

        # 添加到任务页
        filename = os.path.basename(self._current_file)
        event_bus.task_added.emit(task_id)

    def _on_progress(self, filename: str, percent: int):
        """进度更新"""
        if self._current_file and os.path.basename(self._current_file) == filename:
            self.progress_bar.setValue(percent)
            self.lbl_progress_status.setText(f"转换中... {percent}%")

    def _on_finished(self, filename: str):
        """转换完成"""
        if self._current_file and os.path.basename(self._current_file) == filename:
            self.progress_bar.setValue(100)
            self.lbl_progress_status.setText("转换完成！")
            self.btn_convert.setEnabled(True)

            InfoBar.success(
                "转换完成",
                f"{filename} 已成功转换",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )

    def _on_error(self, filename: str, error_msg: str):
        """转换错误"""
        if self._current_file and os.path.basename(self._current_file) == filename:
            self.lbl_progress_status.setText(f"错误: {error_msg}")
            self.btn_convert.setEnabled(True)

            InfoBar.error(
                "转换失败",
                error_msg,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=8000,
            )

    # === 拖放支持 ===

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("background: #1a3a1a;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")

    def dropEvent(self, event):
        self.setStyleSheet("")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._set_file(path)
