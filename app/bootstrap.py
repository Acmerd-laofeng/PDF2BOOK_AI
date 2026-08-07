# -*- coding: utf-8 -*-
"""初始化：数据库、配置、主题"""
import os
from pathlib import Path


class Bootstrap:
    """应用启动初始化"""

    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.cache_dir = self.app_dir / "cache"
        self.models_dir = self.app_dir / "models"
        self.resources_dir = self.app_dir / "resources"
        self.db_path = self.app_dir / "database" / "pdf2book.db"

    def init(self):
        """执行全部初始化"""
        self._ensure_dirs()
        self._init_database()
        self._init_config()

    def _ensure_dirs(self):
        """确保所有必要目录存在"""
        dirs = [
            self.cache_dir / "pages",
            self.cache_dir / "ocr",
            self.cache_dir / "preview",
            self.models_dir / "ocr",
            self.models_dir / "ai",
            self.models_dir / "language",
            self.resources_dir / "templates",
            self.resources_dir / "epub_themes",
            self.resources_dir / "dictionaries",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def _init_database(self):
        """初始化 SQLite 数据库"""
        from database.db import Database
        db = Database(str(self.db_path))
        db.create_tables()

    def _init_config(self):
        """加载配置"""
        from app.config import Config
        Config.load(str(self.app_dir / "database" / "pdf2book.db"))
