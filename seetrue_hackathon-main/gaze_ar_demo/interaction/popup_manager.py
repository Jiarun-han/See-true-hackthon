# interaction/popup_manager.py — Modern UI renderer using Pillow + OpenCV

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from interaction.schemas import AIAnalysisResult
from interaction.states import AppState

# ── Fonts ──────────────────────────────────────────────────────────────────
_FONT_DIR = "C:/Windows/Fonts/"
try:
    _F_TITLE  = ImageFont.truetype(_FONT_DIR + "bahnschrift.ttf", 16)
    _F_LABEL  = ImageFont.truetype(_FONT_DIR + "bahnschrift.ttf", 11)
    _F_VALUE  = ImageFont.truetype(_FONT_DIR + "calibri.ttf",     13)
    _F_BADGE  = ImageFont.truetype(_FONT_DIR + "bahnschrift.ttf", 13)
    _F_PCT    = ImageFont.truetype(_FONT_DIR + "bahnschrift.ttf", 11)
except OSError:
    _F_TITLE = _F_LABEL = _F_VALUE = _F_BADGE = _F_PCT = ImageFont.load_default()

# ── Palette (RGBA) ─────────────────────────────────────────────────────────
_BG          = (12,  14,  20,  210)   # deep navy, semi-transparent
_BORDER      = (90, 160, 255,  180)   # soft blue border
_ACCENT      = (60, 130, 255,  255)   # blue accent bar
_TITLE_C     = (255, 255, 255,  255)  # white title
_LABEL_C     = (160, 185, 230,  255)  # bright blue-grey label
_VALUE_C     = (240, 242, 248,  255)  # bright white value text
_BAR_BG      = (35,  40,  55,  255)   # bar track
_BAR_FG      = (60, 200, 120,  255)   # green fill
_BAR_FG_MID  = (220, 180,  40,  255)  # yellow fill (mid confidence)
_BAR_FG_LOW  = (200,  70,  70,  255)  # red fill (low confidence)
_ANALYZING_C = (40, 160, 255,  255)
_DWELL_C     = (220, 180,  50,  255)
_ERROR_C     = (220,  80,  80,  255)
_DIVIDER     = (40,  50,  70,  255)

# ── Layout ─────────────────────────────────────────────────────────────────
_PAD      = 14
_BOX_W    = 300
_RADIUS   = 12
_MAX_W    = _BOX_W - _PAD * 2 - 6   # text wrap width in pixels


def _cv2pil(frame: np.ndarray) -> Image.Image:
    return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA))


def _pil2cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGBA2BGR)


