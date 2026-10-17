from __future__ import annotations

import argparse
import sys

from app.services.yolo_detector import DEFAULT_MODEL, MODELS_DIR, resolve_model_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fine-tune a local Ultralytics .pt on a dataset YAML.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Starting weights: filename in backend/models/, a path, or an official Ultralytics name",
    )
    parser.add_argument(
        "--data",
        default="coco8.yaml",
        help="Dataset YAML (Ultralytics name or path). coco8.yaml is a tiny smoke-test set.",
    )
    parser.add_argument("--epochs", type=int, default=50, help="Training epochs")
    parser.add_argument("--imgsz", type=int, default=640, help="Training image size")
    parser.add_argument("--batch", type=int, default=8, help="Batch size")
    parser.add_argument("--project", default=str(MODELS_DIR / "runs"), help="Output project directory")
    parser.add_argument("--name", default="food", help="Run name under --project")
    args = parser.parse_args()

    from ultralytics import YOLO

    weights = resolve_model_path(args.model)
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Starting weights: {weights}")
    print(f"Dataset: {args.data}")

    model = YOLO(weights)
    model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
    )
    print(f"Best weights: {args.project}/{args.name}/weights/best.pt")
    print("Point the API at them with YOLO_MODEL=models/runs/food/weights/best.pt in backend/.env")
    return 0


if __name__ == "__main__":
    sys.exit(main())
