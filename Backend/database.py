
import sqlite3


def get_connection():
    connection = sqlite3.connect("fashion.db")
    connection.row_factory = sqlite3.Row
    return connection


def create_tables():

    connection = get_connection()
    cursor = connection.cursor()

    # MEMBER 2: Image tagging results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            image_id TEXT,
            clothing_type TEXT,
            pattern TEXT,
            primary_colour TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Fashion trend detection results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS trends (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trend_name TEXT,
            popularity_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # MEMBER 1: Fashionpedia dataset results
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fashionpedia_results (
            image_id TEXT PRIMARY KEY,
            clothing_type TEXT,
            pattern TEXT,
            image_colour TEXT,
            clothing_colour TEXT
        )
    """)

    # MEMBER 3: Full H&M sales data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hm_sales (
            dimension TEXT,
            label TEXT,
            sales_count INTEGER,
            PRIMARY KEY (dimension, label)
        )
    """)

    # MEMBER 3: Monthly H&M sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hm_monthly_sales (
            dimension TEXT,
            month TEXT,
            label TEXT,
            purchase_records INTEGER,
            PRIMARY KEY (dimension, month, label)
        )
    """)

    # MEMBER 3: Monthly growth percentages
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hm_monthly_growth (
            dimension TEXT,
            month TEXT,
            label TEXT,
            growth_percentage REAL,
            PRIMARY KEY (dimension, month, label)
        )
    """)

    # MEMBER 3: Image vs H&M comparisons
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hm_comparisons (
            dimension TEXT,
            label TEXT,
            image_percentage REAL,
            sales_percentage REAL,
            PRIMARY KEY (dimension, label)
        )
    """)

    # MEMBER 3: Popularity scores
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hm_popularity_scores (
            dimension TEXT,
            label TEXT,
            popularity_score REAL,
            PRIMARY KEY (dimension, label)
        )
    """)

    connection.commit()
    connection.close()

    print("All project database tables created successfully!")


