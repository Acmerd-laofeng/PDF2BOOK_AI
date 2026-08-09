# -*- coding: utf-8 -*-
"""任务进度卡片组件 — 增加耗时显示 + 打开目录按钮"""
import os
import time
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import ProgressBar, PushButton, FluentIcon as FIF


class TaskCard(QFrame):
    """单个任务卡片

    显示文件名、状态文字、进度条、耗时、取消/删除/打开目录按钮。
    """

    cancel_clicked = Signal(int)   # task_id
    delete_clicked = Signal(int)   # task_id
    open_dir_clicked = Signal(int)  # task_id

    STATUS_TEXT = {
        "pending": "⏳ 等待中",
        "analyzing": "🔍 PDF 分析中",
        "ocr": "📖 OCR 识别中",
        "ai": "🤖 AI 增强中",
        "exporting": "📦 导出中",
        "completed": "✅ 已完成",
        "error": "❌ 错误",
        "cancelled": "⚪ 已取消",
        "converting": "🔄 转换中",
    }

    STATUS_COLOR = {
        "pending": "#888",
        "analyzing": "#60cdff",
        "ocr": "#60cdff",
        "ai": "#a78bfa",
        "exporting": "#60cdff",
        "completed": "#4caf50",
        "error": "#ef4444",
        "cancelled": "#888",
        "converting": "#60cdff",
    }

    def __init__(self, task_id: int, filename: str):
        super().__init__()
        self.task_id = task_id
        self.filename = filename
        self._status = "pending"
        self._start_time = None
        self._end_time = None
        self._output_path = ""
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            TaskCard, QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 14px 16px;
            }
            TaskCard:hover, QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QLabel { color: #ddd; }
            QLabel#filename { font-size: 15px; font-weight: bold; color: #fff; }
            QLabel#status { font-size: 13px; }
            QLabel#percent { font-size: 13px; color: #60cdff; font-weight: bold; }
            QLabel#duration { font-size: 12px; color: #666; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 第一行：文件名 + 按钮
        top = QHBoxLayout()
        lbl_file = QLabel(f"📄 {self.filename}")
        lbl_file.setObjectName("filename")
        top.addWidget(lbl_file)
        top.addStretch()

        # 打开目录按钮（完成后显示）
        self.btn_open = PushButton("打开")
        self.btn_open.setFixedWidth(70)
        self.btn_open.setIcon(FIF.FOLDER)
        self.btn_open.setVisible(False)
        self.btn_open.clicked.connect(lambda: self.open_dir_clicked.emit(self.task_id))
        top.addWidget(self.btn_open)

        self.btn_action = PushButton("取消")
        self.btn_action.setFixedWidth(80)
        self.btn_action.clicked.connect(self._on_action_clicked)
        top.addWidget(self.btn_action)
        layout.addLayout(top)

        # 第二行：状态 + 百分比 + 耗时
        mid = QHBoxLayout()
        self.lbl_status = QLabel("⏳ 等待中")
        self.lbl_status.setObjectName("status")
        mid.addWidget(self.lbl_status)
        mid.addStretch()

        self.lbl_duration = QLabel("")
        self.lbl_duration.setObjectName("duration")
        mid.addWidget(self.lbl_duration)

        self.lbl_percent = QLabel("0%")
        self.lbl_percent.setObjectName("percent")
        mid.addWidget(self.lbl_percent)
        layout.addLayout(mid)

        # 第三行：进度条
        self.progress = ProgressBar()
        self.progress.setValue(0)
        layout.addWidget(self.progress)

    def _on_action_clicked(self):
        """按钮点击：根据状态执行取消或删除"""
        if self._status in ("completed", "error", "cancelled"):
            self.delete_clicked.emit(self.task_id)
        else:
            self.cancel_clicked.emit(self.task_id)

    def _format_duration(self, seconds: float) -> str:
        """格式化耗时"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

    def update_status(self, status: str, progress: int):
        """更新任务状态和进度"""
        # 记录时间
        if status in ("analyzing", "ocr", "ai", "exporting", "converting") and self._start_time is None:
            self._start_time = time.time()
        if status in ("completed", "error", "cancelled") and self._end_time is None:
            self._end_time = time.time()
            if self._start_time:
                dur = self._end_time - self._start_time
                self.lbl_duration.setText(f"⏱ {self._format_duration(dur)}")

        self._status = status
        color = self.STATUS_COLOR.get(status, "#888")
        self.lbl_status.setText(self.STATUS_TEXT.get(status, status))
        self.lbl_status.setStyleSheet(f"font-size: 13px; color: {color};")

        if progress > 0:
            self.progress.setValue(progress)
            self.lbl_percent.setText(f"{progress}%")

        if status == "completed":
            self.progress.setValue(100)
            self.lbl_percent.setText("100%")
            self.btn_action.setText("删除")
            self.btn_action.setIcon(FIF.DELETE)
            self.btn_open.setVisible(bool(self._output_path))
        elif status in ("error", "cancelled"):
            self.btn_action.setText("删除")
            self.btn_action.setIcon(FIF.DELETE)
            self.btn_open.setVisible(False)

    def update_progress(self, percent: int):
        """仅更新进度"""
        self.progress.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")

    def set_output_path(self, path: str):
        """设置输出路径（用于打开目录按钮）"""
        self._output_path = path
        if self._status == "completed":
            self.btn_open.setVisible(bool(path))
