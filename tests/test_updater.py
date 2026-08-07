# -*- coding: utf-8 -*-
"""自动更新模块测试"""
import os
import sys
import json
import tempfile
from unittest.mock import patch, MagicMock

# 确保项目根目录在 path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.updater import (
    UpdateInfo,
    _compare_versions,
    check_update,
)
from app.constants import APP_VERSION, UPDATE_CHECK_URL


class TestVersionCompare:
    """版本号比较测试"""

    def test_equal_versions(self):
        assert _compare_versions("4.0.0", "4.0.0") == 0

    def test_equal_with_v_prefix(self):
        assert _compare_versions("v4.0.0", "4.0.0") == 0

    def test_newer_major(self):
        assert _compare_versions("5.0.0", "4.0.0") == 1

    def test_older_major(self):
        assert _compare_versions("3.0.0", "4.0.0") == -1

    def test_newer_minor(self):
        assert _compare_versions("4.1.0", "4.0.0") == 1

    def test_newer_patch(self):
        assert _compare_versions("4.0.1", "4.0.0") == 1

    def test_older_patch(self):
        assert _compare_versions("4.0.0", "4.0.1") == -1

    def test_with_suffix(self):
        assert _compare_versions("4.1.0-beta", "4.0.0") == 1

    def test_double_digit(self):
        assert _compare_versions("4.10.0", "4.9.0") == 1

    def test_missing_parts(self):
        assert _compare_versions("4", "4.0.0") == 0
        assert _compare_versions("4.1", "4.1.0") == 0


class TestCheckUpdate:
    """检查更新测试"""

    def test_no_update_needed(self):
        """当前版本与最新版本一致"""
        mock_response = {
            "tag_name": f"v{APP_VERSION}",
            "body": "Release notes here",
            "html_url": "https://github.com/ACMERD/PDF2BOOK_AI/releases/v4.0.0",
            "assets": [
                {"name": "PDF2BOOK_AI_Setup_v4.0.exe",
                 "browser_download_url": "https://example.com/setup.exe"}
            ],
            "published_at": "2026-08-07T00:00:00Z",
        }
        with patch("core.updater.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            result = check_update(timeout=5)
            assert result is not None
            assert result.has_update is False

    def test_update_available(self):
        """有新版本"""
        mock_response = {
            "tag_name": "v9.9.9",
            "body": "## 新功能\n- 大版本更新",
            "html_url": "https://github.com/ACMERD/PDF2BOOK_AI/releases/v9.9.9",
            "assets": [
                {"name": "PDF2BOOK_AI_Setup_v9.9.9.exe",
                 "browser_download_url": "https://example.com/setup.exe"}
            ],
            "published_at": "2026-08-08T00:00:00Z",
        }
        with patch("core.updater.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            result = check_update(timeout=5)
            assert result is not None
            assert result.has_update is True
            assert result.latest_version == "9.9.9"
            assert "大版本更新" in result.release_notes
            assert result.download_url == "https://example.com/setup.exe"

    def test_update_available_no_exe_asset(self):
        """有新版本但没有 .exe 附件，回退到 html_url"""
        mock_response = {
            "tag_name": "v9.9.9",
            "body": "",
            "html_url": "https://github.com/ACMERD/PDF2BOOK_AI/releases/v9.9.9",
            "assets": [],
            "published_at": "2026-08-08T00:00:00Z",
        }
        with patch("core.updater.urllib.request.urlopen") as mock_urlopen:
            mock_resp = MagicMock()
            mock_resp.__enter__ = MagicMock(return_value=mock_resp)
            mock_resp.__exit__ = MagicMock(return_value=False)
            mock_resp.read.return_value = json.dumps(mock_response).encode()
            mock_urlopen.return_value = mock_resp

            result = check_update(timeout=5)
            assert result is not None
            assert result.has_update is True
            assert result.download_url == "https://github.com/ACMERD/PDF2BOOK_AI/releases/v9.9.9"

    def test_network_failure_returns_none(self):
        """网络失败返回 None"""
        with patch("core.updater.urllib.request.urlopen",
                    side_effect=Exception("Network error")):
            result = check_update(timeout=1)
            assert result is None

    def test_timeout_returns_none(self):
        """超时返回 None"""
        import urllib.error
        with patch("core.updater.urllib.request.urlopen",
                   side_effect=urllib.error.URLError("Timeout")):
            result = check_update(timeout=1)
            assert result is None


class TestConstants:
    """常量配置测试"""

    def test_app_version_format(self):
        """版本号格式正确"""
        assert APP_VERSION.count(".") == 2
        parts = APP_VERSION.split(".")
        for p in parts:
            assert p.isdigit()

    def test_update_url_correct(self):
        """更新 URL 指向正确的仓库"""
        assert "github.com" in UPDATE_CHECK_URL
        assert "ACMERD" in UPDATE_CHECK_URL
        assert "PDF2BOOK_AI" in UPDATE_CHECK_URL
        assert "releases/latest" in UPDATE_CHECK_URL
