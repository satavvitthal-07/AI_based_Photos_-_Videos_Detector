import numpy as np
import pytest

from backend.services import video_service


class FakeCapture:
    def __init__(self):
        self.released = False

    def isOpened(self):
        return True

    def get(self, property_id):
        values = {
            video_service.cv2.CAP_PROP_FPS: 1.0,
            video_service.cv2.CAP_PROP_FRAME_COUNT: 3.0,
            video_service.cv2.CAP_PROP_FRAME_WIDTH: 8.0,
            video_service.cv2.CAP_PROP_FRAME_HEIGHT: 6.0,
        }
        return values[property_id]

    def set(self, _property_id, _value):
        return True

    def read(self):
        return True, np.zeros((6, 8, 3), dtype=np.uint8)

    def release(self):
        self.released = True


def test_video_sampling_uses_bounded_frames_and_documented_aggregation(
    app, tmp_path, monkeypatch
):
    video_path = tmp_path / "sample.mp4"
    video_path.write_bytes(b"\x00\x00\x00\x18ftypisom")
    capture = FakeCapture()
    monkeypatch.setattr(video_service.cv2, "VideoCapture", lambda _path: capture)
    model_outputs = iter(
        [
            {"prediction": "AI-generated indicators detected", "score": 0.8, "top_label": "AI", "model_id": "test/model", "model_revision": "rev1"},
            {"prediction": "AI-generated indicators detected", "score": 0.6, "top_label": "AI", "model_id": "test/model", "model_revision": "rev1"},
            {"prediction": "No AI-generated indicators detected by this model", "score": 0.3, "top_label": "real", "model_id": "test/model", "model_revision": "rev1"},
        ]
    )
    monkeypatch.setattr(video_service, "classify_image", lambda _image: next(model_outputs))

    with app.app_context():
        result = video_service.analyze_video(video_path)

    assert result["prediction"] == "AI-generated indicators detected in sampled frames"
    assert result["score"] == pytest.approx((0.8 + 0.6 + 0.3) / 3)
    assert result["model_id"] == "test/model"
    assert [frame["index"] for frame in result["frames"]] == [0, 1, 2]
    assert [frame["top_label"] for frame in result["frames"]] == ["AI", "AI", "real"]
    assert capture.released is True
