"""Merge Ultralytics ingredients NDJSON exports into a YOLO detect dataset."""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.request import Request, urlopen

SKIP_NAMES = {"-", "pot", "ice"}
ALIASES = {
    "bean": "beans",
    "black beans": "beans",
    "red beans": "beans",
    "eggs": "egg",
    "greenapple": "apple",
    "chicken breast": "chicken",
    "chicken thigh": "chicken",
    "chicken wing": "chicken",
    "chicken gizzards": "chicken",
    "pork belly": "pork",
    "raddish": "radish",
    "mayonaise": "mayonnaise",
    "pomegrante": "pomegranate",
    "yogurt-occluded": "yogurt",
    "humus": "hummus",
    "marmelade": "marmalade",
    "water melon": "watermelon",
    "wallnut": "walnut",
    "brinjal": "eggplant",
    "green brinjal": "eggplant",
    "capsicum": "pepper",
    "chili pepper": "chili",
    "chilli": "chili",
    "olive oil": "oil",
    "garden peas": "pea",
    "green peas": "pea",
    "rice chamal": "rice",
    "rice ball": "rice",
    "sweet potato suthuni": "sweet potato",
    "pumpkin farsi": "pumpkin",
    "lemon nimbu": "lemon",
    "lime kagati": "lime",
    "asparagus kurilo": "asparagus",
    "avocado": "avocado",
    "cornflakec": "cornflakes",
    "chowmein noodles": "noodle",
    "thukpa noodles": "noodle",
    "green-salad": "salad",
    "spring onion": "onion",
    "onion leaves": "onion",
    "soyabean bhatmas": "soy",
    "green soyabean hariyo bhatmas": "soy",
    "soy sauce": "soy sauce",
    "minced meat": "beef",
    "buff meat": "beef",
    "mutton": "lamb",
    "tree tomato rukh tamatar": "tomato",
}


def normalize_name(raw: str) -> str:
    name = raw.strip().lower().replace("_", " ").replace("–", "-")
    name = re.sub(r"\([^)]*\)", " ", name)
    name = re.sub(r"\s*-[^-]+-\s*", " ", name)
    name = re.sub(r"\s+", " ", name).strip(" -")
    return ALIASES.get(name, name)


def load_ndjson(path: Path) -> tuple[dict[int, str], list[dict]]:
    header = None
    images = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get("type") == "dataset":
                header = {int(key): value for key, value in row["class_names"].items()}
            elif row.get("type") == "image":
                images.append(row)
    if header is None:
        raise ValueError(f"No dataset header in {path}")
    return header, images


def safe_stem(name: str, prefix: str) -> str:
    stem = Path(name).stem
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "_", stem)[:80]
    return f"{prefix}_{cleaned}"


def download(url: str, dest: Path, timeout: int = 45) -> str:
    if dest.exists() and dest.stat().st_size > 1000:
        return "exists"
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={"User-Agent": "PantryPlay-dataset/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response, dest.open("wb") as out:
            out.write(response.read())
    except Exception:
        if dest.exists():
            dest.unlink()
        return "fail"
    return "ok" if dest.exists() and dest.stat().st_size > 1000 else "fail"


def write_label(path: Path, boxes: list[list[float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for class_id, x, y, w, h in boxes:
        if min(w, h) <= 0:
            continue
        lines.append(f"{int(class_id)} {x:.6f} {y:.6f} {w:.6f} {h:.6f}")
    path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge ingredients NDJSON files into a YOLO dataset.")
    parser.add_argument("sources", nargs="+", help="Path to an ingredients NDJSON export")
    parser.add_argument("--out", default="datasets/ingredients", help="Output dataset directory")
    parser.add_argument("--workers", type=int, default=16, help="Download workers")
    args = parser.parse_args()

    out = Path(args.out)
    if not out.is_absolute():
        out = Path(__file__).resolve().parent / out

    names: dict[str, int] = {}
    jobs = []
    skipped = 0
    for index, source in enumerate(args.sources):
        path = Path(source)
        header, images = load_ndjson(path)
        prefix = f"d{index}"
        print(f"Loaded {len(images)} images from {path.name} ({len(header)} source classes)", flush=True)
        for image in images:
            mapped = []
            for box in image.get("annotations", {}).get("boxes", []):
                if len(box) < 5:
                    continue
                raw = header.get(int(box[0]), "")
                label = normalize_name(raw)
                if not label or label in SKIP_NAMES:
                    continue
                if label not in names:
                    names[label] = len(names)
                mapped.append([names[label], *box[1:5]])
            if not mapped:
                skipped += 1
                continue
            split = image.get("split") or "train"
            if split == "validation":
                split = "val"
            if split not in {"train", "val", "test"}:
                split = "train"
            stem = safe_stem(image["file"], prefix)
            jobs.append((image["url"], out / "images" / split / f"{stem}.jpg", out / "labels" / split / f"{stem}.txt", mapped))

    class_names = [name for name, _ in sorted(names.items(), key=lambda item: item[1])]
    print(f"Merged {len(jobs)} labeled images, {len(class_names)} classes, skipped {skipped} empty", flush=True)

    out.mkdir(parents=True, exist_ok=True)
    (out / "classes.json").write_text(json.dumps(class_names, indent=2), encoding="utf-8")
    yaml = ["path: " + out.resolve().as_posix(), "train: images/train", "val: images/val", "test: images/test", "names:"]
    yaml.extend(f"  {index}: {name}" for index, name in enumerate(class_names))
    (out / "data.yaml").write_text("\n".join(yaml) + "\n", encoding="utf-8")

    counts = Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download, url, image_path): (image_path, label_path, boxes) for url, image_path, label_path, boxes in jobs}
        done = 0
        for future in as_completed(futures):
            image_path, label_path, boxes = futures[future]
            status = future.result()
            counts[status] += 1
            if status != "fail":
                write_label(label_path, boxes)
            done += 1
            if done % 250 == 0 or done == len(futures):
                print(f"Downloaded {done}/{len(futures)} ({counts['ok']} new, {counts['exists']} cached, {counts['fail']} failed)", flush=True)

    print(f"Dataset ready: {out / 'data.yaml'}")
    return 0 if counts["fail"] < len(jobs) else 1


if __name__ == "__main__":
    sys.exit(main())
