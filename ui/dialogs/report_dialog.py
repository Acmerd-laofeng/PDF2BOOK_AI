# -*- coding: utf-8 -*-
"""转换完成报告弹窗"""
import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout
from qfluentwidgets import PushButton, FluentIcon as FIF
from ui.widgets.report_view import ReportView


class ReportDialog(QDialog):
    """转换完成报告弹窗

    显示转换统计：页数、段落、章节、字数、OCR准确率、耗时等。
    """

    def __init__(self, report_data: dict, parent=None):
        super().__init__(parent)
        self.report_data = report_data
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle("转换完成")
        self.setMinimumSize(520, 560)
        self.setStyleSheet("background: #1e1e1e;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 报告内容
        report_view = ReportView()
        report_view.set_report(self.report_data)
        layout.addWidget(report_view)

        # 按钮行
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 12, 20, 16)
        btn_layout.setSpacing(10)

        btn_layout.addStretch()

        btn_open = PushButton("打开输出目录")
        btn_open.setIcon(FIF.FOLDER)
        btn_open.clicked.connect(self._on_open_dir)
        btn_layout.addWidget(btn_open)

        btn_close = PushButton("关闭")
        btn_close.setIcon(FIF.ACCEPT)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)

        layout.addLayout(btn_layout)

    def _on_open_dir(self):
        """打开输出目录"""
        import subprocess
        output_path = self.report_data.get("output_path", "")
        if output_path:
            folder = os.path.dirname(output_path)
            if os.path.exists(folder):
                subprocess.Popen(f'explorer "{folder}"')
