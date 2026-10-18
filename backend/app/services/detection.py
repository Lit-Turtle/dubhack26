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

CONF_THRESHOLD = float(os.getenv("YOLO_CONF", "0.40"))
IMGSZ = int(os.getenv("YOLO_IMGSZ", "416"))
NMS_IOU = 0.5


def _iou(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    ix1, iy1 = max(ax1, bx1), max(ay1, by1)
    ix2, iy2 = min(ax2, bx2), min(ay2, by2)
    inter = max(0.0, ix2 - ix1) * max(0.0, iy2 - iy1)
    if not inter:
        return 0.0
    area_a = max(0.0, ax2 - ax1) * max(0.0, ay2 - ay1)
    area_b = max(0.0, bx2 - bx1) * max(0.0, by2 - by1)
    return inter / (area_a + area_b - inter)


def _keep_confident(items: list[dict]) -> list[dict]:
    ranked = sorted(
        (item for item in items if item["confidence"] >= CONF_THRESHOLD),
        key=lambda item: item["confidence"],
        reverse=True,
    )
    kept: list[dict] = []
    for item in ranked:
        box = tuple(item["xyxy"])
        if any(_iou(box, tuple(other["xyxy"])) >= NMS_IOU for other in kept):
            continue
        kept.append(item)
    return kept


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
    except (ImportError, FileNotFoundError, ValueError) as error:
        raise HTTPException(503, "Ingredient detection is unavailable. Install backend requirements and include the configured model file.") from error
    summary = YoloDetector.summarize(results)[0]

    detections = [
        Detection(
            label=str(item["label"]).strip().lower(),
            confidence=item["confidence"],
            box=(item["xyxy"][0], item["xyxy"][1], item["xyxy"][2], item["xyxy"][3]),
            uncertain=False,
        )
        for item in _keep_confident(summary["detections"])
    ]

    if detections:
        labels = ", ".join(dict.fromkeys(d.label for d in detections))
        message = f"Detected {len(detections)} object(s) with the 30-ingredient model: {labels}."
    else:
        message = "The 30-ingredient model did not find a confident match. Try a closer, well-lit shot, or add ingredients manually."

    return DetectionResponse(detections=detections, message=message)


async def detect_food(image_bytes: bytes) -> DetectionResponse:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _detect_sync, image_bytes)
