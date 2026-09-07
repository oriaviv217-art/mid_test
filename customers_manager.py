import sqlite3
import uuid

from db import get_connection
from invoice_pdf import generate_invoice_pdf
from validators import validate_name, validate_phone, validate_email, validate_amount, validate_not_past_date



# ---------- ניהול לקוחות ----------

def _find_duplicate_customer(full_name, phone):
    """מחפשת לקוח פעיל קיים עם אותו שם וטלפון (ללא רגישות לרישיות/רווחים). מחזירה שורה או None."""
    conn = get_connection()
    try:
        normalized_name = full_name.strip().lower()
        normalized_phone = (phone or "").strip()
        cursor = conn.execute(
            """
            SELECT * FROM customers
            WHERE is_deleted = 0
              AND LOWER(TRIM(full_name)) = ?
              AND TRIM(IFNULL(phone, '')) = ?
            """,
            (normalized_name, normalized_phone),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def add_customer(full_name, phone, email, address, national_id=None):
    """מוסיפה לקוח חדש למערכת ומחזירה את מספר הלקוח שנוצר, או None אם הקלט אינו תקין או שהלקוח כבר קיים."""
    is_valid, error = validate_name(full_name)
    if not is_valid:
        print(f"שגיאה: {error}")
        return None
    is_valid, error = validate_phone(phone)
    if not is_valid:
        print(f"שגיאה: {error}")
        return None
    is_valid, error = validate_email(email)
    if not is_valid:
        print(f"שגיאה: {error}")
        return None

    duplicate = _find_duplicate_customer(full_name, phone)
    if duplicate is not None:
        print(f"שגיאה: לקוח עם אותו שם וטלפון כבר קיים במערכת (מספר לקוח: {duplicate[0]})")
        return None

    # נקה ת"ז לספרות בלבד לפני שמירה
    clean_nid = "".join(ch for ch in str(national_id) if ch.isdigit()) if national_id else None

    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO customers (full_name, phone, email, address, national_id) VALUES (?,?,?,?,?)",
            (full_name.strip(), phone, email, address, clean_nid or None)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()



def get_all_customers():
    """מחזירה רשימה של כל הלקוחות הפעילים (שאינם מחוקים) במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM customers WHERE is_deleted = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_deleted_customers():
    """מחזירה רשימה של כל הלקוחות המחוקים (מחיקה רכה) במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM customers WHERE is_deleted = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_customers_including_deleted():
    """מחזירה רשימה של כל הלקוחות במערכת, כולל מחוקים."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM customers")
    rows = cursor.fetchall()
    conn.close()
    return rows


def delete_customer(customer_id):
    """
    מוחקת לקוח פעיל לפי מספר לקוח (מחיקה רכה - is_deleted=1).
    כדי לשמור על עקביות הנתונים, כל התורים והחשבוניות של הלקוח
    מסומנים כמחוקים גם כן.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE customers SET is_deleted = 1 WHERE customer_id = ? AND is_deleted = 0",
            (customer_id,)
        )
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא לקוח פעיל עם המספר הזה")
        else:
            conn.execute(
                "UPDATE appointments SET is_deleted = 1 WHERE customer_id = ?",
                (customer_id,)
            )
            conn.execute(
                "UPDATE invoices SET is_deleted = 1 WHERE customer_id = ?",
                (customer_id,)
            )
        conn.commit()
        return found
    finally:
        conn.close()


