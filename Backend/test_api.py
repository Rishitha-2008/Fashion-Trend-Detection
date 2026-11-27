import requests

url = "http://127.0.0.1:5000/api/image-tags"

data = {
    "image_id": "test001",
    "clothing_type": "dress",
    "pattern": "floral",
    "primary_colour": "blue"
}

response = requests.post(url, json=data)

print("Status:", response.status_code)
print("Response:", response.text)