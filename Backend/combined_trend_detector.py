
import sqlite3
import pandas as pd

connection = sqlite3.connect("fashion.db")


# CLEAN CLOTHING CATEGORY NAMES
def clean_category(value):
    value = str(value).lower().strip()

    categories = [
        "trousers", "dress", "sweater", "jacket",
        "shirt", "skirt", "blouse", "shorts",
        "t-shirt", "top", "coat", "hoodie"
    ]

    for category in categories:
        if category in value:
            return category

    return value


# CLEAN PATTERN NAMES
def clean_pattern(value):
    value = str(value).lower().strip()

    if "polka dot" in value or "polka-dot" in value:
        return "dot"

    if "floral" in value:
        return "all over pattern"

    if "striped" in value or "stripe" in value:
        return "stripe"

    if "checked" in value or "check" in value:
        return "check"

    if "solid" in value or "plain" in value:
        return "solid"

    return value


try:

    # STEP 1: READ FASHIONPEDIA DATA
    images = pd.read_sql_query("""
        SELECT clothing_type, pattern
        FROM fashionpedia_results
    """, connection)

    # STEP 2: READ H&M SALES DATA
    hm_categories = pd.read_sql_query("""
        SELECT label, sales_count
        FROM hm_sales
        WHERE dimension = 'category'
    """, connection)

    hm_patterns = pd.read_sql_query("""
        SELECT label, sales_count
        FROM hm_sales
        WHERE dimension = 'pattern'
    """, connection)

    if images.empty or hm_categories.empty or hm_patterns.empty:
        raise ValueError("Required dataset is missing.")

    print("Fashionpedia records:", len(images))

    # STEP 3: CLEAN FASHIONPEDIA CATEGORIES
    images["category"] = (
        images["clothing_type"].apply(clean_category)
    )

    image_categories = (
        images.groupby("category")
        .size()
        .reset_index(name="image_count")
    )

    image_categories["image_percentage"] = (
        image_categories["image_count"] / len(images) * 100
    )

    # STEP 4: CLEAN AND COMBINE H&M CATEGORIES
    hm_categories["category"] = (
        hm_categories["label"].apply(clean_category)
    )

    hm_categories = (
        hm_categories.groupby("category", as_index=False)
        ["sales_count"].sum()
    )

    total_category_sales = hm_categories["sales_count"].sum()

    hm_categories["sales_percentage"] = (
        hm_categories["sales_count"] /
        total_category_sales * 100
    )

    # STEP 5: MATCH CLOTHING CATEGORIES
    category_results = pd.merge(
        image_categories,
        hm_categories[["category", "sales_percentage"]],
        on="category",
        how="inner"
    )

    # STEP 6: CLEAN FASHIONPEDIA PATTERNS
    images["matched_pattern"] = (
        images["pattern"].apply(clean_pattern)
    )

    image_patterns = (
        images.groupby("matched_pattern")
        .size()
        .reset_index(name="image_count")
    )

    image_patterns["image_percentage"] = (
        image_patterns["image_count"] / len(images) * 100
    )

    # STEP 7: CLEAN AND COMBINE H&M PATTERNS
    hm_patterns["matched_pattern"] = (
        hm_patterns["label"].apply(clean_pattern)
    )

    hm_patterns = (
        hm_patterns.groupby("matched_pattern", as_index=False)
        ["sales_count"].sum()
    )

    total_pattern_sales = hm_patterns["sales_count"].sum()

    hm_patterns["sales_percentage"] = (
        hm_patterns["sales_count"] /
        total_pattern_sales * 100
    )

    # STEP 8: MATCH PATTERNS
    pattern_results = pd.merge(
        image_patterns,
        hm_patterns[["matched_pattern", "sales_percentage"]],
        on="matched_pattern",
        how="inner"
    )

    # STEP 9: CALCULATE COMBINED POPULARITY SCORES
    for df in [category_results, pattern_results]:

        df["combined_score"] = (
            df["image_percentage"] * 0.5
            + df["sales_percentage"] * 0.5
        ).round(2)

        df["image_percentage"] = (
            df["image_percentage"].round(2)
        )

        df["sales_percentage"] = (
            df["sales_percentage"].round(2)
        )

    # STEP 10: CREATE DATABASE TABLE
    connection.execute("""
        CREATE TABLE IF NOT EXISTS combined_trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dimension TEXT,
            trend_name TEXT,
            image_percentage REAL,
            sales_percentage REAL,
            combined_score REAL,
            UNIQUE(dimension, trend_name)
        )
    """)

    # DELETE ONLY OLD COMBINED RESULTS
    connection.execute("DELETE FROM combined_trends")

    # STEP 11: SAVE CATEGORY RESULTS
    for _, row in category_results.iterrows():

        connection.execute("""
            INSERT INTO combined_trends
            (dimension, trend_name, image_percentage,
             sales_percentage, combined_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "category",
            row["category"],
            float(row["image_percentage"]),
            float(row["sales_percentage"]),
            float(row["combined_score"])
        ))

    # STEP 12: SAVE PATTERN RESULTS
    for _, row in pattern_results.iterrows():

        connection.execute("""
            INSERT INTO combined_trends
            (dimension, trend_name, image_percentage,
             sales_percentage, combined_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            "pattern",
            row["matched_pattern"],
            float(row["image_percentage"]),
            float(row["sales_percentage"]),
            float(row["combined_score"])
        ))

    connection.commit()

    # STEP 13: DISPLAY RESULTS
    print("\nCATEGORY COMBINED TRENDS\n")

    if not category_results.empty:
        print(
            category_results.sort_values(
                "combined_score", ascending=False
            ).to_string(index=False)
        )
    else:
        print("No matching categories found.")

    print("\nPATTERN COMBINED TRENDS\n")

    if not pattern_results.empty:
        print(
            pattern_results.sort_values(
                "combined_score", ascending=False
            ).to_string(index=False)
        )
    else:
        print("No matching patterns found.")

    total_records = len(category_results) + len(pattern_results)

    print("\nCombined trends saved successfully!")
    print("Total combined records:", total_records)

except Exception as error:

    connection.rollback()
    print("\nError:", error)

finally:
    connection.close()

