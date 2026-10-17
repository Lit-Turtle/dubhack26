from __future__ import annotations

import asyncio
import io
import os
from functools import lru_cache

from PIL import Image, UnidentifiedImageError

from app.schemas import Detection, DetectionResponse
from app.services.yolo_detector import DEFAULT_MODEL, YoloDetector

CONF_THRESHOLD = float(os.getenv("YOLO_CONF", "0.25"))
IMGSZ = int(os.getenv("YOLO_IMGSZ", "640"))


@lru_cache(maxsize=1)
def _detector() -> YoloDetector:
    return YoloDetector(os.getenv("YOLO_MODEL", DEFAULT_MODEL))


def _detect_sync(image_bytes: bytes) -> DetectionResponse:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError:
        return DetectionResponse(
            detections=[],
            message="Could not decode the uploaded image. Use a valid JPEG, PNG, or WebP file.",
        )

    try:
        results = _detector().predict(image, conf=CONF_THRESHOLD, save=False, show=False, imgsz=IMGSZ)
    except ImportError:
        return DetectionResponse(
            detections=[],
            message="YOLO is not installed. Run pip install -r requirements-yolo.txt (Python 3.11–3.13).",
        )
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
