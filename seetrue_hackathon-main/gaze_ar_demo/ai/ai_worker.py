# ai/ai_worker.py — Background thread that processes AI analysis requests

from __future__ import annotations

import queue
import threading

from typing import Protocol

from interaction.schemas import AIAnalysisRequest, AIAnalysisResult


class AIClient(Protocol):
    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResult: ...


class AIWorker(threading.Thread):
    """Consumes AIAnalysisRequest items and produces AIAnalysisResult items.

    Runs entirely in its own thread; never touches OpenCV GUI functions.
    """

    def __init__(
        self,
        request_queue: queue.Queue[AIAnalysisRequest],
        response_queue: queue.Queue[AIAnalysisResult],
        stop_event: threading.Event,
        client: AIClient,
    ) -> None:
        super().__init__(name="AIWorker", daemon=True)
        self._req_q = request_queue
        self._res_q = response_queue
        self._stop = stop_event
        self._client = client

    def run(self) -> None:
        while not self._stop.is_set():
            try:
                request: AIAnalysisRequest = self._req_q.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                result = self._client.analyze(request)
            except Exception as exc:  # noqa: BLE001
                result = AIAnalysisResult(
                    request_id=request.request_id,
                    object_name="",
                    function="",
                    confidence=0.0,
                    short_description="",
                    error=f"AI error: {exc}",
                )

            self._res_q.put(result)
