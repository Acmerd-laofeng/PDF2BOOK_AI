# -*- coding: utf-8 -*-
"""LLM 网关（预留，v4 实现）"""
from typing import Optional


class LLMClient:
    """LLM 客户端

    统一接口支持：
    - 本地模型（Qwen2.5 / MiniCPM）
    - DeepSeek API
    - OpenAI API
    """

    def __init__(self, provider: str = "", api_key: str = ""):
        self.provider = provider
        self.api_key = api_key

    def chat(self, prompt: str, system: str = "") -> Optional[str]:
        """调用 LLM"""
        # TODO: v4 实现各 provider 对接
        return None

    def correct_ocr(self, text: str) -> Optional[str]:
        """OCR 纠错专用 prompt"""
        prompt = f"请纠正以下 OCR 识别文本中的错误：\n\n{text}"
        return self.chat(prompt, system="你是 OCR 纠错助手，只返回纠正后的文本，不要解释。")
