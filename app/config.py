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
        return cls.get("quality_mode", "standard")  # quick / standard / precise / ai

    @classmethod
    def get_theme(cls) -> str:
        return cls.get("epub_theme", "classic")

    @classmethod
    def get_indent_threshold(cls) -> int:
        return int(cls.get("indent_threshold", "30"))

    @classmethod
    def get_gap_ratio(cls) -> float:
        return float(cls.get("gap_ratio", "1.8"))

    # --- AI 配置 ---

    @classmethod
    def get_ai_provider(cls) -> str:
        """AI 服务商：none / gemini / local"""
        return cls.get("ai_provider", "none")

    @classmethod
    def set_ai_provider(cls, provider: str):
        cls.set("ai_provider", provider)

    @classmethod
    def get_ai_api_key(cls) -> str:
        return cls.get("ai_api_key", "")

    @classmethod
    def set_ai_api_key(cls, key: str):
        cls.set("ai_api_key", key)

    @classmethod
    def get_ai_model(cls) -> str:
        return cls.get("ai_model", "gemini-3.5-flash")

    @classmethod
    def set_ai_model(cls, model: str):
        cls.set("ai_model", model)

    @classmethod
    def get_ai_correct_enabled(cls) -> bool:
        return cls.get("ai_correct_enabled", "false") == "true"

    @classmethod
    def set_ai_correct_enabled(cls, enabled: bool):
        cls.set("ai_correct_enabled", "true" if enabled else "false")

    # --- 导出路径 ---

    @classmethod
    def get_output_dir(cls) -> str:
        """获取默认导出目录（空字符串表示 PDF 同级目录）"""
        return cls.get("output_dir", "")

    @classmethod
    def set_output_dir(cls, path: str):
        cls.set("output_dir", path)
