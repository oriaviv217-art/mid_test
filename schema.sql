--schema.sql
--מערכת ניהול תורים - משרד ייעוץ פיננסי והשקעות
-- קובץ זה מגדיר את מבנה בסיס הנתונים (הטבלאות והקשרים ביניהן)
--==========================================================================================================

CREATE TABLE IF NOT EXISTS customers(
    customer_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name     TEXT NOT NULL,
    phone         TEXT,
    email         TEXT,
    address       TEXT,
    is_deleted    INTEGER NOT NULL DEFAULT 0,
    is_active     INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id         INTEGER NOT NULL,
    service_type        TEXT NOT NULL,
    appointment_date    TEXT NOT NULL,
    appointment_time    TEXT NOT NULL,
    status               TEXT NOT NULL DEFAULT 'ממתין',
    is_deleted           INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
);
CREATE TABLE IF NOT EXISTS invoices (
    invoice_date TEXT NOT NULL,
    invoice_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_number  TEXT NOT NULL UNIQUE,
    customer_id INTEGER NOT NULL,
    amount  REAL NOT NULL,
    is_deleted  INTEGER NOT NULL DEFAULT 0,
    pdf_path    TEXT,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id)

);
CREATE TABLE IF NOT EXISTS leads(
    lead_id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name   TEXT    NOT NULL,
    phone   TEXT ,
    source  TEXT,
    status  TEXT    NOT NULL DEFAULT 'חדש',
    notes   TEXT,
    is_deleted  INTEGER NOT NULL DEFAULT 0
);
