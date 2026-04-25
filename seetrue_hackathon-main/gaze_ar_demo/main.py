# main.py — Gaze-triggered real-time AR visual assistant demo
#
# Mouse position simulates eye gaze.
# Stable hover for DWELL_TIME seconds triggers an async AI analysis.
# All AI work runs in a background thread; the main loop is never blocked.

from __future__ import annotations

import queue
import sys
import threading
import time
import uuid

import cv2

import config
from ai.ai_worker import AIWorker
from ai.ericai_client import EricAIClient
from interaction.dwell_detector import DwellDetector
from interaction.popup_manager import PopupManager
from interaction.roi_extractor import ROIExtractor
from interaction.schemas import AIAnalysisRequest, AIAnalysisResult
from interaction.states import AppState


# ---------------------------------------------------------------------------
# Mouse callback — runs in the main thread, just stores coordinates
# ---------------------------------------------------------------------------
_mouse_pos: tuple[int, int] | None = None


def _on_mouse(event: int, x: int, y: int, flags: int, param: object) -> None:
    global _mouse_pos
    _mouse_pos = (x, y)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    global _mouse_pos

    # --- Camera ---
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(
            f"[ERROR] Cannot open camera index {config.CAMERA_INDEX}. "
            "Check CAMERA_INDEX in config.py or connect a webcam.",
            file=sys.stderr,
        )
        sys.exit(1)

    # --- Window & mouse callback ---
    cv2.namedWindow(config.WINDOW_NAME)
    cv2.setMouseCallback(config.WINDOW_NAME, _on_mouse)

    # --- Modules ---
    dwell = DwellDetector(config.DWELL_TIME, config.MOVE_THRESHOLD)
    extractor = ROIExtractor(config.ROI_SIZE)
    popup = PopupManager()

    # --- Queues & worker ---
    request_queue: queue.Queue[AIAnalysisRequest] = queue.Queue(
        maxsize=config.MAX_PENDING_REQUESTS
    )
    response_queue: queue.Queue[AIAnalysisResult] = queue.Queue()
    stop_event = threading.Event()
    worker = AIWorker(request_queue, response_queue, stop_event, EricAIClient())
    worker.start()

    # --- State machine variables ---
    state = AppState.IDLE
    dwell_progress: float = 0.0
    current_request_id: str | None = None
    current_result: AIAnalysisResult | None = None
    result_start_time: float = 0.0
    cooldown_start_time: float = 0.0

    print(f"[INFO] Running — move mouse over '{config.WINDOW_NAME}' window.")
    print("[INFO] Press ESC or Q to quit.")

    try:
        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                # Camera hiccup — skip frame, keep loop alive
                if cv2.waitKey(1) & 0xFF in (27, ord("q")):
                    break
                continue

            now = time.monotonic()
            gaze_pos: tuple[int, int] = _mouse_pos if _mouse_pos is not None else (
                frame.shape[1] // 2, frame.shape[0] // 2
            )
            gx, gy = gaze_pos

            # ----------------------------------------------------------------
            # State machine
            # ----------------------------------------------------------------
            if state == AppState.IDLE:
                triggered, dwell_progress = dwell.update(gx, gy, now)
                if dwell_progress > 0.0:
                    state = AppState.DWELLING

            elif state == AppState.DWELLING:
                triggered, dwell_progress = dwell.update(gx, gy, now)

                if dwell_progress < 0.05 and not triggered:
                    # Gaze moved away — detector reset internally, go back to IDLE
                    state = AppState.IDLE

                elif triggered:
                    # --- Build and dispatch AI request ---
                    try:
                        crop, bbox = extractor.extract(frame, gx, gy)
                        jpeg_bytes = extractor.encode_jpeg(crop)
                    except ValueError as exc:
                        print(f"[WARN] ROI encode failed: {exc}")
                        dwell.reset()
                        state = AppState.IDLE
                    else:
                        req_id = str(uuid.uuid4())
                        request = AIAnalysisRequest(
                            request_id=req_id,
                            timestamp=now,
                            gaze_x=gx,
                            gaze_y=gy,
                            frame_width=frame.shape[1],
                            frame_height=frame.shape[0],
                            crop_jpeg_bytes=jpeg_bytes,
                            crop_bbox=bbox,
                            prompt="Identify this object and describe its function.",
                        )
                        try:
                            request_queue.put_nowait(request)
                            current_request_id = req_id
                            state = AppState.ANALYZING
                        except queue.Full:
                            print("[WARN] request_queue full — skipping trigger")
                            state = AppState.ANALYZING  # still wait for in-flight result
                        dwell.reset()

            elif state == AppState.ANALYZING:
                # Non-blocking poll for result
                try:
                    result = response_queue.get_nowait()
                    if result.request_id == current_request_id:
                        current_result = result
                        result_start_time = now
                        state = AppState.SHOW_RESULT
                    # else: stale result from a previous request — discard silently
                except queue.Empty:
                    pass  # still waiting

            elif state == AppState.SHOW_RESULT:
                if now - result_start_time > config.POPUP_VISIBLE_TIME:
                    cooldown_start_time = now
                    state = AppState.COOLDOWN

            elif state == AppState.COOLDOWN:
                if now - cooldown_start_time > config.COOLDOWN_TIME:
                    current_result = None
                    current_request_id = None
                    dwell_progress = 0.0
                    dwell.reset()
                    state = AppState.IDLE

            # ----------------------------------------------------------------
            # Render
            # ----------------------------------------------------------------
            display = popup.draw(frame, state, gaze_pos, dwell_progress, current_result, now)
            cv2.imshow(config.WINDOW_NAME, display)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break

    finally:
        stop_event.set()
        worker.join(timeout=3.0)
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Shutdown complete.")


if __name__ == "__main__":
    main()
