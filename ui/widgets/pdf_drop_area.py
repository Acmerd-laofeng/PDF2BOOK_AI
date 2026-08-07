# -*- coding: utf-8 -*-
"""PDF 拖拽区域组件"""
import os
from PySide6.QtWidgets import QLabel, QFileDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class PDFDropArea(QLabel):
    """PDF 文件拖拽上传区域

    支持拖拽和点击选择文件。
    """

    file_dropped = Signal(str)

    def __init__(self):
        super().__init__()
        self._default_text = "📘\n\n拖入 PDF 文件\n或点击选择"
        self.setText(self._default_text)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

    def _apply_style(self, hover: bool):
        """应用样式"""
        if hover:
            border_color = "#0078d4"
            bg = "rgba(0, 120, 212, 0.08)"
        else:
            border_color = "#555"
            bg = "rgba(255, 255, 255, 0.03)"
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {border_color};
                border-radius: 16px;
                font-size: 18px;
                background: {bg};
                color: #aaa;
                padding: 30px;
            }}
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(url.toLocalFile().lower().endswith('.pdf') for url in urls):
                event.acceptProposedAction()
                self._apply_style(True)

    def dragLeaveEvent(self, event):
        self._apply_style(False)

    def dropEvent(self, event: QDropEvent):
        self._apply_style(False)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path.lower().endswith('.pdf'):
                filename = os.path.basename(path)
                self.setText(f"📄 {filename}")
                self.file_dropped.emit(path)
                return

    def mousePressEvent(self, event):
        """点击选择文件"""
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf)"
        )
        if path:
            filename = os.path.basename(path)
            self.setText(f"📄 {filename}")
            self.file_dropped.emit(path)

    def reset(self):
        """重置为默认状态"""
        self.setText(self._default_text)
        self._apply_style(False)
