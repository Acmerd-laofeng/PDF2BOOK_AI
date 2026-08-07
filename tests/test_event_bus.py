# -*- coding: utf-8 -*-
"""EventBus 单元测试"""
import pytest
from PySide6.QtWidgets import QApplication
from core.event_bus import EventBus


@pytest.fixture(scope="module")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app


@pytest.fixture
def bus(qapp):
    return EventBus()


class TestEventBus:

    def test_progress_signal(self, bus, qapp):
        received = []
        bus.progress.connect(lambda fn, pct: received.append((fn, pct)))
        bus.progress.emit("test.pdf", 50)
        qapp.processEvents()
        assert received == [("test.pdf", 50)]

    def test_finished_signal(self, bus, qapp):
        received = []
        bus.finished.connect(lambda fn: received.append(fn))
        bus.finished.emit("done.pdf")
        qapp.processEvents()
        assert received == ["done.pdf"]

    def test_error_signal(self, bus, qapp):
        received = []
        bus.error.connect(lambda fn, msg: received.append((fn, msg)))
        bus.error.emit("bad.pdf", "OCR failed")
        qapp.processEvents()
        assert received == [("bad.pdf", "OCR failed")]

    def test_analysis_done_signal(self, bus, qapp):
        received = []
        bus.analysis_done.connect(lambda d: received.append(d))
        bus.analysis_done.emit({"pages": 10, "type": "text"})
        qapp.processEvents()
        assert received[0]["pages"] == 10

    def test_task_signals(self, bus, qapp):
        added = []
        removed = []
        status = []
        progress = []
        bus.task_added.connect(lambda tid: added.append(tid))
        bus.task_removed.connect(lambda tid: removed.append(tid))
        bus.task_status_changed.connect(lambda tid, s: status.append((tid, s)))
        bus.task_progress.connect(lambda tid, pct: progress.append((tid, pct)))

        bus.task_added.emit(1)
        bus.task_progress.emit(1, 30)
        bus.task_status_changed.emit(1, "ocr")
        bus.task_removed.emit(1)
        qapp.processEvents()

        assert added == [1]
        assert progress == [(1, 30)]
        assert status == [(1, "ocr")]
        assert removed == [1]

    def test_book_signals(self, bus, qapp):
        added = []
        removed = []
        bus.book_added.connect(lambda bid: added.append(bid))
        bus.book_removed.connect(lambda bid: removed.append(bid))
        bus.book_added.emit(1)
        bus.book_removed.emit(1)
        qapp.processEvents()
        assert added == [1]
        assert removed == [1]

    def test_correction_learned_signal(self, bus, qapp):
        received = []
        bus.correction_learned.connect(lambda w, c: received.append((w, c)))
        bus.correction_learned.emit("错词", "对词")
        qapp.processEvents()
        assert received == [("错词", "对词")]

    def test_log_message_signal(self, bus, qapp):
        received = []
        bus.log_message.connect(lambda msg: received.append(msg))
        bus.log_message.emit("test log")
        qapp.processEvents()
        assert received == ["test log"]

    def test_report_ready_signal(self, bus, qapp):
        received = []
        bus.report_ready.connect(lambda r: received.append(r))
        bus.report_ready.emit({"chapters": 5, "total_chars": 1000})
        qapp.processEvents()
        assert received[0]["chapters"] == 5

    def test_global_singleton(self):
        from core.event_bus import event_bus
        assert isinstance(event_bus, EventBus)
