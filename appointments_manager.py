import sqlite3
from db import get_connection

def add_appointment(customer_id, service_type, appointment_date, appointment_time):
    conn = get_connection()
    try:
        cursor = conn.execute(
            "insert into appointments (customer_id, service_type, appointment_date, appointment_time) VALUES (?,?,?,?)",
            (customer_id, service_type, appointment_date, appointment_time)
        )
        conn.commit()
        new_id = cursor.lastrowid
        return new_id
    except sqlite3.IntegrityError:
        print("שגיאה: מספר לקוח לא קיים במערכת")
        return None
    finally:
        conn.close()

def get_all_appointments():
    """מחזירה את כל התורים הפעילים (שאינם מחוקים)."""
    conn = get_connection()
    cursor = conn.execute("select * from appointments where is_deleted = 0")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_deleted_appointments():
    """מחזירה את כל התורים המחוקים."""
    conn = get_connection()
    cursor = conn.execute("select * from appointments where is_deleted = 1")
    rows = cursor.fetchall()
    conn.close()
    return rows

def get_all_appointments_including_deleted():
    """מחזירה את כל התורים, כולל מחוקים."""
    conn = get_connection()
    cursor = conn.execute("select * from appointments")
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_appointment_status(appointment_id, new_status):
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE appointments SET status = ? WHERE appointment_id = ? AND is_deleted = 0",
        (new_status, appointment_id)
    )
    conn.commit()
    found = cursor.rowcount > 0
    if not found:
        print("לא נמצא תור פעיל עם המספר הנוכחי")
    conn.close()
    return found

def delete_appointment(appointment_id):
    """מוחקת תור פעיל לפי מספר (מחיקה רכה)."""
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE appointments SET is_deleted = 1 WHERE appointment_id = ? AND is_deleted = 0",
        (appointment_id,)
    )
    conn.commit()
    found = cursor.rowcount > 0
    if not found:
        print("לא נמצא תור פעיל למחיקה")
    conn.close()
    return found

def undelete_appointment(appointment_id):
    """משחזרת תור מחוק לפי מספר."""
    conn = get_connection()
    cursor = conn.execute(
        "UPDATE appointments SET is_deleted = 0 WHERE appointment_id = ? AND is_deleted = 1",
        (appointment_id,)
    )
    conn.commit()
    found = cursor.rowcount > 0
    if not found:
        print("לא נמצא תור מחוק לשחזור")
    conn.close()
    return found
