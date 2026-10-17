from __future__ import annotations

import argparse
import json
import sys

from app.services.yolo_detector import DEFAULT_MODEL, YoloDetector

SAMPLE_IMAGE = "https://ultralytics.com/images/bus.jpg"


def parse_source(raw: str) -> str | int:
    if raw.isdigit():
        return int(raw)
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Ultralytics YOLO26 detection.")
    parser.add_argument(
        "--source",
        default=SAMPLE_IMAGE,
        help="Image/video path, URL, directory, or webcam index (default: sample bus.jpg)",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="YOLO model weights (default: yolo26n.pt)")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--imgsz", type=int, default=640, help="Inference image size")
    parser.add_argument("--show", action="store_true", help="Open a preview window")
    parser.add_argument("--no-save", action="store_true", help="Do not write annotated outputs")
    args = parser.parse_args()

    detector = YoloDetector(args.model)
    results = detector.predict(
        parse_source(args.source),
        conf=args.conf,
        save=not args.no_save,
        show=args.show,
        imgsz=args.imgsz,
    )
    print(json.dumps(detector.summarize(results), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
