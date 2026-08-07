# -*- coding: utf-8 -*-
"""全局配置管理"""
import json
from pathlib import Path


class Config:
    """全局配置单例"""

    _instance = None
    _db_path = None
    _settings = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def load(cls, db_path: str):
        """从数据库加载配置"""
        cls._db_path = db_path
        cls._settings = {}
        try:
            from database.db import Database
            db = Database(db_path)
            rows = db.fetch_all("SELECT key, value FROM settings")
            for row in rows:
                cls._settings[row[0]] = row[1]
        except Exception:
            pass  # 首次运行，表可能不存在

    @classmethod
    def get(cls, key: str, default=None):
        """获取配置项"""
        return cls._settings.get(key, default)

    @classmethod
    def set(cls, key: str, value: str):
        """设置配置项并持久化"""
        cls._settings[key] = value
        if cls._db_path:
            from database.db import Database
            db = Database(cls._db_path)
            db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value)
            )

    # --- 常用配置快捷方法 ---

    @classmethod
    def get_dpi(cls) -> int:
        return int(cls.get("ocr_dpi", "300"))

    @classmethod
    def set_dpi(cls, dpi: int):
        cls.set("ocr_dpi", str(dpi))

    @classmethod
    def get_quality_mode(cls) -> str:
        return cls.get("quality_mode", "recommended")  # fast / recommended / extreme

    @classmethod
    def get_theme(cls) -> str:
        return cls.get("epub_theme", "classic")

    @classmethod
    def get_indent_threshold(cls) -> int:
        return int(cls.get("indent_threshold", "30"))

    @classmethod
    def get_gap_ratio(cls) -> float:
        return float(cls.get("gap_ratio", "1.8"))
