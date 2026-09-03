"""דיבוג חד-פעמי - מציג את השגיאה האמיתית במקום לבלוע אותה."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

key = os.environ.get("GEMINI_API_KEY")
print("key found:", bool(key), "| length:", len(key) if key else 0)

from google import genai
client = genai.Client(api_key=key)

print("\n--- available models ---")
try:
    for m in client.models.list():
        print(m.name)
except Exception as e:
    print("list failed:", type(e).__name__, e)

print("\n--- test call ---")
try:
    r = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Say OK",
    )
    print("response:", r.text)
except Exception as e:
    print("call failed:", type(e).__name__, e)
    