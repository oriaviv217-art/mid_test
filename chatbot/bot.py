"""
מכונת המצבים של השיחה.
כל הודעה מטופלת לפי המצב הנוכחי, לא לפי ניחוש מהטקסט.
"""
import re
from datetime import date

import api_client
import nlu

SERVICE_TYPES = [
    "ייעוץ פנסיוני",
    "תכנון פיננסי",
    "ייעוץ השקעות",
    "בדיקת תיק ביטוח",
    "פגישת מעקב",
    "ייעוץ משכנתא",
]

# תשעת המצבים
START = "START"                       # אין מועמד
CLARIFY = "CLARIFY"                   # כמה התאמות, מחכים להבהרה
AWAIT_ID = "AWAIT_ID"                 # מועמד אחד, מחכים לתעודת זהות
VERIFIED = "VERIFIED"                 # אומת - ממתין לבקשה הבאה
BLOCKED = "BLOCKED"                   # נגמרו הניסיונות
AWAIT_NEW_SERVICE = "AWAIT_NEW_SERVICE"   # יצירת תור: מחכים לסוג שירות
AWAIT_NEW_DATE = "AWAIT_NEW_DATE"         # יצירת תור: מחכים לתאריך
AWAIT_NEW_TIME = "AWAIT_NEW_TIME"         # יצירת תור: מחכים לשעה
AWAIT_CANCEL_CHOICE = "AWAIT_CANCEL_CHOICE"  # ביטול: מחכים לבחירת התור

MAX_ATTEMPTS = 3


def new_state():
    """מצב התחלתי לשיחה חדשה."""
    return {
        "state": START,
        "candidates": [],
        "candidate_id": None,
        "candidate_name": None,
        "claimed_date": None,
        "attempts_left": MAX_ATTEMPTS,
        "appointments": [],
        "pending_service": None,
        "pending_date": None,
    }


def handle_message(user_text, state):
    """מקבל הודעה ומצב, מחזיר (תשובה, מצב מעודכן)."""
    current = state.get("state", START)

    if current == START:
        return _handle_start(user_text, state)
    if current == CLARIFY:
        return _handle_clarify(user_text, state)
    if current == AWAIT_ID:
        return _handle_await_id(user_text, state)
    if current == VERIFIED:
        return _handle_verified(user_text, state)
    if current == AWAIT_NEW_SERVICE:
        return _handle_new_service(user_text, state)
    if current == AWAIT_NEW_DATE:
        return _handle_new_date(user_text, state)
    if current == AWAIT_NEW_TIME:
        return _handle_new_time(user_text, state)
    if current == AWAIT_CANCEL_CHOICE:
        return _handle_cancel_choice(user_text, state)
    if current == BLOCKED:
        return "לא אוכל להמשיך בשיחה הזו. אנא פנה למשרד בטלפון.", state

    return "משהו השתבש. בוא נתחיל מחדש.", new_state()


# ---------- כלי עזר ----------

def _digits_only(text):
    """משאיר רק ספרות."""
    return "".join(ch for ch in str(text) if ch.isdigit())


def _extract_date(text):
    """מחלץ תאריך מטקסט חופשי ומחזיר אותו כ-YYYY-MM-DD, או None."""
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", text)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        return f"{year}-{int(month):02d}-{int(day):02d}"

    return None


def _extract_time(text):
    """מחלץ שעה מטקסט חופשי בפורמט HH:MM, או None."""
    m = re.search(r"(\d{1,2}):(\d{2})", text)
    if m:
        hour, minute = int(m.group(1)), m.group(2)
        if 0 <= hour <= 23:
            return f"{hour:02d}:{minute}"
    return None


def _strip_date_and_digits(text):
    """מוריד מהטקסט תאריכים ורצפי ספרות, כדי שיישאר רק השם."""
    text = re.sub(r"\d{4}-\d{2}-\d{2}", " ", text)
    text = re.sub(r"\d{1,2}[./]\d{1,2}[./]\d{4}", " ", text)
    text = re.sub(r"\d", " ", text)
    return " ".join(text.split())


def _pretty_date(iso_date):
    """2027-01-19  ->  19.01.2027"""
    parts = iso_date.split("-")
    if len(parts) != 3:
        return iso_date
    return f"{parts[2]}.{parts[1]}.{parts[0]}"


def _ask_for_id(state):
    """מנסח את בקשת תעודת הזהות. בלי שום פרט על התור."""
    return f"מצאתי אותך, {state['candidate_name']}. מה תעודת הזהות שלך? (לצורך אימות בלבד)"


def _pick_appointment(appointments):
    """בוחר את התור הרלוונטי: הקרוב ביותר בעתיד, ואם אין - האחרון שהיה."""
    active = [a for a in appointments if a.get("status") != "בוטל"]
    if not active:
        return None

    active.sort(key=lambda a: (a["appointment_date"], a["appointment_time"]))
    today = date.today().isoformat()

    for appt in active:
        if appt["appointment_date"] >= today:
            return appt

    return active[-1]


