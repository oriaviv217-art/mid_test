from db import init_db
from seed_data import seed_if_empty
from appointments_manager import (
    add_appointment,
    get_all_appointments,
    get_all_deleted_appointments,
    get_all_appointments_including_deleted,
    update_appointment_status,
    delete_appointment,
    undelete_appointment
)
from customers_manager import (
    add_customer,
    get_all_customers,
    get_all_deleted_customers,
    get_all_customers_including_deleted,
    delete_customer,
    undelete_customer,
    add_invoice,
    get_all_invoices,
    get_all_deleted_invoices,
    get_all_invoices_including_deleted,
    delete_invoice,
    undelete_invoice,
    get_customer_invoices,
    get_customer_appointments
)
from leads_manager import (
    add_lead,
    get_all_leads,
    get_all_deleted_leads,
    get_all_leads_including_deleted,
    update_lead_status,
    delete_lead,
    undelete_lead,
    convert_lead_to_customer
)


# ==================== עזרים כלליים ====================

def print_rows(rows, empty_message):
    """מדפיסה רשימת רשומות, או הודעה אם הרשימה ריקה."""
    if len(rows) == 0:
        print(empty_message)
    else:
        for row in rows:
            print(row)


# ==================== תפריטי משנה ====================

def appointments_menu():
    """תפריט ניהול תורים"""
    while True:
        print("\n----- ניהול תורים -----")
        print("1. הוספת תור חדש")
        print("2. הצגת כל התורים הפעילים")
        print("3. עדכון סטטוס תור")
        print("4. מחיקת תור")
        print("5. שחזור תור מחוק")
        print("6. הצגת כל התורים המחוקים")
        print("7. הצגת כל התורים (פעילים ומחוקים)")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר אפשרות: ")

        if choice == "1":
            customer_id = input("הזן מספר לקוח: ")
            service_type = input("הזן סוג שירות: ")
            appointment_date = input("הזן תאריך (YYYY-MM-DD): ")
            appointment_time = input("הזן שעה (HH:MM): ")
            new_id = add_appointment(customer_id, service_type, appointment_date, appointment_time)
            if new_id is not None:
                print(f"התור נוצר בהצלחה! מספר תור: {new_id}")

        elif choice == "2":
            print("\n--- רשימת התורים הפעילים ---")
            print_rows(get_all_appointments(), "אין תורים פעילים במערכת")

        elif choice == "3":
            appointment_id = input("הזן מספר תור: ")
            new_status = input("הזן סטטוס חדש (ממתין / בוצע / בוטל): ")
            update_appointment_status(appointment_id, new_status)

        elif choice == "4":
            appointment_id = input("הזן מספר תור למחיקה: ")
            delete_appointment(appointment_id)

        elif choice == "5":
            appointment_id = input("הזן מספר תור לשחזור: ")
            undelete_appointment(appointment_id)

        elif choice == "6":
            print("\n--- רשימת התורים המחוקים ---")
            print_rows(get_all_deleted_appointments(), "אין תורים מחוקים במערכת")

        elif choice == "7":
            print("\n--- רשימת כל התורים (פעילים ומחוקים) ---")
            print_rows(get_all_appointments_including_deleted(), "אין תורים במערכת")

        elif choice == "0":
            break

        else:
            print("בחירה לא תקינה, נסה שוב")


