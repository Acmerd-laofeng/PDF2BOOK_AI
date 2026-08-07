# -*- coding: utf-8 -*-
"""摘要生成器（预留，v4 实现）"""


class Summarizer:
    """摘要生成器

    预留接口，未来用于：
    - 章节摘要生成
    - 书籍简介自动生成
    """

    def summarize(self, text: str, max_length: int = 200) -> str:
        """生成摘要"""
        # TODO: v4 实现
        return text[:max_length] + "..." if len(text) > max_length else text
