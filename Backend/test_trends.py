import requests

url = "http://127.0.0.1:5000/api/trends"

data = {
    "trend_name": "Floral Dresses",
    "popularity_score": 85.5
}

response = requests.post(url, json=data)

print("Status:", response.status_code)
print("Response:", response.text)