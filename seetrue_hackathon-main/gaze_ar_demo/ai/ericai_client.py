# ai/ericai_client.py — Multimodal AI client using Qwen3.6 on EricAI
#
# Qwen3.6-35B-A3B-FP8 is tagged "multimodal" on the EricAI cluster and uses
# early-fusion vision-language training, so it accepts images via the standard
# OpenAI vision message format (content list with image_url items).
# Auth is handled automatically by EricAI SSO — no API key needed.

from __future__ import annotations

import base64
import json
import os
import re
import sys

from dotenv import load_dotenv

from interaction.schemas import AIAnalysisRequest, AIAnalysisResult

load_dotenv()

_MODEL = os.getenv("ERICAI_MODEL_ID", "Qwen/Qwen3.6-35B-A3B-FP8")
_TIMEOUT = int(os.getenv("LLM_TIMEOUT_SECS", "180"))

_SYSTEM = (
    "You are a visual assistant. Analyse the image provided by the user. "
    "Respond ONLY with a single valid JSON object — no markdown, no extra text. "
    'Keys: "object_name" (str), "function" (str, one sentence), '
    '"confidence" (float 0-1), "short_description" (str, one sentence).'
)


def _get_client():
    from ericai import EricAI  # type: ignore[import]
    kwargs: dict = {"timeout": _TIMEOUT}
    if os.getenv("ERICAI_API_KEY"):
        kwargs["api_key"] = os.getenv("ERICAI_API_KEY")
    if os.getenv("ERICAI_API_BASE"):
        kwargs["base_url"] = os.getenv("ERICAI_API_BASE")
    return EricAI(**kwargs)


def _strip(text: str) -> str:
    text = text.strip()
    if "```" in text:
        m = re.search(r"```(?:json)?\s*([\s\S]*?)```", text)
        if m:
            return m.group(1).strip()
    for s, e in (("{", "}"), ("[", "]")):
        si, ei = text.find(s), text.rfind(e)
        if si != -1 and ei > si:
            return text[si : ei + 1]
    return text


def _parse(request_id: str, raw: str) -> AIAnalysisResult:
    if "</think>" in raw:
        raw = raw.split("</think>", 1)[-1].strip()
    try:
        d = json.loads(_strip(raw))
        return AIAnalysisResult(
            request_id=request_id,
            object_name=str(d.get("object_name", "Unknown")),
            function=str(d.get("function", "")),
            confidence=float(d.get("confidence", 0.0)),
            short_description=str(d.get("short_description", "")),
        )
    except Exception as exc:
        return AIAnalysisResult(
            request_id=request_id,
            object_name="Parse error",
            function="", confidence=0.0, short_description="",
            error=f"JSON parse failed: {exc} | raw={raw[:120]}",
        )


class EricAIClient:
    """Sends the ROI crop to Qwen3.6 (multimodal) via OpenAI vision message format."""

    def __init__(self) -> None:
        self._client = _get_client()

    def analyze(self, request: AIAnalysisRequest) -> AIAnalysisResult:
        b64 = base64.b64encode(request.crop_jpeg_bytes).decode()
        data_uri = f"data:image/jpeg;base64,{b64}"

        try:
            resp = self._client.chat.completions.create(
                model=_MODEL,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": data_uri}},
                            {"type": "text", "text": request.prompt},
                        ],
                    },
                ],
                max_tokens=200,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
                stream=False,
            )
            raw = resp.choices[0].message.content or ""
            if os.getenv("LLM_DEBUG", "").lower() in ("1", "true"):
                print(f"[EricAIClient] raw: {raw[:300]}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            return AIAnalysisResult(
                request_id=request.request_id,
                object_name="", function="", confidence=0.0, short_description="",
                error=f"EricAI API error: {exc}",
            )

        return _parse(request.request_id, raw)
