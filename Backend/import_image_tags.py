
import csv
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

csv_path = BASE_DIR.parent / "image_tagging" / "results" / "image_tags.csv"
db_path = BASE_DIR / "fashion.db"

connection = sqlite3.connect(db_path)
cursor = connection.cursor()

imported = 0
skipped = 0

with open(csv_path, "r", encoding="utf-8", newline="") as file:
    reader = csv.DictReader(file)

    for row in reader:
        if row["status"] != "ok":
            skipped += 1
            continue

        # Check whether this image already exists
        existing = cursor.execute(
            "SELECT 1 FROM image_tags WHERE image_id = ?",
            (row["image_id"],)
        ).fetchone()

        if existing:
            skipped += 1
            continue

        cursor.execute("""
            INSERT INTO image_tags
            (image_id, clothing_type, pattern, primary_colour)
            VALUES (?, ?, ?, ?)
        """, (
            row["image_id"],
            row["clothing_type"],
            row["pattern"],
            row["primary_colour"]
        ))

        imported += 1

connection.commit()
connection.close()

print(f"Successfully imported: {imported}")
print(f"Skipped existing/invalid records: {skipped}")

