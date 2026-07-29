from threading import Thread, Event
from typing import Callable, Optional


class BackgroundWorker:
    """
    Runs a blocking task in a daemon thread and returns results using callbacks.

    Supports cancellation via stop() method. The task callable should periodically
    check is_cancelled() to exit gracefully.

    Tkinter UI updates should still be scheduled with root.after(...)
    from the callback caller.
    """

    def __init__(
        self,
        task: Callable,
        on_success: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_finally: Optional[Callable] = None,
    ):
        self.task = task
        self.on_success = on_success
        self.on_error = on_error
        self.on_finally = on_finally
        self._cancel_event = Event()
        self.thread: Optional[Thread] = None

    def start(self):
        self._cancel_event.clear()
        self.thread = Thread(target=self._run, daemon=True)
        self.thread.start()

    def is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancel_event.is_set()

    def stop(self):
        """Request cancellation of the task."""
        self._cancel_event.set()

    def _run(self):
        try:
            result = self.task()
            if self.on_success and not self.is_cancelled():
                self.on_success(result)

        except Exception as exc:
            if self.on_error and not self.is_cancelled():
                self.on_error(exc)

        finally:
            if self.on_finally:
                self.on_finally()