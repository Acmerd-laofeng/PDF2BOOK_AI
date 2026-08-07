# -*- coding: utf-8 -*-
"""数据库模型（SQL 层）- 与 core/models.py 的 dataclass 对应

这些 dataclass 用于数据库行的类型安全映射。
core/models.py 中的 Task/Book/Correction 是业务层模型，
此处的 *Record 是数据库行映射。
"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BookRecord:
    """books 表对应模型"""
    id: int = 0
    title: str = ""
    author: str = "Unknown"
    source_pdf: str = ""
    output_epub: str = ""
    cover_path: str = ""
    total_pages: int = 0
    total_chars: int = 0
    chapter_count: int = 0
    status: str = "completed"
    created_time: str = ""
    tags: str = "[]"  # JSON string


@dataclass
class TaskRecord:
    """tasks 表对应模型"""
    id: int = 0
    filename: str = ""
    pdf_path: str = ""
    settings: str = "{}"  # JSON string
    status: str = "pending"
    progress: int = 0
    current_page: int = 0
    total_pages: int = 0
    output_path: str = ""
    error: str = ""
    start_time: str = ""
    end_time: str = ""


@dataclass
class CorrectionRecord:
    """corrections 表对应模型"""
    id: int = 0
    wrong: str = ""
    correct: str = ""
    count: int = 1
    created_time: str = ""


@dataclass
class SettingRecord:
    """settings 表对应模型"""
    key: str = ""
    value: str = ""
