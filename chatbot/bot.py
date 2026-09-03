"""
מכונת המצבים של השיחה.
כל הודעה מטופלת לפי המצב הנוכחי, לא לפי ניחוש מהטקסט.
"""
import re
from datetime import date

import api_client
import nlu

# חמשת המצבים
START = "START"           # אין מועמד
CLARIFY = "CLARIFY"       # כמה התאמות, מחכים להבהרה
AWAIT_ID = "AWAIT_ID"     # מועמד אחד, מחכים לתעודת זהות
VERIFIED = "VERIFIED"     # אומת
BLOCKED = "BLOCKED"       # נגמרו הניסיונות

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
    if current == BLOCKED:
        return "לא אוכל להמשיך בשיחה הזו. אנא פנה למשרד בטלפון.", state

    return "משהו השתבש. בוא נתחיל מחדש.", new_state()


# ---------- כלי עזר ----------

def _digits_only(text):
    """משאיר רק ספרות."""
    return "".join(ch for ch in str(text) if ch.isdigit())


def _extract_date(text):
    """
    מחלץ תאריך מטקסט חופשי ומחזיר אותו כ-YYYY-MM-DD, או None.
    בהמשך שכבת ה-NLU תחליף את זה - כרגע זו רשת ביטחון בקוד.
    """
    m = re.search(r"(\d{4})-(\d{2})-(\d{2})", text)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    m = re.search(r"(\d{1,2})[./](\d{1,2})[./](\d{4})", text)
    if m:
        day, month, year = m.group(1), m.group(2), m.group(3)
        return f"{year}-{int(month):02d}-{int(day):02d}"

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


# ---------- טיפול לפי מצב ----------
def _search_by_words(raw_name):
    """
    מחפש כל מילה בנפרד ומחזיר את ההתאמות.
    רשת ביטחון עד ששכבת ה-NLU תחלץ את השם במדויק.
    """
    results = api_client.search_customers(raw_name)
    if results:
        return results

    seen = {}
    for word in raw_name.split():
        if len(word) < 3:          # "לי", "בן" - קצרות מדי, יוצרות רעש
            continue
        for c in api_client.search_customers(word):
            seen[c["customer_id"]] = c
    return list(seen.values())


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

    # רשת ביטחון: אם ה-NLU לא זמין או לא זיהה שם
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
    return f"מצאתי {len(results)} לקוחות עם השם הזה. מה השם המלא שלך?", state

def _handle_clarify(text, state):
    """מסנן את רשימת המועמדים לפי ההבהרה שהמשתמש נתן."""
    text = _strip_date_and_digits(text.strip())
    if not text:
        return "לא הבנתי. מה השם המלא שלך?", state

    candidates = state.get("candidates", [])
    matches = []
    for c in candidates:
        if text in c["full_name"]:
            matches.append(c)

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

    return f"עדיין מצאתי {len(matches)} התאמות. אפשר את השם המלא במדויק?", state


def _handle_await_id(text, state):
    """מאמת תעודת זהות. ההשוואה עצמה נעשית ב-API, בקוד."""
    national_id = _digits_only(text)
    if not national_id:
        return "לא זיהיתי מספר. מה תעודת הזהות שלך?", state

    verified, appointments = api_client.get_appointments(
        state["candidate_id"], national_id
    )

    if verified:
        state["state"] = VERIFIED
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
    """אחרי אימות - עונה על שאלות נוספות מהנתונים ששמורים."""
    appointments = state.get("appointments", [])
    return _build_answer(state, appointments), state