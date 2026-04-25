# config.py — Central configuration for Gaze AR Demo

DWELL_TIME: float = 1.5          # seconds before triggering analysis
MOVE_THRESHOLD: int = 35         # pixels; movement beyond this resets dwell
COOLDOWN_TIME: float = 3.0       # seconds to wait after result is dismissed
ROI_SIZE: int = 320              # pixels; square crop side length
POPUP_VISIBLE_TIME: float = 5.0  # seconds to display the result popup
MAX_PENDING_REQUESTS: int = 1    # max items in request_queue
CAMERA_INDEX: int = 0            # cv2.VideoCapture index
WINDOW_NAME: str = "Gaze AR Demo"
