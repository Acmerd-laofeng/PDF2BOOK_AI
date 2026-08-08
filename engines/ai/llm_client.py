# -*- coding: utf-8 -*-
"""LLM 网关 — Gemini API 实现

支持：
- Google Gemini API（2.0 Flash / 1.5 Flash / 1.5 Pro）
- 免费层：15 次/分钟、1500 次/天（2.0 Flash）
"""
import json
import urllib.request
import urllib.error
from typing import Optional


class LLMClient:
    """LLM 客户端 — Gemini API

    使用 REST API 直调，无需额外依赖。

    Args:
        api_key: Gemini API Key
        model: 模型名（默认 gemini-2.0-flash）
    """

    # Gemini API 端点
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"

    # 支持的模型
    MODELS = {
        "gemini-3.5-flash": "Gemini 3.5 Flash（推荐，快速+免费）",
        "gemini-3.5-flash-lite": "Gemini 3.5 Flash Lite（轻量省配额）",
        "gemini-2.0-flash": "Gemini 2.0 Flash（兼容旧版）",
        "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite（备用）",
    }

    def __init__(self, api_key: str = "", model: str = "gemini-3.5-flash"):
        self.api_key = api_key
        self.model = model
        self._call_count = 0
        self._last_error = ""

    @property
    def is_available(self) -> bool:
        """是否可用（有 API Key）"""
        return bool(self.api_key)

    @property
    def call_count(self) -> int:
        """累计调用次数"""
        return self._call_count

    @property
    def last_error(self) -> str:
        """最近一次错误信息"""
        return self._last_error

    def chat(self, prompt: str, system: str = "", temperature: float = 0.1) -> Optional[str]:
        """调用 LLM

        Args:
            prompt: 用户提示词
            system: 系统指令（Gemini 用 system_instruction）
            temperature: 温度（纠错用低温度 0.1 保证稳定）

        Returns:
            LLM 返回的文本，失败返回 None
        """
        if not self.is_available:
            self._last_error = "未配置 API Key"
            return None

        url = f"{self.BASE_URL}/{self.model}:generateContent?key={self.api_key}"

        payload = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,
            },
        }

        if system:
            payload["systemInstruction"] = {
                "parts": [{"text": system}]
            }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            self._call_count += 1

            # 提取文本
            candidates = data.get("candidates", [])
            if not candidates:
                # 可能被安全过滤
                block_reason = data.get("promptFeedback", {}).get("blockReason", "")
                self._last_error = f"无返回内容（blockReason: {block_reason}）" if block_reason else "无候选内容"
                return None

            parts = candidates[0].get("content", {}).get("parts", [])
            if not parts:
                self._last_error = "返回内容为空"
                return None

            text = parts[0].get("text", "")
            return text.strip() if text else None

        except urllib.error.HTTPError as e:
            err_body = ""
            try:
                err_body = e.read().decode("utf-8")
                err_data = json.loads(err_body)
                self._last_error = f"HTTP {e.code}: {err_data.get('error', {}).get('message', err_body[:200])}"
            except Exception:
                self._last_error = f"HTTP {e.code}: {err_body[:200]}"
            return None
        except Exception as e:
            self._last_error = str(e)
            return None

    def correct_ocr(self, text: str) -> Optional[str]:
        """OCR 纠错专用

        只对文本进行纠错，不改变原文结构和格式。
        适用于低置信度段落（置信度 < 0.85）。

        Args:
            text: 待纠错文本（一段或几段）

        Returns:
            纠错后的文本，失败返回 None
        """
        if not text or not text.strip():
            return text

        system = (
            "你是一个专业的 OCR 纠错助手。"
            "用户会给你一段 OCR 识别出来的中文文本，其中可能包含形似字、多字、少字等识别错误。"
            "请直接返回纠正后的文本，不要添加任何解释、标注或格式。"
            "规则：\n"
            "1. 只修正明显的 OCR 错误（形似字如 己→已、贝→见、末→未 等）\n"
            "2. 保持原文的段落结构、标点符号和换行\n"
            "3. 不要增删内容，不要润色\n"
            "4. 如果没有错误，原样返回\n"
        )

        prompt = f"请纠正以下 OCR 文本中的错误：\n\n{text}"

        return self.chat(prompt, system=system, temperature=0.1)

    def correct_batch(self, texts: list[str]) -> list[Optional[str]]:
        """批量纠错（逐段调用，避免单次 token 过长）

        Args:
            texts: 多段文本

        Returns:
            对应的纠错结果列表（失败的位置为 None）
        """
        results = []
        for text in texts:
            if not text or len(text.strip()) < 5:
                # 太短的文本不值得调 API
                results.append(text if text else None)
                continue
            result = self.correct_ocr(text)
            results.append(result)
        return results

    def test_connection(self) -> tuple[bool, str]:
        """测试 API 连通性

        Returns:
            (success, message)
        """
        if not self.is_available:
            return False, "未配置 API Key"

        result = self.chat("请回复 OK", temperature=0)
        if result is not None:
            return True, f"连接成功（模型: {self.model}）"
        else:
            return False, f"连接失败: {self._last_error}"
