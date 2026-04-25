# interaction/states.py — Application state machine enum

from enum import Enum, auto


class AppState(Enum):
    IDLE = auto()         # waiting for dwell to begin
    DWELLING = auto()     # gaze is stable, accumulating dwell time
    ANALYZING = auto()    # AI request in flight
    SHOW_RESULT = auto()  # displaying AI result popup
    COOLDOWN = auto()     # brief pause before accepting new triggers
