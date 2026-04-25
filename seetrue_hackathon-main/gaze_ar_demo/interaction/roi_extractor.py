# interaction/roi_extractor.py — Image region-of-interest cropping

import cv2
import numpy as np


class ROIExtractor:
    """Crops a square ROI centred on the gaze point and encodes it as JPEG."""

    def __init__(self, roi_size: int) -> None:
        self._half = roi_size // 2

    def extract(
        self, frame: np.ndarray, x: int, y: int
    ) -> tuple[np.ndarray, tuple[int, int, int, int]]:
        """Return (crop, bbox) where bbox = (x1, y1, x2, y2), clamped to frame."""
        h, w = frame.shape[:2]
        x1 = max(0, x - self._half)
        y1 = max(0, y - self._half)
        x2 = min(w, x + self._half)
        y2 = min(h, y + self._half)
        crop = frame[y1:y2, x1:x2]
        return crop, (x1, y1, x2, y2)

    def encode_jpeg(self, crop: np.ndarray) -> bytes:
        """Encode crop to JPEG bytes; raises ValueError on failure."""
        ok, buf = cv2.imencode(".jpg", crop)
        if not ok or buf is None:
            raise ValueError("cv2.imencode failed — cannot encode ROI to JPEG")
        return buf.tobytes()
