# -*- coding: utf-8 -*-
"""TaskManager 单元测试"""
import pytest
import tempfile
import os
from PySide6.QtWidgets import QApplication
from core.task_manager import TaskManager
from core.models import Task
from database.db import Database


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = Database(path)
    yield d
    d.close()
    os.unlink(path)


@pytest.fixture
def manager(db):
    return TaskManager(db=db)


class TestTaskManager:

    def test_create_task(self, manager):
        task = manager.create_task("test.pdf", "/path/to/test.pdf", {"quality": "standard"})
        assert task.id > 0
        assert task.filename == "test.pdf"
        assert task.status == "pending"
        assert task.settings == {"quality": "standard"}

    def test_get_task(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        fetched = manager.get_task(task.id)
        assert fetched is task

    def test_update_status(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        assert manager.get_task(task.id).status == "analyzing"

    def test_update_progress(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        manager.update(task.id, status="ocr", progress=50)
        t = manager.get_task(task.id)
        assert t.status == "ocr"
        assert t.progress == 50

    def test_invalid_transition(self, manager):
        """非法状态跳转应被拒绝"""
        task = manager.create_task("test.pdf", "/path/test.pdf")
        # pending → completed 是非法跳转（必须经过 analyzing/ocr/exporting）
        manager.update(task.id, status="completed")
        assert manager.get_task(task.id).status == "pending"

    def test_cancel_task(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        manager.cancel_task(task.id)
        assert manager.get_task(task.id).status == "cancelled"
        assert manager.get_task(task.id).finished_time != ""

    def test_cancel_done_task(self, manager):
        """取消已完成的任务应被拒绝"""
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        manager.update(task.id, status="ocr")
        manager.update(task.id, status="exporting")
        manager.update(task.id, status="completed")
        manager.cancel_task(task.id)
        # 应该仍然是 completed
        assert manager.get_task(task.id).status == "completed"

    def test_retry_task(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        manager.update(task.id, status="error", error="test error")
        retried = manager.retry_task(task.id)
        assert retried.status == "pending"
        assert retried.progress == 0
        assert retried.error == ""

    def test_retry_running_task(self, manager):
        """重试运行中的任务应失败"""
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        result = manager.retry_task(task.id)
        assert result is None

    def test_delete_task(self, manager):
        task = manager.create_task("test.pdf", "/path/test.pdf")
        task_id = task.id
        manager.delete_task(task_id)
        assert manager.get_task(task_id) is None

    def test_list_tasks(self, manager):
        manager.create_task("a.pdf", "/a.pdf")
        manager.create_task("b.pdf", "/b.pdf")
        tasks = manager.list_tasks()
        assert len(tasks) == 2
        # 最新创建的排在前面
        assert tasks[0].filename == "b.pdf"

    def test_list_active_tasks(self, manager):
        t1 = manager.create_task("a.pdf", "/a.pdf")
        manager.create_task("b.pdf", "/b.pdf")
        # a → analyzing（活跃），b → pending（活跃）
        manager.update(t1.id, status="analyzing")
        active = manager.list_active_tasks()
        assert len(active) == 2

    def test_load_from_db(self, db):
        """从数据库加载历史任务"""
        # 先插入一些任务
        db.insert_task("old.pdf", "/old.pdf", "{}")
        db.insert_task("newer.pdf", "/newer.pdf", "{}")

        manager = TaskManager(db=db)
        manager.load_from_db()
        tasks = manager.list_tasks()
        assert len(tasks) >= 2

    def test_finished_time_set(self, manager):
        """终态任务应记录完成时间"""
        task = manager.create_task("test.pdf", "/path/test.pdf")
        manager.update(task.id, status="analyzing")
        manager.update(task.id, status="ocr")
        manager.update(task.id, status="exporting")
        manager.update(task.id, status="completed")
        t = manager.get_task(task.id)
        assert t.finished_time != ""

    def test_task_properties(self):
        """Task 属性 is_running/is_done"""
        t = Task(id=1, filename="test.pdf", pdf_path="/test.pdf")
        assert t.is_running == False  # pending 不算 running
        t.status = "ocr"
        assert t.is_running == True
        t.status = "completed"
        assert t.is_done == True
        t.status = "error"
        assert t.is_done == True
