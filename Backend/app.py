
from flask import Flask, jsonify, request
from database import get_connection, create_tables
from flask_cors import CORS
import pandas as pd
from dotenv import load_dotenv
from google import genai

app = Flask(__name__)
CORS(app)
create_tables()

# Load Gemini API key from .env
load_dotenv()


@app.route("/")
def home():
    return "Fashion Trend Detection Backend is Running!"


# MEMBER 2: IMAGE TAGS API
@app.route("/api/image-tags", methods=["GET", "POST"])
def image_tags():

    if request.method == "POST":

        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "JSON data is required"}), 400

        fields = [
            "image_id",
            "clothing_type",
            "pattern",
            "primary_colour"
        ]

        for field in fields:
            if not isinstance(data.get(field), str) or not data[field].strip():
                return jsonify({"error": field + " is required"}), 400

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO image_tags
            (image_id, clothing_type, pattern, primary_colour)
            VALUES (?, ?, ?, ?)
        """, (
            data["image_id"],
            data["clothing_type"],
            data["pattern"],
            data["primary_colour"]
        ))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Image tag added successfully!"
        }), 201

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM image_tags")
    results = cursor.fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# MEMBER 1: FASHIONPEDIA DATASET API
@app.route("/api/fashionpedia", methods=["GET"])
def fashionpedia():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM fashionpedia_results
        ORDER BY image_id
    """)

    results = cursor.fetchall()
    connection.close()

    return jsonify([dict(row) for row in results])


# FASHION TRENDS API
@app.route("/api/trends", methods=["GET", "POST"])
def trends():

    if request.method == "POST":

        data = request.get_json(silent=True)

        if not data:
            return jsonify({"error": "JSON data is required"}), 400

        trend_name = data.get("trend_name")
        popularity_score = data.get("popularity_score")

        if not isinstance(trend_name, str) or not trend_name.strip():
            return jsonify({"error": "A valid trend name is required"}), 400

        if isinstance(popularity_score, bool):
            return jsonify({"error": "Popularity score must be a number"}), 400

        try:
            popularity_score = float(popularity_score)
        except (ValueError, TypeError):
            return jsonify({"error": "Popularity score must be a number"}), 400

        if not 0 <= popularity_score <= 100:
            return jsonify({
                "error": "Popularity score must be between 0 and 100"
            }), 400

        connection = get_connection()
        cursor = connection.cursor()

        cursor.execute("""
            INSERT INTO trends (trend_name, popularity_score)
            VALUES (?, ?)
        """, (trend_name.strip(), popularity_score))

        connection.commit()
        connection.close()

        return jsonify({
            "message": "Trend added successfully!"
        }), 201

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM trends")
    results = cursor.fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# GEMINI AI TREND ANALYSIS API

# GEMINI AI COMBINED TREND ANALYSIS API
@app.route("/api/ai-analysis", methods=["GET"])
def ai_analysis():

    try:
        connection = get_connection()

        results = connection.execute("""
            SELECT dimension, trend_name,
                   image_percentage, sales_percentage,
                   combined_score
            FROM combined_trends
            ORDER BY combined_score DESC
        """).fetchall()

        connection.close()

        if not results:
            return jsonify({
                "error": "No combined trend data available. Run combined_trend_detector.py first."
            }), 404

        trend_data = pd.DataFrame(
            [dict(row) for row in results]
        )

        trend_summary = trend_data.to_string(index=False)

        prompt = f"""
        You are an expert fashion trend analyst.

        Analyse the following combined fashion trend data.

        The data combines:
        1. Fashionpedia image analysis.
        2. Historical H&M sales data.

        Combined trend results:

        {trend_summary}

        The combined popularity score is calculated using:
        50% image percentage + 50% sales percentage.

        Explain in simple language:

        1. What are the top three fashion trends?
        2. Which clothing category is most popular?
        3. Which pattern is most popular?
        4. Which trends have stronger sales percentages
           compared with their image percentages?
        5. What recommendations would you give fashion businesses?
        6. What should businesses consider when planning
           their future collections?

        Important:
        - Use only the provided data.
        - Do not invent statistics.
        - Explain that these are exploratory results.
        - Do not claim they represent the entire fashion market.
        """

        client = genai.Client()

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=prompt
        )

        client.close()

        return jsonify({
            "message": "Combined fashion trend analysis generated successfully!",
            "analysis": response.text,
            "based_on": "Fashionpedia image analysis and historical H&M sales data"
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500

# MEMBER 3: H&M FULL SALES API
@app.route("/api/hm-sales", methods=["GET"])
def hm_sales():

    dimension = request.args.get("dimension")

    connection = get_connection()

    if dimension:
        results = connection.execute(
            "SELECT * FROM hm_sales WHERE dimension = ?",
            (dimension,)
        ).fetchall()
    else:
        results = connection.execute(
            "SELECT * FROM hm_sales"
        ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# MEMBER 3: H&M MONTHLY SALES API
@app.route("/api/hm-monthly-sales", methods=["GET"])
def hm_monthly_sales():

    dimension = request.args.get("dimension")

    connection = get_connection()

    if dimension:
        results = connection.execute(
            "SELECT * FROM hm_monthly_sales WHERE dimension = ?",
            (dimension,)
        ).fetchall()
    else:
        results = connection.execute(
            "SELECT * FROM hm_monthly_sales"
        ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# MEMBER 3: H&M MONTHLY GROWTH API
@app.route("/api/hm-growth", methods=["GET"])
def hm_growth():

    dimension = request.args.get("dimension")

    connection = get_connection()

    if dimension:
        results = connection.execute(
            "SELECT * FROM hm_monthly_growth WHERE dimension = ?",
            (dimension,)
        ).fetchall()
    else:
        results = connection.execute(
            "SELECT * FROM hm_monthly_growth"
        ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# MEMBER 3: IMAGE VS H&M COMPARISON API
@app.route("/api/hm-comparisons", methods=["GET"])
def hm_comparisons():

    dimension = request.args.get("dimension")

    connection = get_connection()

    if dimension:
        results = connection.execute(
            "SELECT * FROM hm_comparisons WHERE dimension = ?",
            (dimension,)
        ).fetchall()
    else:
        results = connection.execute(
            "SELECT * FROM hm_comparisons"
        ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])


# MEMBER 3: H&M POPULARITY SCORES API
@app.route("/api/hm-popularity", methods=["GET"])
def hm_popularity():

    dimension = request.args.get("dimension")

    connection = get_connection()

    if dimension:
        results = connection.execute(
            "SELECT * FROM hm_popularity_scores WHERE dimension = ?",
            (dimension,)
        ).fetchall()
    else:
        results = connection.execute(
            "SELECT * FROM hm_popularity_scores"
        ).fetchall()

    connection.close()

    return jsonify([dict(row) for row in results])

# COMBINED FASHION TRENDS API
@app.route("/api/combined-trends", methods=["GET"])
def get_combined_trends():

    connection = get_connection()

    try:
        results = connection.execute("""
            SELECT dimension, trend_name,
                   image_percentage, sales_percentage,
                   combined_score
            FROM combined_trends
            ORDER BY combined_score DESC
        """).fetchall()

        return jsonify({
            "total": len(results),
            "combined_trends": [dict(row) for row in results]
        })

    except Exception as error:
        return jsonify({"error": str(error)}), 500

    finally:
        connection.close()
if __name__ == "__main__":
    app.run(debug=True)
