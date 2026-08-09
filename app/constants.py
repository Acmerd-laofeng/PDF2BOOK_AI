# -*- coding: utf-8 -*-
"""应用常量定义"""

APP_NAME = "PDF2BOOK AI"
APP_VERSION = "4.1.0"
APP_DESCRIPTION = "AI智能电子书重构平台"

# 自动更新配置
UPDATE_CHECK_URL = "https://api.github.com/repos/Acmerd-laofeng/PDF2BOOK_AI/releases/latest"
UPDATE_ENABLED = True
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 760

# OCR 配置
DEFAULT_DPI = 300
MIN_DPI = 150
MAX_DPI = 600
DEFAULT_INDENT_THRESHOLD = 30      # 首行缩进检测阈值（像素 @ 300DPI）
DEFAULT_GAP_MULTIPLIER = 1.8       # 行间距分段倍数
DEFAULT_CENTER_TOLERANCE = 0.15    # 居中检测容差（页面宽度比例）
DEFAULT_SHORT_LINE_RATIO = 0.4     # 短行判定（页面宽度比例）
DEFAULT_PAGE_NUM_REGION = 0.75     # 页码区域（底部 1/4）

# EPUB 主题
EPUB_THEMES = {
    "classic": "经典阅读",
    "kindle": "Kindle 风格",
    "modern": "现代简洁",
    "eye_care": "护眼模式",
}

# 转换模式
CONVERT_MODES = {
    "quick": "快速模式（150 DPI，适合纯文字 PDF）",
    "standard": "推荐模式（300 DPI，适合大多数扫描版）",
    "precise": "精准模式（400 DPI，适合小字/古籍）",
    "ai": "AI增强模式（OCR + AI纠错，需联网）",
}

# 任务状态映射
TASK_STATUS = {
    "pending": "等待中",
    "analyzing": "分析中",
    "ocr": "OCR识别中",
    "exporting": "导出中",
    "completed": "已完成",
    "error": "错误",
    "cancelled": "已取消",
}

# 章节检测正则
CHAPTER_PATTERNS = [
    # 中文章回
    r"^第[一二三四五六七八九十百千零〇\d]+[章回节卷篇部].*",
    r"^第[一二三四五六七八九十百千零〇\d]+[章回节卷篇部]$",
    # 中文数字直接开头
    r"^[一二三四五六七八九十]+[、.．].*",
    # 英文章节
    r"^Chapter\s+\d+.*",
    r"^CHAPTER\s+\d+.*",
    r"^Chapter\s+[IVXLCDM]+$",
    # 特殊标题
    r"^序$",
    r"^前言$",
    r"^后记$",
    r"^序言$",
    r"^目录$",
    r"^附录.*",
    r"^结语$",
    r"^引言$",
    r"^楔子$",
    r"^尾声$",
    r"^番外.*",
    r"^引子$",
    r"^终章$",
    r"^序章$",
    r"^跋$",
    r"^后序$",
    # 卷/部
    r"^(上|中|下)[卷部篇]",
    r"^卷[一二三四五六七八九十\d]+",
    r"^第[一二三四五六七八九十百千零〇\d]+卷",
]

# 句末标点（用于跨页断行合并判断）
SENTENCE_END_CHARS = '。？！…"\'」』）)]}】〕'

# 数据库默认路径
DB_PATH = "pdf2book.db"

# 缓存目录
CACHE_DIR = "cache"
PAGE_CACHE_DIR = "cache/pages"

# AI 纠错配置
GEMINI_DEFAULT_MODEL = "gemini-3.5-flash"
GEMINI_MODELS = {
    "gemini-3.5-flash": "Gemini 3.5 Flash（推荐，快速+免费）",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite（轻量省配额）",
    "gemini-2.0-flash": "Gemini 2.0 Flash（兼容旧版）",
    "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite（备用）",
}
AI_CORRECT_MIN_TEXT_LENGTH = 5   # 短于此长度的文本不调 API
AI_CORRECT_BATCH_SIZE = 20        # 每批最多处理段落数
