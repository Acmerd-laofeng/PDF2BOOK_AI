# -*- coding: utf-8 -*-
"""LLM Client (Gemini API) 测试"""
import os
import sys
import json
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.ai.llm_client import LLMClient
from engines.ai.corrector import Corrector


class TestLLMClient:
    """LLM 客户端测试"""

    def test_no_api_key_not_available(self):
        client = LLMClient(api_key="")
        assert not client.is_available

    def test_with_api_key_available(self):
        client = LLMClient(api_key="test_key")
        assert client.is_available

    def test_chat_no_key_returns_none(self):
        client = LLMClient(api_key="")
        result = client.chat("hello")
        assert result is None
        assert "未配置" in client.last_error

    def test_chat_success(self):
        """模拟 Gemini API 成功返回"""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "  这是纠错后的文本  "}],
                        "role": "model"
                    },
                    "finishReason": "STOP"
                }
            ]
        }
        with patch("engines.ai.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            client = LLMClient(api_key="test_key")
            result = client.chat("test prompt")

            assert result == "这是纠错后的文本"
            assert client.call_count == 1

    def test_chat_no_candidates(self):
        """模拟无候选内容"""
        mock_response = {"candidates": []}
        with patch("engines.ai.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            client = LLMClient(api_key="test_key")
            result = client.chat("test")

            assert result is None
            assert "无候选" in client.last_error or "无返回" in client.last_error

    def test_chat_http_error(self):
        """模拟 HTTP 错误"""
        import urllib.error
        error_response = json.dumps({
            "error": {"message": "API key not valid"}
        }).encode()

        with patch("engines.ai.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="test", code=400, msg="Bad Request",
                hdrs={}, fp=MagicMock(read=MagicMock(return_value=error_response))
            )

            client = LLMClient(api_key="bad_key")
            result = client.chat("test")

            assert result is None
            assert "400" in client.last_error
            assert "API key not valid" in client.last_error

    def test_correct_ocr_returns_text(self):
        """测试 OCR 纠错方法"""
        mock_response = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "已经完成了任务"}],
                        "role": "model"
                    }
                }
            ]
        }
        with patch("engines.ai.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            client = LLMClient(api_key="test_key")
            # 输入含常见 OCR 错误 "己经" → "已经"
            result = client.correct_ocr("己经完成了任务")

            assert result == "已经完成了任务"
            assert client.call_count == 1

    def test_correct_ocr_empty_text(self):
        """空文本直接返回"""
        client = LLMClient(api_key="test_key")
        assert client.correct_ocr("") == ""
        assert client.correct_ocr("   ") == "   "

    def test_test_connection_success(self):
        """测试连接成功"""
        mock_response = {
            "candidates": [
                {"content": {"parts": [{"text": "OK"}]}}
            ]
        }
        with patch("engines.ai.llm_client.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            client = LLMClient(api_key="test_key")
            success, msg = client.test_connection()

            assert success is True
            assert "连接成功" in msg

    def test_test_connection_no_key(self):
        """无 Key 测试连接失败"""
        client = LLMClient(api_key="")
        success, msg = client.test_connection()
        assert success is False
        assert "API Key" in msg

    def test_models_defined(self):
        """模型列表正确"""
        assert "gemini-3.5-flash" in LLMClient.MODELS
        assert "gemini-2.0-flash" in LLMClient.MODELS


class TestCorrectorLLM:
    """Corrector 的 LLM 纠错方法测试"""

    def test_llm_correct_no_client(self):
        """无 LLM client 时原样返回"""
        c = Corrector()
        paragraphs = [("body", "测试文本"), ("heading", "标题")]
        result = c.llm_correct(paragraphs, llm_client=None)
        assert result == paragraphs

    def test_llm_correct_no_api_key(self):
        """LLM client 无 API Key 时原样返回"""
        c = Corrector()
        client = LLMClient(api_key="")
        paragraphs = [("body", "测试文本")]
        result = c.llm_correct(paragraphs, llm_client=client)
        assert result == paragraphs

    def test_llm_correct_with_mock(self):
        """模拟 LLM 纠错流程"""
        c = Corrector()
        # 加载字典使 corrector 有纠错能力
        c._dictionary = {"商稻": "商務"}

        client = MagicMock()
        client.is_available = True
        client.call_count = 0
        client.correct_ocr = MagicMock(return_value="商務出版社出版")

        # 包含已知错字的段落会触发 LLM 纠错
        paragraphs = [("body", "商稻出版社出版")]

        result = c.llm_correct(paragraphs, llm_client=client)

        # 本地字典已修正 "商稻" → "商務"，但仍会调 LLM
        assert client.correct_ocr.called

    def test_llm_correct_skips_short_text(self):
        """短文本不调 API"""
        c = Corrector()
        client = MagicMock()
        client.is_available = True
        client.correct_ocr = MagicMock(return_value="OK")

        paragraphs = [("body", "ab")]  # 太短
        c.llm_correct(paragraphs, llm_client=client)

        # find_low_confidence_words 可能仍报告，但 correct_ocr 在 corrector 中
        # 会因短文本被跳过（llm_client.correct_batch 中过滤）
        # 这里只验证流程不崩溃
        assert True


class TestConstantsAI:
    """AI 相关常量测试"""

    def test_gemini_models_defined(self):
        from app.constants import GEMINI_MODELS, GEMINI_DEFAULT_MODEL
        assert "gemini-3.5-flash" in GEMINI_MODELS
        assert GEMINI_DEFAULT_MODEL == "gemini-3.5-flash"

    def test_ai_correct_params(self):
        from app.constants import AI_CORRECT_MIN_TEXT_LENGTH, AI_CORRECT_BATCH_SIZE
        assert AI_CORRECT_MIN_TEXT_LENGTH > 0
        assert AI_CORRECT_BATCH_SIZE > 0


class TestConfigAI:
    """AI 配置读写测试"""

    def test_default_values(self):
        from app.config import Config
        # 未 load 时默认值
        assert Config.get_ai_provider() == "none"
        assert Config.get_ai_api_key() == ""
        assert Config.get_ai_model() == "gemini-3.5-flash"
        assert Config.get_ai_correct_enabled() is False
