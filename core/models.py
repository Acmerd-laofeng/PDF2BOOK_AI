# -*- coding: utf-8 -*-
"""数据模型"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import json


@dataclass
class ConvertSettings:
    """转换参数"""
    dpi: int = 300
    indent_threshold: int = 30          # 首行缩进检测阈值
    detect_chapters: bool = True         # 章节标题检测
    merge_cross_page: bool = True        # 跨页断行合并
    epub_theme: str = "classic"          # EPUB 主题
    quality: str = "standard"            # 转换模式: quick/standard/precise/ai
    enable_ai_correct: bool = False      # AI 纠错（v4）
    enable_image_extract: bool = False   # 图片提取（v4）
    enable_table_detect: bool = False    # 表格检测（v4）

    def to_dict(self) -> dict:
        return {
            "dpi": self.dpi,
            "indent_threshold": self.indent_threshold,
            "detect_chapters": self.detect_chapters,
            "merge_cross_page": self.merge_cross_page,
            "epub_theme": self.epub_theme,
            "quality": self.quality,
            "enable_ai_correct": self.enable_ai_correct,
            "enable_image_extract": self.enable_image_extract,
            "enable_table_detect": self.enable_table_detect,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ConvertSettings":
        if not d:
            return cls()
        return cls(**{k: v for k, v in d.items() if k in cls.__dataclass_fields__})


@dataclass
class Task:
    """转换任务"""
    id: int = 0
    filename: str = ""
    pdf_path: str = ""
    output_path: str = ""
    status: str = "pending"          # pending/analyzing/ocr/exporting/completed/cancelled/error
    stage: str = ""                  # 当前阶段描述
    progress: int = 0
    current_page: int = 0
    total_pages: int = 0
    error: str = ""
    created_time: str = ""
    finished_time: str = ""
    settings: Optional[dict] = None

    def __post_init__(self):
        if not self.created_time:
            self.created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def is_running(self) -> bool:
        return self.status in ("analyzing", "ocr", "exporting")

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_done(self) -> bool:
        return self.status in ("completed", "cancelled", "error")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "pdf_path": self.pdf_path,
            "output_path": self.output_path,
            "status": self.status,
            "stage": self.stage,
            "progress": self.progress,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "error": self.error,
            "created_time": self.created_time,
            "finished_time": self.finished_time,
            "settings": json.dumps(self.settings or {}, ensure_ascii=False),
        }


@dataclass
class Book:
    """书籍信息"""
    id: int = 0
    title: str = ""
    author: str = ""
    source_pdf: str = ""
    output_epub: str = ""
    cover_path: str = ""
    total_pages: int = 0
    total_chars: int = 0
    chapter_count: int = 0
    status: str = "completed"
    created_time: str = ""
    tags: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "source_pdf": self.source_pdf,
            "output_epub": self.output_epub,
            "cover_path": self.cover_path,
            "total_pages": self.total_pages,
            "total_chars": self.total_chars,
            "chapter_count": self.chapter_count,
            "status": self.status,
            "created_time": self.created_time,
            "tags": self.tags,
        }


@dataclass
class Correction:
    """OCR 纠错记录"""
    id: int = 0
    wrong: str = ""
    correct: str = ""
    count: int = 1
    created_time: str = ""
