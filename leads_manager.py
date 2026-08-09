import sqlite3
from db import get_connection
from customers_manager import add_customer


def add_lead(full_name, phone, source, notes):
    """מוסיפה ליד חדש למערכת ומחזירה את מספר הליד שנוצר."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO leads (full_name, phone, source, notes) VALUES (?,?,?,?)",
            (full_name, phone, source, notes)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_all_leads():
    """מחזירה רשימה של כל הלידים הפעילים (שאינם מחוקים) במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM leads WHERE is_deleted = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_deleted_leads():
    """מחזירה רשימה של כל הלידים המחוקים במערכת."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM leads WHERE is_deleted = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_leads_including_deleted():
    """מחזירה רשימה של כל הלידים במערכת, כולל מחוקים."""
    conn = get_connection()
    cursor = conn.execute("SELECT * FROM leads")
    rows = cursor.fetchall()
    conn.close()
    return rows


def update_lead_status(lead_id, new_status):
    """מעדכנת את סטטוס הליד (חדש / בטיפול / הפך ללקוח / נדחה)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE leads SET status = ? WHERE lead_id = ? AND is_deleted = 0",
            (new_status, lead_id)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא ליד פעיל עם המספר הזה")
        return found
    finally:
        conn.close()


def delete_lead(lead_id):
    """מוחקת ליד פעיל לפי מספר (מחיקה רכה)."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE leads SET is_deleted = 1 WHERE lead_id = ? AND is_deleted = 0",
            (lead_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא ליד פעיל עם המספר הזה")
        return found
    finally:
        conn.close()


def undelete_lead(lead_id):
    """משחזרת ליד מחוק לפי מספר."""
    conn = get_connection()
    try:
        cursor = conn.execute(
            "UPDATE leads SET is_deleted = 0 WHERE lead_id = ? AND is_deleted = 1",
            (lead_id,)
        )
        conn.commit()
        found = cursor.rowcount > 0
        if not found:
            print("לא נמצא ליד מחוק עם המספר הזה")
        return found
    finally:
        conn.close()


def convert_lead_to_customer(lead_id):
    """
    ממירה ליד ללקוח: יוצרת רשומת לקוח מנתוני הליד,
    ומעדכנת את סטטוס הליד ל'הפך ללקוח'.
    מחזירה את מספר הלקוח החדש, או None אם הליד לא נמצא.
    """
    conn = get_connection()
    cursor = conn.execute(
        "SELECT full_name, phone FROM leads WHERE lead_id = ? AND is_deleted = 0",
        (lead_id,)
    )
    lead = cursor.fetchone()
    conn.close()

    if lead is None:
        print("לא נמצא ליד פעיל עם המספר הזה")
        return None

    full_name = lead[0]
    phone = lead[1]

    new_customer_id = add_customer(full_name, phone, None, None)
    update_lead_status(lead_id, "הפך ללקוח")
    return new_customer_id
