"""ממשק הצ'אט. להרצה מהשורש: python chatbot/web.py"""
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session

import bot

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# ---- Server-side session (filesystem) ----
# עובר מ-cookie בצד הלקוח (מוגבל ל-4KB) לקבצים בצד השרת.
# זה מתקן שתי בעיות:
#   1. "התחל שיחה מחדש" לא עבד - כי ה-cookie חרג מ-4KB ו-session.clear() נכשל בשקט.
#   2. הבוט החזיר תשובות ישנות - כי ה-state לא התעדכן לאחר שה-cookie גדש.
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_FILE_DIR"] = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "flask_session_data"
)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True  # חותמת על session ID למניעת זיוף
Session(app)


@app.route("/")
def chat_page():
    """מציג את עמוד הצ'אט עם היסטוריית ההודעות."""
    messages = session.get("messages", [])
    return render_template("chat.html", messages=messages)


@app.route("/send", methods=["POST"])
def send_message():
    """מקבל הודעה, מעביר לבוט, ושומר את שתיהן."""
    user_text = request.form.get("message", "").strip()
    if not user_text:
        return redirect(url_for("chat_page"))

    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_text})

    conv = session.get("conv", bot.new_state())
    reply, conv = bot.handle_message(user_text, conv)
    session["conv"] = conv

    messages.append({"role": "bot", "content": reply})
    session["messages"] = messages
    return redirect(url_for("chat_page"))


@app.route("/reset", methods=["POST"])
def reset():
    """מנקה את השיחה - שימושי בבדיקות."""
    session.clear()
    return redirect(url_for("chat_page"))


if __name__ == "__main__":
    app.run(port=5002, debug=True)