# -*- coding: utf-8 -*-
"""格式转换 Worker — 独立 QThread

复用 Worker 模式，但运行 FormatPipeline 而非 OCR Pipeline。
"""
from PySide6.QtCore import QThread, Signal

from core.event_bus import event_bus


class FormatWorker(QThread):
    """格式转换 Worker 线程"""

    finished = Signal(int)          # task_id
    error = Signal(int, str)        # (task_id, error_msg)

    def __init__(self, pipeline, task_id: int, source_path: str,
                 target_format: str, output_path: str = "",
                 options: dict = None, parent=None):
        super().__init__(parent)
        self.pipeline = pipeline
        self.task_id = task_id
        self.source_path = source_path
        self.target_format = target_format
        self.output_path = output_path
        self.options = options
        self._cancelled = False

    def run(self):
        """线程入口"""
        try:
            result = self.pipeline.run(
                self.source_path,
                self.target_format,
                self.output_path,
                self.options,
            )
            if self._cancelled:
                return
            self.finished.emit(self.task_id)

        except Exception as e:
            if self._cancelled:
                return
            err_msg = str(e)
            event_bus.error.emit(self.source_path, err_msg)
            self.error.emit(self.task_id, err_msg)

    def cancel(self):
        """请求取消"""
        self._cancelled = True
        self.pipeline.cancel()
