from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_MODEL = "yolo26n.pt"
# Official Ultralytics open-vocabulary weights: detect named foods without training.
OPEN_VOCAB_MODEL = "yolov8s-worldv2.pt"
# COCO pantry labels plus the single-class name used by backend/models/best.pt.
FOOD_CLASS_NAMES = {
    "apple",
    "banana",
    "broccoli",
    "cake",
    "carrot",
    "donut",
    "food",
    "hot dog",
    "orange",
    "pizza",
    "sandwich",
}
# Text prompts for YOLO-World / YOLOE. best.pt cannot use these; it only knows "food".
PANTRY_CLASS_NAMES = [
    "apple",
    "avocado",
    "banana",
    "beef",
    "bread",
    "broccoli",
    "carrot",
    "cheese",
    "chicken",
    "cucumber",
    "egg",
    "fish",
    "garlic",
    "grape",
    "lemon",
    "lettuce",
    "milk",
    "mushroom",
    "onion",
    "orange",
    "pasta",
    "pepper",
    "pizza",
    "potato",
    "rice",
    "strawberry",
    "tomato",
    "yogurt",
]
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"


def food_class_ids(names: Any) -> list[int] | None:
    """Return COCO/food class ids, or None so a custom model is not silenced."""
    name_items = names.items() if isinstance(names, dict) else enumerate(names)
    food_classes = [
        class_id
        for class_id, name in name_items
        if str(name).lower() in FOOD_CLASS_NAMES
    ]
    return food_classes or None


def is_open_vocab_model(model_name: str) -> bool:
    lowered = Path(model_name).name.lower()
    return "world" in lowered or "yoloe" in lowered


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
    """Thin wrapper around Ultralytics YOLO for closed-set and open-vocabulary inference."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        class_names: list[str] | None = None,
    ) -> None:
        from ultralytics import YOLO

        self.model_name = model_name
        self.open_vocab = is_open_vocab_model(model_name)
        self.model = YOLO(resolve_model_path(model_name))
        if self.open_vocab:
            names = class_names or PANTRY_CLASS_NAMES
            self.model.set_classes(names)

    def predict(
        self,
        source: str | int,
        *,
        conf: float = 0.25,
        save: bool = True,
        show: bool = False,
        imgsz: int = 640,
    ) -> list[Any]:
        kwargs: dict[str, Any] = {
            "source": source,
            "conf": conf,
            "save": save,
            "show": show,
            "imgsz": imgsz,
            "verbose": False,
        }
        if not self.open_vocab:
            food_classes = food_class_ids(self.model.names)
            if food_classes is not None:
                kwargs["classes"] = food_classes
        return self.model.predict(**kwargs)

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
