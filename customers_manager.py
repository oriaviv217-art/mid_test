import sqlite3
from db import get_connection



# ---------- ניהול לקוחות ----------

def add_customer(full_name, phone, email, address):
    """מוסיפה לקוח חדש למערכת ומחזירה את מספר הלקוח שנוצר."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO customers (full_name, phone, email, address) VALUES (?,?,?,?)",
            (full_name, phone, email, address)
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


# ---------- ניהול חשבוניות מס ----------

def add_invoice(invoice_number, customer_id, amount, invoice_date):
    """יוצרת חשבונית מס עבור לקוח קיים ומחזירה את מזהה החשבונית."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO invoices (invoice_number, customer_id, amount, invoice_date) VALUES (?,?,?,?)",
            (invoice_number, customer_id, amount, invoice_date)
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE" in str(e):
            print("שגיאה: מספר חשבונית זה כבר קיים במערכת")
        else:
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
