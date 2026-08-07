# -*- coding: utf-8 -*-
"""检查更新模块 — 请求 GitHub Releases API 比对版本号"""
import json
import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional
from app.constants import APP_VERSION, UPDATE_CHECK_URL


@dataclass
class UpdateInfo:
    """更新信息"""
    has_update: bool = False
    latest_version: str = ""
    release_notes: str = ""
    download_url: str = ""
    published_at: str = ""
    html_url: str = ""


def _compare_versions(v1: str, v2: str) -> int:
    """语义化版本比较，返回 1(v1>v2) / -1(v1<v2) / 0(相等)

    支持形如 4.0.0 / v4.1.0 / 4.0.0-beta 等格式
    """
    def normalize(v: str) -> list:
        v = v.strip().lstrip("vV")
        # 取主版本部分（去掉 -beta 等后缀）
        main = v.split("-")[0]
        parts = []
        for p in main.split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        while len(parts) < 3:
            parts.append(0)
        return parts[:3]

    a = normalize(v1)
    b = normalize(v2)
    for i in range(3):
        if a[i] > b[i]:
            return 1
        elif a[i] < b[i]:
            return -1
    return 0


def check_update(timeout: int = 5) -> Optional[UpdateInfo]:
    """检查是否有新版本

    Args:
        timeout: 请求超时秒数
    Returns:
        UpdateInfo: 有更新时 has_update=True；无更新或失败时 has_update=False
        None: 请求失败（调用方应静默忽略）
    """
    try:
        req = urllib.request.Request(
            UPDATE_CHECK_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "PDF2BOOK-AI/" + APP_VERSION,
            },
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        latest = data.get("tag_name", "").lstrip("vV")

        # 无更新
        if _compare_versions(latest, APP_VERSION) <= 0:
            return UpdateInfo(has_update=False, latest_version=latest)

        # 找到安装包下载链接（优先 .exe，否则取 browser_download_url 第一个）
        download_url = ""
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.endswith(".exe"):
                download_url = asset.get("browser_download_url", "")
                break
        if not download_url:
            # 没有附件，用 Release 页面
            download_url = data.get("html_url", "")

        return UpdateInfo(
            has_update=True,
            latest_version=latest,
            release_notes=data.get("body", ""),
            download_url=download_url,
            published_at=data.get("published_at", ""),
            html_url=data.get("html_url", ""),
        )

    except Exception:
        # 静默失败：网络问题、API 限流、解析错误等
        return None
