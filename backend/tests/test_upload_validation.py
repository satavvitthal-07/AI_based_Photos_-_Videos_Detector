from io import BytesIO


def test_missing_upload_is_rejected(client):
    response = client.post("/api/detect/image", data={})

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "missing_file"


def test_unsupported_format_is_rejected(client):
    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(b"GIF89a"), "image.gif", "image/gif")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_format"


def test_mime_mismatch_is_rejected(client):
    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(b"\xff\xd8\xffdata"), "image.jpg", "image/png")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "mime_mismatch"


def test_oversized_image_is_rejected(app, client):
    app.config["IMAGE_MAX_BYTES"] = 8
    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(b"\xff\xd8\xff" + b"x" * 20), "large.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "file_too_large"


def test_invalid_image_signature_is_rejected(client):
    response = client.post(
        "/api/detect/image",
        data={"file": (BytesIO(b"not an image"), "broken.jpg", "image/jpeg")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "signature_mismatch"


def test_video_requires_mp4_extension(client):
    response = client.post(
        "/api/detect/video",
        data={"file": (BytesIO(b"video"), "clip.avi", "video/x-msvideo")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_format"
