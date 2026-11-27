from database import get_connection

connection = get_connection()

tables = [
    "hm_sales",
    "hm_monthly_sales",
    "hm_monthly_growth",
    "hm_comparisons",
    "hm_popularity_scores"
]

for table in tables:
    result = connection.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()

    print(table, ":", result[0], "records")

connection.close()