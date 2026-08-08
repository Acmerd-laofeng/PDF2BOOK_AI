# -*- coding: utf-8 -*-
"""格式转换服务层 — UI 调用入口

职责：
- 创建/启动/取消格式转换任务
- 管理 FormatWorker 线程
- 数据库持久化（任务 + 书库）
- EventBus 信号桥接
- 自动生成 task_id（独立计数器，不与 OCR Task 冲突）
"""
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from core.format_pipeline import FormatPipeline
from core.format_worker import FormatWorker
from core.event_bus import event_bus
from app.format_constants import (
    FORMAT_CONVERSION_MATRIX,
    FORMAT_LABELS,
    DEFAULT_EXPORT_OPTIONS,
)


class FormatConverterService:
    """格式转换服务"""

    # 独立 task_id 计数器（从 10000 起，避免与 OCR task_id 冲突）
    _next_task_id = 10000

    def __init__(self, db=None):
        self.db = db
        self.pipeline = FormatPipeline()
        self._workers: dict[int, FormatWorker] = {}
        self._task_info: dict[int, dict] = {}

        # 连接 EventBus
        event_bus.task_progress.connect(self._on_task_progress)

    def get_supported_targets(self, source_format: str) -> list:
        """获取源格式支持的目标格式"""
        return FORMAT_CONVERSION_MATRIX.get(source_format.lower(), [])

    def create_task(self, source_path: str, target_format: str,
                    output_path: str = "",
                    options: dict = None) -> int:
        """创建格式转换任务

        Returns:
            task_id
        """
        task_id = self._next_task_id
        self._next_task_id += 1

        filename = os.path.basename(source_path)
        basename = os.path.splitext(filename)[0]

        if not output_path:
            output_path = str(
                Path(source_path).parent / f"{basename}.{target_format}"
            )

        self._task_info[task_id] = {
            "task_id": task_id,
            "filename": filename,
            "source_path": source_path,
            "target_format": target_format,
            "output_path": output_path,
            "options": options or {},
            "status": "pending",
            "progress": 0,
            "created_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "error": "",
        }

        event_bus.log_message.emit(
            f"格式转换任务 #{task_id} 已创建: {filename} → {target_format.upper()}"
        )

        return task_id

    def start_task(self, task_id: int):
        """启动格式转换任务"""
        info = self._task_info.get(task_id)
        if not info:
            event_bus.log_message.emit(f"任务 #{task_id} 不存在")
            return

        if task_id in self._workers and self._workers[task_id].isRunning():
            event_bus.log_message.emit(f"任务 #{task_id} 已在运行中")
            return

        info["status"] = "converting"
        event_bus.task_status_changed.emit(task_id, "converting")

        worker = FormatWorker(
            pipeline=self.pipeline,
            task_id=task_id,
            source_path=info["source_path"],
            target_format=info["target_format"],
            output_path=info["output_path"],
            options=info["options"],
        )
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        self._workers[task_id] = worker

        worker.start()
        event_bus.log_message.emit(f"任务 #{task_id} 已启动")

    def cancel_task(self, task_id: int):
        """取消任务"""
        info = self._task_info.get(task_id)
        if info:
            info["status"] = "cancelled"

        worker = self._workers.get(task_id)
        if worker and worker.isRunning():
            worker.cancel()
            worker.quit()
            worker.wait(3000)

        event_bus.task_status_changed.emit(task_id, "cancelled")
        event_bus.log_message.emit(f"任务 #{task_id} 已取消")

    def get_task_info(self, task_id: int) -> dict:
        """获取任务信息"""
        return self._task_info.get(task_id, {})

    def list_tasks(self) -> list:
        """列出所有格式转换任务"""
        return list(self._task_info.values())

    def _on_task_progress(self, task_id: int, percent: int):
        """任务进度更新"""
        if task_id in self._task_info:
            self._task_info[task_id]["progress"] = percent

    def _on_worker_finished(self, task_id: int):
        """Worker 完成"""
        worker = self._workers.pop(task_id, None)
        if worker:
            worker.deleteLater()

        info = self._task_info.get(task_id)
        if info:
            info["status"] = "completed"
            info["progress"] = 100

            # 从 pipeline 报告中获取统计信息
            report = getattr(self.pipeline, '_last_report', {})

            # 写入书库
            if self.db:
                try:
                    self.db.insert_book(
                        title=report.get("title", info.get("filename", "Unknown").rsplit(".", 1)[0]),
                        author=report.get("author", "Unknown"),
                        source_pdf=info.get("source_path", ""),
                        output_epub=info.get("output_path", ""),
                        total_pages=0,
                        total_chars=report.get("total_chars", 0),
                        chapter_count=report.get("chapters", 0),
                    )
                    event_bus.book_added.emit(0)
                except Exception as e:
                    event_bus.log_message.emit(f"书库入库失败: {e}")

        event_bus.task_status_changed.emit(task_id, "completed")
        event_bus.log_message.emit(f"任务 #{task_id} 已完成")

    def _on_worker_error(self, task_id: int, error: str):
        """Worker 错误"""
        worker = self._workers.pop(task_id, None)
        if worker:
            worker.deleteLater()

        info = self._task_info.get(task_id)
        if info:
            info["status"] = "error"
            info["error"] = error

        event_bus.task_status_changed.emit(task_id, "error")
        event_bus.log_message.emit(f"任务 #{task_id} 错误: {error}")

    def shutdown(self):
        """关闭所有 Worker"""
        for task_id, worker in list(self._workers.items()):
            if worker.isRunning():
                worker.cancel()
                worker.quit()
                worker.wait(2000)
            worker.deleteLater()
        self._workers.clear()
