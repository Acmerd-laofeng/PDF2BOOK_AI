# -*- coding: utf-8 -*-
"""格式转换常量与配置"""

# 支持的格式
SUPPORTED_FORMATS = ["pdf", "epub", "txt", "mobi"]

# 格式转换矩阵：source_format → [target_formats]
FORMAT_CONVERSION_MATRIX = {
    "pdf":  ["epub", "txt"],
    "epub": ["pdf", "txt"],
    "txt":  ["epub", "pdf"],
    "mobi": ["epub", "txt", "pdf"],   # MOBI 可作为源格式读取，但不作为导出目标
}

# 格式显示名
FORMAT_LABELS = {
    "pdf":  "PDF",
    "epub": "EPUB",
    "txt":  "TXT",
    "mobi": "MOBI",
}

# 格式图标（FluentIcon 名称）
FORMAT_ICONS = {
    "pdf":  "DOCUMENT",
    "epub": "BOOK_SHELF",
    "txt":  "DOCUMENT",
    "mobi": "BOOK_SHELF",
}

# 格式描述
FORMAT_DESCRIPTIONS = {
    "pdf":  "PDF 文档 — 适合打印和固定排版",
    "epub": "EPUB 电子书 — 自适应屏幕，Kindle 推荐",
    "txt":  "纯文本 — 最小体积，最大兼容",
    "mobi": "MOBI 电子书 — 已过时（Kindle 2022 起停止支持，可读取但不导出）",
}

# TXT 分章正则（从 TXT 转换时用于自动分章）
TXT_CHAPTER_PATTERNS = [
    r"^第[一二三四五六七八九十百千零〇\d]+[章回节卷篇部].*",
    r"^Chapter\s+\d+.*",
    r"^CHAPTER\s+\d+.*",
    r"^序章.*",
    r"^序$",
    r"^前言$",
    r"^后记$",
    r"^楔子$",
    r"^尾声$",
    r"^终章$",
    r"^番外.*",
]

# 格式转换任务类型（区分 OCR 转换任务）
TASK_TYPE_FORMAT_CONVERT = "format_convert"

# 默认导出选项
DEFAULT_EXPORT_OPTIONS = {
    "epub": {
        "theme": "classic",
        "encoding": "utf-8",
    },
    "pdf": {
        "page_size": "A4",
        "font_size": 12,
        "encoding": "utf-8",
    },
    "txt": {
        "encoding": "utf-8",
        "chapter_separator": "\n\n",  # 章节间分隔符
    },
    "mobi": {
        "encoding": "utf-8",
    },
}