def _build_answer(state, appointments):
    """מנסח את התשובה הסופית, כולל תיקון אם המשתמש טעה בתאריך."""
    appt = _pick_appointment(appointments)

    if appt is None:
        return "האימות הצליח, אבל לא מצאתי לך תורים פתוחים במערכת."

    real_date = appt["appointment_date"]
    real_time = appt["appointment_time"]
    service = appt.get("service_type", "")
    claimed = state.get("claimed_date")

    base = f"התור שלך הוא ב-{_pretty_date(real_date)} בשעה {real_time}"
    if service:
        base += f" ({service})"

    if claimed and claimed != real_date:
        return (
            f"מצאתי אותך! שים לב: {base}, "
            f"ולא ב-{_pretty_date(claimed)} כפי שציינת."
        )

    return f"מצאתי אותך! {base}."


def _search_by_words(raw_name):
    """מחפש כל מילה בנפרד ומחזיר את ההתאמות. רשת ביטחון עד ששכבת ה-NLU תחלץ שם מדויק."""
    results = api_client.search_customers(raw_name)
    if results:
        return results

    seen = {}
    for word in raw_name.split():
        if len(word) < 3:
            continue
        for c in api_client.search_customers(word):
            seen[c["customer_id"]] = c
    return list(seen.values())


def _detect_intent(text):
    """מזהה כוונה גסה מתוך הטקסט: 'create', 'cancel', או 'show' (ברירת מחדל)."""
    t = text.strip()
    if any(word in t for word in ["בטל", "לבטל", "ביטול", "מחק"]):
        return "cancel"
    if any(word in t for word in ["קבע", "לקבוע", "תור חדש", "רוצה תור", "להזמין", "לקבל תור"]):
        return "create"
    return "show"


# ---------- טיפול לפי מצב ----------

def _handle_start(text, state):
    """מחפש לקוח לפי השם. מנסה NLU, ואם נכשל - נופל על חילוץ בקוד."""
    raw = text.strip()
    if not raw:
        return "לא הבנתי. מה שמך?", state

    name = None
    parsed = nlu.extract(raw)
    if parsed:
        name = parsed.get("name")
        if parsed.get("claimed_date"):
            state["claimed_date"] = parsed["claimed_date"]

    if not name:
        claimed = _extract_date(raw)
        if claimed:
            state["claimed_date"] = claimed
        name = _strip_date_and_digits(raw)

    if not name:
        return "לא זיהיתי שם. מה שמך?", state

    results = _search_by_words(name)

    if len(results) == 0:
        return "לא מצאתי אף לקוח בשם הזה. אפשר לנסות שם מלא יותר?", state

    if len(results) == 1:
        state["candidate_id"] = results[0]["customer_id"]
        state["candidate_name"] = results[0]["full_name"]
        state["state"] = AWAIT_ID
        return _ask_for_id(state), state

    state["candidates"] = results
    state["state"] = CLARIFY
    return "יש כמה לקוחות עם השם הזה. מה השם המלא שלך?", state


def _handle_clarify(text, state):
    """מסנן את רשימת המועמדים לפי ההבהרה שהמשתמש נתן."""
    text = _strip_date_and_digits(text.strip())
    if not text:
        return "לא הבנתי. מה השם המלא שלך?", state

    candidates = state.get("candidates", [])
    matches = [c for c in candidates if text in c["full_name"]]

    if len(matches) == 0:
        state["state"] = START
        state["candidates"] = []
        return "לא מצאתי התאמה. בוא נתחיל מחדש - מה שמך?", state

    if len(matches) == 1:
        state["candidate_id"] = matches[0]["customer_id"]
        state["candidate_name"] = matches[0]["full_name"]
        state["candidates"] = []
        state["state"] = AWAIT_ID
        return _ask_for_id(state), state

    return "עדיין יש כמה התאמות. אפשר את השם המלא במדויק?", state


def _handle_await_id(text, state):
    """מאמת תעודת זהות. ההשוואה עצמה נעשית ב-API, בקוד."""
    national_id = _digits_only(text)
    if not national_id:
        return "לא זיהיתי מספר. מה תעודת הזהות שלך?", state

    verified, appointments = api_client.get_appointments(state["candidate_id"], national_id)

    if verified:
        state["state"] = VERIFIED
        state["national_id"] = national_id
        state["appointments"] = appointments
        return _build_answer(state, appointments), state

    state["attempts_left"] = state.get("attempts_left", MAX_ATTEMPTS) - 1

    if state["attempts_left"] <= 0:
        state["state"] = BLOCKED
        state["candidate_id"] = None
        state["candidate_name"] = None
        return "לא הצלחתי לאמת אותך. מטעמי אבטחה אני מסיים כאן - אנא פנה למשרד בטלפון.", state

    return (
        f"תעודת הזהות אינה תואמת. נותרו {state['attempts_left']} ניסיונות. "
        "אפשר לנסות שוב?"
    ), state


