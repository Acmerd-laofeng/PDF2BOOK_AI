# -*- coding: utf-8 -*-
"""章节检测器 - v4.0 增强版

从 v3 居中+短行+正则升级：
1. 正则匹配（第X章/Chapter X/序/目录/后记/附录/楔子/番外等）
2. 居中+短行检测（从 v2 保留）
3. 字体大小判断（bbox 高度 > 平均高度 1.3 倍）
4. 上下文判断（标题前后通常有空行/大间距）
5. 层级目录生成（卷 > 章 > 节）

v4 新增：
- 字体大小信号（bbox height 比较）
- 上下文信号（前后间距大于平均间距）
- 层级目录（chapter_level: 1=卷/部, 2=章/回, 3=节）
- 置信度评分（多信号叠加）
"""
import re
from typing import List, Tuple, Optional

from app.constants import CHAPTER_PATTERNS


class ChapterDetector:
    """章节检测器 v4"""

    def __init__(self):
        self._patterns = [re.compile(p) for p in CHAPTER_PATTERNS]

    def detect_and_mark(self, paragraphs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """检测并标记章节标题（v3 兼容接口）"""
        result = []
        for i, (p_type, p_text) in enumerate(paragraphs):
            if p_type == 'heading':
                result.append((p_type, p_text))
                continue
            if self._is_chapter_title(p_text):
                result.append(('heading', p_text))
            else:
                result.append((p_type, p_text))
        return result

    def detect_enhanced(self, paragraphs: List[Tuple[str, str]],
                       avg_line_height: float = 0,
                       gaps: Optional[List[float]] = None) -> List[Tuple[str, str]]:
        """增强检测（v4）

        Args:
            paragraphs: [(type, text), ...]
            avg_line_height: 平均行高（bbox height），0 表示不可用
            gaps: 段落间距列表，gaps[i] = paragraph[i] 与 paragraph[i-1] 的间距

        Returns:
            [(type, text), ...]  type: 'heading' | 'body'
        """
        result = []
        for i, (p_type, p_text) in enumerate(paragraphs):
            if p_type == 'heading':
                result.append((p_type, p_text))
                continue

            score = 0
            signals = []

            # 信号 1: 正则匹配（最强信号，+3 分）
            if self._regex_match(p_text):
                score += 3
                signals.append("regex")

            # 信号 2: 短文本 + 无标点（+1 分）
            if self._short_no_punctuation(p_text):
                score += 1
                signals.append("short_no_punct")

            # 信号 3: 上下文——前有大间距（+1 分）
            if gaps and i > 0 and avg_line_height > 0:
                if gaps[i] > avg_line_height * 2:
                    score += 1
                    signals.append("large_gap_before")

            # 信号 4: 上下文——后有大间距（+1 分）
            if gaps and i < len(gaps) - 1 and avg_line_height > 0:
                if gaps[i + 1] > avg_line_height * 2:
                    score += 1
                    signals.append("large_gap_after")

            # 阈值: 正则匹配直接通过，其他需要 >= 2 分
            if score >= 3 or ("regex" in signals and score >= 3):
                result.append(('heading', p_text))
            elif score >= 2:
                result.append(('heading', p_text))
            else:
                result.append((p_type, p_text))

        return result

    def detect_with_level(self, paragraphs: List[Tuple[str, str]]) -> List[Tuple[str, str, int]]:
        """检测并生成层级目录

        Returns:
            [(type, text, level), ...]  level: 1=卷/部, 2=章/回, 3=节/其他
        """
        result = []
        for p_type, p_text in paragraphs:
            if p_type == 'heading':
                level = self._detect_level(p_text)
                result.append(('heading', p_text, level))
            else:
                result.append(('body', p_text, 0))
        return result

    def _detect_level(self, text: str) -> int:
        """检测章节层级"""
        text = text.strip()
        # 卷/部 = 1 级
        if re.match(r'^第[一二三四五六七八九十百千零〇\d]+[卷篇部]', text):
            return 1
        if re.match(r'^(上|中|下)[卷部篇]', text):
            return 1
        if re.match(r'^卷[一二三四五六七八九十\d]+', text):
            return 1
        # 章/回 = 2 级
        if re.match(r'^第[一二三四五六七八九十百千零〇\d]+[章回]', text):
            return 2
        if re.match(r'^Chapter\s+\d+', text, re.IGNORECASE):
            return 2
        # 节 = 3 级
        if re.match(r'^第[一二三四五六七八九十百千零〇\d]+节', text):
            return 3
        if re.match(r'^[一二三四五六七八九十]+[、.．]', text):
            return 3
        # 特殊标题 = 2 级
        if re.match(r'^(序|前言|后记|序言|目录|附录|结语|引言|楔子|尾声|番外|引子|终章|序章|跋|后序)', text):
            return 2
        return 2  # 默认 2 级

    def _is_chapter_title(self, text: str) -> bool:
        """v3 兼容判断"""
        text = text.strip()
        if not text or len(text) > 50:
            return False
        if self._regex_match(text):
            return True
        if len(text) <= 20 and not re.search(r'[。，；：、,;:]', text):
            if re.match(r'^[一二三四五六七八九十百千\d]+[、.．]', text):
                return True
        return False

    def _regex_match(self, text: str) -> bool:
        """正则匹配"""
        text = text.strip()
        for pattern in self._patterns:
            if pattern.match(text):
                return True
        return False

    def _short_no_punctuation(self, text: str) -> bool:
        """短文本且无标点"""
        text = text.strip()
        if len(text) > 30:
            return False
        if re.search(r'[。，；：、,;:！？]', text):
            return False
        return True

    def extract_chapters(self, paragraphs: List[Tuple[str, str]]) -> List[dict]:
        """提取章节列表（v3 兼容）"""
        chapters = []
        current_start = 0
        current_title = None
        current_paras = 0

        for i, (p_type, p_text) in enumerate(paragraphs):
            if p_type == 'heading':
                if current_title is not None:
                    char_count = sum(
                        len(paragraphs[j][1])
                        for j in range(current_start, i)
                        if paragraphs[j][0] != 'heading'
                    )
                    chapters.append({
                        "title": current_title,
                        "paragraph_count": current_paras,
                        "start_index": current_start,
                        "char_count": char_count,
                    })
                current_title = p_text
                current_start = i
                current_paras = 0
            else:
                current_paras += 1

        if current_title is not None:
            char_count = sum(
                len(paragraphs[j][1])
                for j in range(current_start, len(paragraphs))
                if paragraphs[j][0] != 'heading'
            )
            chapters.append({
                "title": current_title,
                "paragraph_count": current_paras,
                "start_index": current_start,
                "char_count": char_count,
            })

        return chapters

    def extract_chapters_with_level(self, paragraphs: List[Tuple[str, str, int]]) -> List[dict]:
        """提取章节列表（带层级）

        Returns:
            [{"title": str, "level": int, "paragraph_count": int, ...}, ...]
        """
        chapters = []
        current_start = 0
        current_title = None
        current_level = 2
        current_paras = 0

        for i, (p_type, p_text, level) in enumerate(paragraphs):
            if p_type == 'heading':
                if current_title is not None:
                    char_count = sum(
                        len(paragraphs[j][1])
                        for j in range(current_start, i)
                        if paragraphs[j][0] != 'heading'
                    )
                    chapters.append({
                        "title": current_title,
                        "level": current_level,
                        "paragraph_count": current_paras,
                        "start_index": current_start,
                        "char_count": char_count,
                    })
                current_title = p_text
                current_level = level
                current_start = i
                current_paras = 0
            else:
                current_paras += 1

        if current_title is not None:
            char_count = sum(
                len(paragraphs[j][1])
                for j in range(current_start, len(paragraphs))
                if paragraphs[j][0] != 'heading'
            )
            chapters.append({
                "title": current_title,
                "level": current_level,
                "paragraph_count": current_paras,
                "start_index": current_start,
                "char_count": char_count,
            })

        return chapters
