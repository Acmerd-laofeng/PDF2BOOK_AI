# -*- coding: utf-8 -*-
"""格式转换页面 — 独立于 OCR 转换页

支持 PDF/EPUB/TXT/MOBI 互转（MOBI 仅读取）。
拖入或选择文件 → 选择目标格式 → 开始转换 → 进度反馈 → 打开输出。
"""
import os
import subprocess

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFileDialog, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from qfluentwidgets import (
    TitleLabel, BodyLabel, PushButton, ComboBox, FluentIcon as FIF,
    InfoBar, InfoBarPosition, CardWidget, LineEdit,
    ProgressBar, StrongBodyLabel, CaptionLabel
)

from core.format_converter import FormatConverterService
from core.event_bus import event_bus
from app.format_constants import (
    SUPPORTED_FORMATS, FORMAT_CONVERSION_MATRIX, FORMAT_LABELS,
)


class FormatConvertPage(QWidget):
    """格式转换页面"""

    start_conversion = Signal(dict)

    def __init__(self):
        super().__init__()
        self.setObjectName("format_convert_page")
        self._service = FormatConverterService()
        self._current_file = None
        self._current_task_id = None
        self._last_output = ""
        self._init_ui()
        self._connect_events()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 30, 40, 30)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(20)

        # === 标题 ===
        header = QHBoxLayout()
        header.addWidget(TitleLabel("格式转换"))
        header.addStretch()
        content_layout.addLayout(header)

        desc = BodyLabel(
            "支持 PDF、EPUB、TXT、MOBI 格式互转（MOBI 仅可读取）。\n"
            "无需 OCR，直接提取文本并转换格式。"
        )
        desc.setStyleSheet("color: #888; font-size: 14px;")
        content_layout.addWidget(desc)

        # === 文件选择卡片 ===
        file_card = CardWidget()
        file_layout = QVBoxLayout(file_card)
        file_layout.setContentsMargins(24, 20, 24, 20)
        file_layout.setSpacing(12)

        file_layout.addWidget(StrongBodyLabel("选择文件"))

        file_row = QHBoxLayout()
        self.input_file = LineEdit()
        self.input_file.setPlaceholderText("点击下方按钮选择，或直接拖入文件")
        self.input_file.setReadOnly(True)
        file_row.addWidget(self.input_file)

        self.btn_browse = PushButton("浏览")
        self.btn_browse.setIcon(FIF.FOLDER)
        file_row.addWidget(self.btn_browse)
        file_layout.addLayout(file_row)

        self.lbl_drop = CaptionLabel("💡 支持拖放文件到此处")
        self.lbl_drop.setStyleSheet("color: #666;")
        file_layout.addWidget(self.lbl_drop)

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

        settings_layout.addWidget(StrongBodyLabel("转换设置"))

        # 目标格式
        format_row = QHBoxLayout()
        format_row.addWidget(BodyLabel("目标格式:"))
        self.combo_target = ComboBox()
        self.combo_target.setMinimumWidth(200)
        format_row.addWidget(self.combo_target)
        format_row.addStretch()
        settings_layout.addLayout(format_row)

        # EPUB 主题
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

        # 完成后自动打开目录开关
        auto_col = QVBoxLayout()
        auto_col.setSpacing(4)
        from qfluentwidgets import SwitchButton
        auto_col.addWidget(BodyLabel("完成后自动打开目录"))
        self.auto_open_switch = SwitchButton()
        self.auto_open_switch.setChecked(False)
        auto_col.addWidget(self.auto_open_switch)
        btn_row.addLayout(auto_col)
        btn_row.addSpacing(24)

        self.btn_convert = PushButton("开始转换")
        self.btn_convert.setIcon(FIF.ACCEPT)
        self.btn_convert.setEnabled(False)
        btn_row.addWidget(self.btn_convert)

        self.btn_cancel = PushButton("取消转换")
        self.btn_cancel.setIcon(FIF.CANCEL)
        self.btn_cancel.setVisible(False)
        btn_row.addWidget(self.btn_cancel)

        content_layout.addLayout(btn_row)

        # === 进度区 ===
        self.progress_card = CardWidget()
        progress_layout = QVBoxLayout(self.progress_card)
        progress_layout.setContentsMargins(24, 20, 24, 20)
        progress_layout.setSpacing(8)

        progress_layout.addWidget(StrongBodyLabel("转换进度"))
        self.progress_bar = ProgressBar()
        progress_layout.addWidget(self.progress_bar)

        # 大字百分比 + 预估时间
        progress_info_row = QHBoxLayout()
        progress_info_row.setSpacing(16)

        from PySide6.QtWidgets import QLabel
        self.lbl_progress_pct = QLabel("0%")
        self.lbl_progress_pct.setStyleSheet("font-size: 32px; font-weight: bold; color: #0078d4;")
        progress_info_row.addWidget(self.lbl_progress_pct)

        self.lbl_eta = QLabel("")
        self.lbl_eta.setStyleSheet("color: #888; font-size: 13px;")
        progress_info_row.addWidget(self.lbl_eta)
        progress_info_row.addStretch()
        progress_layout.addLayout(progress_info_row)

        self.lbl_progress_status = BodyLabel("等待开始...")
        self.lbl_progress_status.setStyleSheet("color: #888; font-size: 13px;")
        progress_layout.addWidget(self.lbl_progress_status)

        # 完成后操作按钮
        done_row = QHBoxLayout()
        done_row.addStretch()
        self.btn_open_dir = PushButton("打开输出目录")
        self.btn_open_dir.setIcon(FIF.FOLDER)
        self.btn_open_dir.setVisible(False)
        done_row.addWidget(self.btn_open_dir)
        progress_layout.addLayout(done_row)

        self.progress_card.setVisible(False)
        content_layout.addWidget(self.progress_card)

        content_layout.addStretch()
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        self.setAcceptDrops(True)

    def _connect_events(self):
        self.btn_browse.clicked.connect(self._on_browse)
        self.btn_output_browse.clicked.connect(self._on_output_browse)
        self.btn_convert.clicked.connect(self._on_convert)
        self.btn_cancel.clicked.connect(self._on_cancel)
        self.btn_open_dir.clicked.connect(self._on_open_dir)
        self.combo_target.currentIndexChanged.connect(self._on_target_changed)

        event_bus.progress.connect(self._on_progress)
        event_bus.finished.connect(self._on_finished)
        event_bus.error.connect(self._on_error)

    def _on_browse(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "",
            "支持的格式 (*.pdf *.epub *.txt *.mobi);;所有文件 (*.*)"
        )
        if path:
            self._set_file(path)

    def _on_output_browse(self):
        target = self.combo_target.currentData() or "txt"
        # 预填建议文件名
        if self._current_file:
            basename = os.path.splitext(os.path.basename(self._current_file))[0]
            default_name = f"{basename}.{target}"
        else:
            default_name = f"output.{target}"

        path, _ = QFileDialog.getSaveFileName(
            self, "选择输出路径", default_name,
            f"{target.upper()} 文件 (*.{target})"
        )
        if path:
            self.input_output.setText(path)

    def _set_file(self, file_path: str):
        self._current_file = file_path
        self.input_file.setText(file_path)

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

        # 预填输出路径
        basename = os.path.splitext(file_path)[0]
        if targets:
            self.input_output.setText(f"{basename}.{targets[0]}")

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
        self.btn_open_dir.setVisible(False)

    def _on_target_changed(self):
        target = self.combo_target.currentData() or ""
        self.theme_widget.setVisible(target == "epub")

        # 更新输出路径扩展名
        if self._current_file and target:
            current_output = self.input_output.text().strip()
            if current_output:
                base = os.path.splitext(current_output)[0]
                self.input_output.setText(f"{base}.{target}")
            else:
                basename = os.path.splitext(self._current_file)[0]
                self.input_output.setText(f"{basename}.{target}")

    def _on_convert(self):
        if not self._current_file:
            InfoBar.warning("提示", "请先选择文件", parent=self)
            return

        target = self.combo_target.currentData()
        if not target:
            InfoBar.warning("提示", "请选择目标格式", parent=self)
            return

        output_path = self.input_output.text().strip()
        options = {}

        if target == "epub":
            theme_keys = ["classic", "kindle", "modern", "eye_care"]
            idx = self.combo_theme.currentIndex()
            if 0 <= idx < len(theme_keys):
                options["theme"] = theme_keys[idx]

        task_id = self._service.create_task(
            source_path=self._current_file,
            target_format=target,
            output_path=output_path,
            options=options,
        )
        self._current_task_id = task_id

        # UI 切换到转换中状态
        self.progress_card.setVisible(True)
        self.progress_bar.setValue(0)
        self.lbl_progress_status.setText("正在转换...")
        self.btn_convert.setVisible(False)
        self.btn_cancel.setVisible(True)
        self.btn_open_dir.setVisible(False)

        self._service.start_task(task_id)
        event_bus.task_added.emit(task_id)

    def _on_cancel(self):
        if self._current_task_id:
            self._service.cancel_task(self._current_task_id)
            self.lbl_progress_status.setText("已取消")
            self._reset_buttons()

    def _on_progress(self, filename: str, percent: int):
        # 只响应当前格式转换任务的进度
        if self._current_task_id and self._current_file:
            expected = os.path.basename(self._current_file)
            if filename == expected and self._service.get_task_info(self._current_task_id).get("status") == "converting":
                self.progress_bar.setValue(percent)
                self.lbl_progress_pct.setText(f"{percent}%")
                self.lbl_progress_status.setText(f"转换中... {percent}%")

                # 预估剩余时间
                if percent > 3 and not hasattr(self, '_progress_start'):
                    from time import time
                    self._progress_start = time()
                if percent > 3 and hasattr(self, '_progress_start'):
                    from time import time
                    elapsed = time() - self._progress_start
                    eta = elapsed / percent * (100 - percent)
                    if eta < 60:
                        self.lbl_eta.setText(f"预计剩余 {int(eta)} 秒")
                    else:
                        self.lbl_eta.setText(f"预计剩余 {int(eta / 60)} 分 {int(eta % 60)} 秒")
                elif percent == 0:
                    self.lbl_eta.setText("")
                    if hasattr(self, '_progress_start'):
                        del self._progress_start

    def _on_finished(self, filename: str):
        # 只响应当前格式转换任务
        if self._current_task_id and self._current_file:
            expected = os.path.basename(self._current_file)
            if filename != expected:
                return
            info = self._service.get_task_info(self._current_task_id)
            if info.get("status") != "completed":
                return
            self.progress_bar.setValue(100)
            self.lbl_progress_pct.setText("100%")
            self.lbl_eta.setText("")
            self.lbl_progress_status.setText("✅ 转换完成！")

            self._last_output = info.get("output_path", "")
            self._reset_buttons()
            self.btn_open_dir.setVisible(bool(self._last_output))

            # 自动打开目录
            if self.auto_open_switch.isChecked() and self._last_output:
                import subprocess, os
                if os.path.exists(self._last_output):
                    if os.name == "nt":
                        subprocess.Popen(["explorer", "/select,", self._last_output])
                    else:
                        subprocess.Popen(["xdg-open", os.path.dirname(self._last_output)])

            InfoBar.success(
                "转换完成",
                f"{filename} 已成功转换",
                parent=self,
                position=InfoBarPosition.TOP,
                duration=5000,
            )

    def _on_error(self, filename: str, error_msg: str):
        # 只响应当前格式转换任务
        if self._current_task_id and self._current_file:
            expected = os.path.basename(self._current_file)
            if filename != expected:
                return
            self.lbl_progress_status.setText(f"❌ 错误: {error_msg}")
            self._reset_buttons()

            InfoBar.error(
                "转换失败",
                error_msg,
                parent=self,
                position=InfoBarPosition.TOP,
                duration=8000,
            )

    def _reset_buttons(self):
        """恢复操作按钮状态"""
        self.btn_convert.setVisible(True)
        self.btn_convert.setEnabled(True)
        self.btn_cancel.setVisible(False)

    def _on_open_dir(self):
        """打开输出文件所在目录"""
        path = self._last_output
        if path and os.path.exists(path):
            folder = os.path.dirname(path)
            if os.name == "nt":
                subprocess.Popen(["explorer", "/select,", path])
            else:
                subprocess.Popen(["xdg-open", folder])

    # === 拖放 ===
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet("FormatConvertPage { background: rgba(0, 120, 212, 0.08); border: 2px dashed #0078d4; border-radius: 12px; }")
            self.lbl_drop.setText("📁 松开以加载文件")
            self.lbl_drop.setStyleSheet("color: #0078d4; font-size: 16px; font-weight: bold;")

    def dragLeaveEvent(self, event):
        self.setStyleSheet("")
        self.lbl_drop.setText("💡 支持拖放文件到此处")
        self.lbl_drop.setStyleSheet("color: #666;")

    def dropEvent(self, event):
        self.setStyleSheet("")
        self.lbl_drop.setText("💡 支持拖放文件到此处")
        self.lbl_drop.setStyleSheet("color: #666;")
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self._set_file(path)
