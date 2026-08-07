# -*- coding: utf-8 -*-
"""多线程 Worker - QThread 子类

在独立线程中运行 Pipeline，通过 EventBus 更新 UI。
关键：避免 UI 线程阻塞。
"""
from PySide6.QtCore import QThread, Signal

from core.event_bus import event_bus


class Worker(QThread):
    """转换 Worker 线程"""

    # Worker 自身信号（与 EventBus 互补，方便直接连接）
    finished = Signal(int)          # task_id
    error = Signal(int, str)        # (task_id, error_msg)
    progress = Signal(int, int)     # (task_id, percent)

    def __init__(self, pipeline, task, parent=None):
        super().__init__(parent)
        self.pipeline = pipeline
        self.task = task
        self._cancelled = False

    def run(self):
        """线程入口"""
        try:
            result = self.pipeline.run(self.task)
            if self._cancelled:
                return

            # 发送报告
            if result:
                event_bus.report_ready.emit(result)
                event_bus.finished.emit(self.task.filename)
            self.finished.emit(self.task.id)

        except Exception as e:
            if self._cancelled:
                return
            err_msg = str(e)
            event_bus.error.emit(self.task.filename, err_msg)
            self.error.emit(self.task.id, err_msg)

    def cancel(self):
        """请求取消（非阻塞，Pipeline 会在下一页检查）"""
        self._cancelled = True
        self.pipeline.cancel()

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled
