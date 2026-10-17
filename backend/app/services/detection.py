from app.schemas import DetectionResponse


async def detect_food(image_bytes: bytes) -> DetectionResponse:
    """Replace with YOLO inference. Never invent detections in the stub."""
    return DetectionResponse(
        detections=[],
        message="YOLO is not connected yet. Please enter the ingredients from your photo manually.",
    )