def undelete_customer(customer_id):
    """משחזרת לקוח מחוק לפי מספר לקוח. אינה משחזרת אוטומטית תורים/חשבוניות."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE customers SET is_deleted = 0 WHERE customer_id = ? AND is_deleted = 1",
            (customer_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא לקוח מחוק עם המספר הזה")
        return found
    finally:
        conn.close()


def deactivate_customer(customer_id):
    """מסמנת לקוח פעיל כ'לא פעיל' (סטטוס עסקי, שונה ממחיקה - הלקוח נשאר גלוי בכל הרשימות)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE customers SET is_active = 0 WHERE customer_id = ? AND is_deleted = 0",
            (customer_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא לקוח פעיל עם המספר הזה")
        return found
    finally:
        conn.close()


def activate_customer(customer_id):
    """מסמנת לקוח 'לא פעיל' בחזרה כ'פעיל'."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE customers SET is_active = 1 WHERE customer_id = ? AND is_deleted = 0",
            (customer_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא לקוח עם המספר הזה")
        return found
    finally:
        conn.close()


# ---------- ניהול חשבוניות מס ----------

def add_invoice(customer_id, amount, invoice_date):
    """
    יוצרת חשבונית מס עבור לקוח קיים: מספר החשבונית נוצר אוטומטית (INV-000001 וכו'),
    וקובץ PDF נוצר ונשמר בתיקיית invoices_pdf. מחזירה את מזהה החשבונית, או None בעת כשל.
    """
    is_valid, error = validate_amount(amount)
    if not is_valid:
        print(f"שגיאה: {error}")
        return None
    is_valid, error = validate_not_past_date(invoice_date)
    if not is_valid:
        print(f"שגיאה: {error}")
        return None
    amount = float(amount)

    conn = get_connection()
    try:
        placeholder_number = f"TMP-{uuid.uuid4().hex}"
        cursor = conn.execute(
            "INSERT INTO invoices (invoice_number, customer_id, amount, invoice_date) VALUES (?,?,?,?)",
            (placeholder_number, customer_id, amount, invoice_date)
        )
        invoice_id = cursor.lastrowid
        invoice_number = f"INV-{invoice_id:06d}"

        customer_row = conn.execute(
            "SELECT full_name FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        customer_name = customer_row[0] if customer_row else "לקוח לא ידוע"

        pdf_path = None
        try:
            pdf_path = generate_invoice_pdf(invoice_number, customer_name, amount, invoice_date)
        except Exception as e:
            print(f"אזהרה: יצירת קובץ ה-PDF נכשלה ({e}) - החשבונית נשמרה ללא PDF")

        conn.execute(
            "UPDATE invoices SET invoice_number = ?, pdf_path = ? WHERE invoice_id = ?",
            (invoice_number, pdf_path, invoice_id)
        )
        conn.commit()
        return invoice_id
    except sqlite3.IntegrityError:
        print("שגיאה: מספר לקוח לא קיים במערכת")
        return None
    finally:
        conn.close()


def get_all_invoices():
    """מחזירה רשימה של כל החשבוניות הפעילות (שאינן מחוקות) במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM invoices WHERE is_deleted = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_deleted_invoices():
    """מחזירה רשימה של כל החשבוניות המחוקות במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM invoices WHERE is_deleted = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_invoices_including_deleted():
    """מחזירה רשימה של כל החשבוניות במערכת, כולל מחוקות."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM invoices")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_invoice_by_id(invoice_id):
    """מחזירה חשבונית בודדת לפי מזהה (כולל אם היא מחוקה), או None אם לא נמצאה."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id,))
    row = cursor.fetchone()
    conn.close()
    return row


def delete_invoice(invoice_id):
    """מוחקת חשבונית פעילה לפי מזהה (מחיקה רכה)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE invoices SET is_deleted = 1 WHERE invoice_id = ? AND is_deleted = 0",
            (invoice_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצאה חשבונית פעילה עם המספר הזה")
        return found
    finally:
        conn.close()


def undelete_invoice(invoice_id):
    """משחזרת חשבונית מחוקה לפי מזהה."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE invoices SET is_deleted = 0 WHERE invoice_id = ? AND is_deleted = 1",
            (invoice_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצאה חשבונית מחוקה עם המספר הזה")
        return found
    finally:
        conn.close()


def get_customer_invoices(customer_id):
    """מחזירה את כל החשבוניות הפעילות של לקוח מסוים."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM invoices WHERE customer_id = ? AND is_deleted = 0",
        (customer_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_customer_appointments(customer_id):
    """מחזירה את היסטוריית התורים הפעילים של לקוח מסוים."""
    conn = get_connection()
    cursor = conn.execute(
        "SELECT * FROM appointments WHERE customer_id = ? AND is_deleted = 0",
        (customer_id,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows
