"""CPU inference for the bundled YOLO model, without importing PyTorch."""
import ast
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from PIL import Image


def _class_names(path, session):
    raw = session.get_modelmeta().custom_metadata_map.get('names')
    names = ast.literal_eval(raw) if raw else None
    if isinstance(names, dict):
        return {int(key): str(value) for key, value in names.items()}
    if isinstance(names, (list, tuple)):
        return {index: str(value) for index, value in enumerate(names)}
    info = Path(path).with_name('model-info.json')
    if info.is_file():
        classes = json.loads(info.read_text()).get('classes') or []
        return {index: str(value) for index, value in enumerate(classes)}
    raise ValueError('ONNX model is missing class names')


class OnnxDetector:
    def __init__(self, path):
        import onnxruntime as ort
        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1
        self.session = ort.InferenceSession(str(path), sess_options=options, providers=['CPUExecutionProvider'])
        self.input = self.session.get_inputs()[0]
        self.height, self.width = self.input.shape[2:]
        self.names = _class_names(path, self.session)
        shape = self.session.get_outputs()[0].shape
        if shape[-1] != 6:
            raise ValueError('Expected an ONNX export with embedded NMS and six columns per detection')

    def preprocess(self, image):
        image = image.convert('RGB')
        ratio = min(self.width / image.width, self.height / image.height)
        size = (round(image.width * ratio), round(image.height * ratio))
        left = round((self.width - size[0]) / 2 - 0.1)
        top = round((self.height - size[1]) / 2 - 0.1)
        canvas = Image.new('RGB', (self.width, self.height), (114, 114, 114))
        canvas.paste(image.resize(size, Image.Resampling.BILINEAR), (left, top))
        tensor = np.asarray(canvas, dtype=np.float32).transpose(2, 0, 1)[None] / 255.0
        return np.ascontiguousarray(tensor), ratio, left, top

    def predict(self, image, *, conf=0.25, **kwargs):
        tensor, ratio, left, top = self.preprocess(image)
        output = self.session.run(None, {self.input.name: tensor})[0][0]
        boxes = []
        for row in output:
            if not np.isfinite(row).all() or row[4] < conf:
                continue
            class_id = int(row[5])
            if class_id not in self.names:
                continue
            xyxy = row[:4].copy()
            xyxy[[0, 2]] = np.clip((xyxy[[0, 2]] - left) / ratio, 0, image.width)
            xyxy[[1, 3]] = np.clip((xyxy[[1, 3]] - top) / ratio, 0, image.height)
            if xyxy[2] <= xyxy[0] or xyxy[3] <= xyxy[1]:
                continue
            boxes.append(SimpleNamespace(cls=[class_id], conf=[float(row[4])], xyxy=[xyxy]))
        return [SimpleNamespace(names=self.names, boxes=boxes, path='', save_dir=None)]
