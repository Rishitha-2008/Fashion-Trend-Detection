
import sqlite3
import pandas as pd
from dotenv import load_dotenv
from google import genai

# Load Gemini API key
load_dotenv()
client = genai.Client()

# Read actual image data from SQLite
connection = sqlite3.connect("fashion.db")

df = pd.read_sql_query(
    """
    SELECT clothing_type, pattern, primary_colour
    FROM image_tags
    WHERE clothing_type != ''
    """,
    connection
)

connection.close()

if df.empty:
    print("No fashion data available!")
else:
    # Calculate trend popularity
    trends = (
        df.groupby(["clothing_type", "pattern"])
        .size()
        .reset_index(name="image_count")
    )

    trends["popularity_score"] = (
        trends["image_count"] / len(df) * 100
    ).round(2)

    trend_data = trends.to_string(index=False)

    # Ask Gemini to analyse the actual results
    prompt = f"""
    You are a fashion trend analyst.

    Analyse these fashion trends detected from our dataset:

    {trend_data}

    Explain:
    1. Which fashion trend is most popular?
    2. Why might this trend appeal to customers?
    3. What suggestions would you give fashion businesses?

    Mention that these results are based on our analysed dataset.
    Do not claim they represent the entire fashion market.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    print("\nFASHION TREND ANALYSIS\n")
    print(response.text)

    client.close()
