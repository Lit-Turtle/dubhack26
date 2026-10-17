from __future__ import annotations

from pathlib import Path
from typing import Any

DEFAULT_MODEL = "yolo26n.pt"


class YoloDetector:
    """Thin wrapper around Ultralytics YOLO26 for image, video, and webcam inference."""

    def __init__(self, model_name: str = DEFAULT_MODEL) -> None:
        from ultralytics import YOLO

        self.model = YOLO(model_name)

    def predict(
        self,
        source: str | int,
        *,
        conf: float = 0.25,
        save: bool = True,
        show: bool = False,
        imgsz: int = 640,
    ) -> list[Any]:
        return self.model.predict(
            source=source,
            conf=conf,
            save=save,
            show=show,
            imgsz=imgsz,
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
