# -*- coding: utf-8 -*-
"""PageCache 单元测试"""
import pytest
import tempfile
import os
from core.cache import PageCache
from engines.ocr.base import OCRBlock


def make_block(text="test", x0=100, y0=100, x1=300, y1=140, conf=0.95):
    return OCRBlock(
        text=text,
        bbox=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
        confidence=conf,
    )


class TestPageCache:

    @pytest.fixture
    def cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield PageCache(tmpdir)

    def test_save_and_get(self, cache):
        blocks = [make_block("hello"), make_block("world")]
        cache.save(1, blocks, "hash123")
        result = cache.get(1, "hash123")
        assert result is not None
        assert len(result) == 2
        assert result[0].text == "hello"
        assert result[1].text == "world"

    def test_get_nonexistent(self, cache):
        assert cache.get(999, "nohash") is None

    def test_has(self, cache):
        cache.save(5, [make_block()], "abc")
        assert cache.has(5, "abc")
        assert not cache.has(6, "abc")

    def test_get_cached_pages(self, cache):
        cache.save(1, [make_block()], "abc")
        cache.save(3, [make_block()], "abc")
        cache.save(5, [make_block()], "abc")
        pages = cache.get_cached_pages("abc")
        assert pages == [1, 3, 5]

    def test_clear_specific_hash(self, cache):
        cache.save(1, [make_block()], "hashA")
        cache.save(2, [make_block()], "hashB")
        cache.clear("hashA")
        assert not cache.has(1, "hashA")
        assert cache.has(2, "hashB")

    def test_clear_all(self, cache):
        cache.save(1, [make_block()], "hashA")
        cache.save(2, [make_block()], "hashB")
        cache.clear()
        assert not cache.has(1, "hashA")
        assert not cache.has(2, "hashB")

    def test_get_resume_info(self, cache):
        """缓存恢复信息"""
        # 缓存第 1-3 页
        for i in range(1, 4):
            cache.save(i, [make_block(f"page{i}")], "abc")

        info = cache.get_resume_info(10, "abc")
        assert info["cached_count"] == 3
        assert info["total_pages"] == 10
        assert info["skip_ratio"] == 0.3
        assert info["can_resume"] == True
        assert set(info["cached_pages"]) == {1, 2, 3}

    def test_resume_info_no_cache(self, cache):
        info = cache.get_resume_info(10, "nonexistent")
        assert info["cached_count"] == 0
        assert info["can_resume"] == False
        assert info["skip_ratio"] == 0

    def test_resume_info_out_of_range(self, cache):
        """超出范围的缓存页不计入"""
        cache.save(1, [make_block()], "abc")
        cache.save(15, [make_block()], "abc")  # 超出 10 页
        info = cache.get_resume_info(10, "abc")
        assert info["cached_count"] == 1  # 只有第 1 页在范围内

    def test_get_cache_size(self, cache):
        cache.save(1, [make_block("test")], "abc")
        size = cache.get_cache_size("abc")
        assert size > 0

    def test_compute_pdf_hash(self, tmp_path):
        """PDF 哈希计算"""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"fake pdf content")
        h1 = PageCache.compute_pdf_hash(str(pdf))
        h2 = PageCache.compute_pdf_hash(str(pdf))
        assert h1 == h2
        assert len(h1) == 12

    def test_hash_changes_with_modification(self, tmp_path):
        """修改文件后哈希变化"""
        pdf = tmp_path / "test.pdf"
        pdf.write_bytes(b"content v1 short")
        h1 = PageCache.compute_pdf_hash(str(pdf))
        pdf.write_bytes(b"content v2 much longer so size differs")
        h2 = PageCache.compute_pdf_hash(str(pdf))
        assert h1 != h2

    def test_roundtrip_preserves_bbox(self, cache):
        """序列化/反序列化保持 bbox 完整"""
        original = OCRBlock(
            text="测试",
            bbox=[[10.5, 20.3], [300.1, 20.3], [300.1, 60.7], [10.5, 60.7]],
            confidence=0.88,
        )
        cache.save(1, [original], "abc")
        result = cache.get(1, "abc")
        assert result[0].bbox == original.bbox
        assert result[0].confidence == 0.88
