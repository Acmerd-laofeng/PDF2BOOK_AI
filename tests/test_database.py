# -*- coding: utf-8 -*-
"""Database 单元测试"""
import pytest
import tempfile
import os
import json
from database.db import Database


@pytest.fixture
def db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        path = f.name
    d = Database(path)
    yield d
    d.close()
    os.unlink(path)


class TestBooks:

    def test_insert_and_get(self, db):
        book_id = db.insert_book(
            title="测试书", author="作者",
            source_pdf="/test.pdf", output_epub="/test.epub",
            total_pages=100, total_chars=50000, chapter_count=10,
        )
        assert book_id > 0

        book = db.get_book_by_id(book_id)
        assert book["title"] == "测试书"
        assert book["author"] == "作者"
        assert book["total_pages"] == 100

    def test_get_books(self, db):
        db.insert_book("书A", "作者A")
        db.insert_book("书B", "作者B")
        books = db.get_books()
        assert len(books) == 2

    def test_search_books(self, db):
        db.insert_book("Python编程", "作者A")
        db.insert_book("Java入门", "作者B")
        results = db.search_books("Python")
        assert len(results) == 1
        assert results[0]["title"] == "Python编程"

    def test_update_book(self, db):
        book_id = db.insert_book("旧标题", "作者")
        db.update_book(book_id, title="新标题", total_pages=200)
        book = db.get_book_by_id(book_id)
        assert book["title"] == "新标题"
        assert book["total_pages"] == 200

    def test_delete_book(self, db):
        book_id = db.insert_book("待删除", "作者")
        db.delete_book(book_id)
        assert db.get_book_by_id(book_id) is None

    def test_count_books(self, db):
        db.insert_book("书1", "作者")
        db.insert_book("书2", "作者")
        assert db.count_books() == 2


class TestTasks:

    def test_insert_and_get(self, db):
        task_id = db.insert_task("test.pdf", "/test.pdf", '{"quality":"standard"}')
        assert task_id > 0

        task = db.get_task_by_id(task_id)
        assert task["filename"] == "test.pdf"
        assert task["status"] == "pending"

    def test_update_status(self, db):
        task_id = db.insert_task("test.pdf", "/test.pdf")
        db.update_task_status(task_id, "ocr", 50)
        task = db.get_task_by_id(task_id)
        assert task["status"] == "ocr"
        assert task["progress"] == 50

    def test_update_progress(self, db):
        task_id = db.insert_task("test.pdf", "/test.pdf")
        db.update_task_progress(task_id, 75, current_page=15, total_pages=20)
        task = db.get_task_by_id(task_id)
        assert task["progress"] == 75
        assert task["current_page"] == 15
        assert task["total_pages"] == 20

    def test_completed_sets_end_time(self, db):
        task_id = db.insert_task("test.pdf", "/test.pdf")
        db.update_task_status(task_id, "completed", 100)
        task = db.get_task_by_id(task_id)
        assert task["end_time"] is not None
        assert task["end_time"] != ""

    def test_get_tasks(self, db):
        db.insert_task("a.pdf", "/a.pdf")
        db.insert_task("b.pdf", "/b.pdf")
        tasks = db.get_tasks()
        assert len(tasks) == 2

    def test_get_active_tasks(self, db):
        id1 = db.insert_task("active.pdf", "/a.pdf")
        id2 = db.insert_task("done.pdf", "/d.pdf")
        db.update_task_status(id2, "completed", 100)
        active = db.get_active_tasks()
        assert len(active) == 1
        assert active[0]["filename"] == "active.pdf"

    def test_delete_task(self, db):
        task_id = db.insert_task("test.pdf", "/test.pdf")
        db.delete_task(task_id)
        assert db.get_task_by_id(task_id) is None

    def test_count_tasks(self, db):
        db.insert_task("a.pdf", "/a.pdf")
        db.insert_task("b.pdf", "/b.pdf")
        assert db.count_tasks() == 2
        assert db.count_tasks(status="pending") == 2


class TestCorrections:

    def test_add_and_get(self, db):
        db.add_correction("错词", "对词")
        corrections = db.get_corrections()
        assert corrections["错词"] == "对词"

    def test_count_increment(self, db):
        db.add_correction("错词", "对词")
        db.add_correction("错词", "对词")
        stats = db.get_correction_stats()
        assert stats[0]["count"] == 2

    def test_delete_correction(self, db):
        db.add_correction("错词", "对词")
        db.delete_correction("错词", "对词")
        corrections = db.get_corrections()
        assert "错词" not in corrections

    def test_get_correction_stats(self, db):
        db.add_correction("高频错词", "正确")
        db.add_correction("高频错词", "正确")
        db.add_correction("低频错词", "正确")
        stats = db.get_correction_stats()
        assert len(stats) == 2
        # 按频率排序，高频在前
        assert stats[0]["count"] >= stats[1]["count"]


class TestSettings:

    def test_set_and_get(self, db):
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"

    def test_get_default(self, db):
        assert db.get_setting("nonexistent", "default") == "default"

    def test_overwrite(self, db):
        db.set_setting("key", "value1")
        db.set_setting("key", "value2")
        assert db.get_setting("key") == "value2"

    def test_get_all(self, db):
        db.set_setting("a", "1")
        db.set_setting("b", "2")
        settings = db.get_all_settings()
        assert settings["a"] == "1"
        assert settings["b"] == "2"

    def test_delete(self, db):
        db.set_setting("temp", "value")
        db.delete_setting("temp")
        assert db.get_setting("temp") == ""
