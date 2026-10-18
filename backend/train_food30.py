"""Prepare a reproducible 30-ingredient dataset and run a bounded CPU training trial."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
import os
from pathlib import Path
import random
import shutil
import signal
import time

INGREDIENTS = [
    'onion', 'tomato', 'potato', 'carrot', 'broccoli', 'spinach', 'lettuce',
    'cabbage', 'cucumber', 'pepper', 'garlic', 'mushroom', 'eggplant', 'corn',
    'pea', 'egg', 'chicken', 'beef', 'pork', 'flour', 'oil', 'cheese', 'milk',
    'butter', 'rice', 'bread', 'apple', 'banana', 'lemon', 'beans',
]
ROOT = Path(__file__).resolve().parent


def write_json(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def select_labels(text, mapping):
    """Reject invalid annotations; preserve every selected box and its coordinates."""
    output = set()
    for row in text.splitlines():
        fields = row.split()
        if not fields:
            continue
        if len(fields) != 5:
            raise ValueError('Expected class x y width height')
        class_id = int(fields[0])
        values = list(map(float, fields[1:]))
        if (not all(math.isfinite(v) and 0 <= v <= 1 for v in values)
                or min(values[2:]) <= 0):
            raise ValueError('Invalid or zero-area box')
        if class_id not in mapping:
            raise ValueError(f'Unknown source class: {class_id}')
        if mapping[class_id] is not None:
            output.add(' '.join([str(mapping[class_id]), *fields[1:]]))
    return sorted(output)


def prepare(source, output, train_per_class=150):
    import yaml
    if output.exists():
        raise FileExistsError(f'Refusing to overwrite dataset: {output}')
    cfg = yaml.safe_load(source.read_text())
    names = cfg['names']
    if isinstance(names, list):
        names = dict(enumerate(names))
    missing = set(INGREDIENTS) - set(names.values())
    if missing:
        raise ValueError(f'Missing source classes: {sorted(missing)}')
    mapping = {int(i): INGREDIENTS.index(n) if n in INGREDIENTS else None for i, n in names.items()}
    source_root = Path(cfg['path'])
    report = {'source': str(source), 'ingredients': INGREDIENTS, 'seed': 42,
              'train_per_class_selection_cap': train_per_class,
              'selection_note': 'Images shared by classes may exceed the per-class selection cap.',
              'deduplication': 'Exact file SHA256; test takes precedence over val, then train. Near duplicates are not ruled out.',
              'splits': {}}
    selected = {}
    seen = set()
    rng = random.Random(42)
    for split in ['test', 'val', 'train']:
        images = {p.stem: p for p in (source_root / cfg[split]).iterdir()
                  if p.suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}}
        grouped = {}
        rejected = Counter()
        for label in sorted((source_root / 'labels' / split).glob('*.txt')):
            if label.stem not in images:
                rejected['missing_image'] += 1
                continue
            try:
                rows = select_labels(label.read_text(), mapping)
            except ValueError:
                rejected['invalid_annotations'] += 1
                continue
            image = images[label.stem]
            digest = hashlib.sha256(image.read_bytes()).hexdigest()
            if digest in seen:
                rejected['duplicate_in_another_split'] += 1
                continue
            if digest in grouped:
                grouped[digest]['rows'].update(rows)
                rejected['duplicate_within_split'] += 1
            else:
                grouped[digest] = {'image': image, 'rows': set(rows), 'sha256': digest}
        # Reserve every holdout image, even if it has no selected labels.
        seen.update(grouped)
        candidates = [r for r in grouped.values() if r['rows']]
        rng.shuffle(candidates)
        if split == 'train':
            chosen = {}
            for i in range(len(INGREDIENTS)):
                matches = [r for r in candidates if any(int(row.split()[0]) == i for row in r['rows'])]
                for record in matches[:train_per_class]:
                    chosen[record['sha256']] = record
            candidates = list(chosen.values())
        selected[split] = candidates
        counts = Counter()
        boxes = Counter()
        for record in candidates:
            ids = [int(row.split()[0]) for row in record['rows']]
            counts.update(set(ids)); boxes.update(ids)
        report['splits'][split] = {
            'images': len(candidates), 'excluded': dict(rejected),
            'images_per_class': {n: counts[i] for i, n in enumerate(INGREDIENTS)},
            'boxes_per_class': {n: boxes[i] for i, n in enumerate(INGREDIENTS)},
        }
        if not candidates or any(counts[i] == 0 for i in range(30)):
            raise ValueError(f'{split} lacks examples for one or more target classes')
    output.mkdir(parents=True)
    manifest = []
    for split, records in selected.items():
        (output / 'images' / split).mkdir(parents=True)
        (output / 'labels' / split).mkdir(parents=True)
        for record in records:
            image = record['image']; stem = record['sha256']
            os.link(image, output / 'images' / split / (stem + image.suffix.lower()))
            (output / 'labels' / split / (stem + '.txt')).write_text('\n'.join(sorted(record['rows'])) + '\n')
            manifest.append({'split': split, 'sha256': stem, 'source': str(image)})
    dataset = output / 'dataset.yaml'
    dataset.write_text(yaml.safe_dump({'path': str(output.resolve()), 'train': 'images/train',
                                     'val': 'images/val', 'test': 'images/test',
                                     'names': dict(enumerate(INGREDIENTS))}, sort_keys=False))
    write_json(output / 'preparation-report.json', report)
    write_json(output / 'image-manifest.json', manifest)
    print(json.dumps(report, indent=2), flush=True)
    return dataset


def class_scores(metrics):
    scores = {name: 0.0 for name in INGREDIENTS}
    for index, ap in zip(metrics.box.ap_class_index, metrics.box.ap50):
        scores[INGREDIENTS[int(index)]] = float(ap)
    return scores


def train(dataset, model_path, hours, target):
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(2)
    started = time.monotonic()
    run = ROOT / 'models' / 'food30-runs' / time.strftime('%Y%m%d-%H%M%S')
    run.mkdir(parents=True)
    prep = json.loads((dataset.parent / 'preparation-report.json').read_text())
    status_path = run / 'status.json'
    state = {'status': 'starting', 'target_AP50_each': target, 'hours_limit': hours,
             'dataset': str(dataset), 'starting_model': str(model_path), 'run': str(run),
             'deployed': False, 'target_reached': False,
             'test_images_per_class': prep['splits']['test']['images_per_class']}
    write_json(status_path, state)
    reserve = min(900, hours * 3600 * 0.25)
    training_deadline = started + hours * 3600 - reserve
    best_score = (-1.0, -1.0)
    target_best = run / 'best-per-class.pt'
    history = []

    def update(trainer):
        nonlocal best_score
        # final_eval also calls this callback; only record completed training epochs once.
        if history and history[-1]['epoch'] == trainer.epoch + 1:
            return
        scores = class_scores(trainer.validator.metrics)
        score = (min(scores.values()), sum(scores.values()) / len(scores))
        entry = {'epoch': trainer.epoch + 1, 'elapsed_minutes': (time.monotonic()-started)/60,
                 'AP50': scores, 'minimum_AP50': score[0], 'mean_AP50': score[1]}
        history.append(entry)
        if score > best_score and Path(trainer.last).exists():
            best_score = score
            shutil.copy2(trainer.last, target_best)
            state['best_validation'] = entry
        state.update(status='training', last_epoch=entry, candidate=str(target_best))
        write_json(run / 'history.json', history)
        write_json(status_path, state)
        if score[0] >= target:
            state['stop_reason'] = 'validation_target_reached'
            trainer.stop = True
        elif time.monotonic() >= training_deadline:
            state['stop_reason'] = 'training_time_limit'
            trainer.stop = True
        print('FOOD30_PROGRESS ' + json.dumps(entry), flush=True)

    def check_time(trainer):
        if time.monotonic() >= training_deadline:
            trainer.stop = True

    def timeout_handler(signum, frame):
        raise TimeoutError('Two-hour run budget exhausted')

    previous = signal.signal(signal.SIGALRM, timeout_handler)
    signal.setitimer(signal.ITIMER_REAL, hours * 3600)
    try:
        model = YOLO(str(model_path))
        if not set(INGREDIENTS).issubset(set(model.names.values())):
            raise ValueError('Starting weights do not contain all target class names')
        model.add_callback('on_fit_epoch_end', update)
        model.add_callback('on_train_batch_end', check_time)
        model.train(data=str(dataset), epochs=100, time=max(0.01, (training_deadline-time.monotonic())/3600),
                    imgsz=416, batch=4, device='cpu', workers=0, freeze=10,
                    optimizer='AdamW', lr0=0.0002, warmup_epochs=1.0, warmup_bias_lr=0.0002,
                    cos_lr=True, patience=8, seed=42, deterministic=True, cls_remap=True,
                    amp=False, cache=False, plots=False, mosaic=0.2, mixup=0.0, close_mosaic=0,
                    project=str(run), name='training', save=True)
        if not target_best.exists():
            raise RuntimeError('No candidate checkpoint was saved')
        state['status'] = 'evaluating_test'
        write_json(status_path, state)
        candidate = YOLO(str(target_best))
        if list(candidate.names.values()) != INGREDIENTS:
            raise ValueError('Candidate class order does not match the dataset')
        # The test split is evaluated only after checkpoint selection is complete.
        result = candidate.val(data=str(dataset), split='test', imgsz=416, batch=4,
                               device='cpu', workers=0, plots=True, project=str(run), name='test')
        scores = class_scores(result)
        state['test_AP50'] = scores
        state['test_metrics'] = result.results_dict
        state['target_reached'] = all(v >= target for v in scores.values())
        state['classes_below_target'] = {k: v for k, v in scores.items() if v < target}
        state['low_support_classes'] = {k:v for k,v in state['test_images_per_class'].items() if v < 20}
        state['status'] = 'completed'
        state['stop_reason'] = state.get('stop_reason', 'trainer_finished')
    except (TimeoutError, KeyboardInterrupt) as error:
        state['status'] = 'time_limit_or_interrupted'
        state['error'] = str(error)
    except Exception as error:
        state['status'] = 'failed'
        state['error'] = repr(error)
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        state['elapsed_minutes'] = (time.monotonic()-started)/60
        write_json(status_path, state)
        print('FOOD30_RESULT ' + json.dumps(state), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'datasets/pantry-evaluation-77h3_knk/dataset.yaml')
    parser.add_argument('--output', type=Path, default=ROOT/'datasets/food30')
    parser.add_argument('--model', type=Path, default=ROOT/'models/runs/food/weights/best.pt')
    parser.add_argument('--train-per-class', type=int, default=150)
    parser.add_argument('--hours', type=float, default=2)
    parser.add_argument('--target', type=float, default=0.8)
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--prepared', action='store_true', help='Use the previously prepared dataset without changing splits')
    args = parser.parse_args()
    if args.hours <= 0 or not 0 < args.target <= 1 or args.train_per_class <= 0:
        parser.error('Hours, target, and training sample limit must be positive; target must be <= 1')
    dataset = args.output.resolve()/'dataset.yaml' if args.prepared else prepare(args.source.resolve(), args.output.resolve(), args.train_per_class)
    if not args.prepare_only:
        train(dataset, args.model.resolve(), args.hours, args.target)


if __name__ == '__main__':
    main()
