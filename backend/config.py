import os
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("TRUTHLENS_SECRET_KEY", "local-development-only")
    DATABASE_PATH = Path(os.getenv("TRUTHLENS_DATABASE", BACKEND_DIR / "truthlens.sqlite3"))
    MAX_CONTENT_LENGTH = 51 * 1024 * 1024
    IMAGE_MAX_BYTES = 10 * 1024 * 1024
    VIDEO_MAX_BYTES = 50 * 1024 * 1024
    IMAGE_MAX_PIXELS = 40_000_000
    IMAGE_MAX_DIMENSION = 12_000
    VIDEO_MAX_SECONDS = 60
    VIDEO_MAX_FRAMES = 8
    VIDEO_MAX_DECODE_FRAMES = 2_000
    VIDEO_SAMPLE_COUNT = 8
    VIDEO_MAX_DIMENSION = 3_840
    MODEL_ID = os.getenv("TRUTHLENS_MODEL_ID", "").strip()
    MODEL_REVISION = os.getenv("TRUTHLENS_MODEL_REVISION", "").strip() or None
    MODEL_VERIFIED = os.getenv("TRUTHLENS_MODEL_VERIFIED", "").strip().lower() == "true"
    AI_LABELS = tuple(
        label.strip()
        for label in os.getenv("TRUTHLENS_AI_LABELS", "").split(",")
        if label.strip()
    )
    CORS_ORIGINS = tuple(
        origin.strip()
        for origin in os.getenv(
            "TRUTHLENS_CORS_ORIGINS",
            "http://127.0.0.1:5000,http://localhost:5000,"
            "http://127.0.0.1:5500,http://localhost:5500,"
            "http://127.0.0.1:8000,http://localhost:8000",
        ).split(",")
        if origin.strip()
    )
