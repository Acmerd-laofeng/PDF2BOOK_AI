# -*- coding: utf-8 -*-
"""OCR 纠错引擎

三层纠错策略：
1. 本地字典纠错（已知错误映射）— v3 实现
2. ngram/词频模型纠错 — v4 预留
3. LLM API 纠错 — v4 预留
"""
import json
import re
from pathlib import Path
from typing import Tuple


class Corrector:
    """OCR 纠错器"""

    def __init__(self):
        self._dictionary: dict[str, str] = {}  # wrong → correct
        self._llm_client = None
        self._correction_count = 0

    def load_dictionary(self, path: str) -> int:
        """加载纠错字典

        Args:
            path: JSON 文件路径

        Returns:
            加载的词条数
        """
        dict_path = Path(path)
        if dict_path.exists():
            with open(dict_path, 'r', encoding='utf-8') as f:
                self._dictionary = json.load(f)
            # 过滤掉 key==value 的无效条目
            self._dictionary = {
                k: v for k, v in self._dictionary.items() if k != v
            }
            return len(self._dictionary)
        return 0

    def correct(self, text: str) -> Tuple[str, int]:
        """纠错

        Args:
            text: 待纠错文本

        Returns:
            (corrected_text, correction_count)
        """
        count = 0
        for wrong, correct in self._dictionary.items():
            if not wrong or not correct:
                continue
            if wrong in text:
                occurrences = text.count(wrong)
                text = text.replace(wrong, correct)
                count += occurrences

        self._correction_count += count
        return text, count

    def correct_paragraphs(self, paragraphs: list[tuple[str, str]]) -> list[tuple[str, str]]:
        """批量纠错段落

        Args:
            paragraphs: [(type, text), ...]

        Returns:
            纠错后的段落列表
        """
        corrected = []
        total_corrections = 0
        for p_type, p_text in paragraphs:
            new_text, n = self.correct(p_text)
            total_corrections += n
            corrected.append((p_type, new_text))

        if total_corrections > 0:
            from core.event_bus import event_bus
            event_bus.log_message.emit(f"OCR 纠错：共修正 {total_corrections} 处")

        return corrected

    def find_low_confidence_words(self, text: str, threshold: float = 0.85) -> list[dict]:
        """标记低置信度区域（v4）

        在文本中找出可能存在 OCR 错误的区域。
        基于：
        - 字典中已知的错字模式
        - 常见 OCR 错误模式（形似字、多字/少字）

        Args:
            text: 待检测文本
            threshold: 置信度阈值（未使用，预留）

        Returns:
            [{"word": str, "position": int, "suggestion": str}, ...]
        """
        findings = []

        # 检查已知错字
        for wrong, correct in self._dictionary.items():
            if not wrong or not correct:
                continue
            start = 0
            while True:
                pos = text.find(wrong, start)
                if pos == -1:
                    break
                findings.append({
                    "word": wrong,
                    "position": pos,
                    "suggestion": correct,
                    "type": "known_error",
                })
                start = pos + len(wrong)

        # 检查常见形似字（硬编码高频错误）
        common_confusable = {
            '己': '已',
            '戊': '戌',
            '己': '已',
            '未': '末',
            '土': '士',
            '人': '入',
            '干': '千',
            '日': '曰',
            '贝': '见',
            '广': '厂',
        }
        for wrong, correct in common_confusable.items():
            start = 0
            while True:
                pos = text.find(wrong, start)
                if pos == -1:
                    break
                # 避免重复报告已知错字
                if wrong not in self._dictionary:
                    findings.append({
                        "word": wrong,
                        "position": pos,
                        "suggestion": correct,
                        "type": "confusable",
                    })
                start = pos + len(wrong)

        return findings

    def generate_correction_report(self, paragraphs: list[tuple[str, str]]) -> dict:
        """生成纠错报告（v4）

        Args:
            paragraphs: [(type, text), ...]

        Returns:
            {"total_findings": int, "known_corrections": int,
             "low_confidence": int, "details": [...]}
        """
        all_findings = []
        for i, (p_type, p_text) in enumerate(paragraphs):
            findings = self.find_low_confidence_words(p_text)
            for f in findings:
                f["paragraph_index"] = i
                f["paragraph_type"] = p_type
                all_findings.append(f)

        known = sum(1 for f in all_findings if f["type"] == "known_error")
        confusable = sum(1 for f in all_findings if f["type"] == "confusable")

        return {
            "total_findings": len(all_findings),
            "known_corrections": known,
            "confusable_chars": confusable,
            "details": all_findings[:100],  # 限制前 100 条
        }

    def llm_correct(self, paragraphs: list[tuple[str, str]], llm_client=None) -> list[tuple[str, str]]:
        """使用 LLM 对低置信度段落进行 AI 纠错

        策略：只对包含低置信度区域的段落调用 LLM，减少 API 调用次数。
        先用本地字典纠错，再对剩余可疑段落调用 LLM。

        Args:
            paragraphs: [(type, text), ...]
            llm_client: LLMClient 实例（必须已配置 api_key）

        Returns:
            纠错后的段落列表
        """
        if not llm_client or not llm_client.is_available:
            return paragraphs

        from core.event_bus import event_bus

        # 找出需要 LLM 纠错的段落（有低置信度标记的）
        needs_correction = []
        needs_indices = []
        for i, (p_type, p_text) in enumerate(paragraphs):
            findings = self.find_low_confidence_words(p_text)
            # 有可疑字符或段落较长（可能含隐含错误）
            if findings or (len(p_text) > 50 and p_type == "body"):
                needs_correction.append(p_text)
                needs_indices.append(i)

        if not needs_correction:
            event_bus.log_message.emit("[AI纠错] 未发现需要 AI 纠错的段落")
            return paragraphs

        event_bus.log_message.emit(
            f"[AI纠错] 对 {len(needs_correction)} 个段落调用 Gemini 纠错..."
        )

        # 逐段调用 LLM 纠错
        corrected_count = 0
        for idx, text in zip(needs_indices, needs_correction):
            result = llm_client.correct_ocr(text)
            if result and result != text:
                # 记录学到的纠错（简单提取差异）
                paragraphs[idx] = (paragraphs[idx][0], result)
                corrected_count += 1

        event_bus.log_message.emit(
            f"[AI纠错] 完成: {corrected_count}/{len(needs_correction)} 段落被修正, "
            f"API 调用 {llm_client.call_count} 次"
        )

        return paragraphs

    def learn(self, wrong: str, correct: str):
        """学习用户修正（存入字典）"""
        if wrong and correct and wrong != correct:
            self._dictionary[wrong] = correct

    def save_dictionary(self, path: str):
        """保存纠错字典"""
        dict_path = Path(path)
        dict_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dict_path, 'w', encoding='utf-8') as f:
            json.dump(self._dictionary, f, ensure_ascii=False, indent=2)

    @property
    def total_corrections(self) -> int:
        """累计纠错次数"""
        return self._correction_count

    @property
    def dictionary_size(self) -> int:
        """字典大小"""
        return len(self._dictionary)
