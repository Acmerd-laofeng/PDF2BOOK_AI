# -*- coding: utf-8 -*-
"""v2 vs v3 迁移验证测试

对比 v2 (pdf_to_epub.py) 和 v3 (engines/) 的核心逻辑输出一致性。

迁移对应关系：
  v2._parse_ocr_result() → v3 BBoxParser + ParagraphDetector.detect()
  v2._postprocess()      → v3 ParagraphDetector.postprocess()
  v2._create_epub()      → v3 EPUBBuilder.build()
  v2._escape_html()      → v3 EPUBBuilder 内部处理
"""
import sys
import os
import re
import json
import tempfile
from pathlib import Path

# v3 imports
sys.path.insert(0, str(Path(__file__).parent))
os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent))

from engines.ocr.base import OCRBlock
from engines.layout.bbox_parser import BBoxParser
from engines.layout.paragraph_detector import ParagraphDetector
from engines.layout.chapter_detector import ChapterDetector
from engines.export.epub import EPUBBuilder


# ============================================================
# v2 核心逻辑提取（从 pdf_to_epub.py 原样复制）
# ============================================================

def v2_parse_ocr_result(result, page_num=1):
    """v2 _parse_ocr_result 原样提取"""
    if not result or not result[0]:
        return []

    lines = []
    for item in result[0]:
        if len(item) < 2 or not item[1]:
            continue
        bbox = item[0]
        text = item[1].strip()
        conf = item[2] if len(item) > 2 else 0
        if not text:
            continue
        y_top = min(p[1] for p in bbox)
        y_bot = max(p[1] for p in bbox)
        x_left = min(p[0] for p in bbox)
        x_right = max(p[0] for p in bbox)
        y_center = (y_top + y_bot) / 2
        x_center = (x_left + x_right) / 2
        lines.append({
            'text': text, 'conf': conf,
            'y_top': y_top, 'y_bot': y_bot, 'y_center': y_center,
            'x_left': x_left, 'x_right': x_right, 'x_center': x_center,
            'height': y_bot - y_top, 'width': x_right - x_left,
        })

    if not lines:
        return []

    page_w = max(l['x_right'] for l in lines)
    page_h = max(l['y_bot'] for l in lines)

    filtered = []
    for l in lines:
        is_page_num = (
            l['y_top'] > page_h * 0.75 and
            l['width'] < 120 and
            re.match(r'^\d{1,4}$', l['text'])
        )
        if not is_page_num:
            filtered.append(l)
    lines = filtered
    if not lines:
        return []

    x_lefts = sorted(l['x_left'] for l in lines)
    body_x = x_lefts[len(x_lefts) // 4] if len(x_lefts) > 4 else x_lefts[0]

    lines.sort(key=lambda x: x['y_top'])
    if len(lines) > 1:
        gaps = [lines[i]['y_top'] - lines[i-1]['y_bot'] for i in range(1, len(lines))]
        avg_gap = sum(gaps) / len(gaps) if gaps else 0
    else:
        avg_gap = 0

    paragraphs = []
    current_para = []
    current_type = 'body'

    for idx, line in enumerate(lines):
        is_new_para = False
        para_type = 'body'

        indent = line['x_left'] - body_x
        if indent > 30:
            is_new_para = True

        if idx > 0 and avg_gap > 0:
            gap = line['y_top'] - lines[idx-1]['y_bot']
            if gap > avg_gap * 1.8:
                is_new_para = True

        is_centered = abs(line['x_center'] - page_w / 2) < page_w * 0.15
        is_short = line['width'] < page_w * 0.4
        if is_centered and is_short and len(line['text']) < 30:
            para_type = 'heading'

        if line['x_left'] > page_w * 0.5 and len(line['text']) < 30:
            is_new_para = True
            para_type = 'body'

        if is_new_para and current_para:
            para_text = ''.join(l['text'] for l in current_para)
            if para_text.strip():
                paragraphs.append((current_type, para_text))
            current_para = []
            current_type = para_type

        if para_type == 'heading' and is_new_para:
            if current_para:
                para_text = ''.join(l['text'] for l in current_para)
                if para_text.strip():
                    paragraphs.append((current_type, para_text))
                current_para = []
            paragraphs.append(('heading', line['text']))
            current_type = 'body'
            continue

        current_para.append(line)
        current_type = para_type

    if current_para:
        para_text = ''.join(l['text'] for l in current_para)
        if para_text.strip():
            paragraphs.append((current_type, para_text))

    return paragraphs


def v2_postprocess(paragraphs):
    """v2 _postprocess 原样提取"""
    if not paragraphs:
        return []
    sentence_end = re.compile(r'[。？！…\u201d\u300d\u300f]\)?$')
    merged = []
    i = 0
    while i < len(paragraphs):
        p_type, p_text = paragraphs[i]
        if p_type == 'heading':
            merged.append((p_type, p_text))
            i += 1
            continue
        if i + 1 < len(paragraphs):
            next_type, next_text = paragraphs[i + 1]
            if (next_type != 'heading'
                    and not sentence_end.search(p_text)
                    and len(p_text) > 10
                    and len(next_text) > 2):
                p_text = p_text + next_text
                i += 1
                while i + 1 < len(paragraphs):
                    next_type2, next_text2 = paragraphs[i + 1]
                    if (next_type2 != 'heading'
                            and not sentence_end.search(p_text)
                            and len(next_text2) > 2):
                        p_text = p_text + next_text2
                        i += 1
                    else:
                        break
                merged.append((p_type, p_text))
                i += 1
                continue
        merged.append((p_type, p_text))
        i += 1
    filtered = []
    for p_type, p_text in merged:
        if p_type == 'heading':
            filtered.append((p_type, p_text))
        elif len(p_text) >= 2:
            filtered.append((p_type, p_text))
    return filtered


def v2_escape_html(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ============================================================
# v3 核心逻辑
# ============================================================

def make_v2_result(blocks):
    """将 OCRBlock 列表转为 v2 格式 result = (list_of_tuples, elapsed)"""
    items = []
    for b in blocks:
        items.append((b.bbox, b.text, b.confidence))
    return (items, 0.0)


def v3_detect(blocks, page_num=1):
    """v3 段落检测（blocks 已是 OCRBlock 列表，直接进 ParagraphDetector）"""
    detector = ParagraphDetector()
    return detector.detect(blocks, page_num=page_num)


def v3_postprocess(paragraphs):
    """v3 后处理"""
    detector = ParagraphDetector()
    return detector.postprocess(paragraphs)


# ============================================================
# 测试用例
# ============================================================

def make_block(text, x0, y0, x1, y1, conf=0.95):
    """构造 OCRBlock（text 自动 strip，与 v2 一致）"""
    return OCRBlock(
        text=text.strip(),
        bbox=[[x0, y0], [x1, y0], [x1, y1], [x0, y1]],
        confidence=conf,
    )


# 测试 1: 基本段落 - 首行缩进检测
TEST_CASE_1 = [
    make_block("第一章 引言", 800, 100, 1200, 140),    # 居中标题
    make_block("这是第一段的内容，", 350, 200, 1200, 240),  # 缩进
    make_block("继续第一段的内容。", 300, 250, 1200, 290),    # 不缩进，句号结尾
    make_block("这是第二段的内容。", 350, 350, 1200, 390),  # 缩进，句号结尾
]

# 测试 2: 页码过滤
TEST_CASE_2 = [
    make_block("正文内容在这里。", 300, 200, 1200, 240),
    make_block("42", 2200, 2800, 2280, 2840),  # 右下角页码
]

# 测试 3: 跨页合并
TEST_CASE_3_PAGE1 = [
    make_block("  这是一段很长很长的文字内容", 350, 200, 1200, 240),
    make_block("继续这段文字但还没有结束", 300, 250, 1200, 290),
]
TEST_CASE_3_PAGE2 = [
    make_block("这里是这段文字的结尾部分。", 300, 100, 1200, 140),
]

# 测试 4: 大间距分段
TEST_CASE_4 = [
    make_block("第一段文字内容。", 300, 100, 1200, 140),
    make_block("第二段文字内容。", 300, 400, 1200, 440),  # 大间距
]

# 测试 5: 签名/落款
TEST_CASE_5 = [
    make_block("正文内容结束。", 300, 100, 1200, 140),
    make_block("作者签名", 1600, 200, 2000, 240),  # 右半部分短行
]


def compare_paragraphs(v2_result, v3_result, test_name):
    """对比 v2 和 v3 段落列表"""
    print(f"\n{'='*60}")
    print(f"测试: {test_name}")
    print(f"{'='*60}")

    print(f"  v2: {len(v2_result)} 段落")
    for i, (ptype, ptext) in enumerate(v2_result):
        print(f"    [{i}] ({ptype}) {ptext[:50]}...")

    print(f"  v3: {len(v3_result)} 段落")
    for i, (ptype, ptext) in enumerate(v3_result):
        print(f"    [{i}] ({ptype}) {ptext[:50]}...")

    # 对比
    if len(v2_result) != len(v3_result):
        print(f"  ❌ 段落数不一致: v2={len(v2_result)} vs v3={len(v3_result)}")
        return False

    for i, (v2_p, v3_p) in enumerate(zip(v2_result, v3_result)):
        v2_type, v2_text = v2_p
        v3_type, v3_text = v3_p
        if v2_type != v3_type:
            print(f"  ❌ [{i}] 类型不一致: v2={v2_type} vs v3={v3_type}")
            return False
        if v2_text != v3_text:
            print(f"  ❌ [{i}] 文本不一致:")
            print(f"       v2: {v2_text[:80]}")
            print(f"       v3: {v3_text[:80]}")
            return False

    print(f"  ✅ 完全一致 ({len(v2_result)} 段落)")
    return True


def test_basic_paragraphs():
    """测试 1: 基本段落检测"""
    # v2
    v2_result = v2_parse_ocr_result(make_v2_result(TEST_CASE_1), page_num=1)
    v2_result = v2_postprocess(v2_result)

    # v3
    v3_result = v3_detect(TEST_CASE_1, page_num=1)
    v3_result = v3_postprocess(v3_result)

    return compare_paragraphs(v2_result, v3_result, "基本段落 - 首行缩进+标题")


def test_page_number_filter():
    """测试 2: 页码过滤"""
    v2_result = v2_parse_ocr_result(make_v2_result(TEST_CASE_2), page_num=1)
    v2_result = v2_postprocess(v2_result)

    v3_result = v3_detect(TEST_CASE_2, page_num=1)
    v3_result = v3_postprocess(v3_result)

    return compare_paragraphs(v2_result, v3_result, "页码过滤")


def test_cross_page_merge():
    """测试 3: 跨页断行合并"""
    # v2: 两页合并处理
    v2_p1 = v2_parse_ocr_result(make_v2_result(TEST_CASE_3_PAGE1), page_num=1)
    v2_p2 = v2_parse_ocr_result(make_v2_result(TEST_CASE_3_PAGE2), page_num=2)
    v2_all = v2_p1 + v2_p2
    v2_result = v2_postprocess(v2_all)

    # v3
    v3_p1 = v3_detect(TEST_CASE_3_PAGE1, page_num=1)
    v3_p2 = v3_detect(TEST_CASE_3_PAGE2, page_num=2)
    v3_all = v3_p1 + v3_p2
    v3_result = v3_postprocess(v3_all)

    return compare_paragraphs(v2_result, v3_result, "跨页断行合并")


def test_large_gap():
    """测试 4: 大间距分段"""
    v2_result = v2_parse_ocr_result(make_v2_result(TEST_CASE_4), page_num=1)
    v2_result = v2_postprocess(v2_result)

    v3_result = v3_detect(TEST_CASE_4, page_num=1)
    v3_result = v3_postprocess(v3_result)

    return compare_paragraphs(v2_result, v3_result, "大间距分段")


def test_signature():
    """测试 5: 签名/落款"""
    v2_result = v2_parse_ocr_result(make_v2_result(TEST_CASE_5), page_num=1)
    v2_result = v2_postprocess(v2_result)

    v3_result = v3_detect(TEST_CASE_5, page_num=1)
    v3_result = v3_postprocess(v3_result)

    return compare_paragraphs(v2_result, v3_result, "签名/落款")


def test_epub_output():
    """测试 6: EPUB 输出对比"""
    print(f"\n{'='*60}")
    print(f"测试: EPUB 输出对比")
    print(f"{'='*60}")

    paragraphs = [('heading', '测试章节'), ('body', '这是段落内容。')]

    with tempfile.TemporaryDirectory() as tmpdir:
        # v2 EPUB
        v2_epub_path = os.path.join(tmpdir, "v2_test.epub")
        v2_create_epub(paragraphs, "测试", "作者", v2_epub_path)

        # v3 EPUB
        v3_epub_path = os.path.join(tmpdir, "v3_test.epub")
        builder = EPUBBuilder()
        resources_dir = Path(__file__).parent / "resources" / "epub_themes"
        stats = builder.build(
            paragraphs=paragraphs,
            title="测试",
            author="作者",
            output_path=v3_epub_path,
            theme="classic",
            theme_dir=str(resources_dir) if resources_dir.exists() else None,
        )

        v2_size = os.path.getsize(v2_epub_path)
        v3_size = os.path.getsize(v3_epub_path)

        print(f"  v2 EPUB: {v2_size} bytes")
        print(f"  v3 EPUB: {v3_size} bytes")

        # 验证都是合法 EPUB
        import zipfile
        for name, path in [("v2", v2_epub_path), ("v3", v3_epub_path)]:
            with zipfile.ZipFile(path) as zf:
                names = zf.namelist()
                has_meta = any("META-INF" in n for n in names)
                has_content = any(n.endswith((".xhtml", ".html")) for n in names)
                print(f"  {name}: {len(names)} files, META-INF={has_meta}, content={has_content}")
                assert has_meta, f"{name} missing META-INF"
                assert has_content, f"{name} missing content files"

        print(f"  ✅ 两个 EPUB 均合法")
        return True


def v2_create_epub(paragraphs, title, author, output_path):
    """v2 _create_epub 简化版（不依赖 tkinter）"""
    from ebooklib import epub
    from datetime import datetime

    book = epub.EpubBook()
    book.set_identifier(f"pdf2epub-{datetime.now().strftime('%Y%m%d%H%M%S')}")
    book.set_title(title)
    book.add_author(author)
    book.set_language("zh-CN")

    style = """
body { font-family: serif; line-height: 1.8; margin: 5%; }
p { text-indent: 2em; margin: 0.5em 0; }
h1 { text-align: center; font-size: 1.6em; margin: 1.5em 0 0.5em; }
h2 { text-align: center; font-size: 1.3em; margin: 1.2em 0 0.5em; color: #333; }
"""
    css = epub.EpubItem(uid="style", file_name="style/default.css",
                        media_type="text/css", content=style.encode("utf-8"))
    book.add_item(css)

    chapters = []
    current_chap = []
    for p_type, p_text in paragraphs:
        if p_type == 'heading':
            if current_chap:
                chapters.append(current_chap)
            current_chap = [('heading', p_text)]
        else:
            current_chap.append((p_type, p_text))
    if current_chap:
        chapters.append(current_chap)
    if not chapters:
        chapters = [paragraphs]
    if chapters and chapters[0] and chapters[0][0][0] != 'heading':
        chapters[0].insert(0, ('heading', title))

    spine = ["nav"]
    epub_chapters = []
    for ci, chap_paras in enumerate(chapters):
        chap_title = "Unknown"
        for p_type, p_text in chap_paras:
            if p_type == 'heading':
                chap_title = p_text
                break
        else:
            chap_title = f"第 {ci+1} 章"

        file_name = f"chap_{ci+1}.xhtml"
        html_parts = [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<!DOCTYPE html>',
            '<html xmlns="http://www.w3.org/1999/xhtml">',
            '<head>',
            f'<title>{v2_escape_html(chap_title)}</title>',
            '<link rel="stylesheet" type="text/css" href="style/default.css"/>',
            '</head>',
            '<body>',
        ]
        for p_type, p_text in chap_paras:
            safe = v2_escape_html(p_text)
            if p_type == 'heading':
                if ci == 0 and p_text == chap_title:
                    html_parts.append(f'<h1>{safe}</h1>')
                else:
                    html_parts.append(f'<h2>{safe}</h2>')
            else:
                html_parts.append(f'<p>{safe}</p>')
        html_parts.extend(['</body>', '</html>'])
        html_content = "\n".join(html_parts)

        chapter = epub.EpubHtml(title=chap_title, file_name=file_name,
                                content=html_content.encode("utf-8"))
        chapter.add_item(css)
        book.add_item(chapter)
        epub_chapters.append(chapter)
        spine.append(chapter)

    book.toc = epub_chapters
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = spine
    epub.write_epub(output_path, book, {})


def test_edge_cases():
    """测试 7: 边界情况"""
    print(f"\n{'='*60}")
    print(f"测试: 边界情况")
    print(f"{'='*60}")

    results = []

    # 空输入
    v2_empty = v2_parse_ocr_result(([], 0.0))
    v3_empty = v3_detect([])
    results.append(("空输入", len(v2_empty) == 0 and len(v3_empty) == 0))

    # 单行
    single = [make_block("单行文字", 300, 100, 800, 140)]
    v2_single = v2_parse_ocr_result(make_v2_result(single))
    v3_single = v3_detect(single)
    results.append(("单行文字", len(v2_single) >= 1 and len(v3_single) >= 1))

    # 纯页码（应全部过滤）
    page_num_only = [make_block("99", 2200, 2800, 2280, 2840)]
    v2_pn = v2_parse_ocr_result(make_v2_result(page_num_only))
    v3_pn = v3_detect(page_num_only)
    results.append(("纯页码过滤", len(v2_pn) == 0 and len(v3_pn) == 0))

    for name, passed in results:
        print(f"  {'✅' if passed else '❌'} {name}")

    return all(r[1] for r in results)


# ============================================================
# 主函数
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("v2 vs v3 迁移验证测试")
    print("=" * 60)

    results = []
    results.append(("基本段落", test_basic_paragraphs()))
    results.append(("页码过滤", test_page_number_filter()))
    results.append(("跨页合并", test_cross_page_merge()))
    results.append(("大间距分段", test_large_gap()))
    results.append(("签名落款", test_signature()))
    results.append(("EPUB输出", test_epub_output()))
    results.append(("边界情况", test_edge_cases()))

    print(f"\n{'='*60}")
    print("迁移验证总结")
    print(f"{'='*60}")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    for name, r in results:
        print(f"  {'✅' if r else '❌'} {name}")
    print(f"\n  {passed}/{total} 通过")

    if passed == total:
        print("\n  🎉 v2 → v3 迁移验证全部通过！核心逻辑一致。")
    else:
        print("\n  ⚠️ 部分测试未通过，需检查差异。")
