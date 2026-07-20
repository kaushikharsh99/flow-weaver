from typing import Optional, Callable


class ProgressTracker:
    """Helper utility for tracking and reporting operation progress."""
    def __init__(self, total: Optional[int] = None, callback: Optional[Callable[[int, Optional[int]], None]] = None):
        self.total = total
        self.processed = 0
        self.callback = callback

    def update(self, count: int = 1):
        self.processed += count
        if self.callback:
            self.callback(self.processed, self.total)
