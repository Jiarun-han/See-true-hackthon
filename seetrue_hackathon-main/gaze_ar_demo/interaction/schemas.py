# interaction/schemas.py — Typed data contracts between modules

from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class AIAnalysisRequest:
    request_id: str
    timestamp: float
    gaze_x: int
    gaze_y: int
    frame_width: int
    frame_height: int
    crop_jpeg_bytes: bytes
    crop_bbox: tuple[int, int, int, int]   # (x1, y1, x2, y2)
    prompt: str


@dataclass
class AIAnalysisResult:
    request_id: str
    object_name: str
    function: str
    confidence: float
    short_description: str
    error: str | None = None
