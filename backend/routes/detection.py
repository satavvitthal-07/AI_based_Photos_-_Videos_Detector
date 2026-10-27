from pathlib import Path
from time import perf_counter

from flask import Blueprint, current_app, jsonify

from backend.database.repository import create_analysis
from backend.services.image_service import analyze_image
from backend.services.video_service import analyze_video
from backend.utils.errors import ApiError, DetectorUnavailable
from backend.utils.security import safe_display_name
from backend.utils.validation import save_uploaded_file

detection = Blueprint("detection", __name__, url_prefix="/api/detect")


def _process(media_type: str):
    started = perf_counter()
    temp_path: Path | None = None
    try:
        temp_path, file_size, original_name, expected_mime = save_uploaded_file(media_type)
        display_name = safe_display_name(original_name)
        result = (
            analyze_image(temp_path, expected_mime)
            if media_type == "image"
            else analyze_video(temp_path)
        )
        processing_ms = max(0, round((perf_counter() - started) * 1000))
        record = create_analysis(
            display_name=display_name,
            media_type=media_type,
            file_size=file_size,
            model_id=result["model_id"],
            model_revision=result.get("model_revision"),
            top_label=result.get("top_label"),
            scores=result.get("scores"),
            prediction=result["prediction"],
            score=result["score"],
            status="completed",
            processing_ms=processing_ms,
            frames=result.get("frames"),
        )
        record.update(
            {
                key: value
                for key, value in result.items()
                if key not in {"prediction", "score", "model_id", "frames", "status", "scores"}
            }
        )
        return jsonify(record), 200
    except DetectorUnavailable as error:
        processing_ms = max(0, round((perf_counter() - started) * 1000))
        record = create_analysis(
            display_name=safe_display_name(original_name),
            media_type=media_type,
            file_size=file_size,
            model_id=current_app.config["MODEL_ID"] or None,
            model_revision=current_app.config["MODEL_REVISION"],
            top_label=None,
            scores=None,
            prediction="Detection unavailable",
            score=None,
            status="unavailable",
            processing_ms=processing_ms,
            error_message=str(error),
        )
        response = {
            **record,
            "error": {"code": "detector_unavailable", "message": str(error)},
        }
        return jsonify(response), 503
    except ApiError as error:
        return jsonify({"error": {"code": error.code, "message": error.message}}), error.status_code
    except Exception:
        current_app.logger.exception("Unexpected error while processing uploaded %s", media_type)
        if temp_path is not None and "file_size" in locals() and "display_name" in locals():
            processing_ms = max(0, round((perf_counter() - started) * 1000))
            record = create_analysis(
                display_name=display_name,
                media_type=media_type,
                file_size=file_size,
                model_id=None,
                model_revision=None,
                top_label=None,
                scores=None,
                prediction="Analysis failed",
                score=None,
                status="failed",
                processing_ms=processing_ms,
                error_message="Media processing failed unexpectedly. Check the backend log and retry.",
            )
            return jsonify(
                {
                    **record,
                    "error": {
                        "code": "processing_failed",
                        "message": "Media processing failed unexpectedly. Check the backend log and retry.",
                    },
                }
            ), 500
        return jsonify({"error": {"code": "processing_failed", "message": "Media processing failed unexpectedly."}}), 500
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


@detection.post("/image")
def detect_image():
    return _process("image")


@detection.post("/video")
def detect_video():
    return _process("video")
