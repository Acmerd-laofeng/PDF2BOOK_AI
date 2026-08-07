# -*- coding: utf-8 -*-
"""逐页 OCR 结果缓存系统

缓存格式：cache/pages/{pdf_hash}_page_NNNN.json
JSON 内容：[{"text": "...", "bbox": [...], "confidence": 0.95}, ...]

支持中断恢复：
- Pipeline 检测已有缓存，跳过已处理页面
- get_resume_info() 返回缓存概况（命中页数/总页数/跳过比例）
- clear() 清空指定 PDF 的缓存
"""
import json
import os
import hashlib
from pathlib import Path
from typing import List, Optional, Dict
from engines.ocr.base import OCRBlock


class PageCache:
    """逐页缓存管理器"""

    def __init__(self, cache_dir: str = "cache/pages"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, page_num: int, pdf_hash: str = "") -> Path:
        """获取缓存文件路径"""
        prefix = f"{pdf_hash}_" if pdf_hash else ""
        return self.cache_dir / f"{prefix}page_{page_num:04d}.json"

    def get(self, page_num: int, pdf_hash: str = "") -> Optional[List[OCRBlock]]:
        """读取缓存

        Returns:
            OCRBlock 列表，或 None（无缓存）
        """
        path = self._cache_path(page_num, pdf_hash)
        if not path.exists():
            return None

        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            blocks = []
            for item in data:
                blocks.append(OCRBlock(
                    text=item['text'],
                    bbox=item['bbox'],
                    confidence=item.get('confidence', 0.0),
                ))
            return blocks
        except (json.JSONDecodeError, KeyError):
            return None

    def save(self, page_num: int, blocks: List[OCRBlock], pdf_hash: str = ""):
        """保存缓存"""
        path = self._cache_path(page_num, pdf_hash)
        data = []
        for block in blocks:
            data.append({
                'text': block.text,
                'bbox': block.bbox,
                'confidence': block.confidence,
            })

        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)

    def has(self, page_num: int, pdf_hash: str = "") -> bool:
        """检查是否有缓存"""
        return self._cache_path(page_num, pdf_hash).exists()

    def get_cached_pages(self, pdf_hash: str = "") -> List[int]:
        """获取所有已缓存的页码"""
        prefix = f"{pdf_hash}_" if pdf_hash else ""
        pages = []
        for p in self.cache_dir.glob(f"{prefix}page_*.json"):
            try:
                name = p.stem  # e.g. "abc123_page_0003" or "page_0003"
                num_str = name.split('_')[-1]
                pages.append(int(num_str))
            except (ValueError, IndexError):
                continue
        return sorted(pages)

    def get_resume_info(self, total_pages: int, pdf_hash: str = "") -> Dict:
        """获取中断恢复信息

        Args:
            total_pages: PDF 总页数
            pdf_hash: PDF 哈希值

        Returns:
            {
                "cached_pages": [1, 2, 3, ...],
                "cached_count": 3,
                "total_pages": 10,
                "skip_ratio": 0.3,
                "can_resume": True,
            }
        """
        cached = self.get_cached_pages(pdf_hash)
        cached_in_range = [p for p in cached if 0 <= p < total_pages]
        skip_ratio = len(cached_in_range) / total_pages if total_pages > 0 else 0

        return {
            "cached_pages": cached_in_range,
            "cached_count": len(cached_in_range),
            "total_pages": total_pages,
            "skip_ratio": round(skip_ratio, 2),
            "can_resume": len(cached_in_range) > 0,
        }

    def clear(self, pdf_hash: str = ""):
        """清空缓存

        Args:
            pdf_hash: 指定 PDF 哈希。空字符串则清空全部。
        """
        if pdf_hash:
            prefix = f"{pdf_hash}_"
            for p in self.cache_dir.glob(f"{prefix}page_*.json"):
                p.unlink()
        else:
            for p in self.cache_dir.glob("page_*.json"):
                p.unlink()
            for p in self.cache_dir.glob("*_page_*.json"):
                p.unlink()

    def get_cache_size(self, pdf_hash: str = "") -> int:
        """获取缓存文件总大小（字节）"""
        prefix = f"{pdf_hash}_" if pdf_hash else ""
        total = 0
        for p in self.cache_dir.glob(f"{prefix}page_*.json"):
            total += p.stat().st_size
        return total

    @staticmethod
    def compute_pdf_hash(pdf_path: str) -> str:
        """计算 PDF 文件哈希（用于缓存键）

        使用 文件名+文件大小+修改时间 作为简易哈希，
        避免读取整个大文件计算 MD5。
        """
        stat = os.stat(pdf_path)
        key = f"{os.path.basename(pdf_path)}_{stat.st_size}_{int(stat.st_mtime)}"
        return hashlib.md5(key.encode()).hexdigest()[:12]