def customers_menu():
    """תפריט ניהול לקוחות וחשבוניות"""
    while True:
        print("\n----- ניהול לקוחות וחשבוניות -----")
        print("1. הוספת לקוח חדש")
        print("2. הצגת כל הלקוחות הפעילים")
        print("3. מחיקת לקוח")
        print("4. שחזור לקוח מחוק")
        print("5. הצגת כל הלקוחות המחוקים")
        print("6. הצגת כל הלקוחות (פעילים ומחוקים)")
        print("7. יצירת חשבונית מס")
        print("8. הצגת חשבוניות של לקוח")
        print("9. הצגת היסטוריית תורים של לקוח")
        print("10. מחיקת חשבונית")
        print("11. שחזור חשבונית מחוקה")
        print("12. הצגת כל החשבוניות הפעילות")
        print("13. הצגת כל החשבוניות המחוקות")
        print("14. הצגת כל החשבוניות (פעילות ומחוקות)")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר אפשרות: ")

        if choice == "1":
            full_name = input("הזן שם מלא: ")
            phone = input("הזן טלפון: ")
            email = input("הזן אימייל: ")
            address = input("הזן כתובת: ")
            new_id = add_customer(full_name, phone, email, address)
            print(f"הלקוח נוסף בהצלחה! מספר לקוח: {new_id}")

        elif choice == "2":
            print("\n--- רשימת הלקוחות הפעילים ---")
            print_rows(get_all_customers(), "אין לקוחות פעילים במערכת")

        elif choice == "3":
            customer_id = input("הזן מספר לקוח למחיקה: ")
            delete_customer(customer_id)

        elif choice == "4":
            customer_id = input("הזן מספר לקוח לשחזור: ")
            undelete_customer(customer_id)

        elif choice == "5":
            print("\n--- רשימת הלקוחות המחוקים ---")
            print_rows(get_all_deleted_customers(), "אין לקוחות מחוקים במערכת")

        elif choice == "6":
            print("\n--- רשימת כל הלקוחות (פעילים ומחוקים) ---")
            print_rows(get_all_customers_including_deleted(), "אין לקוחות במערכת")

        elif choice == "7":
            invoice_number = input("הזן מספר חשבונית: ")
            customer_id = input("הזן מספר לקוח: ")
            amount = input("הזן סכום: ")
            invoice_date = input("הזן תאריך (YYYY-MM-DD): ")
            new_id = add_invoice(invoice_number, customer_id, amount, invoice_date)
            if new_id is not None:
                print(f"החשבונית נוצרה בהצלחה! מזהה: {new_id}")

        elif choice == "8":
            customer_id = input("הזן מספר לקוח: ")
            print("\n--- חשבוניות הלקוח (פעילות) ---")
            print_rows(get_customer_invoices(customer_id), "אין חשבוניות פעילות ללקוח זה")

        elif choice == "9":
            customer_id = input("הזן מספר לקוח: ")
            print("\n--- היסטוריית תורים (פעילים) ---")
            print_rows(get_customer_appointments(customer_id), "אין תורים פעילים ללקוח זה")

        elif choice == "10":
            invoice_id = input("הזן מזהה חשבונית למחיקה: ")
            delete_invoice(invoice_id)

        elif choice == "11":
            invoice_id = input("הזן מזהה חשבונית לשחזור: ")
            undelete_invoice(invoice_id)

        elif choice == "12":
            print("\n--- רשימת החשבוניות הפעילות ---")
            print_rows(get_all_invoices(), "אין חשבוניות פעילות במערכת")

        elif choice == "13":
            print("\n--- רשימת החשבוניות המחוקות ---")
            print_rows(get_all_deleted_invoices(), "אין חשבוניות מחוקות במערכת")

        elif choice == "14":
            print("\n--- רשימת כל החשבוניות (פעילות ומחוקות) ---")
            print_rows(get_all_invoices_including_deleted(), "אין חשבוניות במערכת")

        elif choice == "0":
            break

        else:
            print("בחירה לא תקינה, נסה שוב")


def leads_menu():
    """תפריט ניהול לידים"""
    while True:
        print("\n----- ניהול לידים -----")
        print("1. הוספת ליד חדש")
        print("2. הצגת כל הלידים הפעילים")
        print("3. עדכון סטטוס ליד")
        print("4. המרת ליד ללקוח")
        print("5. מחיקת ליד")
        print("6. שחזור ליד מחוק")
        print("7. הצגת כל הלידים המחוקים")
        print("8. הצגת כל הלידים (פעילים ומחוקים)")
        print("0. חזרה לתפריט הראשי")
        choice = input("בחר אפשרות: ")

        if choice == "1":
            full_name = input("הזן שם מלא: ")
            phone = input("הזן טלפון: ")
            source = input("הזן מקור פנייה: ")
            notes = input("הזן הערות: ")
            new_id = add_lead(full_name, phone, source, notes)
            print(f"הליד נוסף בהצלחה! מספר ליד: {new_id}")

        elif choice == "2":
            print("\n--- רשימת הלידים הפעילים ---")
            print_rows(get_all_leads(), "אין לידים פעילים במערכת")

        elif choice == "3":
            lead_id = input("הזן מספר ליד: ")
            new_status = input("הזן סטטוס חדש (חדש / בטיפול / הפך ללקוח / נדחה): ")
            update_lead_status(lead_id, new_status)

        elif choice == "4":
            lead_id = input("הזן מספר ליד להמרה: ")
            new_customer_id = convert_lead_to_customer(lead_id)
            if new_customer_id is not None:
                print(f"הליד הומר ללקוח בהצלחה! מספר לקוח: {new_customer_id}")

        elif choice == "5":
            lead_id = input("הזן מספר ליד למחיקה: ")
            delete_lead(lead_id)

        elif choice == "6":
            lead_id = input("הזן מספר ליד לשחזור: ")
            undelete_lead(lead_id)

        elif choice == "7":
            print("\n--- רשימת הלידים המחוקים ---")
            print_rows(get_all_deleted_leads(), "אין לידים מחוקים במערכת")

        elif choice == "8":
            print("\n--- רשימת כל הלידים (פעילים ומחוקים) ---")
            print_rows(get_all_leads_including_deleted(), "אין לידים במערכת")

        elif choice == "0":
            break

        else:
            print("בחירה לא תקינה, נסה שוב")


# ==================== תפריט ראשי ====================

def print_main_menu():
    print("\n===== מערכת ניהול תורים - משרד ייעוץ פיננסי =====")
    print("1. ניהול תורים")
    print("2. ניהול לקוחות וחשבוניות")
    print("3. ניהול לידים")
    print("0. יציאה")


def main():
    init_db()                       # מוודא שהטבלאות קיימות
    seed_if_empty()                 # ממלאת נתוני דוגמה אם המערכת ריקה
    while True:
        print_main_menu()
        choice = input("בחר אפשרות: ")

        if choice == "1":
            appointments_menu()
        elif choice == "2":
            customers_menu()
        elif choice == "3":
            leads_menu()
        elif choice == "0":
            print("להתראות!")
            break
        else:
            print("בחירה לא תקינה, נסה שוב")


if __name__ == "__main__":
    main()
