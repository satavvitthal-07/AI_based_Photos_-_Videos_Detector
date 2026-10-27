from io import BytesIO

from PIL import Image


def test_temporary_file_is_removed_when_detector_is_unavailable(client, monkeypatch):
    temp_paths = []
    from backend.services import image_service

    original_analyze = image_service.analyze_image

    def track_and_analyze(path, mime):
        temp_paths.append(path)
        return original_analyze(path, mime)

    monkeypatch.setattr("backend.routes.detection.analyze_image", track_and_analyze)
    buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")

    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(buffer.getvalue()), "cleanup.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 503
    assert len(temp_paths) == 1
    assert not temp_paths[0].exists()


def test_temporary_file_is_removed_after_unexpected_processing_failure(client, monkeypatch):
    temp_paths = []

    def fail_processing(path, _mime):
        temp_paths.append(path)
        raise RuntimeError("controlled test failure")

    monkeypatch.setattr("backend.routes.detection.analyze_image", fail_processing)
    buffer = BytesIO()
    Image.new("RGB", (1, 1)).save(buffer, format="PNG")

    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(buffer.getvalue()), "failure.png", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 500
    body = response.get_json()
    assert body["status"] == "failed"
    assert body["error"]["code"] == "processing_failed"
    assert len(temp_paths) == 1
    assert not temp_paths[0].exists()
