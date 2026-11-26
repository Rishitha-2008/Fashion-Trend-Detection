# Image Tagging Module (Member 2)

Tags each fashion image with clothing type, pattern and colours using CLIP (zero-shot) + k-means.

## Files
- `image_tagger.py`: the module (CLIP classification, colour detection, batch processing, export)
- `fashionpedia_eval.py`: builds a labelled test set from Fashionpedia and scores accuracy
- `results/image_tags.csv`, `image_tags.json`, `fashion.db`: sample output on 150 test crops

## Setup
```
pip install torch torchvision transformers pillow scikit-learn numpy pandas tqdm
```

## Run
```
python image_tagger.py --input ./your_images --output ./results --batch-size 8
```
First run downloads the CLIP model (~600 MB). Works on CPU (about 2 s per batch of 8).
Optional: `--model openai/clip-vit-base-patch16`.

## Output (one row per image)
| Column | Meaning |
|---|---|
| image_id, path | file name and path |
| clothing_type, clothing_confidence | predicted category and its probability |
| clothing_top_k | top 3 guesses (`label:prob;...`) |
| pattern, pattern_confidence | solid, striped, checked, floral, etc. |
| primary_colour | most dominant named colour |
| colours | all colours with share, e.g. `navy:0.69;yellow:0.28` |
| needs_review | True if clothing confidence < 0.35 |
| status, error | `ok` or `error` (bad files are skipped, not fatal) |
| processed_at | timestamp |

SQLite: `results/fashion.db`, table `image_tags` (same columns).

## Evaluate (Fashionpedia validation set)
```
python fashionpedia_eval.py prepare --images ./val_test2020/test --ann ./instances_attributes_val2020.json --out ./crops --per-class 15
python image_tagger.py --input ./crops --output ./results
python fashionpedia_eval.py score --csv ./results/image_tags.csv
```
Result: **54.7% accuracy** on 150 garment crops, 10 classes (random guess is about 10%).
Best: pants 80%. Weakest: jumpsuit 20%, jacket 40%.
Common confusions: skirt/dress, shirt/jacket/top.

## Known limits
- One label per image (no multi-garment detection)
- Colour can include background or skin
- Similar categories overlap

## Next steps
- Skip images already in the DB (needed for the 3-day scheduler)
- Detect or segment each garment before classifying
- Fine-tune CLIP on Fashionpedia
- Edit `CLOTHING_LABELS` / `PATTERN_LABELS` at the top of `image_tagger.py`
