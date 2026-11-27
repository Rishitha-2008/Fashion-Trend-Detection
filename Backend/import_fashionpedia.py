
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

csv_path = (
    BASE_DIR.parent
    / "dataset_analysis"
    / "fashionpedia_final_results.csv"
)

db_path = BASE_DIR / "fashion.db"

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

imported = 0
skipped = 0

with open(csv_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        image_id = row["image_id"].strip()

        if not image_id:
            skipped += 1
            continue

        cursor.execute("""
            INSERT OR IGNORE INTO fashionpedia_results
            (image_id, clothing_type, pattern, image_colour, clothing_colour)
            VALUES (?, ?, ?, ?, ?)
        """, (
            image_id,
            row["clothing_type"],
            row["pattern"],
            row["colour"],
            row["clothing_colour"]
        ))

        if cursor.rowcount == 1:
            imported += 1
        else:
            skipped += 1

connection.commit()
connection.close()

print(f"Successfully imported: {imported}")
print(f"Skipped duplicate/invalid records: {skipped}")
