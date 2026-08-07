# -*- coding: utf-8 -*-
"""转换服务层 - UI 调用入口

UI 层通过此服务与核心引擎交互。
职责：
- 创建/启动/取消/重试任务
- 管理 Worker 线程生命周期
- 数据库持久化（任务进度 + 书库入库 + 纠错学习）
- EventBus 信号桥接
"""
import json
from pathlib import Path
from typing import Optional

from core.pipeline import Pipeline
from core.task_manager import TaskManager
from core.worker import Worker
from core.models import Task, ConvertSettings
from core.event_bus import event_bus


class ConverterService:
    """转换服务"""

    def __init__(self, db=None):
        self.task_manager = TaskManager(db=db)
        self.pipeline = Pipeline()
        self.db = db
        self._workers: dict[int, Worker] = {}

        # 连接 EventBus 信号 → 数据库同步
        event_bus.task_progress.connect(self._on_task_progress)
        event_bus.task_status_changed.connect(self._on_task_status)
        event_bus.report_ready.connect(self._on_report_ready)
        event_bus.correction_learned.connect(self._on_correction_learned)

    # ========================
    # 任务生命周期
    # ========================

    def create_task(self, filename: str, pdf_path: str,
                    settings: dict = None,
                    output_path: str = "") -> Task:
        """创建转换任务"""
        if not output_path:
            book_title = filename.rsplit(".", 1)[0]
            output_path = str(Path(pdf_path).parent / f"{book_title}.epub")

        task = self.task_manager.create_task(
            filename=filename,
            pdf_path=pdf_path,
            settings=settings,
            output_path=output_path,
        )
        return task

    def start_task(self, task: Task):
        """在 Worker 线程中启动转换任务"""
        # 防止重复启动
        if task.id in self._workers and self._workers[task.id].isRunning():
            event_bus.log_message.emit(f"任务 #{task.id} 已在运行中")
            return

        worker = Worker(self.pipeline, task)
        worker.finished.connect(self._on_worker_finished)
        worker.error.connect(self._on_worker_error)
        self._workers[task.id] = worker

        self.task_manager.update(task.id, status="analyzing", stage="准备开始转换")
        worker.start()
        event_bus.log_message.emit(f"任务 #{task.id} 已启动: {task.filename}")

    def cancel_task(self, task_id: int):
        """取消任务"""
        self.task_manager.cancel_task(task_id)
        worker = self._workers.get(task_id)
        if worker and worker.isRunning():
            worker.cancel()
            worker.quit()
            worker.wait(3000)  # 等待最多 3 秒
        event_bus.log_message.emit(f"任务 #{task_id} 已取消")

    def retry_task(self, task_id: int):
        """重试任务"""
        task = self.task_manager.retry_task(task_id)
        if task:
            self.start_task(task)
        return task

    def delete_task(self, task_id: int):
        """删除任务（先取消再删除）"""
        if task_id in self._workers:
            worker = self._workers[task_id]
            if worker.isRunning():
                worker.cancel()
                worker.quit()
                worker.wait(2000)
            self._workers.pop(task_id, None)

        self.task_manager.delete_task(task_id)

        if self.db:
            self.db.delete_task(task_id)

    def run_task_sync(self, task: Task) -> dict:
        """同步执行转换任务（测试用，不启动线程）"""
        return self.pipeline.run(task)

    # ========================
    # 状态查询
    # ========================

    def get_task_status(self, task_id: int) -> dict:
        """获取任务状态"""
        task = self.task_manager.get_task(task_id)
        if not task:
            return {}
        return {
            "id": task.id,
            "filename": task.filename,
            "status": task.status,
            "stage": task.stage,
            "progress": task.progress,
            "current_page": task.current_page,
            "total_pages": task.total_pages,
            "output_path": task.output_path,
            "error": task.error,
            "created_time": task.created_time,
            "finished_time": task.finished_time,
        }

    def list_tasks(self, include_done: bool = True) -> list:
        """列出任务"""
        return [self.get_task_status(t.id) for t in self.task_manager.list_tasks(include_done)]

    def list_active_tasks(self) -> list:
        """活跃任务"""
        return [self.get_task_status(t.id) for t in self.task_manager.list_active_tasks()]

    # ========================
    # EventBus 回调
    # ========================

    def _on_task_progress(self, task_id: int, percent: int):
        """任务进度更新 → 同步数据库"""
        if self.db:
            self.db.update_task_progress(task_id, percent)

    def _on_task_status(self, task_id: int, status: str):
        """任务状态变更 → 同步数据库"""
        if self.db:
            self.db.update_task_status(task_id, status)

    def _on_report_ready(self, report: dict):
        """转换报告就绪 → 写入书库"""
        if not self.db:
            return

        try:
            book_id = self.db.insert_book(
                title=report.get("filename", "Unknown").rsplit(".", 1)[0],
                author="Unknown",
                source_pdf="",
                output_epub=report.get("output_path", ""),
                total_pages=report.get("total_pages", 0),
                total_chars=report.get("total_chars", 0),
                chapter_count=report.get("chapters", 0),
            )
            event_bus.book_added.emit(book_id)
            event_bus.log_message.emit(
                f"已入库: {report.get('filename', 'Unknown')} → 书库 #{book_id}"
            )
        except Exception as e:
            event_bus.log_message.emit(f"书库入库失败: {e}")

    def _on_correction_learned(self, wrong: str, correct: str):
        """纠错学习 → 写入数据库"""
        if self.db:
            self.db.add_correction(wrong, correct)

    # ========================
    # Worker 回调
    # ========================

    def _on_worker_finished(self, task_id: int):
        """Worker 完成"""
        worker = self._workers.pop(task_id, None)
        if worker:
            worker.deleteLater()

        task = self.task_manager.get_task(task_id)
        if task:
            self.task_manager.update(task_id, status="completed")
            event_bus.log_message.emit(
                f"任务 #{task_id} 完成: {task.filename}"
            )

    def _on_worker_error(self, task_id: int, error: str):
        """Worker 错误"""
        worker = self._workers.pop(task_id, None)
        if worker:
            worker.deleteLater()

        self.task_manager.update(task_id, status="error", error=error)
        event_bus.log_message.emit(f"任务 #{task_id} 错误: {error}")

    # ========================
    # 清理
    # ========================

    def shutdown(self):
        """关闭所有 Worker（应用退出时调用）"""
        for task_id, worker in list(self._workers.items()):
            if worker.isRunning():
                worker.cancel()
                worker.quit()
                worker.wait(2000)
            worker.deleteLater()
        self._workers.clear()
