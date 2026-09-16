"""ממשק הצ'אט — Blueprint לשילוב ב-app.py הראשי.
להרצה עצמאית לפיתוח: python chatbot/web.py
"""
import os
import sys
from pathlib import Path
from flask import Blueprint, render_template, request, redirect, url_for, session

# מאפשר import של bot ו-api_client גם כשמריצים מהשורש
sys.path.insert(0, str(Path(__file__).resolve().parent))

import bot

bp = Blueprint(
    "chatbot",
    __name__,
    template_folder="templates",
)


@bp.route("/")
def chat_page():
    """מציג את עמוד הצ'אט עם היסטוריית ההודעות."""
    messages = session.get("messages", [])
    return render_template("chat.html", messages=messages)


@bp.route("/send", methods=["POST"])
def send_message():
    """מקבל הודעה, מעביר לבוט, ושומר את שתיהן."""
    user_text = request.form.get("message", "").strip()
    if not user_text:
        return redirect(url_for("chatbot.chat_page"))

    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_text})

    conv = session.get("conv", bot.new_state())
    reply, conv = bot.handle_message(user_text, conv)
    session["conv"] = conv

    messages.append({"role": "bot", "content": reply})
    session["messages"] = messages
    return redirect(url_for("chatbot.chat_page"))


@bp.route("/reset", methods=["POST"])
def reset():
    """מנקה את השיחה - שימושי בבדיקות."""
    session.clear()
    return redirect(url_for("chatbot.chat_page"))


# --- הרצה עצמאית לפיתוח בלבד ---
if __name__ == "__main__":
    from flask import Flask
    from flask_session import Session

    _app = Flask(__name__)
    _app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")
    _app.config["SESSION_TYPE"] = "filesystem"
    _app.config["SESSION_FILE_DIR"] = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "flask_session_data"
    )
    _app.config["SESSION_PERMANENT"] = False
    _app.config["SESSION_USE_SIGNER"] = True
    Session(_app)
    _app.register_blueprint(bp)
    _app.run(port=5002, debug=True)