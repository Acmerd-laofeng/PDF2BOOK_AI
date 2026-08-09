# -*- coding: utf-8 -*-
"""文件拖拽区域组件 — 支持多格式"""
import os
from PySide6.QtWidgets import QLabel, QFileDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent


class PDFDropArea(QLabel):
    """文件拖拽上传区域

    支持拖拽和点击选择文件。
    支持 PDF / EPUB / TXT / MOBI 格式。
    """

    file_dropped = Signal(str)

    SUPPORTED_EXTS = {'.pdf', '.epub', '.txt', '.mobi'}

    def __init__(self, supported_exts=None):
        super().__init__()
        if supported_exts:
            self.SUPPORTED_EXTS = supported_exts
        self._default_text = "📄\n\n拖入文件 或 点击选择\n\n支持: " + " / ".join(ext.upper().lstrip('.') for ext in sorted(self.SUPPORTED_EXTS))
        self.setText(self._default_text)
        self.setAlignment(Qt.AlignCenter)
        self.setAcceptDrops(True)
        self.setMinimumHeight(180)
        self.setCursor(Qt.PointingHandCursor)
        self._apply_style(False)

    def _apply_style(self, hover: bool):
        """应用样式"""
        if hover:
            border_color = "#0078d4"
            bg = "rgba(0, 120, 212, 0.10)"
        else:
            border_color = "#444"
            bg = "rgba(255, 255, 255, 0.03)"
        self.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed {border_color};
                border-radius: 16px;
                font-size: 16px;
                background: {bg};
                color: #aaa;
                padding: 30px;
            }}
        """)

    def _is_supported(self, path: str) -> bool:
        return os.path.splitext(path.lower())[1] in self.SUPPORTED_EXTS

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(self._is_supported(url.toLocalFile()) for url in urls):
                event.acceptProposedAction()
                self._apply_style(True)

    def dragLeaveEvent(self, event):
        self._apply_style(False)

    def dropEvent(self, event: QDropEvent):
        self._apply_style(False)
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if self._is_supported(path):
                filename = os.path.basename(path)
                size = os.path.getsize(path)
                if size < 1024 * 1024:
                    size_str = f"{size / 1024:.0f} KB"
                else:
                    size_str = f"{size / 1024 / 1024:.1f} MB"
                self.setText(f"📄 {filename}\n{size_str}")
                self.file_dropped.emit(path)
                return

    def mousePressEvent(self, event):
        """点击选择文件"""
        exts = " ".join(f"*{ext}" for ext in sorted(self.SUPPORTED_EXTS))
        filter_str = f"支持的文件 ({exts});;所有文件 (*.*)"
        path, _ = QFileDialog.getOpenFileName(self, "选择文件", "", filter_str)
        if path and self._is_supported(path):
            filename = os.path.basename(path)
            size = os.path.getsize(path)
            if size < 1024 * 1024:
                size_str = f"{size / 1024:.0f} KB"
            else:
                size_str = f"{size / 1024 / 1024:.1f} MB"
            self.setText(f"📄 {filename}\n{size_str}")
            self.file_dropped.emit(path)

    def reset(self):
        """重置为默认状态"""
        self.setText(self._default_text)
        self._apply_style(False)
