
import sqlite3
import pandas as pd


# Connect to project database
connection = sqlite3.connect("fashion.db")


def clean_clothing_type(value):
    """Convert long clothing descriptions into simple labels."""

    value = str(value).lower()

    clothing_types = [
        "jumpsuit", "trousers", "leggings", "cardigan",
        "sweater", "jacket", "blazer", "coat",
        "dress", "skirt", "shorts", "jeans",
        "shirt", "blouse", "hoodie", "t-shirt",
        "top", "vest", "suit"
    ]

    for clothing_type in clothing_types:
        if clothing_type in value:
            return clothing_type

    return value.strip()


def clean_pattern(value):
    """Convert pattern descriptions into simple labels."""

    value = str(value).lower()

    patterns = {
        "polka dot": ["polka dot", "polka-dot"],
        "floral": ["floral"],
        "striped": ["striped", "stripe"],
        "checked": ["checked", "check"],
        "solid": ["solid", "plain"]
    }

    for pattern, keywords in patterns.items():
        if any(word in value for word in keywords):
            return pattern

    return value.strip()


try:
    # Read Member 1's Fashionpedia dataset
    df = pd.read_sql_query(
        """
        SELECT clothing_type, pattern, clothing_colour
        FROM fashionpedia_results
        """,
        connection
    )

    if df.empty:
        print("No Fashionpedia data available.")

    else:
        # Clean clothing types and patterns
        df["clothing_type"] = df["clothing_type"].apply(
            clean_clothing_type
        )

        df["pattern"] = df["pattern"].apply(
            clean_pattern
        )

        df["clothing_colour"] = (
            df["clothing_colour"]
            .fillna("")
            .str.strip()
            .str.lower()
        )

        # Remove incomplete records
        df = df[
            (df["clothing_type"] != "") &
            (df["pattern"] != "")
        ]

        total_images = len(df)

        print("\nTOTAL FASHIONPEDIA IMAGES:", total_images)

        # Calculate clothing type + pattern trends
        combination_trends = (
            df.groupby(["clothing_type", "pattern"])
            .size()
            .reset_index(name="image_count")
        )

        combination_trends["popularity_score"] = (
            combination_trends["image_count"] /
            total_images * 100
        ).round(2)

        combination_trends = combination_trends.sort_values(
            by="popularity_score",
            ascending=False
        )

        # Calculate individual distributions
        type_trends = (
            df.groupby("clothing_type")
            .size()
            .reset_index(name="image_count")
        )

        pattern_trends = (
            df.groupby("pattern")
            .size()
            .reset_index(name="image_count")
        )

        colour_trends = (
            df[df["clothing_colour"] != ""]
            .groupby("clothing_colour")
            .size()
            .reset_index(name="image_count")
        )

        for trend_df in [type_trends, pattern_trends, colour_trends]:
            trend_df["popularity_score"] = (
                trend_df["image_count"] /
                total_images * 100
            ).round(2)

        # Display results
        print("\nCLOTHING TYPE + PATTERN TRENDS\n")
        print(combination_trends.to_string(index=False))

        print("\nCLOTHING TYPE DISTRIBUTION\n")
        print(type_trends.to_string(index=False))

        print("\nPATTERN DISTRIBUTION\n")
        print(pattern_trends.to_string(index=False))

        print("\nCLOTHING COLOUR DISTRIBUTION\n")
        print(colour_trends.to_string(index=False))

        # Remove previously calculated trends
        connection.execute("DELETE FROM trends")

        # Save combination trends
        for _, row in combination_trends.iterrows():
            trend_name = (
                f"{row['pattern']} {row['clothing_type']}"
            )

            connection.execute(
                """
                INSERT INTO trends (trend_name, popularity_score)
                VALUES (?, ?)
                """,
                (trend_name, float(row["popularity_score"]))
            )

        # Save individual clothing type trends
        for _, row in type_trends.iterrows():
            connection.execute(
                """
                INSERT INTO trends (trend_name, popularity_score)
                VALUES (?, ?)
                """,
                (
                    f"Type: {row['clothing_type']}",
                    float(row["popularity_score"])
                )
            )

        # Save individual pattern trends
        for _, row in pattern_trends.iterrows():
            connection.execute(
                """
                INSERT INTO trends (trend_name, popularity_score)
                VALUES (?, ?)
                """,
                (
                    f"Pattern: {row['pattern']}",
                    float(row["popularity_score"])
                )
            )

        # Save clothing colour trends
        for _, row in colour_trends.iterrows():
            connection.execute(
                """
                INSERT INTO trends (trend_name, popularity_score)
                VALUES (?, ?)
                """,
                (
                    f"Colour: {row['clothing_colour']}",
                    float(row["popularity_score"])
                )
            )

        connection.commit()

        print("\nAll Fashionpedia trends saved successfully!")

finally:
    connection.close()
