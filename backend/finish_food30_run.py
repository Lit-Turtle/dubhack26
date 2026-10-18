"""Evaluate the multi-ingredient checkpoint and, if it improves, publish it."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from train_food30 import INGREDIENTS, class_scores, write_json

ROOT = Path(__file__).resolve().parent
RUN = ROOT / 'models' / 'food30-runs' / '20261018-005455'
SRC = RUN / 'best-per-class.keep.pt'
if not SRC.exists():
    SRC = RUN / 'best-per-class.pt'
DATA = ROOT / 'datasets' / 'food30-multi' / 'dataset.yaml'
DEST = ROOT / 'models' / 'food30'
CURRENT = json.loads((DEST / 'model-info.json').read_text())
SUPPORT = CURRENT.get('low_support_classes') or {}


def main():
    from ultralytics import YOLO
    model = YOLO(str(SRC))
    result = model.val(data=str(DATA), split='test', imgsz=416, batch=4,
                       device='cpu', workers=0, plots=False, project=str(RUN), name='final-test')
    scores = class_scores(result)
    metrics = {key: float(value) for key, value in result.results_dict.items()}
    exported = Path(model.export(format='onnx', imgsz=416, nms=True, simplify=True))
    new_map = metrics['metrics/mAP50(B)']
    old_map = float(CURRENT['test_metrics']['metrics/mAP50(B)'])
    improved = new_map >= old_map
    info = {
        'model': 'food30',
        'classes': INGREDIENTS,
        'imgsz': 416,
        'format': 'ONNX with embedded NMS',
        'source_checkpoint': str(SRC),
        'test_AP50': scores,
        'test_metrics': metrics,
        'low_support_classes': CURRENT.get('low_support_classes', {}),
        'target_reached': all(value >= 0.8 for value in scores.values()),
        'classes_below_target': {name: score for name, score in scores.items() if score < 0.8},
        'previous_test_mAP50': old_map,
        'deployed': improved,
        'training': '7-hour multi-ingredient fine-tune, stopped for demo wrap-up after 27 epochs',
    }
    write_json(RUN / 'final-test.json', info)
    print('FOOD30_FINAL ' + json.dumps({
        'new_mAP50': new_map, 'old_mAP50': old_map, 'improved': improved,
        'min_AP50': min(scores.values()), 'classes_at_80': sum(v >= 0.8 for v in scores.values()),
        'onnx': str(exported),
    }))
    if improved:
        shutil.copy2(SRC, DEST / 'best.pt')
        shutil.copy2(exported, DEST / 'best.onnx')
        write_json(DEST / 'model-info.json', info)
        print('Published new food30 weights')
    else:
        print('Kept existing food30 weights; new run did not beat test mAP50')


if __name__ == '__main__':
    main()
