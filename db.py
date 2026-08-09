import sqlite3
def get_connection():
    conn = sqlite3.connect("appointments.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _add_missing_columns(conn):
    """מוסיפה עמודות חדשות (כמו is_deleted) לטבלאות שכבר קיימות מגרסה קודמת של הסכמה."""
    required_columns = {
        "customers": [("is_deleted", "INTEGER NOT NULL DEFAULT 0")],
        "appointments": [("is_deleted", "INTEGER NOT NULL DEFAULT 0")],
        "invoices": [("is_deleted", "INTEGER NOT NULL DEFAULT 0")],
        "leads": [("is_deleted", "INTEGER NOT NULL DEFAULT 0")],
    }
    for table, columns in required_columns.items():
        existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
        for column_name, column_def in columns:
            if column_name not in existing:
                conn.execute(f"ALTER TABLE {table} ADD COLUMN {column_name} {column_def}")


def init_db():
    conn = get_connection()
    with open("schema.sql", "r", encoding="utf-8") as f:
        script = f.read()
    conn.executescript(script)
    _add_missing_columns(conn)
    conn.commit()
    conn.close()
