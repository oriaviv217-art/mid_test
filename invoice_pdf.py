"""יצירת קובצי PDF לחשבוניות מס, עם תמיכה בטקסט עברי (RTL)."""

import os
import re

from fpdf import FPDF
from bidi.algorithm import get_display

PDF_DIR = "invoices_pdf"

_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\ARIAL.TTF",
    "/usr/share/fonts/truetype/dejavu/NotoSansHebrew-Regular.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
]

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


def _find_hebrew_font():
    for path in _FONT_CANDIDATES:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "לא נמצא גופן התומך בעברית ליצירת PDF. יש לוודא שגופן Arial מותקן במערכת, "
        "או להוסיף נתיב לגופן תומך-עברית ברשימת _FONT_CANDIDATES בקובץ invoice_pdf.py."
    )


def _rtl(text):
    """ממירה טקסט עברי לסדר תצוגה נכון (ימין-לשמאל) לצורך ציור ב-PDF."""
    return get_display(str(text))


def _sanitize_filename_part(text):
    text = _INVALID_FILENAME_CHARS.sub("", str(text))
    text = text.strip().replace(" ", "_")
    return text or "לא_ידוע"


def generate_invoice_pdf(invoice_number, customer_name, amount, invoice_date):
    """
    יוצרת קובץ PDF עבור חשבונית ושומרת אותו בתיקיית PDF_DIR, עם שם קובץ אינדיקטיבי
    הכולל תאריך, שם לקוח ומספר חשבונית. מחזירה את הנתיב היחסי של הקובץ שנוצר.
    """
    os.makedirs(PDF_DIR, exist_ok=True)
    font_path = _find_hebrew_font()

    pdf = FPDF()
    pdf.add_page()
    pdf.add_font("Hebrew", "", font_path)

    pdf.set_font("Hebrew", size=20)
    pdf.cell(0, 14, _rtl("חשבונית מס"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Hebrew", size=10)
    pdf.cell(0, 8, _rtl("משרד ייעוץ פיננסי והשקעות"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)

    pdf.set_font("Hebrew", size=13)

    def line(label, value):
        pdf.cell(0, 10, _rtl(f"{label}: {value}"), align="R", new_x="LMARGIN", new_y="NEXT")

    line("מספר חשבונית", invoice_number)
    line("תאריך", invoice_date)
    line("שם לקוח", customer_name)
    pdf.ln(4)
    pdf.set_font("Hebrew", size=15)
    line("סכום לתשלום", f'{amount:.2f} ש"ח')

    filename = f"{invoice_date}_{_sanitize_filename_part(customer_name)}_{invoice_number}.pdf"
    filepath = os.path.join(PDF_DIR, filename)
    pdf.output(filepath)
    return filepath
