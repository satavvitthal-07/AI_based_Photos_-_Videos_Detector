import sys
from io import BytesIO
from types import SimpleNamespace

from PIL import Image

from backend.ai import model_adapter


def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (4, 3), color=(40, 80, 120)).save(buffer, format="PNG")
    return buffer.getvalue()


def configure_detector(app):
    app.config.update(
        MODEL_ID="Organika/sdxl-detector",
        MODEL_REVISION="b37fede8562cb72b89ec201c0987f96ba21b518a",
        MODEL_VERIFIED=True,
        AI_LABELS=("artificial",),
    )


def test_successful_inference_score_is_returned_and_saved(app, client, monkeypatch):
    configure_detector(app)

    def predict(image, top_k):
        assert image.mode == "RGB"
        assert top_k is None
        return [
            {"label": "artificial", "score": 0.81},
            {"label": "human", "score": 0.19},
        ]

    monkeypatch.setattr(model_adapter, "_pipeline", predict)

    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(png_bytes()), "sample.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    result = response.get_json()
    assert result["status"] == "completed"
    assert result["prediction"] == "AI-generated indicators detected"
    assert result["score"] == 0.81
    assert result["top_label"] == "artificial"
    assert result["scores"] == [
        {"label": "artificial", "score": 0.81},
        {"label": "human", "score": 0.19},
    ]

    saved = client.get(f"/api/history/{result['analysis_id']}").get_json()
    assert saved["score"] == 0.81
    assert saved["scores"] == result["scores"]
    assert saved["model_id"] == "Organika/sdxl-detector"
    assert saved["model_revision"] == "b37fede8562cb72b89ec201c0987f96ba21b518a"


def test_model_loading_failure_is_logged_and_returns_unavailable(
    app, client, monkeypatch, caplog
):
    configure_detector(app)
    monkeypatch.setattr(model_adapter, "_pipeline", None)

    def fail_to_load(task, **options):
        assert task == "image-classification"
        assert options["model"] == "Organika/sdxl-detector"
        assert options["revision"] == "b37fede8562cb72b89ec201c0987f96ba21b518a"
        raise OSError("test model weights are unavailable")

    monkeypatch.setitem(sys.modules, "transformers", SimpleNamespace(pipeline=fail_to_load))

    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(png_bytes()), "sample.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 503
    result = response.get_json()
    assert result["status"] == "unavailable"
    assert result["score"] is None
    assert result["error"]["code"] == "detector_unavailable"
    assert "Could not load configured detector Organika/sdxl-detector" in caplog.text
    assert "test model weights are unavailable" in caplog.text


def test_inference_failure_is_logged_without_returning_a_fake_score(
    app, client, monkeypatch, caplog
):
    configure_detector(app)

    def fail_during_inference(image, top_k):
        assert image.mode == "RGB"
        assert top_k is None
        raise RuntimeError("test inference failure")

    monkeypatch.setattr(model_adapter, "_pipeline", fail_during_inference)

    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(png_bytes()), "sample.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 503
    result = response.get_json()
    assert result["status"] == "unavailable"
    assert result["score"] is None
    assert "Check the backend log" in result["error"]["message"]
    assert "test inference failure" in caplog.text
