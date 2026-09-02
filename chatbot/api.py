

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


@app.route("/api/customers/verify", methods=["POST"])
def verify_customer():
    """מאמת תעודת זהות מול הדאטה. מחזיר true/false בלבד."""
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id")
    national_id = str(data.get("national_id", "")).strip()
    if not customer_id or not national_id:
        return jsonify({"verified": False})
    for customer in get_all_customers():
        if customer[C_ID] == customer_id:
            return jsonify({"verified": clean_id(customer[C_NATIONAL_ID]) == clean_id(national_id)})

    return jsonify({"verified": False})    

    

if __name__ == "__main__":
    app.run(port=5001, debug=True)