def _handle_verified(text, state):
    """אחרי אימות - מזהה כוונה: הצגה, יצירה, או ביטול."""
    intent = _detect_intent(text)

    if intent == "create":
        state["state"] = AWAIT_NEW_SERVICE
        return "בשמחה! איזה סוג שירות תרצה לקבוע?", state

    if intent == "cancel":
        appointments = state.get("appointments", [])
        active = [a for a in appointments if a.get("status") != "בוטל"]
        if not active:
            return "אין לך תורים פתוחים לביטול.", state
        lines = []
        for i, a in enumerate(active, start=1):
            lines.append(f"{i}. {_pretty_date(a['appointment_date'])} בשעה {a['appointment_time']} ({a.get('service_type', '')})")
        state["state"] = AWAIT_CANCEL_CHOICE
        return "איזה תור לבטל? " + " | ".join(lines) + " - כתוב את המספר.", state

    appointments = state.get("appointments", [])
    return _build_answer(state, appointments), state


def _handle_new_service(text, state):
    """שלב 1 ביצירת תור: סוג השירות. חייב להיות אחד מהסוגים הקיימים."""
    service = text.strip()

    matches = [s for s in SERVICE_TYPES if service in s or s in service]

    if len(matches) == 1:
        state["pending_service"] = matches[0]
        state["state"] = AWAIT_NEW_DATE
        return "מעולה. באיזה תאריך? (לדוגמה: 15.03.2027)", state

    options = ", ".join(SERVICE_TYPES)
    return f"לא זיהיתי את סוג השירות. הסוגים הקיימים הם: {options}. איזה מהם תרצה?", state


def _handle_new_date(text, state):
    """שלב 2 ביצירת תור: התאריך. חייב להיות תקין ובעתיד."""
    parsed_date = _extract_date(text)
    if not parsed_date:
        return "לא זיהיתי תאריך. אפשר בפורמט כמו 15.03.2027?", state

    try:
        parsed_obj = date.fromisoformat(parsed_date)
    except ValueError:
        return "התאריך הזה לא תקין. אפשר בפורמט כמו 15.03.2027?", state

    today = date.today()
    if parsed_obj < today:
        return "התאריך הזה כבר עבר. אפשר תאריך עתידי?", state

    state["pending_date"] = parsed_date
    state["state"] = AWAIT_NEW_TIME
    return "ובאיזו שעה? (לדוגמה: 14:00)", state
def _handle_new_time(text, state):
    """שלב 3 ביצירת תור: השעה, בדיקת תפוסה, ואז ביצוע בפועל."""
    parsed_time = _extract_time(text)
    if not parsed_time:
        return "לא זיהיתי שעה. אפשר בפורמט כמו 14:00?", state

    if not api_client.check_availability(state["pending_date"], parsed_time):
        return "השעה הזו כבר תפוסה. אפשר לבחור שעה אחרת?", state

    verified, created, appointment_id = api_client.create_appointment(
        state["candidate_id"],
        state.get("national_id", ""),
        state["pending_service"],
        state["pending_date"],
        parsed_time,
    )

    state["state"] = VERIFIED
    state["pending_service"] = None
    state["pending_date"] = None

    if not verified or not created:
        return "לא הצלחתי לקבוע את התור. נסה שוב או פנה למשרד.", state

    verified2, appointments = api_client.get_appointments(state["candidate_id"], state.get("national_id", ""))
    if verified2:
        state["appointments"] = appointments

    return f"התור נקבע בהצלחה! מספר תור: {appointment_id}.", state


def _handle_cancel_choice(text, state):
    """מקבל את מספר הבחירה, ומבטל את התור המתאים."""
    digits = _digits_only(text)
    if not digits:
        return "אנא כתוב את מספר התור מהרשימה.", state

    choice = int(digits)
    appointments = state.get("appointments", [])
    active = [a for a in appointments if a.get("status") != "בוטל"]

    if choice < 1 or choice > len(active):
        return "מספר לא תקין. אנא בחר מספר מהרשימה שהוצגה.", state

    target = active[choice - 1]

    verified, cancelled = api_client.cancel_appointment(
        state["candidate_id"], state.get("national_id", ""), target["appointment_id"]
    )

    state["state"] = VERIFIED

    if not verified or not cancelled:
        return "לא הצלחתי לבטל את התור. נסה שוב או פנה למשרד.", state

    verified2, appointments = api_client.get_appointments(state["candidate_id"], state.get("national_id", ""))
    if verified2:
        state["appointments"] = appointments

    return "התור בוטל בהצלחה.", state
    