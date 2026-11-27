
import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("Gemini API key not found in .env file!")

# Connect to Gemini
client = genai.Client(api_key=api_key)

# Send a test prompt
response = client.models.generate_content(
    model="gemini-3.5-flash-lite",
    contents="Explain in two sentences why floral dresses might become a fashion trend."
)

print("\nGEMINI RESPONSE:\n")
print(response.text)

client.close()
