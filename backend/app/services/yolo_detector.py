from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_MODEL = "yolo26n.pt"
FOOD_CLASS_NAMES = {
    "apple",
    "banana",
    "broccoli",
    "cake",
    "carrot",
    "donut",
    "hot dog",
    "orange",
    "pizza",
    "sandwich",
}
# Official COCO checkpoints mix food with people, vehicles, furniture, etc.
COCO_NONFOOD_HINTS = {
    "person",
    "bicycle",
    "car",
    "motorcycle",
    "airplane",
    "bus",
    "train",
    "truck",
    "boat",
    "traffic light",
    "chair",
    "couch",
    "bed",
    "tv",
    "laptop",
}
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def resolve_model_path(model_name: str) -> str:
    """Prefer an explicit path, then backend/models/<name>, else the Ultralytics name."""
    candidate = Path(model_name).expanduser()
    if candidate.is_file():
        return str(candidate.resolve())
    local = MODELS_DIR / model_name
    if local.is_file():
        return str(local.resolve())
    return model_name


class YoloDetector:
    """Thin wrapper around Ultralytics YOLO26 for image, video, and webcam inference."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        from ultralytics import YOLO

        self.model = YOLO(resolve_model_path(model_name))

    def predict(
        self,
        source: str | int,
        *,
        conf: float = 0.25,
        save: bool = True,
        show: bool = False,
        imgsz: int = 640,
    ) -> list[Any]:
        names = self.model.names
        name_items = list(names.items()) if isinstance(names, dict) else list(enumerate(names))
        food_classes = [
            class_id
            for class_id, name in name_items
            if str(name).lower() in FOOD_CLASS_NAMES
        ]
        looks_like_coco = any(str(name).lower() in COCO_NONFOOD_HINTS for _, name in name_items)
        # A trained ingredients model is already food-only — keep every class.
        classes = food_classes if looks_like_coco and food_classes else None
        return self.model.predict(
            source=source,
            conf=conf,
            save=save,
            show=show,
            imgsz=imgsz,
            classes=classes,
            verbose=False,
        )

    @staticmethod
    def summarize(results: list[Any]) -> list[dict[str, Any]]:
        summaries: list[dict[str, Any]] = []
        for result in results:
            detections = []
            names = result.names
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    cls_id = int(box.cls[0])
                    detections.append(
                        {
                            "label": names[cls_id],
                            "confidence": round(float(box.conf[0]), 4),
                            "xyxy": [round(float(v), 1) for v in box.xyxy[0].tolist()],
                        }
                    )
            summaries.append(
                {
                    "source": str(getattr(result, "path", "")),
                    "save_dir": str(Path(result.save_dir)) if getattr(result, "save_dir", None) else None,
                    "detections": detections,
                }
            )
        return summaries
