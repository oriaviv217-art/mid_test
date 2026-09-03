

"""עוטף את הקריאות ל-API. כל כתובות ה-HTTP מרוכזות כאן."""
import requests

API_BASE = "http://127.0.0.1:5001"
TIMEOUT = 5


def search_customers(name):
    """מחזיר רשימת dict עם customer_id ו-full_name. רשימה ריקה אם אין או אם ה-API נפל."""
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
    """מחזיר טאפל (verified, appointments). התורים ריקים אם האימות נכשל."""
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