

"""
שכבת API שמחזירה JSON, לשימוש הבוט בלבד.
לא נוגע בקבצים של פרויקט האמצע - רק מייבא מהם.
להרצה מתיקיית השורש: python chatbot/api.py
"""
import sys
from pathlib import Path

# מאפשר לייבא את המודולים של פרויקט האמצע שיושבים בתיקייה שמעל
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from flask import Flask, request, jsonify
from customers_manager import get_all_customers, get_customer_appointments
from appointments_manager import add_appointment, delete_appointment

app = Flask(__name__)

# אינדקסים של השדות בשורת לקוח
C_ID, C_NAME, C_NATIONAL_ID = 0, 1, 7


@app.route("/api/customers/search")
def search_customers():
    """מחזיר לקוחות ששמם מכיל את המחרוזת. שם ומזהה בלבד - בלי שום פרט אישי."""
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify([])
    customers = get_all_customers()
    results = []
    for customer in customers:
        if name in customer[C_NAME]:
            results.append({"customer_id": customer[C_ID], "full_name": customer[C_NAME]})
    return jsonify(results)


def clean_id(value):
    """משאיר רק ספרות - כדי שמקפים ורווחים לא יפילו אימות תקין."""
    return "".join(ch for ch in str(value) if ch.isdigit())


def is_verified(customer_id, national_id):
    """מחזירה True רק אם הת"ז תואמת בדיוק ללקוח הזה."""
    if not customer_id or not clean_id(national_id):
        return False
    for customer in get_all_customers():
        if customer[C_ID] == customer_id:
            db_id = clean_id(customer[C_NATIONAL_ID])
            return bool(db_id) and db_id == clean_id(national_id)
    return False


@app.route("/api/customers/verify", methods=["POST"])
def verify_customer():
    """מאמת תעודת זהות מול הדאטה. מחזיר true/false בלבד."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    national_id = str(data.get("national_id", "")).strip()
    return jsonify({"verified": is_verified(customer_id, national_id)})


# אינדקסים של השדות בשורת תור
A_ID, A_CUSTOMER_ID, A_SERVICE, A_DATE, A_TIME, A_STATUS = 0, 1, 2, 3, 4, 5


@app.route("/api/customers/appointments", methods=["POST"])
def customer_appointments():
    """מחזיר את התורים של לקוח - רק אחרי אימות ת"ז מוצלח."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    national_id = str(data.get("national_id", "")).strip()

    if not is_verified(customer_id, national_id):
        return jsonify({"verified": False, "appointments": []})

    results = []
    for appt in get_customer_appointments(customer_id):
        results.append({
            "appointment_id": appt[A_ID],
            "service_type": appt[A_SERVICE],
            "appointment_date": appt[A_DATE],
            "appointment_time": appt[A_TIME],
            "status": appt[A_STATUS],
        })
    return jsonify({"verified": True, "appointments": results})


@app.route("/api/customers/appointments/create", methods=["POST"])
def create_appointment():
    """יוצר תור חדש - רק אחרי אימות ת"ז מוצלח."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    national_id = str(data.get("national_id", "")).strip()
    service_type = str(data.get("service_type", "")).strip()
    appointment_date = str(data.get("appointment_date", "")).strip()
    appointment_time = str(data.get("appointment_time", "")).strip()

    if not is_verified(customer_id, national_id):
        return jsonify({"verified": False, "created": False})

    if not (service_type and appointment_date and appointment_time):
        return jsonify({"verified": True, "created": False, "error": "missing_fields"})

    new_id = add_appointment(customer_id, service_type, appointment_date, appointment_time)
    if new_id is None:
        return jsonify({"verified": True, "created": False, "error": "invalid_input"})

    return jsonify({"verified": True, "created": True, "appointment_id": new_id})


@app.route("/api/customers/appointments/cancel", methods=["POST"])
def cancel_appointment():
    """מבטל תור - רק אחרי אימות ת"ז, ורק אם התור שייך ללקוח המאומת."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    national_id = str(data.get("national_id", "")).strip()
    appointment_id = data.get("appointment_id")

    if not is_verified(customer_id, national_id):
        return jsonify({"verified": False, "cancelled": False})

    owned_ids = [appt[A_ID] for appt in get_customer_appointments(customer_id)]
    if appointment_id not in owned_ids:
        return jsonify({"verified": True, "cancelled": False, "error": "not_found_or_not_yours"})

    success = delete_appointment(appointment_id)
    return jsonify({"verified": True, "cancelled": success})


if __name__ == "__main__":
    app.run(port=5001, debug=True)
    