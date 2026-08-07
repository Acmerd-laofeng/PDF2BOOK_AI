# -*- coding: utf-8 -*-
"""首页最近任务进度卡片"""
from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from qfluentwidgets import ProgressBar


class ProgressCard(QFrame):
    """最近转换任务的小卡片（首页用）"""

    def __init__(self, name: str):
        super().__init__()
        self.name = name
        self._init_ui()

    def _init_ui(self):
        self.setStyleSheet("""
            ProgressCard, QFrame {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 10px 14px;
            }
            QLabel { color: #ddd; font-size: 14px; }
            QLabel#status { color: #888; font-size: 12px; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(14, 10, 14, 10)

        top = QHBoxLayout()
        lbl_name = QLabel(f"📄 {self.name}")
        top.addWidget(lbl_name)
        top.addStretch()

        self.lbl_status = QLabel("等待中")
        self.lbl_status.setObjectName("status")
        top.addWidget(self.lbl_status)
        layout.addLayout(top)

        self.bar = ProgressBar()
        self.bar.setValue(0)
        self.bar.setFixedHeight(6)
        layout.addWidget(self.bar)

    def set_progress(self, value: int):
        """设置进度"""
        self.bar.setValue(value)
        if value >= 100:
            self.lbl_status.setText("✅ 完成")
            self.lbl_status.setStyleSheet("color: #4caf50; font-size: 12px;")
        elif value > 0:
            self.lbl_status.setText("处理中")
            self.lbl_status.setStyleSheet("color: #60cdff; font-size: 12px;")
        else:
            self.lbl_status.setText("等待中")
            self.lbl_status.setStyleSheet("color: #888; font-size: 12px;")
