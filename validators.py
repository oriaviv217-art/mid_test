"""פונקציות אימות (Validation) משותפות לשדות הקלט בכל המערכת.

כל פונקציה מחזירה זוג (is_valid, error_or_value):
- אם התקינות עברה: (True, None) או (True, הערך המפוענח - למשל אובייקט date)
- אם התקינות נכשלה: (False, הודעת השגיאה בעברית)
"""

import re
from datetime import date, datetime

_NAME_PATTERN = re.compile(r"^[א-תa-zA-Z][א-תa-zA-Z '\-\.]{1,99}$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_name(name):
    """שם מלא: שדה חובה, 2-100 תווים, אותיות (עברית/אנגלית), רווחים, גרש ומקף בלבד."""
    if not name or not name.strip():
        return False, "יש להזין שם מלא"
    if not _NAME_PATTERN.match(name.strip()):
        return False, "שם לא תקין - יש להזין אותיות בלבד (2 עד 100 תווים)"
    return True, None


def validate_phone(phone):
    """טלפון: שדה אופציונלי. אם הוזן - חייב להכיל 9-10 ספרות ולהתחיל ב-0."""
    if not phone or not str(phone).strip():
        return True, None
    digits_only = str(phone).strip().replace("-", "").replace(" ", "")
    if not digits_only.isdigit() or not digits_only.startswith("0") or not (9 <= len(digits_only) <= 10):
        return False, "מספר טלפון לא תקין (לדוגמה: 050-1234567)"
    return True, None


def validate_email(email):
    """אימייל: שדה אופציונלי. אם הוזן - חייב להיות בפורמט תקין."""
    if not email or not str(email).strip():
        return True, None
    if not _EMAIL_PATTERN.match(str(email).strip()):
        return False, "כתובת אימייל לא תקינה"
    return True, None


def validate_required_text(value, field_label, max_length=200):
    """שדה טקסט חובה: לא ריק ולא ארוך מדי."""
    if not value or not str(value).strip():
        return False, f"יש להזין {field_label}"
    if len(str(value).strip()) > max_length:
        return False, f"{field_label} ארוך מדי (מקסימום {max_length} תווים)"
    return True, None


def validate_date(value):
    """תאריך תקין בפורמט YYYY-MM-DD."""
    try:
        return True, date.fromisoformat(value)
    except (TypeError, ValueError):
        return False, "תאריך לא תקין"


def validate_not_past_date(value):
    """תאריך תקין שאינו קודם להיום."""
    is_valid, result = validate_date(value)
    if not is_valid:
        return False, result
    if result < date.today():
        return False, "לא ניתן להזין תאריך שכבר עבר"
    return True, None


def validate_time(value):
    """שעה תקינה בפורמט HH:MM."""
    try:
        datetime.strptime(value, "%H:%M")
        return True, None
    except (TypeError, ValueError):
        return False, "שעה לא תקינה (פורמט: HH:MM)"


def validate_amount(value):
    """סכום כספי: מספר תקין הגדול מאפס."""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return False, "סכום לא תקין"
    if amount <= 0:
        return False, "הסכום חייב להיות גדול מאפס"
    return True, None
