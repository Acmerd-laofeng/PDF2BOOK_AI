# -*- coding: utf-8 -*-
"""段落检测器 - 从 v2 迁移并增强

核心算法：
1. 首行缩进检测（x_left - body_x > threshold）
2. 大间距检测（gap > avg_gap * multiplier）
3. 居中+短行 = 章节标题
4. 右半部分+短行 = 签名/落款
5. 底部纯数字 = 页码（过滤）
6. 跨页断行合并（句末标点检测）

v3 改进：
- 阈值参数化（不再硬编码）
- 输入为 OCRBlock 列表（标准化）
- 输出为 (type, text) 列表
"""
import re
from typing import List, Tuple

from engines.ocr.base import OCRBlock
from app.constants import (
    DEFAULT_INDENT_THRESHOLD,
    DEFAULT_GAP_MULTIPLIER,
    DEFAULT_CENTER_TOLERANCE,
    DEFAULT_SHORT_LINE_RATIO,
    DEFAULT_PAGE_NUM_REGION,
    SENTENCE_END_CHARS,
)


class ParagraphDetector:
    """段落检测器"""

    def __init__(self):
        self.indent_threshold = DEFAULT_INDENT_THRESHOLD
        self.gap_multiplier = DEFAULT_GAP_MULTIPLIER
        self.center_tolerance = DEFAULT_CENTER_TOLERANCE
        self.short_line_ratio = DEFAULT_SHORT_LINE_RATIO
        self.page_num_region = DEFAULT_PAGE_NUM_REGION
        self.detect_chapters = True
        self.merge_cross_page = True

    def configure(self, indent_threshold: int = None, gap_multiplier: float = None,
                  detect_chapters: bool = None, merge_cross_page: bool = None,
                  center_tolerance: float = None, short_line_ratio: float = None):
        """配置检测参数"""
        if indent_threshold is not None:
            self.indent_threshold = indent_threshold
        if gap_multiplier is not None:
            self.gap_multiplier = gap_multiplier
        if detect_chapters is not None:
            self.detect_chapters = detect_chapters
        if merge_cross_page is not None:
            self.merge_cross_page = merge_cross_page
        if center_tolerance is not None:
            self.center_tolerance = center_tolerance
        if short_line_ratio is not None:
            self.short_line_ratio = short_line_ratio

    def detect(self, blocks: List[OCRBlock], page_num: int = 0) -> List[Tuple[str, str]]:
        """检测段落结构

        Args:
            blocks: OCR 识别块列表
            page_num: 页码（用于日志）

        Returns:
            [(type, text), ...]  type: 'heading' | 'body'
        """
        if not blocks:
            return []

        # 过滤空文本
        lines = [b for b in blocks if b.text and b.text.strip()]
        if not lines:
            return []

        # 计算页面尺寸
        page_w = max(b.x_right for b in lines)
        page_h = max(b.y_bot for b in lines)

        # 过滤页码
        lines = self._filter_page_numbers(lines, page_w, page_h)
        if not lines:
            return []

        # 找正文左边界（第 25 百分位）
        x_lefts = sorted(b.x_left for b in lines)
        body_x = x_lefts[len(x_lefts) // 4] if len(x_lefts) > 4 else x_lefts[0]

        # 按 Y 坐标排序
        lines.sort(key=lambda b: b.y_top)

        # 计算平均行间距
        if len(lines) > 1:
            gaps = []
            for i in range(1, len(lines)):
                gap = lines[i].y_top - lines[i - 1].y_bot
                gaps.append(gap)
            avg_gap = sum(gaps) / len(gaps) if gaps else 0
        else:
            avg_gap = 0

        # 分段
        return self._segment(lines, page_w, body_x, avg_gap)

    def _filter_page_numbers(self, lines: List[OCRBlock], page_w: float, page_h: float) -> List[OCRBlock]:
        """过滤页码"""
        filtered = []
        for b in lines:
            is_page_num = (
                b.y_top > page_h * self.page_num_region and  # 底部区域
                b.width < 120 and                            # 很窄
                re.match(r'^\d{1,4}$', b.text)               # 纯数字
            )
            if not is_page_num:
                filtered.append(b)
        return filtered

    def _segment(self, lines: List[OCRBlock], page_w: float,
                 body_x: float, avg_gap: float) -> List[Tuple[str, str]]:
        """分段检测"""
        paragraphs = []
        current_para: List[OCRBlock] = []
        current_type = 'body'

        for idx, line in enumerate(lines):
            is_new_para = False  # v2 兼容：第一行不强制新段落
            para_type = 'body'

            # 首行缩进
            indent = line.x_left - body_x
            if indent > self.indent_threshold:
                is_new_para = True

            # 大间距
            if idx > 0 and avg_gap > 0:
                gap = line.y_top - lines[idx - 1].y_bot
                if gap > avg_gap * self.gap_multiplier:
                    is_new_para = True

            # 章节标题检测：居中 + 短行
            if self.detect_chapters:
                is_centered = abs(line.x_center - page_w / 2) < page_w * self.center_tolerance
                is_short = line.width < page_w * self.short_line_ratio
                if is_centered and is_short and len(line.text) < 30:
                    para_type = 'heading'

            # 签名/落款：右半部分短行
            if line.x_left > page_w * 0.5 and len(line.text) < 30:
                is_new_para = True
                para_type = 'body'

            if is_new_para and current_para:
                para_text = ''.join(b.text for b in current_para)
                if para_text.strip():
                    paragraphs.append((current_type, para_text))
                current_para = []
                current_type = para_type

            if para_type == 'heading' and is_new_para:
                # 标题单独成段
                if current_para:
                    para_text = ''.join(b.text for b in current_para)
                    if para_text.strip():
                        paragraphs.append((current_type, para_text))
                    current_para = []
                paragraphs.append(('heading', line.text))
                current_type = 'body'
                continue

            current_para.append(line)
            current_type = para_type

        # 最后一段
        if current_para:
            para_text = ''.join(b.text for b in current_para)
            if para_text.strip():
                paragraphs.append((current_type, para_text))

        return paragraphs

    def postprocess(self, paragraphs: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """后处理：跨页合并 + 噪音过滤"""
        if not paragraphs:
            return []

        if not self.merge_cross_page:
            # 仅过滤噪音
            return [(t, p) for t, p in paragraphs if t == 'heading' or len(p) >= 2]

        # 句末标点正则（转义特殊字符，避免 ] 等破坏字符类）
        sentence_end = re.compile(r'[' + re.escape(SENTENCE_END_CHARS) + r']\)?$')

        merged = []
        i = 0
        while i < len(paragraphs):
            p_type, p_text = paragraphs[i]

            if p_type == 'heading':
                merged.append((p_type, p_text))
                i += 1
                continue

            # 跨页断行合并
            while i + 1 < len(paragraphs):
                next_type, next_text = paragraphs[i + 1]
                if (next_type != 'heading'
                        and not sentence_end.search(p_text)
                        and len(p_text) > 10
                        and len(next_text) > 2):
                    p_text = p_text + next_text
                    i += 1
                else:
                    break

            merged.append((p_type, p_text))
            i += 1

        # 过滤过短噪音段落
        filtered = []
        for p_type, p_text in merged:
            if p_type == 'heading':
                filtered.append((p_type, p_text))
            elif len(p_text) >= 2:
                filtered.append((p_type, p_text))

        return filtered
