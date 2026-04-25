# interaction/dwell_detector.py — Gaze dwell stability detector

import math


class DwellDetector:
    """Detects when a gaze point has been stable for `dwell_time` seconds.

    Caller must pass `now = time.monotonic()` on every update; this class
    never calls time functions internally so it is trivially testable.
    """

    def __init__(self, dwell_time: float, move_threshold: int) -> None:
        self._dwell_time = dwell_time
        self._move_threshold = move_threshold
        self._anchor_x: int | None = None
        self._anchor_y: int | None = None
        self._start_time: float | None = None

    # ------------------------------------------------------------------
    def update(self, x: int, y: int, now: float) -> tuple[bool, float]:
        """Return (triggered, progress).

        triggered — True once elapsed >= dwell_time (fires once per dwell).
        progress  — 0.0 … 1.0 fraction of dwell_time elapsed.
        """
        if self._anchor_x is None:
            self._anchor_x, self._anchor_y, self._start_time = x, y, now
            return False, 0.0

        dist = math.hypot(x - self._anchor_x, y - self._anchor_y)  # type: ignore[arg-type]
        if dist > self._move_threshold:
            # Gaze moved — reset anchor to current position
            self._anchor_x, self._anchor_y, self._start_time = x, y, now
            return False, 0.0

        elapsed = now - self._start_time  # type: ignore[operator]
        progress = min(elapsed / self._dwell_time, 1.0)
        triggered = elapsed >= self._dwell_time
        return triggered, progress

    def reset(self) -> None:
        """Reset detector; call after a trigger has been consumed."""
        self._anchor_x = None
        self._anchor_y = None
        self._start_time = None