def _rounded_rect(draw: ImageDraw.ImageDraw, xy: tuple, radius: int,
                  fill: tuple, outline: tuple | None = None, width: int = 1) -> None:
    x1, y1, x2, y2 = xy
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill,
                            outline=outline, width=width)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont,
               max_w: int) -> list[str]:
    """Word-wrap text to fit within max_w pixels."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    for word in words:
        test = (cur + " " + word).strip()
        w = d.textlength(test, font=font)
        if w <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines or [""]


def _text_block_h(lines: list[str], font: ImageFont.FreeTypeFont,
                  line_gap: int = 4) -> int:
    dummy = Image.new("RGBA", (1, 1))
    d = ImageDraw.Draw(dummy)
    _, _, _, h = d.textbbox((0, 0), "Ag", font=font)
    return len(lines) * (h + line_gap)


def _draw_lines(draw: ImageDraw.ImageDraw, lines: list[str],
                font: ImageFont.FreeTypeFont, x: int, y: int,
                color: tuple, line_gap: int = 4) -> int:
    """Draw wrapped lines, return final y."""
    dummy_d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    _, _, _, lh = dummy_d.textbbox((0, 0), "Ag", font=font)
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += lh + line_gap
    return y


def _conf_color(conf: float) -> tuple:
    if conf >= 0.7:
        return _BAR_FG
    if conf >= 0.4:
        return _BAR_FG_MID
    return _BAR_FG_LOW


# ── OpenCV helpers (cursor, no Pillow needed) ──────────────────────────────
def _draw_cursor_cv(img: np.ndarray, gx: int, gy: int,
                    state: AppState, progress: float) -> None:
    color_map = {
        AppState.IDLE:        (200, 200, 200),
        AppState.DWELLING:    (50,  180, 220),
        AppState.ANALYZING:   (40,  160, 255),
        AppState.SHOW_RESULT: (60,  200, 120),
        AppState.COOLDOWN:    (160, 160, 160),
    }
    c = color_map.get(state, (200, 200, 200))

    cv2.circle(img, (gx, gy), 18, c, 1, cv2.LINE_AA)
    cv2.circle(img, (gx, gy), 3,  c, -1, cv2.LINE_AA)
    for dx, dy in [(-28, 0), (28, 0), (0, -28), (0, 28)]:
        sx = gx + (dx // abs(dx) * 22 if dx != 0 else 0)
        sy = gy + (dy // abs(dy) * 22 if dy != 0 else 0)
        cv2.line(img, (sx, sy), (gx + dx, gy + dy), c, 1, cv2.LINE_AA)

    if state == AppState.DWELLING and progress > 0:
        cv2.ellipse(img, (gx, gy), (18, 18), -90,
                    0, int(360 * progress), (50, 180, 220), 2, cv2.LINE_AA)
        pct = f"{int(progress * 100)}%"
        cv2.putText(img, pct, (gx + 24, gy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42, (50, 180, 220), 1, cv2.LINE_AA)


# ── PopupManager ───────────────────────────────────────────────────────────
class PopupManager:
    """Renders modern bubble UI via Pillow; cursor via OpenCV."""

    def draw(
        self,
        frame: np.ndarray,
        state: AppState,
        gaze_pos: tuple[int, int],
        dwell_progress: float,
        result: AIAnalysisResult | None,
        now: float,
    ) -> np.ndarray:
        # Cursor is pure OpenCV (fast, no copy needed)
        _draw_cursor_cv(frame, gaze_pos[0], gaze_pos[1], state, dwell_progress)

        if state == AppState.ANALYZING:
            frame = self._draw_analyzing(frame, gaze_pos)
        elif state == AppState.SHOW_RESULT and result is not None:
            frame = self._draw_result(frame, gaze_pos, result)

        return frame

    # ── Analyzing badge ────────────────────────────────────────────────────
    def _draw_analyzing(self, frame: np.ndarray,
                        gaze_pos: tuple[int, int]) -> np.ndarray:
        h, w = frame.shape[:2]
        gx, gy = gaze_pos
        text = "Analyzing…"

        dummy = Image.new("RGBA", (1, 1))
        tw = int(ImageDraw.Draw(dummy).textlength(text, font=_F_BADGE))
        bw, bh = tw + 24, 32
        bx = min(gx + 30, w - bw - 4)
        by = max(gy - bh - 10, 4)

        pil = _cv2pil(frame)
        overlay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)
        _rounded_rect(d, (bx, by, bx + bw, by + bh), 8,
                      fill=(20, 20, 35, 200),
                      outline=(40, 160, 255, 180), width=1)
        # Pulsing dot
        d.ellipse((bx + 10, by + 11, bx + 20, by + 21),
                  fill=_ANALYZING_C)
        d.text((bx + 24, by + 8), text, font=_F_BADGE, fill=_ANALYZING_C)
        pil = Image.alpha_composite(pil, overlay)
        return _pil2cv(pil)

    # ── Result card ────────────────────────────────────────────────────────
    def _draw_result(self, frame: np.ndarray,
                     gaze_pos: tuple[int, int],
                     result: AIAnalysisResult) -> np.ndarray:
        h, w = frame.shape[:2]
        gx, gy = gaze_pos

        # ── Measure content ──
        title_lines = _wrap_text(result.object_name.upper(), _F_TITLE, _MAX_W)
        func_lines  = _wrap_text(result.function,            _F_VALUE, _MAX_W)
        desc_lines  = _wrap_text(result.short_description,   _F_VALUE, _MAX_W)
        conf        = max(0.0, min(1.0, result.confidence))

        dummy_d = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        def lh(font): return dummy_d.textbbox((0,0),"Ag",font=font)[3] + 4

        title_h = _text_block_h(title_lines, _F_TITLE)
        func_h  = lh(_F_LABEL) + _text_block_h(func_lines, _F_VALUE)
        desc_h  = lh(_F_LABEL) + _text_block_h(desc_lines, _F_VALUE)
        conf_h  = lh(_F_LABEL) + 10 + lh(_F_PCT)   # label + bar + pct
        err_h   = (_text_block_h(_wrap_text(result.error, _F_VALUE, _MAX_W),
                                 _F_VALUE) + 8) if result.error else 0

        gap = 10
        total_h = (_PAD + title_h + gap
                   + 1 + gap               # divider
                   + func_h  + gap
                   + desc_h  + gap
                   + conf_h
                   + (gap + err_h if err_h else 0)
                   + _PAD)

        bw = _BOX_W

        # ── Position ──
        bx = gx + 36
        if bx + bw > w - 4:
            bx = gx - bw - 36
        bx = max(4, min(bx, w - bw - 4))
        by = max(4, min(gy - total_h // 2, h - total_h - 4))

        # ── Render onto Pillow RGBA ──
        pil = _cv2pil(frame)
        overlay = Image.new("RGBA", pil.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(overlay)

        # Card background
        _rounded_rect(d, (bx, by, bx + bw, by + total_h), _RADIUS,
                      fill=_BG, outline=_BORDER, width=1)

        # Left accent bar
        d.rounded_rectangle([bx, by + _RADIUS, bx + 3, by + total_h - _RADIUS],
                             radius=2, fill=_ACCENT)

        cx = bx + _PAD + 4
        cy = by + _PAD

        # Title
        cy = _draw_lines(d, title_lines, _F_TITLE, cx, cy, _TITLE_C)
        cy += gap

        # Divider
        d.line([(cx, cy), (bx + bw - _PAD, cy)], fill=_DIVIDER, width=1)
        cy += 1 + gap

        # Function
        d.text((cx, cy), "FUNCTION", font=_F_LABEL, fill=_LABEL_C)
        cy += lh(_F_LABEL)
        cy = _draw_lines(d, func_lines, _F_VALUE, cx, cy, _VALUE_C)
        cy += gap

        # Description
        d.text((cx, cy), "DESCRIPTION", font=_F_LABEL, fill=_LABEL_C)
        cy += lh(_F_LABEL)
        cy = _draw_lines(d, desc_lines, _F_VALUE, cx, cy, _VALUE_C)
        cy += gap

        # Confidence
        d.text((cx, cy), "CONFIDENCE", font=_F_LABEL, fill=_LABEL_C)
        cy += lh(_F_LABEL)
        bar_x1, bar_y1 = cx, cy
        bar_x2, bar_y2 = bx + bw - _PAD, cy + 8
        d.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2],
                             radius=4, fill=_BAR_BG)
        fill_x = bar_x1 + int((bar_x2 - bar_x1) * conf)
        if fill_x > bar_x1:
            d.rounded_rectangle([bar_x1, bar_y1, fill_x, bar_y2],
                                 radius=4, fill=_conf_color(conf))
        cy = bar_y2 + 4
        d.text((cx, cy), f"{int(conf * 100)}%", font=_F_PCT, fill=_VALUE_C)
        cy += lh(_F_PCT)

        # Error
        if result.error:
            cy += gap
            err_lines = _wrap_text(result.error, _F_VALUE, _MAX_W)
            _draw_lines(d, err_lines, _F_VALUE, cx, cy, _ERROR_C)

        pil = Image.alpha_composite(pil, overlay)
        return _pil2cv(pil)
