"""把耗时操作放到 QThreadPool；回调一定在 GUI 线程里执行。"""

import itertools

from PyQt5.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal, pyqtSlot


class _Signals(QObject):
    done = pyqtSignal(int, object)
    failed = pyqtSignal(int, object)


class _Task(QRunnable):
    def __init__(self, task_id, fn, args, signals):
        super().__init__()
        self.setAutoDelete(False)  # 生命周期由 TaskRunner._pending 管理
        self._id, self._fn, self._args, self._signals = task_id, fn, args, signals

    def run(self):
        try:
            result = self._fn(*self._args)
        except Exception as exc:  # noqa: BLE001 - 交给界面层统一展示
            self._signals.failed.emit(self._id, exc)
        else:
            self._signals.done.emit(self._id, result)


class TaskRunner(QObject):
    def __init__(self, parent):
        super().__init__(parent)
        self._signals = _Signals(self)
        self._signals.done.connect(self._on_done)
        self._signals.failed.connect(self._on_failed)
        self._ids = itertools.count(1)
        self._pending = {}

    def run(self, fn, *args, on_success, on_error, busy=(), busy_text="处理中…"):
        """busy 中的按钮在运行期间禁用，第一个按钮显示 busy_text。"""
        saved = [(button, button.text()) for button in busy]
        for button in busy:
            button.setEnabled(False)
        if busy:
            busy[0].setText(busy_text)
        task_id = next(self._ids)
        task = _Task(task_id, fn, args, self._signals)
        self._pending[task_id] = (task, saved, on_success, on_error)
        QThreadPool.globalInstance().start(task)

    def _finish(self, task_id):
        _, saved, on_success, on_error = self._pending.pop(task_id)
        for button, text in saved:
            button.setText(text)
            button.setEnabled(True)
        return on_success, on_error

    @pyqtSlot(int, object)
    def _on_done(self, task_id, result):
        on_success, _ = self._finish(task_id)
        on_success(result)

    @pyqtSlot(int, object)
    def _on_failed(self, task_id, exc):
        _, on_error = self._finish(task_id)
        on_error(exc)
