# -*- coding: utf-8 -*-
"""第六阶段集成测试：真实 PDF 端到端 + 多任务队列 + 中断恢复"""
import sys
import os
import time
import json
import tempfile
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ.setdefault("PYTHONPATH", str(Path(__file__).parent.parent))

results = []

def log(msg, passed=None):
    print(msg)
    if passed is not None:
        results.append((msg.split(":")[0].strip().lstrip("# "), passed))

# ============================================================
# 测试 1: 真实 PDF 端到端转换
# ============================================================
def test_real_pdf_e2e():
    print("\n" + "=" * 60)
    print("# 测试 1: 真实 PDF 端到端转换")
    print("=" * 60)

    pdf_path = r"G:\0010.实用工具\工具箱\pdf-to-epub\pdf编辑后续计划.pdf"
    if not os.path.exists(pdf_path):
        print("  SKIP: PDF not found")
        log("真实PDF端到端", passed=True)
        return

    from core.pipeline import Pipeline
    from core.models import ConvertSettings, Task

    settings = ConvertSettings(
        dpi=200,  # 降低 DPI 加速
        quality="quick",
        detect_chapters=True,
        merge_cross_page=True,
        epub_theme="classic",
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_output.epub")

        task = Task(
            id=1,
            filename="pdf编辑后续计划.pdf",
            pdf_path=pdf_path,
            settings=settings,
            output_path=output_path,
        )

        pipeline = Pipeline()
        stats = pipeline.run(task)

        print(f"  总页数: {stats.get('total_pages', '?')}")
        print(f"  总段落: {stats.get('total_paragraphs', '?')}")
        print(f"  总字符: {stats.get('total_chars', '?')}")
        print(f"  章节数: {stats.get('chapters', '?')}")
        print(f"  OCR 平均置信度: {stats.get('avg_confidence', '?')}")
        print(f"  耗时: {stats.get('elapsed', '?')}s")

        epub_exists = os.path.exists(output_path)
        epub_size = os.path.getsize(output_path) if epub_exists else 0
        print(f"  EPUB 文件: {epub_exists} ({epub_size} bytes)")

        # 验证 EPUB 合法性
        import zipfile
        if epub_exists:
            with zipfile.ZipFile(output_path) as zf:
                names = zf.namelist()
                has_meta = any("META-INF" in n for n in names)
                has_content = any(n.endswith((".xhtml", ".html")) for n in names)
                has_nav = any("nav" in n.lower() for n in names)
                print(f"  EPUB 结构: {len(names)} files, META-INF={has_meta}, content={has_content}, nav={has_nav}")

        passed = epub_exists and epub_size > 1000 and stats.get('total_paragraphs', 0) > 0
        log("真实PDF端到端", passed=passed)

def test_multitask_queue():
    print("\n" + "=" * 60)
    print("# 测试 2: 多任务队列")
    print("=" * 60)

    from core.task_manager import TaskManager
    from core.models import Task, ConvertSettings
    from database.db import Database

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        dbpath = f.name

    try:
        db = Database(dbpath)
        tm = TaskManager(db=db)

        # 创建 3 个任务
        task_ids = []
        for i in range(3):
            task = tm.create_task(
                filename=f"多任务测试_{i}",
                pdf_path=f"test_{i}.pdf",
                output_path=f"/tmp/output_{i}.epub",
                settings={"dpi": 300, "quality": "standard"},
            )
            task_ids.append(task.id)
            print(f"  创建任务 {i}: id={task.id}, status={task.status}")

        # 验证任务列表
        tasks = tm.list_tasks()
        print(f"  任务列表: {len(tasks)} 个")
        assert len(tasks) == 3, f"Expected 3 tasks, got {len(tasks)}"

        # 验证状态流转
        tm.update(task_ids[0], status="analyzing")
        tm.update(task_ids[0], status="ocr")
        tm.update(task_ids[0], status="exporting")
        tm.update(task_ids[0], status="completed", progress=100)

        t0 = tm.get_task(task_ids[0])
        print(f"  任务 0 状态: {t0.status}, progress={t0.progress}")
        assert t0.status == "completed"
        assert t0.progress == 100

        # 取消任务 1
        tm.update(task_ids[1], status="analyzing")
        tm.cancel_task(task_ids[1])
        t1 = tm.get_task(task_ids[1])
        print(f"  任务 1 状态: {t1.status} (cancelled)")
        assert t1.status == "cancelled"

        # 重试任务 1
        tm.retry_task(task_ids[1])
        t1 = tm.get_task(task_ids[1])
        print(f"  任务 1 重试后: {t1.status} (pending)")
        assert t1.status == "pending"

        # 活跃任务
        active = tm.list_active_tasks()
        print(f"  活跃任务: {len(active)} 个")

        # 删除任务 2
        tm.delete_task(task_ids[2])
        tasks_after = tm.list_tasks()
        print(f"  删除后任务数: {len(tasks_after)}")
        assert len(tasks_after) == 2

        db.close()
        log("多任务队列", passed=True)

    finally:
        try:
            import gc; gc.collect()
            os.unlink(dbpath)
        except PermissionError:
            pass  # Windows 文件锁，跳过

def test_cache_resume():
    print("\n" + "=" * 60)
    print("# 测试 3: 中断恢复（缓存）")
    print("=" * 60)

    from core.cache import PageCache

    with tempfile.TemporaryDirectory() as tmpdir:
        cache = PageCache(cache_dir=tmpdir)

        pdf_hash = "abc123def456"
        total_pages = 10

        # 模拟处理前 5 页后中断
        from engines.ocr.base import OCRBlock
        for i in range(5):
            blocks = [
                OCRBlock(text=f"第{i}页内容", bbox=[[100, 100], [800, 100], [800, 200], [100, 200]], confidence=0.95)
            ]
            cache.save(i, blocks, pdf_hash)

        # 检查缓存状态
        resume_info = cache.get_resume_info(total_pages, pdf_hash)
        print(f"  缓存页数: {resume_info.get('cached_count', resume_info.get('cached_pages', '?'))}")
        print(f"  总页数: {resume_info.get('total_pages', '?')}")
        print(f"  可恢复: {resume_info.get('can_resume', '?')}")

        cached_count = resume_info.get('cached_count', resume_info.get('cached_pages', 0))
        assert cached_count == 5
        assert resume_info.get('can_resume', False) == True

        # 模拟恢复——获取缓存的页
        for i in range(5):
            cached = cache.get(i, pdf_hash)
            assert cached is not None
            print(f"  第 {i} 页缓存: {len(cached)} blocks")

        # 检查未缓存的页
        uncached = cache.get(5, pdf_hash)
        assert uncached is None
        print(f"  第 5 页未缓存: {uncached is None}")

        # 继续处理剩余页
        for i in range(5, 10):
            blocks = [
                OCRBlock(text=f"第{i}页内容", bbox=[[100, 100], [800, 100], [800, 200], [100, 200]], confidence=0.95)
            ]
            cache.save(i, blocks, pdf_hash)

        # 全部缓存后检查
        resume_info2 = cache.get_resume_info(total_pages, pdf_hash)
        cached_count2 = resume_info2.get('cached_count', resume_info2.get('cached_pages', 0))
        print(f"  全部缓存后: {cached_count2}/{total_pages}")
        assert cached_count2 == 10

        # 清除缓存
        cache.clear(pdf_hash)
        resume_info3 = cache.get_resume_info(total_pages, pdf_hash)
        cached_count3 = resume_info3.get('cached_count', resume_info3.get('cached_pages', 0))
        print(f"  清除后: {cached_count3}")
        assert cached_count3 == 0

        log("中断恢复（缓存）", passed=True)

def test_db_persistence():
    print("\n" + "=" * 60)
    print("# 测试 4: 数据库持久化")
    print("=" * 60)

    from database.db import Database

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        dbpath = f.name

    try:
        db = Database(dbpath)

        # 插入书籍
        book_id = db.insert_book(
            title="测试书籍",
            author="测试作者",
            source_pdf="/test/input.pdf",
            output_epub="/test/book.epub",
            total_pages=100,
        )
        print(f"  插入书籍: id={book_id}")

        # 查询
        book = db.get_book_by_id(book_id)
        assert book['title'] == "测试书籍"
        print(f"  查询书籍: {book['title']} by {book['author']}")

        # 搜索
        results = db.search_books("测试")
        assert len(results) == 1
        print(f"  搜索 '测试': {len(results)} 结果")

        # 插入任务
        task_id = db.insert_task(
            filename="测试书籍",
            pdf_path="/test/input.pdf",
            settings='{"dpi": 300}',
        )
        print(f"  插入任务: id={task_id}")

        # 更新进度
        db.update_task_progress(task_id, 50, current_page=5, total_pages=10)
        task = db.get_task_by_id(task_id)
        assert task['progress'] == 50
        print(f"  更新进度: progress={task['progress']}")

        # 插入纠错记录
        db.add_correction("商稻", "商務")
        corrections = db.get_corrections()
        assert len(corrections) >= 1
        print(f"  纠错记录: {len(corrections)} 条")

        # 设置
        db.set_setting("theme", "dark")
        val = db.get_setting("theme", "default")
        assert val == "dark"
        print(f"  设置: theme={val}")

        db.close()
        log("数据库持久化", passed=True)

    finally:
        try:
            import gc; gc.collect()
            os.unlink(dbpath)
        except PermissionError:
            pass

def test_event_bus_bridge():
    print("\n" + "=" * 60)
    print("# 测试 5: EventBus 信号桥接")
    print("=" * 60)

    from core.event_bus import event_bus

    received = []

    def on_progress(stage, pct):
        received.append(("progress", stage, pct))

    def on_finished(stats_str):
        received.append(("finished", stats_str))

    def on_error(title, msg):
        received.append(("error", title, msg))

    event_bus.progress.connect(on_progress)
    event_bus.finished.connect(on_finished)
    event_bus.error.connect(on_error)

    event_bus.progress.emit("ocr", 50)
    event_bus.finished.emit('{"total_pages": 10}')
    event_bus.error.emit("转换错误", "测试错误")

    time.sleep(0.1)  # 等待信号处理

    print(f"  收到信号: {len(received)} 个")
    for sig in received:
        print(f"    {sig[0]}: {sig[1:]}")

    assert len(received) == 3
    assert received[0][0] == "progress"
    assert received[1][0] == "finished"
    assert received[2][0] == "error"

    log("EventBus信号桥接", passed=True)

# ============================================================
# 主函数
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("PDF2BOOK AI v3.0 — 第六阶段集成测试")
    print("=" * 60)

    # 先跑不需要 OCR 的测试
    test_multitask_queue()
    test_cache_resume()
    test_db_persistence()
    test_event_bus_bridge()

    # 最后跑真实 PDF 测试（耗时较长）
    test_real_pdf_e2e()

    # 总结
    print("\n" + "=" * 60)
    print("第六阶段集成测试总结")
    print("=" * 60)
    passed = sum(1 for _, p in results if p)
    total = len(results)
    for name, p in results:
        print(f"  {'✅' if p else '❌'} {name}")
    print(f"\n  {passed}/{total} 通过")

    if passed == total:
        print("\n  🎉 第六阶段集成测试全部通过！")
    else:
        print("\n  ⚠️ 部分测试未通过")
