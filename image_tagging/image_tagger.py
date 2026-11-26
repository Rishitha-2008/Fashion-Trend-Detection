"""
image_tagger.py  --  Member 2: Image Intelligence module
Project: Automatic System for Detecting Trends in Fashion

What it does
  1. Zero-shot CLIP classification  -> clothing type + pattern (+ confidence)
  2. Colour detection (k-means, named colours, background-aware)
  3. Batch processing of a whole image folder
  4. Structured export -> CSV, JSON, optional SQLite

Usage
  pip install torch torchvision transformers pillow scikit-learn numpy pandas tqdm
  python image_tagger.py --input ./images --output ./results --batch-size 16

Member 3 (data/trends) consumes:  results/image_tags.csv  (or the SQLite table image_tags)
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np
from PIL import Image, ImageOps

log = logging.getLogger("image_tagger")

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

# --------------------------------------------------------------------------
# 1. LABEL VOCABULARIES  (edit these - this is where accuracy is won or lost)
# --------------------------------------------------------------------------
CLOTHING_LABELS: List[str] = [
    "shirt", "t-shirt", "blouse", "top", "sweater", "hoodie", "jacket", "coat",
    "blazer", "dress", "skirt", "jeans", "trousers", "shorts", "jumpsuit",
    "kurta", "saree", "lehenga", "leggings", "suit", "tracksuit",
]

PATTERN_LABELS: List[str] = [
    "solid plain", "striped", "checked plaid", "floral", "polka dot",
    "graphic print", "animal print", "geometric", "camouflage", "tie-dye",
    "embroidered", "paisley",
]

# Several prompt templates per label, embeddings are averaged (prompt ensembling).
CLOTHING_TEMPLATES = [
    "a photo of a {}.",
    "a photo of a person wearing a {}.",
    "a fashion photo of a {}.",
    "a {} on a clothing website.",
]
PATTERN_TEMPLATES = [
    "a photo of clothing with a {} pattern.",
    "a {} garment.",
    "fabric with a {} pattern.",
]

# Display names after classification (so CSV says "solid", not "solid plain")
PATTERN_DISPLAY = {"solid plain": "solid", "checked plaid": "checked"}

# Named colours for tagging (name -> sRGB). Extend freely.
NAMED_COLOURS: Dict[str, tuple] = {
    "black": (20, 20, 20), "white": (245, 245, 245), "grey": (128, 128, 128),
    "charcoal": (60, 60, 65), "silver": (192, 192, 192),
    "red": (200, 30, 40), "maroon": (110, 20, 35), "pink": (240, 150, 180),
    "orange": (240, 130, 30), "yellow": (240, 210, 50), "mustard": (205, 160, 30),
    "beige": (225, 205, 170), "cream": (250, 240, 215), "sand": (210, 185, 140),
    "brown": (110, 70, 40), "tan": (180, 140, 95),
    "olive": (110, 115, 50), "green": (40, 150, 70), "teal": (20, 130, 130),
    "navy": (20, 30, 90), "blue": (40, 90, 200), "light blue": (140, 190, 235),
    "denim blue": (70, 100, 150), "purple": (110, 50, 150), "lavender": (190, 170, 225),
}


# --------------------------------------------------------------------------
# 2. COLOUR DETECTION
# --------------------------------------------------------------------------
def _srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """rgb: (N,3) 0-255 -> CIE Lab (N,3). Lab distance ~ perceived colour difference."""
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c > 0.04045, ((c + 0.055) / 1.055) ** 2.4, c / 12.92)
    m = np.array([[0.4124, 0.3576, 0.1805],
                  [0.2126, 0.7152, 0.0722],
                  [0.0193, 0.1192, 0.9505]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[:, 1] - 16,
                     500 * (f[:, 0] - f[:, 1]),
                     200 * (f[:, 1] - f[:, 2])], axis=1)


_NAMES = list(NAMED_COLOURS)
_NAME_LAB = _srgb_to_lab(np.array(list(NAMED_COLOURS.values())))


def name_colour(rgb: Sequence[int]) -> str:
    lab = _srgb_to_lab(np.array([rgb]))
    return _NAMES[int(np.argmin(np.linalg.norm(_NAME_LAB - lab, axis=1)))]


def _foreground_mask(arr: np.ndarray) -> np.ndarray:
    """
    Cheap background suppression: assume the 4 image borders are background,
    drop pixels close to the median border colour. Falls back to everything
    if that would remove too much (e.g. full-frame garment).
    """
    h, w, _ = arr.shape
    b = max(2, int(0.06 * min(h, w)))
    border = np.concatenate([arr[:b].reshape(-1, 3), arr[-b:].reshape(-1, 3),
                             arr[:, :b].reshape(-1, 3), arr[:, -b:].reshape(-1, 3)])
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(arr.astype(float) - bg, axis=2)
    mask = dist > 35
    return mask if mask.mean() > 0.15 else np.ones((h, w), dtype=bool)


def extract_colours(img: Image.Image, k: int = 4, size: int = 120,
                    min_share: float = 0.08) -> List[dict]:
    """Return [{name, hex, share}] sorted by share, using k-means on foreground pixels."""
    from sklearn.cluster import KMeans

    small = ImageOps.fit(img.convert("RGB"), (size, size))
    arr = np.asarray(small)

    # centre-weighted crop: garment is usually in the middle, skin/background at the edges
    m = int(size * 0.15)
    centre = arr[m:-m, m:-m]
    pixels = centre[_foreground_mask(centre)].reshape(-1, 3)
    if len(pixels) < k:
        pixels = centre.reshape(-1, 3)

    km = KMeans(n_clusters=k, n_init=3, random_state=0).fit(pixels)
    counts = np.bincount(km.labels_, minlength=k)
    shares = counts / counts.sum()

    merged: Dict[str, dict] = {}  # merge clusters that map to the same colour name
    for centre_rgb, share in zip(km.cluster_centers_.astype(int), shares):
        n = name_colour(centre_rgb)
        if n in merged:
            merged[n]["share"] += float(share)
        else:
            merged[n] = {"name": n, "hex": "#%02x%02x%02x" % tuple(centre_rgb), "share": float(share)}
    out = sorted(merged.values(), key=lambda d: -d["share"])
    out = [d for d in out if d["share"] >= min_share] or out[:1]
    for d in out:
        d["share"] = round(d["share"], 3)
    return out


# --------------------------------------------------------------------------
# 3. CLIP CLASSIFIER
# --------------------------------------------------------------------------
class ClipTagger:
    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str | None = None):
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.torch = torch
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        log.info("Loading %s on %s", model_name, self.device)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device).eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)

        # text side is encoded ONCE and cached - this is the key speed trick
        self.clothing_emb = self._encode_labels(CLOTHING_LABELS, CLOTHING_TEMPLATES)
        self.pattern_emb = self._encode_labels(PATTERN_LABELS, PATTERN_TEMPLATES)

    def _text_feats(self, toks):
        out = self.model.text_model(input_ids=toks["input_ids"],
                                    attention_mask=toks.get("attention_mask"))
        return self.model.text_projection(out.pooler_output)

    def _image_feats(self, pixel_values):
        out = self.model.vision_model(pixel_values=pixel_values)
        return self.model.visual_projection(out.pooler_output)

    def _encode_labels(self, labels: List[str], templates: List[str]):
        torch = self.torch
        embs = []
        with torch.no_grad():
            for lab in labels:
                toks = self.processor(text=[t.format(lab) for t in templates],
                                      return_tensors="pt", padding=True).to(self.device)
                e = self._text_feats(toks)
                e = e / e.norm(dim=-1, keepdim=True)
                e = e.mean(dim=0)
                embs.append(e / e.norm())
        return torch.stack(embs)

    def classify(self, images: List[Image.Image], top_k: int = 3) -> List[dict]:
        torch = self.torch
        inputs = self.processor(images=images, return_tensors="pt").to(self.device)
        with torch.no_grad():
            f = self._image_feats(inputs["pixel_values"])
            f = f / f.norm(dim=-1, keepdim=True)
            scale = self.model.logit_scale.exp()
            c_prob = (scale * f @ self.clothing_emb.T).softmax(dim=-1).cpu().numpy()
            p_prob = (scale * f @ self.pattern_emb.T).softmax(dim=-1).cpu().numpy()

        results = []
        for cp, pp in zip(c_prob, p_prob):
            order = np.argsort(-cp)[:top_k]
            p_best = int(np.argmax(pp))
            p_name = PATTERN_LABELS[p_best]
            results.append({
                "clothing_type": CLOTHING_LABELS[order[0]],
                "clothing_confidence": round(float(cp[order[0]]), 4),
                "clothing_top_k": [(CLOTHING_LABELS[i], round(float(cp[i]), 4)) for i in order],
                "pattern": PATTERN_DISPLAY.get(p_name, p_name),
                "pattern_confidence": round(float(pp[p_best]), 4),
            })
        return results


# --------------------------------------------------------------------------
# 4. BATCH PIPELINE + EXPORT
# --------------------------------------------------------------------------
@dataclass
class ImageTag:
    image_id: str
    path: str
    clothing_type: str = ""
    clothing_confidence: float = 0.0
    clothing_top_k: list = field(default_factory=list)
    pattern: str = ""
    pattern_confidence: float = 0.0
    primary_colour: str = ""
    colours: list = field(default_factory=list)
    needs_review: bool = False
    status: str = "ok"
    error: str = ""
    processed_at: str = ""


def list_images(folder: Path) -> List[Path]:
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in IMAGE_EXTS)


def run_pipeline(input_dir: Path, output_dir: Path, batch_size: int = 16,
                 model_name: str = "openai/clip-vit-base-patch32",
                 review_threshold: float = 0.35, sqlite: bool = True) -> List[ImageTag]:
    from tqdm import tqdm

    output_dir.mkdir(parents=True, exist_ok=True)
    paths = list_images(input_dir)
    log.info("Found %d images", len(paths))
    tagger = ClipTagger(model_name)
    tags: List[ImageTag] = []

    for i in tqdm(range(0, len(paths), batch_size), desc="batches"):
        batch_paths = paths[i:i + batch_size]
        loaded, ok_paths = [], []
        for p in batch_paths:                       # one bad file must not kill the batch
            try:
                loaded.append(Image.open(p).convert("RGB"))
                ok_paths.append(p)
            except Exception as e:                  # noqa: BLE001
                tags.append(ImageTag(p.stem, str(p), status="error", error=str(e),
                                     processed_at=datetime.now().isoformat(timespec="seconds")))
        if not loaded:
            continue

        for p, img, res in zip(ok_paths, loaded, tagger.classify(loaded)):
            try:
                cols = extract_colours(img)
                tags.append(ImageTag(
                    image_id=p.stem, path=str(p), **res,
                    primary_colour=cols[0]["name"], colours=cols,
                    needs_review=res["clothing_confidence"] < review_threshold,
                    processed_at=datetime.now().isoformat(timespec="seconds")))
            except Exception as e:                  # noqa: BLE001
                tags.append(ImageTag(p.stem, str(p), status="error", error=str(e)))

    export(tags, output_dir, sqlite)
    return tags


def export(tags: List[ImageTag], out: Path, sqlite: bool = True) -> None:
    import pandas as pd

    rows = [asdict(t) for t in tags]
    (out / "image_tags.json").write_text(json.dumps(rows, indent=2))

    flat = []
    for r in rows:                                   # CSV-friendly flat version
        f = dict(r)
        f["colours"] = ";".join(f"{c['name']}:{c['share']}" for c in r["colours"])
        f["clothing_top_k"] = ";".join(f"{n}:{p}" for n, p in r["clothing_top_k"])
        flat.append(f)
    df = pd.DataFrame(flat)
    df.to_csv(out / "image_tags.csv", index=False)

    if sqlite:
        with sqlite3.connect(out / "fashion.db") as con:
            df.to_sql("image_tags", con, if_exists="replace", index=False)
    log.info("Exported %d rows to %s", len(df), out)


# --------------------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="CLIP clothing/pattern/colour tagger")
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", default=Path("results"), type=Path)
    ap.add_argument("--batch-size", default=16, type=int)
    ap.add_argument("--model", default="openai/clip-vit-base-patch32")
    ap.add_argument("--review-threshold", default=0.35, type=float)
    args = ap.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    run_pipeline(args.input, args.output, args.batch_size, args.model, args.review_threshold)
