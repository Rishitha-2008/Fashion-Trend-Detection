import requests

url = "http://127.0.0.1:5000/api/trends"

# Test 1: Valid data
valid_data = {
    "trend_name": "Summer Fashion",
    "popularity_score": 90
}

response = requests.post(url, json=valid_data)
print("Valid data:", response.status_code, response.text)


# Test 2: Invalid popularity score
invalid_data = {
    "trend_name": "Winter Fashion",
    "popularity_score": 150
}

response = requests.post(url, json=invalid_data)
print("Invalid data:", response.status_code, response.text)