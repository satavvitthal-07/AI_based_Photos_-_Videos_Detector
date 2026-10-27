from flask import Blueprint, jsonify

from backend.ai.model_adapter import detector_status

health = Blueprint("health", __name__, url_prefix="/api")


@health.get("/health")
def get_health():
    return jsonify({"status": "ok", "detector": detector_status()})
