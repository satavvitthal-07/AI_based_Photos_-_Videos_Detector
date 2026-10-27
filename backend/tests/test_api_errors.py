from io import BytesIO

from PIL import Image


def png_bytes():
    buffer = BytesIO()
    Image.new("RGB", (2, 2), color=(12, 24, 36)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_detector_unavailable_is_explicit_and_saved(client):
    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(png_bytes()), "private/path/photo.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "unavailable"
    assert body["prediction"] == "Detection unavailable"
    assert body["score"] is None
    assert body["analysis_id"]
    assert body["error"]["code"] == "detector_unavailable"
    assert body["error_message"] == body["error"]["message"]
    assert body["display_name"] == "photo.png"
    saved = client.get(f"/api/history/{body['analysis_id']}").get_json()
    assert saved["error_message"] == body["error_message"]


def test_unknown_history_record_returns_structured_error(client):
    response = client.get("/api/history/does-not-exist")

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_invalid_history_limit_returns_structured_error(client):
    response = client.get("/api/history?limit=999")

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "invalid_limit"
