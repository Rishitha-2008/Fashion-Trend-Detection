
import sqlite3
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR.parent / "member3_analysis" / "outputs"
DB_PATH = BASE_DIR / "fashion.db"

connection = sqlite3.connect(DB_PATH)


def import_full_sales(filename, dimension):
    df = pd.read_csv(OUTPUT_DIR / filename)

    for _, row in df.iterrows():
        connection.execute("""
            INSERT OR REPLACE INTO hm_sales
            (dimension, label, sales_count)
            VALUES (?, ?, ?)
        """, (
            dimension,
            str(row.iloc[0]),
            int(row.iloc[1])
        ))

    print(f"Imported {len(df)} {dimension} sales records")


def import_monthly_sales(filename, dimension):
    df = pd.read_csv(OUTPUT_DIR / filename)

    for _, row in df.iterrows():
        connection.execute("""
            INSERT OR REPLACE INTO hm_monthly_sales
            (dimension, month, label, purchase_records)
            VALUES (?, ?, ?, ?)
        """, (
            dimension,
            str(row["month"]),
            str(row.iloc[1]),
            int(row.iloc[2])
        ))

    print(f"Imported {len(df)} monthly {dimension} records")


def import_monthly_growth(filename, dimension):
    df = pd.read_csv(OUTPUT_DIR / filename)

    melted = df.melt(
        id_vars=["month"],
        var_name="label",
        value_name="growth_percentage"
    )

    melted = melted.dropna(subset=["growth_percentage"])

    for _, row in melted.iterrows():
        connection.execute("""
            INSERT OR REPLACE INTO hm_monthly_growth
            (dimension, month, label, growth_percentage)
            VALUES (?, ?, ?, ?)
        """, (
            dimension,
            str(row["month"]),
            str(row["label"]),
            float(row["growth_percentage"])
        ))

    print(f"Imported {len(melted)} monthly {dimension} growth records")


def import_comparison(filename, dimension):
    df = pd.read_csv(OUTPUT_DIR / filename)

    for _, row in df.iterrows():
        connection.execute("""
            INSERT OR REPLACE INTO hm_comparisons
            (dimension, label, image_percentage, sales_percentage)
            VALUES (?, ?, ?, ?)
        """, (
            dimension,
            str(row["label"]),
            float(row["image_percentage"]),
            float(row["sales_percentage"])
        ))

    print(f"Imported {len(df)} {dimension} comparison records")


def import_popularity(filename, dimension):
    df = pd.read_csv(OUTPUT_DIR / filename)

    label_column = df.columns[0]
    score_column = df.columns[-1]

    for _, row in df.iterrows():
        try:
            score = float(row[score_column])
            label = str(row[label_column])

            connection.execute("""
                INSERT OR REPLACE INTO hm_popularity_scores
                (dimension, label, popularity_score)
                VALUES (?, ?, ?)
            """, (dimension, label, score))

        except (ValueError, TypeError):
            continue

    print(f"Imported {len(df)} {dimension} popularity records")


try:
    # Full sales data
    import_full_sales("full_category_sales.csv", "category")
    import_full_sales("full_colour_sales.csv", "colour")
    import_full_sales("full_pattern_sales.csv", "pattern")

    # Monthly sales data
    import_monthly_sales("monthly_category_sales.csv", "category")
    import_monthly_sales("monthly_colour_sales.csv", "colour")
    import_monthly_sales("monthly_pattern_sales.csv", "pattern")

    # Monthly growth data
    import_monthly_growth("monthly_category_growth.csv", "category")
    import_monthly_growth("monthly_colour_growth.csv", "colour")
    import_monthly_growth("monthly_pattern_growth.csv", "pattern")

    # Final image vs H&M comparisons
    import_comparison("final_category_comparison.csv", "category")
    import_comparison("final_colour_comparison.csv", "colour")
    import_comparison("final_pattern_comparison.csv", "pattern")

    # Popularity scores
    import_popularity("category_popularity_scores.csv", "category")
    import_popularity("colour_popularity_scores.csv", "colour")
    import_popularity("pattern_popularity_scores.csv", "pattern")

    connection.commit()
    print("\nH&M data imported successfully!")

except Exception as error:
    connection.rollback()
    print("\nImport failed:", error)

finally:
    connection.close()
