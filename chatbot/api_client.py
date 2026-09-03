"""עוטף את הקריאות ל-API. כל כתובות ה-HTTP מרוכזות כאן.
במצב LOCAL (USE_LOCAL_API=1) קורא ישירות לפונקציות של פרויקט האמצע,
בלי HTTP - משמש בפריסה כשיש רק Web App אחד."""
import os
import sys
from pathlib import Path

import requests

API_BASE = "http://127.0.0.1:5001"
TIMEOUT = 5

LOCAL_MODE = os.environ.get("USE_LOCAL_API") == "1"

if LOCAL_MODE:
    _root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(_root))
    os.chdir(_root)
    from customers_manager import get_all_customers, get_customer_appointments

    C_ID, C_NAME, C_NATIONAL_ID = 0, 1, 7
    A_ID, A_SERVICE, A_DATE, A_TIME, A_STATUS = 0, 2, 3, 4, 5

    def _clean_id(value):
        return "".join(ch for ch in str(value) if ch.isdigit())

    def _is_verified(customer_id, national_id):
        if not customer_id or not _clean_id(national_id):
            return False
        for c in get_all_customers():
            if c[C_ID] == customer_id:
                db_id = _clean_id(c[C_NATIONAL_ID])
                return bool(db_id) and db_id == _clean_id(national_id)
        return False


def search_customers(name):
    """מחזיר רשימת dict עם customer_id ו-full_name. רשימה ריקה אם אין או אם קרתה שגיאה."""
    if LOCAL_MODE:
        try:
            return [
                {"customer_id": c[C_ID], "full_name": c[C_NAME]}
                for c in get_all_customers() if name in c[C_NAME]
            ]
        except Exception:
            return []
    try:
        response = requests.get(
            API_BASE + "/api/customers/search",
            params={"name": name},
            timeout=TIMEOUT,
        )
        return response.json()
    except Exception:
        return []


def verify(customer_id, national_id):
    """מחזיר True אם הת"ז תואמת ללקוח, אחרת False."""
    if LOCAL_MODE:
        try:
            return _is_verified(customer_id, national_id)
        except Exception:
            return False
    try:
        response = requests.post(
            API_BASE + "/api/customers/verify",
            json={"customer_id": customer_id, "national_id": national_id},
            timeout=TIMEOUT,
        )
        return response.json().get("verified", False)
    except Exception:
        return False


def get_appointments(customer_id, national_id):
    """מחזיר טאפל (verified, appointments)."""
    if LOCAL_MODE:
        try:
            if not _is_verified(customer_id, national_id):
                return False, []
            results = [
                {
                    "appointment_id": a[A_ID],
                    "service_type": a[A_SERVICE],
                    "appointment_date": a[A_DATE],
                    "appointment_time": a[A_TIME],
                    "status": a[A_STATUS],
                }
                for a in get_customer_appointments(customer_id)
            ]
            return True, results
        except Exception:
            return False, []
    try:
        response = requests.post(
            API_BASE + "/api/customers/appointments",
            json={"customer_id": customer_id, "national_id": national_id},
            timeout=TIMEOUT,
        )
        data = response.json()
        return data.get("verified", False), data.get("appointments", [])
    except Exception:
        return False, []
