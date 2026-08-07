# -*- coding: utf-8 -*-
"""任务进度卡片组件"""
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel
)
from PySide6.QtCore import Signal, Qt
from qfluentwidgets import ProgressBar, PushButton, FluentIcon as FIF


class TaskCard(QFrame):
    """单个任务卡片

    显示文件名、状态文字、进度条、取消/删除按钮。
    """

    cancel_clicked = Signal(int)   # task_id
    delete_clicked = Signal(int)   # task_id

    STATUS_TEXT = {
        "pending": "⏳ 等待中",
        "analyzing": "🔍 PDF 分析中",
        "ocr": "📖 OCR 识别中",
        "ai": "🤖 AI 增强中",
        "exporting": "📦 导出中",
        "completed": "✅ 已完成",
        "error": "❌ 错误",
        "cancelled": "⚪ 已取消",
    }

    def __init__(self, task_id: int, filename: str):
        super().__init__()
        self.task_id = task_id
        self.filename = filename
        self._status = "pending"
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            TaskCard, QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 10px;
                padding: 14px 16px;
            }
            QLabel { color: #ddd; }
            QLabel#filename { font-size: 15px; font-weight: bold; color: #fff; }
            QLabel#status { font-size: 13px; color: #888; }
            QLabel#percent { font-size: 13px; color: #60cdff; font-weight: bold; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # 第一行：文件名 + 按钮
        top = QHBoxLayout()
        lbl_file = QLabel(f"📄 {self.filename}")
        lbl_file.setObjectName("filename")
        top.addWidget(lbl_file)
        top.addStretch()

        self.btn_action = PushButton("取消")
        self.btn_action.setFixedWidth(80)
        self.btn_action.clicked.connect(self._on_action_clicked)
        top.addWidget(self.btn_action)
        layout.addLayout(top)

        # 第二行：状态 + 百分比
        mid = QHBoxLayout()
        self.lbl_status = QLabel("⏳ 等待中")
        self.lbl_status.setObjectName("status")
        mid.addWidget(self.lbl_status)
        mid.addStretch()

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

    def update_status(self, status: str, progress: int):
        """更新任务状态和进度"""
        self._status = status
        self.lbl_status.setText(self.STATUS_TEXT.get(status, status))

        if progress > 0:
            self.progress.setValue(progress)
            self.lbl_percent.setText(f"{progress}%")

        if status == "completed":
            self.progress.setValue(100)
            self.lbl_percent.setText("100%")
            self.btn_action.setText("删除")
            self.btn_action.setIcon(FIF.DELETE)
        elif status in ("error", "cancelled"):
            self.btn_action.setText("删除")
            self.btn_action.setIcon(FIF.DELETE)

    def update_progress(self, percent: int):
        """仅更新进度"""
        self.progress.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")
