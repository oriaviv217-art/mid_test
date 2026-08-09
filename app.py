import os
import threading
import webbrowser

from flask import Flask, render_template, request, redirect, url_for, flash

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

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

init_db()
seed_if_empty()


@app.context_processor
def inject_customer_names():
    """מאפשרת לתבניות להציג את שם הלקוח לצד מזהה הלקוח (גם עבור לקוחות מחוקים)."""
    return {"customer_names": {c[0]: c[1] for c in get_all_customers_including_deleted()}}


# ==================== דף בית ====================

@app.route("/")
def index():
    return render_template(
        "index.html",
        customers_count=len(get_all_customers()),
        appointments_count=len(get_all_appointments()),
        invoices_count=len(get_all_invoices()),
        leads_count=len(get_all_leads()),
    )


# ==================== לקוחות ====================

@app.route("/customers")
def customers_list():
    return render_template("customers.html", customers=get_all_customers(), mode="active")


@app.route("/customers/deleted")
def customers_deleted():
    return render_template("customers.html", customers=get_all_deleted_customers(), mode="deleted")


@app.route("/customers/all")
def customers_all():
    return render_template("customers.html", customers=get_all_customers_including_deleted(), mode="all")


@app.route("/customers/add", methods=["POST"])
def customers_add():
    full_name = request.form.get("full_name", "").strip()
    if not full_name:
        flash("יש להזין שם מלא", "error")
        return redirect(url_for("customers_list"))
    new_id = add_customer(
        full_name,
        request.form.get("phone") or None,
        request.form.get("email") or None,
        request.form.get("address") or None,
    )
    flash(f"הלקוח נוסף בהצלחה! מספר לקוח: {new_id}", "success")
    return redirect(url_for("customers_list"))


@app.route("/customers/<int:customer_id>/delete", methods=["POST"])
def customers_delete(customer_id):
    if delete_customer(customer_id):
        flash("הלקוח נמחק בהצלחה (כולל התורים והחשבוניות שלו)", "success")
    else:
        flash("לא נמצא לקוח פעיל עם המספר הזה", "error")
    return redirect(request.referrer or url_for("customers_list"))


@app.route("/customers/<int:customer_id>/undelete", methods=["POST"])
def customers_undelete(customer_id):
    if undelete_customer(customer_id):
        flash("הלקוח שוחזר בהצלחה", "success")
    else:
        flash("לא נמצא לקוח מחוק עם המספר הזה", "error")
    return redirect(request.referrer or url_for("customers_deleted"))


@app.route("/customers/<int:customer_id>")
def customer_detail(customer_id):
    customer = next(
        (c for c in get_all_customers_including_deleted() if c[0] == customer_id),
        None,
    )
    if customer is None:
        flash("לקוח לא נמצא", "error")
        return redirect(url_for("customers_list"))
    return render_template(
        "customer_detail.html",
        customer=customer,
        invoices=get_customer_invoices(customer_id),
        appointments=get_customer_appointments(customer_id),
    )


# ==================== חשבוניות ====================

@app.route("/invoices")
def invoices_list():
    return render_template("invoices.html", invoices=get_all_invoices(), mode="active", customers=get_all_customers())


@app.route("/invoices/deleted")
def invoices_deleted():
    return render_template("invoices.html", invoices=get_all_deleted_invoices(), mode="deleted", customers=get_all_customers())


@app.route("/invoices/all")
def invoices_all():
    return render_template("invoices.html", invoices=get_all_invoices_including_deleted(), mode="all", customers=get_all_customers())


@app.route("/invoices/add", methods=["POST"])
def invoices_add():
    new_id = add_invoice(
        request.form.get("invoice_number", "").strip(),
        request.form.get("customer_id"),
        request.form.get("amount"),
        request.form.get("invoice_date"),
    )
    if new_id is not None:
        flash(f"החשבונית נוצרה בהצלחה! מזהה: {new_id}", "success")
    else:
        flash("שגיאה ביצירת החשבונית (מספר חשבונית כפול או לקוח לא קיים)", "error")
    return redirect(request.referrer or url_for("invoices_list"))


@app.route("/invoices/<int:invoice_id>/delete", methods=["POST"])
def invoices_delete(invoice_id):
    if delete_invoice(invoice_id):
        flash("החשבונית נמחקה בהצלחה", "success")
    else:
        flash("לא נמצאה חשבונית פעילה עם המספר הזה", "error")
    return redirect(request.referrer or url_for("invoices_list"))


@app.route("/invoices/<int:invoice_id>/undelete", methods=["POST"])
def invoices_undelete(invoice_id):
    if undelete_invoice(invoice_id):
        flash("החשבונית שוחזרה בהצלחה", "success")
    else:
        flash("לא נמצאה חשבונית מחוקה עם המספר הזה", "error")
    return redirect(request.referrer or url_for("invoices_deleted"))


# ==================== תורים ====================

@app.route("/appointments")
def appointments_list():
    return render_template("appointments.html", appointments=get_all_appointments(), mode="active", customers=get_all_customers())


