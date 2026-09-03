"""
שכבת NLU: מקבלת משפט חופשי ומחזירה JSON קבוע.
זו חילוץ מידע (extraction), לא שיחה - Gemini לא מחליט כלום.
אם משהו נכשל, מחזירה None והבוט נופל חזרה על חילוץ בקוד.
"""
import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

# טוען את chatbot/.env - שם יושב המפתח, והוא לא נכנס לגיט
load_dotenv(Path(__file__).resolve().parent / ".env")

MODEL = "gemini-3.6-flash"

PROMPT = """אתה מחלץ מידע ממשפט בעברית. החזר JSON בלבד, בלי טקסט לפני או אחרי, בלי סימוני קוד.

הפורמט המדויק:
{"name": null, "claimed_date": null}

כללים:
- name: השם הפרטי או המלא שהמשתמש מזהה בו את עצמו. אם אין - null.
- claimed_date: התאריך שהמשתמש טוען לו, בפורמט YYYY-MM-DD בלבד. אם אין - null.
- אל תמציא ערכים. אם המידע לא מופיע במשפט - null.
- אל תחזיר שום שדה נוסף.

המשפט:
"""


def _get_client():
    """יוצר לקוח Gemini. מחזיר None אם אין מפתח או שהספרייה חסרה."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def safe_parse(raw_text):
    """
    מנקה ומפרסר את התשובה של המודל.
    מחזיר dict עם name ו-claimed_date, או None אם הפרסור נכשל.
    """
    if not raw_text:
        return None

    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()

    # אם יש טקסט מסביב - לוקחים רק את הסוגריים המסולסלים
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        return None
    text = text[start:end + 1]

    try:
        data = json.loads(text)
    except Exception:
        return None

    if not isinstance(data, dict):
        return None

    name = data.get("name")
    claimed = data.get("claimed_date")

    # אימות פורמט התאריך בקוד - לא סומכים על המודל
    if claimed is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(claimed)):
            claimed = None

    return {
        "name": str(name).strip() if name else None,
        "claimed_date": claimed,
    }


def extract(text):
    """
    "קוראים לי רותם ויש לי תור ב-18.01.2027"
    ->  {"name": "רותם", "claimed_date": "2027-01-18"}
    מחזיר None אם ה-NLU לא זמין או נכשל.
    """
    client = _get_client()
    if client is None:
        return None

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=PROMPT + text,
        )
        return safe_parse(response.text)
    except Exception:
        return None