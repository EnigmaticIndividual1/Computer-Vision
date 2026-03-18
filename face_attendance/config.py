from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
REPORTS_DIR = DATA_DIR / "reports"
CAPTURES_DIR = DATA_DIR / "captures"
ATTENDANCE_CSV = REPORTS_DIR / "attendance_log.csv"

SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_MODEL_NAME = "Facenet512"
DEFAULT_DETECTOR = "opencv"
DEFAULT_DISTANCE_METRIC = "cosine"
