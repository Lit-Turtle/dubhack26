from types import SimpleNamespace
import numpy as np
from PIL import Image
from app.services.onnx_detector import OnnxDetector
from app.services.yolo_detector import YoloDetector
from app.services import detection
from app.main import app
from fastapi.testclient import TestClient


def test_letterbox_boxes_are_scaled_to_original_image():
    detector = OnnxDetector.__new__(OnnxDetector)
    detector.width = detector.height = 416
    detector.names = {0: 'cheese'}
    detector.input = SimpleNamespace(name='images')
    # Image 200x100 gets resized to 416x208, with 104 pixels of top padding.
    detector.session = SimpleNamespace(run=lambda *_: [np.array([[[20.8, 145.6, 208, 249.6, .9, 0], [0, 0, 1, 1, .1, 0]]], dtype=np.float32)])
    image = Image.new('RGB', (200, 100))
    tensor, ratio, left, top = detector.preprocess(image)
    assert tensor.shape == (1, 3, 416, 416)
    assert (ratio, left, top) == (2.08, 0, 104)
    boxes = YoloDetector.summarize(detector.predict(image))[0]['detections']
    assert len(boxes) == 1
    assert boxes[0]['label'] == 'cheese'
    np.testing.assert_allclose(boxes[0]['xyxy'], [10, 20, 100, 70], atol=.1)


def test_missing_model_returns_service_unavailable(monkeypatch):
    import io
    body=io.BytesIO();Image.new('RGB',(10,10)).save(body,format='PNG')
    def unavailable():
        raise FileNotFoundError('missing model')
    monkeypatch.setattr(detection, '_detector', unavailable)
    response=TestClient(app).post('/api/detect',files={'image':('photo.png',body.getvalue(),'image/png')})
    assert response.status_code == 503
    assert 'unavailable' in response.json()['detail']
