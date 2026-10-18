from __future__ import annotations

import asyncio
import io
import os
from functools import lru_cache

from PIL import Image, ImageOps, UnidentifiedImageError
from fastapi import HTTPException
from pathlib import Path

from app.schemas import Detection, DetectionResponse
from app.services.yolo_detector import DEFAULT_MODEL, YoloDetector, resolve_model_path

CONF_THRESHOLD = float(os.getenv("YOLO_CONF", "0.25"))
IMGSZ = int(os.getenv("YOLO_IMGSZ", "416"))


@lru_cache(maxsize=1)
def _detector() -> YoloDetector:
    model_path = resolve_model_path(os.getenv("YOLO_MODEL", DEFAULT_MODEL))
    if model_path.endswith('.onnx'):
        from app.services.onnx_detector import OnnxDetector
        if not Path(model_path).is_file():
            raise FileNotFoundError(model_path)
        return OnnxDetector(model_path)
    return YoloDetector(model_path)


def _detect_sync(image_bytes: bytes) -> DetectionResponse:
    try:
        image = ImageOps.exif_transpose(Image.open(io.BytesIO(image_bytes))).convert("RGB")
    except UnidentifiedImageError:
        return DetectionResponse(
            detections=[],
            message="Could not decode the uploaded image. Use a valid JPEG, PNG, or WebP file.",
        )

    try:
        results = _detector().predict(image, conf=CONF_THRESHOLD, save=False, show=False, imgsz=IMGSZ)
    except (ImportError, FileNotFoundError) as error:
        raise HTTPException(503, "Ingredient detection is unavailable. Install backend requirements and include the configured model file.") from error
    summary = YoloDetector.summarize(results)[0]

    detections = [
        Detection(
            label=item["label"],
            confidence=item["confidence"],
            box=(item["xyxy"][0], item["xyxy"][1], item["xyxy"][2], item["xyxy"][3]),
        )
        for item in summary["detections"]
    ]

    if detections:
        labels = ", ".join(dict.fromkeys(d.label for d in detections))
        message = f"Detected {len(detections)} object(s): {labels}."
    else:
        message = "No objects detected above the confidence threshold. Add ingredients manually."

    return DetectionResponse(detections=detections, message=message)


async def detect_food(image_bytes: bytes) -> DetectionResponse:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _detect_sync, image_bytes)
