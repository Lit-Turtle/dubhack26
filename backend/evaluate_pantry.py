"""Evaluate pantry-merged using the same ingredient-name normalization as training."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import tempfile


def remap_labels(text, class_map):
    lines = []
    for row in text.splitlines():
        fields = row.split()
        if not fields:
            continue
        if len(fields) != 5:
            raise ValueError('Expected YOLO detection labels: class x y width height')
        old_id = int(fields[0])
        if old_id not in class_map:
            raise ValueError(f'Unknown dataset class ID {old_id}')
        new_id = class_map[old_id]
        if new_id is not None:
            lines.append(' '.join([str(new_id), *fields[1:]]))
    return '\n'.join(lines) + ('\n' if lines else '')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--data',default='datasets/pantry-merged/dataset.yaml')
    p.add_argument('--model',default='models/runs/food/weights/best.pt')
    p.add_argument('--split',choices=['val','test'],default='test')
    args=p.parse_args()
    import torch
    import yaml
    from ultralytics import YOLO
    from prepare_ingredients import normalize_name, SKIP_NAMES
    torch.set_num_threads(2)
    model=YOLO(args.model)
    names=dict(model.names)
    lookup={name.strip().lower():i for i,name in names.items()}
    source=Path(args.data).resolve()
    config=yaml.safe_load(source.read_text())
    source_root=Path(config.get('path',source.parent))
    if not source_root.is_absolute():source_root=(source.parent/source_root).resolve()
    source_names=config['names']
    if isinstance(source_names,list):source_names=dict(enumerate(source_names))
    class_map={}
    skipped=[]
    for old_id,name in source_names.items():
        normalized=normalize_name(name)
        if not normalized or normalized in SKIP_NAMES:
            class_map[int(old_id)]=None
            skipped.append(name)
        elif normalized in lookup:
            class_map[int(old_id)]=lookup[normalized]
        else:
            raise ValueError(f'Dataset label {name!r} has no matching model class')
    output=Path(tempfile.mkdtemp(prefix='pantry-evaluation-',dir=source.parent.parent))
    counts={}
    splits={}
    for split in ['train','val','test']:
        relative=config.get(split)
        if not relative:continue
        if not isinstance(relative,str):raise ValueError('Expected a directory path for each split')
        images=Path(relative) if Path(relative).is_absolute() else source_root/relative
        images=images.resolve()
        if images.parent.name!='images':raise ValueError('Expected images/<split> folder layout')
        labels=images.parent.parent/'labels'/images.name
        destination_images=output/'images'/split
        destination_images.mkdir(parents=True)
        dest_labels=output/'labels'/split
        dest_labels.mkdir(parents=True)
        split_counts=Counter()
        for image in images.iterdir():
            if image.suffix.lower() not in {'.jpg','.jpeg','.png','.webp','.bmp'}:continue
            os.link(image,destination_images/image.name)
            label=labels/(image.stem+'.txt')
            if not label.is_file():raise FileNotFoundError(f'Missing annotations: {label}')
            mapped=remap_labels(label.read_text(),class_map)
            (dest_labels/label.name).write_text(mapped)
            split_counts.update(int(line.split()[0]) for line in mapped.splitlines())
        splits[split]=f'images/{split}'
        counts[split]={names[i]:count for i,count in split_counts.items()}
    dataset=output/'dataset.yaml'
    dataset.write_text(yaml.safe_dump({'path':str(output),**splits,'names':names},sort_keys=False))
    (output/'mapping-report.json').write_text(json.dumps({'source':str(source),'model':str(Path(args.model).resolve()),'class_map':class_map,'skipped_source_labels':skipped,'boxes_per_class':counts},indent=2))
    print('Mapped dataset:',dataset,flush=True)
    print('Excluded source labels:',skipped,flush=True)
    result=model.val(data=str(dataset),split=args.split,device='cpu',batch=4,workers=0,
                     imgsz=640,plots=True,project='models/evaluations',name='pantry-merged')
    summary={'source':str(source),'split':args.split,'mapped_dataset':str(dataset),'metrics':result.results_dict,'output_dir':str(result.save_dir)}
    destination=Path(result.save_dir)/'evaluation-summary.json'
    destination.write_text(json.dumps(summary,indent=2,default=str)+'\n')
    print('Evaluation summary:',destination,flush=True)


if __name__=='__main__':main()
