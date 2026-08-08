# -*- coding: utf-8 -*-
"""SQLite 数据库封装

表结构：
- books: 书库（id, title, author, source_pdf, output_epub, cover_path,
        total_pages, total_chars, chapter_count, status, created_time, tags）
- tasks: 转换任务（id, filename, pdf_path, settings, status, progress,
         current_page, total_pages, output_path, error, start_time, end_time）
- corrections: OCR 纠错记录（id, wrong, correct, count, created_time）
- settings: 配置键值对（key, value）
"""
import sqlite3
import json
import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from app.constants import DB_PATH

# 解析为绝对路径：优先用 constants 中的 DB_PATH，如果是相对路径则基于项目根目录
_APP_DIR = Path(__file__).parent.parent.parent
if os.path.isabs(DB_PATH):
    _DEFAULT_DB = DB_PATH
else:
    _DEFAULT_DB = str(_APP_DIR / DB_PATH)


class Database:
    """SQLite 数据库管理"""

    def __init__(self, db_path: str = None):
        self.db_path = db_path or _DEFAULT_DB
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self.connect()
        self._create_tables()

    def connect(self):
        """连接数据库"""
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def create_tables(self):
        """创建表（公开接口）"""
        self._create_tables()

    def _create_tables(self):
        """建表"""
        cur = self._conn.cursor()

        # 书库表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                author      TEXT DEFAULT 'Unknown',
                source_pdf  TEXT,
                output_epub TEXT,
                cover_path  TEXT,
                total_pages INTEGER DEFAULT 0,
                total_chars INTEGER DEFAULT 0,
                chapter_count INTEGER DEFAULT 0,
                status      TEXT DEFAULT 'completed',
                created_time TEXT,
                tags        TEXT DEFAULT '[]'
            )
        """)

        # 任务表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT NOT NULL,
                pdf_path    TEXT NOT NULL,
                settings    TEXT DEFAULT '{}',
                status      TEXT DEFAULT 'pending',
                progress    INTEGER DEFAULT 0,
                current_page INTEGER DEFAULT 0,
                total_pages INTEGER DEFAULT 0,
                output_path TEXT,
                error       TEXT,
                start_time  TEXT,
                end_time    TEXT
            )
        """)

        # OCR 纠错记录表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS corrections (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                wrong       TEXT NOT NULL,
                correct     TEXT NOT NULL,
                count       INTEGER DEFAULT 1,
                created_time TEXT
            )
        """)

        # 配置键值表
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key     TEXT PRIMARY KEY,
                value   TEXT
            )
        """)

        self._conn.commit()

    # ========================
    # Books
    # ========================

    def insert_book(self, title: str, author: str = "Unknown",
                    source_pdf: str = "", output_epub: str = "",
                    cover_path: str = "", total_pages: int = 0,
                    total_chars: int = 0, chapter_count: int = 0,
                    tags: list = None) -> int:
        """插入书籍记录"""
        cur = self._conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tags_json = json.dumps(tags or [], ensure_ascii=False)
        cur.execute("""
            INSERT INTO books (title, author, source_pdf, output_epub, cover_path,
                              total_pages, total_chars, chapter_count, status, created_time, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'completed', ?, ?)
        """, (title, author, source_pdf, output_epub, cover_path,
              total_pages, total_chars, chapter_count, now, tags_json))
        self._conn.commit()
        return cur.lastrowid

    def get_books(self, limit: int = 100, offset: int = 0) -> list:
        """获取书库列表"""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM books ORDER BY created_time DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cur.fetchall()]

    def get_book_by_id(self, book_id: int) -> Optional[dict]:
        """获取单本书"""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM books WHERE id = ?", (book_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def search_books(self, keyword: str, limit: int = 50) -> list:
        """搜索书库"""
        cur = self._conn.cursor()
        pattern = f"%{keyword}%"
        cur.execute(
            "SELECT * FROM books WHERE title LIKE ? OR author LIKE ? ORDER BY created_time DESC LIMIT ?",
            (pattern, pattern, limit)
        )
        return [dict(row) for row in cur.fetchall()]

    def update_book(self, book_id: int, **kwargs):
        """更新书籍信息"""
        if not kwargs:
            return
        fields = []
        values = []
        for k, v in kwargs.items():
            if k == "tags":
                v = json.dumps(v, ensure_ascii=False)
            fields.append(f"{k} = ?")
            values.append(v)
        values.append(book_id)
        cur = self._conn.cursor()
        cur.execute(f"UPDATE books SET {', '.join(fields)} WHERE id = ?", values)
        self._conn.commit()

    def delete_book(self, book_id: int):
        """删除书籍"""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM books WHERE id = ?", (book_id,))
        self._conn.commit()

    def count_books(self) -> int:
        """书籍总数"""
        cur = self._conn.cursor()
        cur.execute("SELECT COUNT(*) FROM books")
        return cur.fetchone()[0]

    # ========================
    # Tasks
    # ========================

    def insert_task(self, filename: str, pdf_path: str, settings: str = "{}") -> int:
        """插入任务记录"""
        cur = self._conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute("""
            INSERT INTO tasks (filename, pdf_path, settings, status, start_time)
            VALUES (?, ?, ?, 'pending', ?)
        """, (filename, pdf_path, settings, now))
        self._conn.commit()
        return cur.lastrowid

    def update_task_status(self, task_id: int, status: str, progress: int = None):
        """更新任务状态"""
        cur = self._conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if status in ("completed", "error", "cancelled"):
            cur.execute("""
                UPDATE tasks SET status = ?, progress = ?, end_time = ?
                WHERE id = ?
            """, (status, progress if progress is not None else 0, now, task_id))
        else:
            cur.execute("""
                UPDATE tasks SET status = ?, progress = ?
                WHERE id = ?
            """, (status, progress if progress is not None else 0, task_id))
        self._conn.commit()

    def update_task_progress(self, task_id: int, progress: int,
                              current_page: int = None, total_pages: int = None):
        """更新任务进度（不改变状态）"""
        cur = self._conn.cursor()
        if current_page is not None and total_pages is not None:
            cur.execute("""
                UPDATE tasks SET progress = ?, current_page = ?, total_pages = ?
                WHERE id = ?
            """, (progress, current_page, total_pages, task_id))
        elif current_page is not None:
            cur.execute("""
                UPDATE tasks SET progress = ?, current_page = ? WHERE id = ?
            """, (progress, current_page, task_id))
        else:
            cur.execute("UPDATE tasks SET progress = ? WHERE id = ?", (progress, task_id))
        self._conn.commit()

    def get_tasks(self, limit: int = 50, offset: int = 0) -> list:
        """获取任务列表"""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM tasks ORDER BY start_time DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
        return [dict(row) for row in cur.fetchall()]

    def get_task_by_id(self, task_id: int) -> Optional[dict]:
        """获取单个任务"""
        cur = self._conn.cursor()
        cur.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def get_active_tasks(self) -> list:
        """获取未完成任务"""
        cur = self._conn.cursor()
        cur.execute(
            "SELECT * FROM tasks WHERE status NOT IN ('completed', 'cancelled', 'error') ORDER BY start_time DESC"
        )
        return [dict(row) for row in cur.fetchall()]

    def delete_task(self, task_id: int):
        """删除任务"""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self._conn.commit()

    def count_tasks(self, status: str = None) -> int:
        """任务总数（可按状态过滤）"""
        cur = self._conn.cursor()
        if status:
            cur.execute("SELECT COUNT(*) FROM tasks WHERE status = ?", (status,))
        else:
            cur.execute("SELECT COUNT(*) FROM tasks")
        return cur.fetchone()[0]

    # ========================
    # Corrections
    # ========================

    def add_correction(self, wrong: str, correct: str):
        """添加纠错记录（自动累加 count）"""
        cur = self._conn.cursor()
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(
            "SELECT id, count FROM corrections WHERE wrong = ? AND correct = ?",
            (wrong, correct)
        )
        row = cur.fetchone()
        if row:
            cur.execute(
                "UPDATE corrections SET count = count + 1 WHERE id = ?",
                (row["id"],)
            )
        else:
            cur.execute("""
                INSERT INTO corrections (wrong, correct, count, created_time)
                VALUES (?, ?, 1, ?)
            """, (wrong, correct, now))
        self._conn.commit()

    def get_corrections(self) -> dict:
        """获取纠错字典 {wrong: correct}"""
        cur = self._conn.cursor()
        cur.execute("SELECT wrong, correct FROM corrections")
        return {row["wrong"]: row["correct"] for row in cur.fetchall()}

    def get_correction_stats(self) -> list:
        """获取纠错统计（含 count）"""
        cur = self._conn.cursor()
        cur.execute("SELECT wrong, correct, count FROM corrections ORDER BY count DESC")
        return [dict(row) for row in cur.fetchall()]

    def delete_correction(self, wrong: str, correct: str):
        """删除纠错记录"""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM corrections WHERE wrong = ? AND correct = ?", (wrong, correct))
        self._conn.commit()

    # ========================
    # Settings
    # ========================

    def get_setting(self, key: str, default: str = "") -> str:
        """获取配置"""
        cur = self._conn.cursor()
        cur.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        """设置配置"""
        cur = self._conn.cursor()
        cur.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
        self._conn.commit()

    def get_all_settings(self) -> dict:
        """获取所有配置"""
        cur = self._conn.cursor()
        cur.execute("SELECT key, value FROM settings")
        return {row["key"]: row["value"] for row in cur.fetchall()}

    def delete_setting(self, key: str):
        """删除配置"""
        cur = self._conn.cursor()
        cur.execute("DELETE FROM settings WHERE key = ?", (key,))
        self._conn.commit()

    # ========================
    # 通用
    # ========================

    def fetch_all(self, sql: str, params: tuple = ()) -> list:
        """执行查询，返回所有行"""
        cur = self._conn.cursor()
        cur.execute(sql, params)
        return cur.fetchall()

    def execute(self, sql: str, params: tuple = ()):
        """执行单条 SQL"""
        cur = self._conn.cursor()
        cur.execute(sql, params)
        self._conn.commit()

    def transaction(self):
        """返回事务上下文管理器"""
        return self._conn

    def vacuum(self):
        """清理碎片"""
        self._conn.execute("VACUUM")


# 全局单例
_db: Optional[Database] = None


def get_db() -> Database:
    """获取数据库单例"""
    global _db
    if _db is None:
        _db = Database()
    return _db