@app.route("/appointments/deleted")
def appointments_deleted():
    return render_template("appointments.html", appointments=get_all_deleted_appointments(), mode="deleted", customers=get_all_customers())


@app.route("/appointments/all")
def appointments_all():
    return render_template("appointments.html", appointments=get_all_appointments_including_deleted(), mode="all", customers=get_all_customers())


@app.route("/appointments/add", methods=["POST"])
def appointments_add():
    new_id = add_appointment(
        request.form.get("customer_id"),
        request.form.get("service_type", "").strip(),
        request.form.get("appointment_date"),
        request.form.get("appointment_time"),
    )
    if new_id is not None:
        flash(f"התור נוצר בהצלחה! מספר תור: {new_id}", "success")
    else:
        flash("שגיאה: מספר לקוח לא קיים במערכת", "error")
    return redirect(url_for("appointments_list"))


@app.route("/appointments/<int:appointment_id>/status", methods=["POST"])
def appointments_status(appointment_id):
    new_status = request.form.get("status")
    if update_appointment_status(appointment_id, new_status):
        flash("סטטוס התור עודכן בהצלחה", "success")
    else:
        flash("לא נמצא תור פעיל עם המספר הזה", "error")
    return redirect(request.referrer or url_for("appointments_list"))


@app.route("/appointments/<int:appointment_id>/delete", methods=["POST"])
def appointments_delete(appointment_id):
    if delete_appointment(appointment_id):
        flash("התור נמחק בהצלחה", "success")
    else:
        flash("לא נמצא תור פעיל למחיקה", "error")
    return redirect(request.referrer or url_for("appointments_list"))


@app.route("/appointments/<int:appointment_id>/undelete", methods=["POST"])
def appointments_undelete(appointment_id):
    if undelete_appointment(appointment_id):
        flash("התור שוחזר בהצלחה", "success")
    else:
        flash("לא נמצא תור מחוק לשחזור", "error")
    return redirect(request.referrer or url_for("appointments_deleted"))


# ==================== לידים ====================

@app.route("/leads")
def leads_list():
    return render_template("leads.html", leads=get_all_leads(), mode="active")


@app.route("/leads/deleted")
def leads_deleted():
    return render_template("leads.html", leads=get_all_deleted_leads(), mode="deleted")


@app.route("/leads/all")
def leads_all():
    return render_template("leads.html", leads=get_all_leads_including_deleted(), mode="all")


@app.route("/leads/add", methods=["POST"])
def leads_add():
    full_name = request.form.get("full_name", "").strip()
    if not full_name:
        flash("יש להזין שם מלא", "error")
        return redirect(url_for("leads_list"))
    new_id = add_lead(
        full_name,
        request.form.get("phone") or None,
        request.form.get("source") or None,
        request.form.get("notes") or None,
    )
    flash(f"הליד נוסף בהצלחה! מספר ליד: {new_id}", "success")
    return redirect(url_for("leads_list"))


@app.route("/leads/<int:lead_id>/status", methods=["POST"])
def leads_status(lead_id):
    new_status = request.form.get("status")
    if update_lead_status(lead_id, new_status):
        flash("סטטוס הליד עודכן בהצלחה", "success")
    else:
        flash("לא נמצא ליד פעיל עם המספר הזה", "error")
    return redirect(request.referrer or url_for("leads_list"))


@app.route("/leads/<int:lead_id>/convert", methods=["POST"])
def leads_convert(lead_id):
    new_customer_id = convert_lead_to_customer(lead_id)
    if new_customer_id is not None:
        flash(f"הליד הומר ללקוח בהצלחה! מספר לקוח: {new_customer_id}", "success")
    else:
        flash("לא נמצא ליד פעיל עם המספר הזה", "error")
    return redirect(request.referrer or url_for("leads_list"))


@app.route("/leads/<int:lead_id>/delete", methods=["POST"])
def leads_delete(lead_id):
    if delete_lead(lead_id):
        flash("הליד נמחק בהצלחה", "success")
    else:
        flash("לא נמצא ליד פעיל עם המספר הזה", "error")
    return redirect(request.referrer or url_for("leads_list"))


@app.route("/leads/<int:lead_id>/undelete", methods=["POST"])
def leads_undelete(lead_id):
    if undelete_lead(lead_id):
        flash("הליד שוחזר בהצלחה", "success")
    else:
        flash("לא נמצא ליד מחוק עם המספר הזה", "error")
    return redirect(request.referrer or url_for("leads_deleted"))


if __name__ == "__main__":
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    port = int(os.environ.get("PORT", 5000))

    # פותחת את הדפדפן אוטומטית כשהשרת עולה. ב-debug mode ה-reloader של Werkzeug
    # מריץ תהליך ילד עם WERKZEUG_RUN_MAIN=true - פותחים רק משם כדי לא לפתוח פעמיים.
    if not debug_mode or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{port}/")).start()

    app.run(host="0.0.0.0", port=port, debug=debug_mode)
