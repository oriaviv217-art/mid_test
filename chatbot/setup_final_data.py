"""
הכנת הדאטה לפרויקט הסוף.
לא נוגע בקבצים של פרויקט האמצע - כל הפעולות ישירות מול appointments.db.
בטוח להרצה חוזרת.
"""
import sqlite3
from pathlib import Path

# תיקיית האב של chatbot - שם יושב ה-DB האמיתי
DB_PATH = Path(__file__).resolve().parent.parent / "appointments.db"
EXISTING_IDS = {
    "דנה כהן": "312456789",
    "אבי לוי": "045678123",
    "מיכל ברק": "298765432",
    "יוסי מזרחי": "056789234",
    "שירה אבידן": "331122445",
    "עומר גולן": "067234891",
    "נועה שפירא": "289334567",
    "איתי פרידמן": "078912345",
    "טל רוזן": "345678901",
    "ליאור אשכנזי": "089123456",
    "קרן פלד": "356789012",
    "רון שוורץ": "090234567",
}

# (שם מלא, טלפון, מייל, כתובת, תעודת זהות)
NEW_CUSTOMERS = [
    ("רותם מירון", "050-4455667", "rotem.miron@example.com", "רחוב אלנבי 40, תל אביב", "123456789"),
    ("רותם שרעבי", "052-5566778", "rotem.sharabi@example.com", "רחוב ביאליק 8, רמת גן", "987654321"),
    ("עדי כרמלי", "054-6677889", "adi.carmeli@example.com", "רחוב הרצל 3, חולון", "246813579"),
]

# (שם לקוח, סוג שירות, תאריך, שעה)
# עדי כרמלי לא מופיעה כאן בכוונה - היא הלקוחה בלי אף תור
NEW_APPOINTMENTS = [
    ("רותם מירון", "ייעוץ פנסיוני", "2027-01-19", "19:00"),
    ("רותם שרעבי", "ייעוץ השקעות", "2027-02-03", "11:00"),
]


def add_national_id_column(conn):
    cols = [row[1] for row in conn.execute("PRAGMA table_info(customers)")]
    if "national_id" in cols:
        print("[1] column national_id: already exists")
    else:
        conn.execute("ALTER TABLE customers ADD COLUMN national_id TEXT")
        print("[1] column national_id: added")


def fill_existing_ids(conn):
    updated, missing = 0, []
    for name, nid in EXISTING_IDS.items():
        cur = conn.execute(
            "UPDATE customers SET national_id = ? WHERE full_name = ?", (nid, name)
        )
        if cur.rowcount == 0:
            missing.append(name)
        else:
            updated += cur.rowcount
    print(f"[2] existing customers updated: {updated}")
    if missing:
        print("    NOT FOUND (check spelling):", missing)


def add_new_customers(conn):
    added, skipped = 0, 0
    for name, phone, email, address, nid in NEW_CUSTOMERS:
        row = conn.execute(
            "SELECT customer_id FROM customers WHERE full_name = ?", (name,)
        ).fetchone()
        if row:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO customers (full_name, phone, email, address, national_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (name, phone, email, address, nid),
        )
        added += 1
    print(f"[3] new customers added: {added}, skipped: {skipped}")


def add_new_appointments(conn):
    added, skipped = 0, 0
    for name, service, appt_date, appt_time in NEW_APPOINTMENTS:
        row = conn.execute(
            "SELECT customer_id FROM customers WHERE full_name = ?", (name,)
        ).fetchone()
        if not row:
            print(f"    customer not found: {name}")
            continue
        cid = row[0]
        exists = conn.execute(
            "SELECT 1 FROM appointments "
            "WHERE customer_id = ? AND appointment_date = ? AND appointment_time = ?",
            (cid, appt_date, appt_time),
        ).fetchone()
        if exists:
            skipped += 1
            continue
        conn.execute(
            "INSERT INTO appointments (customer_id, service_type, appointment_date, appointment_time) "
            "VALUES (?, ?, ?, ?)",
            (cid, service, appt_date, appt_time),
        )
        added += 1
    print(f"[4] new appointments added: {added}, skipped: {skipped}")
def fill_missing_ids(conn):
    """נותן ת"ז אוטומטית לכל לקוח שנשאר בלי - שאף לקוח לא יהיה מבוי סתום."""
    rows = conn.execute(
        "SELECT customer_id FROM customers WHERE national_id IS NULL"
    ).fetchall()
    for (cid,) in rows:
        conn.execute(
            "UPDATE customers SET national_id = ? WHERE customer_id = ?",
            (str(400000000 + cid), cid),
        )
    print(f"[5] auto-filled missing ids: {len(rows)}")

def verify(conn):
    print("\n--- verification ---")
    total = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
    with_id = conn.execute(
        "SELECT COUNT(*) FROM customers WHERE national_id IS NOT NULL"
    ).fetchone()[0]
    print(f"customers: {total}, with national_id: {with_id}")

    rotem = conn.execute(
        "SELECT customer_id, full_name, national_id FROM customers WHERE full_name LIKE ?",
        ("%רותם%",),
    ).fetchall()
    print(f"'rotem' matches: {len(rotem)} (need 2)")
    for r in rotem:
        print("   ", r)

    no_appt = conn.execute(
        "SELECT full_name FROM customers WHERE customer_id NOT IN "
        "(SELECT customer_id FROM appointments)"
    ).fetchall()
    print(f"customers with no appointments: {len(no_appt)} -> {no_appt}")

    future = conn.execute(
        "SELECT full_name, appointment_date, appointment_time, status "
        "FROM appointments a JOIN customers c USING(customer_id) "
        "WHERE appointment_date > '2026-09-02'"
    ).fetchall()
    print(f"future appointments: {len(future)}")
    for f in future:
        print("   ", f)


def main():
    if not DB_PATH.exists():
        print(f"DB not found at: {DB_PATH}")
        return
    conn = sqlite3.connect(DB_PATH)
    add_national_id_column(conn)
    fill_existing_ids(conn)
    add_new_customers(conn)
    add_new_appointments(conn)
    fill_missing_ids(conn)
    conn.commit()
    verify(conn)
    conn.close()


if __name__ == "__main__":
    main()
    