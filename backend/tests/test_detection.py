from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.services import detection as detection_module
from app.services.yolo_detector import YoloDetector, resolve_model_path

client = TestClient(app)

# 1×1 PNG
TINY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01"
    b"\x00\x00\x05\x00\x01\r\n-\xdb\x00\x00\x00\x00IEND\xaeB`\x82"
)


class _FakeBox:
    cls = [0]
    conf = [0.91]

    @property
    def xyxy(self):
        return [_FakeTensor([10.0, 20.0, 110.0, 120.0])]


class _FakeTensor:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class _FakeResult:
    names = {0: "broccoli"}
    boxes = [_FakeBox()]
    path = ""
    save_dir = None


def test_resolve_model_path_prefers_existing_file(tmp_path):
    weights = tmp_path / "custom.pt"
    weights.write_bytes(b"fake")
    assert resolve_model_path(str(weights)) == str(weights.resolve())
    resolved = resolve_model_path("yolo26n.pt")
    assert resolved == "yolo26n.pt" or Path(resolved).name == "yolo26n.pt"


def test_summarize_maps_boxes():
    summary = YoloDetector.summarize([_FakeResult()])[0]
    assert summary["detections"] == [
        {"label": "broccoli", "confidence": 0.91, "xyxy": [10.0, 20.0, 110.0, 120.0]}
    ]


def test_predict_filters_to_food_classes():
    class _FakeModel:
        names = {0: "person", 1: "table", 2: "banana", 3: "broccoli"}

        def predict(self, **kwargs):
            self.kwargs = kwargs
            return ["result"]

    detector = YoloDetector.__new__(YoloDetector)
    detector.model = _FakeModel()

    assert detector.predict("image.jpg", save=False) == ["result"]
    assert detector.model.kwargs["classes"] == [2, 3]


def test_predict_skips_coco_filter_for_custom_food_model():
    class _FakeModel:
        names = {0: "tomato", 1: "onion", 2: "banana", 3: "chicken"}

        def predict(self, **kwargs):
            self.kwargs = kwargs
            return ["result"]

    detector = YoloDetector.__new__(YoloDetector)
    detector.model = _FakeModel()

    assert detector.predict("image.jpg", save=False) == ["result"]
    assert detector.model.kwargs["classes"] is None


def test_detect_endpoint_with_mocked_yolo(monkeypatch):
    detection_module._detector.cache_clear()

    class _FakeDetector:
        def predict(self, *args, **kwargs):
            return [_FakeResult()]

    monkeypatch.setattr(detection_module, "_detector", lambda: _FakeDetector())

    response = client.post(
        "/detect",
        files={"image": ("pantry.png", TINY_PNG, "image/png")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detections"] == [
        {"label": "broccoli", "confidence": 0.91, "box": [10.0, 20.0, 110.0, 120.0]}
    ]
    assert "broccoli" in body["message"]


def test_detect_rejects_invalid_image_bytes():
    detection_module._detector.cache_clear()
    response = client.post(
        "/detect",
        files={"image": ("photo.jpg", b"not-an-image", "image/jpeg")},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["detections"] == []
    assert "decode" in body["message"].lower()


def test_detect_rejects_bad_mime():
    assert client.post("/detect", files={"image": ("x.txt", b"text", "text/plain")}).status_code == 415
