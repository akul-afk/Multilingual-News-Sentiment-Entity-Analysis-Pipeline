import os
from google import genai
from google.genai import types

api_key = "AIzaSyC8tnSxP_Fp0OtJwGbUBrrdNRUret48fCs"
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents="Say hello"
    )
    print("SUCCESS:", response.text)
except Exception as e:
    print("FAILED:", e)
