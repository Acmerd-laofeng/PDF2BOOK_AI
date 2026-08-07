# -*- coding: utf-8 -*-
"""任务管理器

管理任务生命周期：创建 → 运行 → 完成/取消/错误
- 内存任务表 + SQLite 持久化
- 状态流转控制
- EventBus 通知
"""
import json
from typing import Dict, Optional, List
from datetime import datetime

from core.models import Task, ConvertSettings
from core.event_bus import event_bus


# 合法状态流转
_VALID_TRANSITIONS = {
    "pending":    {"analyzing", "cancelled", "error"},
    "analyzing":  {"ocr", "cancelled", "error"},
    "ocr":        {"exporting", "cancelled", "error"},
    "exporting":  {"completed", "cancelled", "error"},
    "completed":  {"pending"},          # retry → pending
    "cancelled":  {"pending"},          # retry → pending
    "error":      {"pending"},          # retry → pending
}


class TaskManager:
    """任务管理器"""

    def __init__(self, db=None):
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1
        self._db = db

    def create_task(self, filename: str, pdf_path: str,
                    settings: dict = None,
                    output_path: str = "") -> Task:
        """创建新任务

        Args:
            filename: PDF 文件名
            pdf_path: PDF 完整路径
            settings: 转换设置 dict
            output_path: 输出 EPUB 路径（空则自动生成）

        Returns:
            Task 对象
        """
        task = Task(
            id=self._next_id,
            filename=filename,
            pdf_path=pdf_path,
            settings=settings,
            output_path=output_path,
        )

        # 持久化到数据库
        if self._db:
            settings_json = json.dumps(settings or {}, ensure_ascii=False)
            db_id = self._db.insert_task(filename, pdf_path, settings_json)
            task.id = db_id
        else:
            task.id = self._next_id

        self._tasks[task.id] = task
        self._next_id = max(self._next_id, task.id) + 1

        event_bus.task_added.emit(task.id)
        event_bus.log_message.emit(f"任务已创建: {filename} (#{task.id})")
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """获取任务"""
        return self._tasks.get(task_id)

    def update(self, task_id: int,
               progress: int = None,
               status: str = None,
               current_page: int = None,
               total_pages: int = None,
               output_path: str = None,
               error: str = None,
               stage: str = None):
        """更新任务状态

        状态流转校验：非法跳转会忽略并记录日志。
        """
        task = self._tasks.get(task_id)
        if not task:
            return

        # 状态流转校验
        if status and status != task.status:
            allowed = _VALID_TRANSITIONS.get(task.status, set())
            if status not in allowed:
                event_bus.log_message.emit(
                    f"警告: 非法状态跳转 {task.status} → {status} (task #{task_id})"
                )
                return
            task.status = status
            event_bus.task_status_changed.emit(task_id, status)

            # 数据库持久化
            if self._db:
                self._db.update_task_status(task_id, status, progress)

        if stage is not None:
            task.stage = stage

        if progress is not None:
            task.progress = progress
            event_bus.task_progress.emit(task_id, progress)

            if self._db:
                self._db.execute(
                    "UPDATE tasks SET progress = ? WHERE id = ?",
                    (progress, task_id)
                )

        if current_page is not None:
            task.current_page = current_page
            if self._db:
                self._db.execute(
                    "UPDATE tasks SET current_page = ? WHERE id = ?",
                    (current_page, task_id)
                )

        if total_pages is not None:
            task.total_pages = total_pages
            if self._db:
                self._db.execute(
                    "UPDATE tasks SET total_pages = ? WHERE id = ?",
                    (total_pages, task_id)
                )

        if output_path is not None:
            task.output_path = output_path
            if self._db:
                self._db.execute(
                    "UPDATE tasks SET output_path = ? WHERE id = ?",
                    (output_path, task_id)
                )

        if error is not None:
            task.error = error
            if self._db:
                self._db.execute(
                    "UPDATE tasks SET error = ? WHERE id = ?",
                    (error, task_id)
                )

        # 终态记录完成时间
        if task.status in ("completed", "cancelled", "error"):
            if not task.finished_time:
                task.finished_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if self._db:
                    self._db.execute(
                        "UPDATE tasks SET end_time = ? WHERE id = ?",
                        (task.finished_time, task_id)
                    )

    def cancel_task(self, task_id: int):
        """取消任务"""
        task = self._tasks.get(task_id)
        if not task:
            return

        if task.is_done:
            event_bus.log_message.emit(f"任务 #{task_id} 已结束，无法取消")
            return

        # 直接设置状态（绕过流转校验，因为取消可以来自任何状态）
        task.status = "cancelled"
        task.finished_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        event_bus.task_status_changed.emit(task_id, "cancelled")
        event_bus.log_message.emit(f"任务 #{task_id} 已取消")

        if self._db:
            self._db.update_task_status(task_id, "cancelled", task.progress)

    def retry_task(self, task_id: int) -> Optional[Task]:
        """重试任务"""
        task = self._tasks.get(task_id)
        if not task:
            return None

        if not task.is_done:
            event_bus.log_message.emit(f"任务 #{task_id} 仍在运行，无法重试")
            return None

        task.status = "pending"
        task.progress = 0
        task.error = ""
        task.current_page = 0
        task.stage = ""
        task.finished_time = ""

        event_bus.task_status_changed.emit(task_id, "pending")
        event_bus.log_message.emit(f"任务 #{task_id} 已重置，准备重试")

        if self._db:
            self._db.update_task_status(task_id, "pending", 0)

        return task

    def delete_task(self, task_id: int):
        """删除任务"""
        task = self._tasks.pop(task_id, None)
        if task:
            event_bus.task_removed.emit(task_id)
            event_bus.log_message.emit(f"任务 #{task_id} 已删除")

    def list_tasks(self, include_done: bool = True) -> List[Task]:
        """列出所有任务"""
        tasks = sorted(self._tasks.values(), key=lambda t: t.id, reverse=True)
        if not include_done:
            tasks = [t for t in tasks if not t.is_done]
        return tasks

    def list_active_tasks(self) -> List[Task]:
        """列出活跃任务（含 pending）"""
        return [t for t in self._tasks.values() if not t.is_done]

    def load_from_db(self):
        """从数据库加载历史任务"""
        if not self._db:
            return

        rows = self._db.get_tasks(limit=200)
        for row in rows:
            task = Task(
                id=row["id"],
                filename=row["filename"],
                pdf_path=row["pdf_path"],
                status=row["status"],
                progress=row["progress"],
                current_page=row["current_page"],
                total_pages=row["total_pages"],
                output_path=row.get("output_path", ""),
                error=row.get("error", ""),
                created_time=row.get("start_time", ""),
                finished_time=row.get("end_time", ""),
                settings=json.loads(row.get("settings", "{}")),
            )
            self._tasks[task.id] = task
            self._next_id = max(self._next_id, task.id + 1)

        event_bus.log_message.emit(f"从数据库加载 {len(rows)} 条历史任务")
