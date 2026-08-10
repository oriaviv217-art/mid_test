"""נתוני דוגמה - ממלאת את מסד הנתונים בישויות לדוגמה כאשר הוא ריק, כדי שהממשק לא יוצג ריק."""

from datetime import date, timedelta

from customers_manager import (
    add_customer,
    add_invoice,
    delete_customer,
    delete_invoice,
    deactivate_customer,
    get_all_customers_including_deleted,
)
from appointments_manager import add_appointment, update_appointment_status, delete_appointment
from leads_manager import add_lead, update_lead_status, delete_lead


CUSTOMERS = [
    ("דנה כהן", "050-1234567", "dana.cohen@example.com", "רחוב הרצל 12, תל אביב"),
    ("אבי לוי", "052-2345678", "avi.levy@example.com", "שדרות רוטשילד 5, תל אביב"),
    ("מיכל ברק", "054-3456789", "michal.barak@example.com", "רחוב ויצמן 22, רמת גן"),
    ("יוסי מזרחי", "053-4567890", "yossi.mizrahi@example.com", "רחוב הנביאים 8, חיפה"),
    ("שירה אבידן", "058-5678901", "shira.avidan@example.com", "רחוב בן גוריון 3, פתח תקווה"),
    ("עומר גולן", "050-6789012", "omer.golan@example.com", "רחוב הירקון 45, תל אביב"),
    ("נועה שפירא", "052-7890123", "noa.shapira@example.com", "רחוב סוקולוב 17, הרצליה"),
    ("איתי פרידמן", "054-8901234", "itay.friedman@example.com", "רחוב ז'בוטינסקי 9, רמת גן"),
    ("טל רוזן", "053-9012345", "tal.rosen@example.com", "רחוב אחד העם 30, תל אביב"),
    ("ליאור אשכנזי", "058-0123456", "lior.ashkenazi@example.com", "רחוב העצמאות 14, נתניה"),
    ("קרן פלד", "050-1122334", "keren.peled@example.com", "רחוב המייסדים 6, רעננה"),
    ("רון שוורץ", "052-2233445", "ron.schwartz@example.com", "רחוב הגליל 21, כפר סבא"),
]

SERVICE_TYPES = [
    "ייעוץ פנסיוני",
    "תכנון פיננסי",
    "ייעוץ השקעות",
    "בדיקת תיק ביטוח",
    "פגישת מעקב",
    "ייעוץ משכנתא",
]

# (customer_index, service_type, date, time, status)
APPOINTMENTS = [
    (0, "ייעוץ פנסיוני", "2026-08-12", "09:00", "ממתין"),
    (1, "תכנון פיננסי", "2026-08-12", "10:30", "ממתין"),
    (2, "ייעוץ השקעות", "2026-08-13", "11:00", "בוצע"),
    (3, "בדיקת תיק ביטוח", "2026-08-13", "13:00", "ממתין"),
    (4, "פגישת מעקב", "2026-08-14", "09:30", "בוצע"),
    (5, "ייעוץ משכנתא", "2026-08-14", "14:00", "בוטל"),
    (6, "ייעוץ פנסיוני", "2026-08-15", "10:00", "ממתין"),
    (7, "ייעוץ השקעות", "2026-08-15", "15:30", "ממתין"),
    (0, "פגישת מעקב", "2026-08-18", "09:00", "ממתין"),
    (8, "תכנון פיננסי", "2026-08-18", "11:30", "בוצע"),
    (9, "בדיקת תיק ביטוח", "2026-08-19", "12:00", "ממתין"),
    (10, "ייעוץ השקעות", "2026-08-19", "16:00", "ממתין"),
    (11, "ייעוץ פנסיוני", "2026-08-20", "09:00", "ממתין"),
    (2, "פגישת מעקב", "2026-08-05", "10:00", "בוטל"),
]

# (customer_index, amount) - התאריך נקבע דינמית (היום ואילך), כי לא ניתן להזין חשבונית בתאריך שכבר עבר
INVOICES = [
    (0, 850.0),
    (1, 1200.0),
    (2, 640.0),
    (3, 950.0),
    (4, 1500.0),
    (5, 420.0),
    (6, 780.0),
    (8, 1100.0),
    (9, 690.0),
    (0, 300.0),
]

# (full_name, phone, source, status, notes)
LEADS = [
    ("גיא נחמיאס", "050-1112223", "אתר האינטרנט", "חדש", "מעוניין בייעוץ פנסיוני"),
    ("הדר וייס", "052-2223334", "פייסבוק", "בטיפול", "ביקשה הצעת מחיר לתכנון פיננסי"),
    ("אלון בכר", "054-3334445", "המלצה", "חדש", "הומלץ על ידי לקוח קיים"),
    ("שני אור", "053-4445556", "גוגל", "נדחה", "לא רלוונטי כרגע"),
    ("דור קפלן", "058-5556667", "פה לאוזן", "בטיפול", "מתעניין בייעוץ השקעות"),
    ("מאיה זיו", "050-6667778", "אתר האינטרנט", "חדש", ""),
    ("עידן שגיא", "052-7778889", "פייסבוק", "הפך ללקוח", "הומר ללקוח בעבר"),
]


def _is_db_empty():
    return len(get_all_customers_including_deleted()) == 0


def seed_if_empty():
    """אם מסד הנתונים ריק לגמרי - ממלאת אותו בישויות לדוגמה לכל הישויות, כולל כמה רשומות מחוקות להדגמת השחזור."""
    if not _is_db_empty():
        return False

    customer_ids = [add_customer(*c) for c in CUSTOMERS]

    for customer_index, service_type, appt_date, appt_time, status in APPOINTMENTS:
        appointment_id = add_appointment(customer_ids[customer_index], service_type, appt_date, appt_time)
        if status != "ממתין" and appointment_id is not None:
            update_appointment_status(appointment_id, status)

    today = date.today()
    invoice_ids = []
    for i, (customer_index, amount) in enumerate(INVOICES):
        invoice_date = (today + timedelta(days=i)).isoformat()
        invoice_ids.append(add_invoice(customer_ids[customer_index], amount, invoice_date))

    lead_ids = []
    for full_name, phone, source, status, notes in LEADS:
        lead_id = add_lead(full_name, phone, source, notes)
        lead_ids.append(lead_id)
        if status != "חדש":
            update_lead_status(lead_id, status)

    # מדגימות את פונקציונליות המחיקה/שחזור עם כמה רשומות מחוקות מראש
    delete_customer(customer_ids[11])
    delete_invoice(invoice_ids[5])
    delete_lead(lead_ids[3])

    # מדגימה סטטוס "לא פעיל" (שונה ממחיקה) עבור לקוח
    deactivate_customer(customer_ids[10])

    return True
