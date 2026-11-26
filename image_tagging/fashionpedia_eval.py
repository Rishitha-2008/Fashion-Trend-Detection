"""
fashionpedia_eval.py -- build a labelled test set from Fashionpedia and score image_tagger.py

Step 1 (crop garments out of the validation photos):
  python fashionpedia_eval.py prepare --images ./val_images --ann ./instances_attributes_val2020.json \
         --out ./images --per-class 15

Step 2 (run the tagger):
  python image_tagger.py --input ./images --output ./results

Step 3 (accuracy + confusion table):
  python fashionpedia_eval.py score --csv ./results/image_tags.csv
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

# Fashionpedia category name -> short group (matched by prefix on the lowercased name)
FP_GROUPS = {
    "shirt": "shirt", "top": "top", "sweater": "sweater", "jacket": "jacket",
    "coat": "coat", "dress": "dress", "skirt": "skirt", "pants": "pants",
    "shorts": "shorts", "jumpsuit": "jumpsuit",
}

# Our CLIP labels -> same groups (so "jeans" and "trousers" both count as "pants")
PRED_TO_GROUP = {
    "shirt": "shirt", "blouse": "shirt",
    "t-shirt": "top", "top": "top", "hoodie": "top",
    "sweater": "sweater", "jacket": "jacket", "blazer": "jacket",
    "coat": "coat", "dress": "dress", "skirt": "skirt",
    "jeans": "pants", "trousers": "pants", "leggings": "pants",
    "shorts": "shorts", "jumpsuit": "jumpsuit",
}


def fp_group(name: str):
    n = name.lower().strip()
    for key, grp in FP_GROUPS.items():
        if n == key or n.startswith(key + ",") or n.startswith(key + " "):
            return grp
    return None


def prepare(images: Path, ann: Path, out: Path, per_class: int, min_side: int = 100):
    from PIL import Image

    data = json.loads(ann.read_text())
    cats = {c["id"]: fp_group(c["name"]) for c in data["categories"]}
    files = {im["id"]: im["file_name"] for im in data["images"]}
    out.mkdir(parents=True, exist_ok=True)

    # biggest garments first = clearest crops
    anns = sorted(data["annotations"], key=lambda a: -a["bbox"][2] * a["bbox"][3])
    counts = defaultdict(int)
    for a in anns:
        grp = cats.get(a["category_id"])
        if grp is None or counts[grp] >= per_class:
            continue
        x, y, w, h = a["bbox"]
        if w < min_side or h < min_side:
            continue
        src = images / files[a["image_id"]]
        if not src.exists():
            continue
        im = Image.open(src).convert("RGB")
        pad = 0.05
        box = (max(0, x - pad * w), max(0, y - pad * h),
               min(im.width, x + w * (1 + pad)), min(im.height, y + h * (1 + pad)))
        counts[grp] += 1
        im.crop(tuple(int(v) for v in box)).save(out / f"{grp}_{counts[grp]:04d}.jpg")
    print("Saved crops per class:", dict(counts))


def score(csv_path: Path):
    import pandas as pd

    df = pd.read_csv(csv_path)
    df = df[df["status"] == "ok"].copy()
    df["true"] = df["image_id"].str.split("_").str[0]
    df["pred"] = df["clothing_type"].map(PRED_TO_GROUP).fillna(df["clothing_type"])
    acc = (df["true"] == df["pred"]).mean()
    print(f"\nOverall accuracy: {acc:.1%}  ({len(df)} images)\n")
    print("Per-class accuracy:")
    print(df.assign(ok=df["true"] == df["pred"]).groupby("true")["ok"].mean().round(2).to_string())
    print("\nConfusion table (rows = true, columns = predicted):")
    print(pd.crosstab(df["true"], df["pred"]).to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("prepare")
    p.add_argument("--images", type=Path, required=True)
    p.add_argument("--ann", type=Path, required=True)
    p.add_argument("--out", type=Path, default=Path("images"))
    p.add_argument("--per-class", type=int, default=15)
    s = sub.add_parser("score")
    s.add_argument("--csv", type=Path, required=True)
    a = ap.parse_args()
    if a.cmd == "prepare":
        prepare(a.images, a.ann, a.out, a.per_class)
    else:
        score(a.csv)
