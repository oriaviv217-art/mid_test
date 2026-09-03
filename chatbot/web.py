"""ממשק הצ'אט. להרצה מהשורש: python chatbot/web.py"""
import os
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")


@app.route("/")
def chat_page():
    """מציג את עמוד הצ'אט עם היסטוריית ההודעות."""
    messages = session.get("messages", [])
    return render_template("chat.html", messages=messages)


@app.route("/send", methods=["POST"])
def send_message():
    """מקבל הודעה, מייצר תשובה, שומר את שתיהן."""
    user_text = request.form.get("message", "").strip()
    if not user_text:
        return redirect(url_for("chat_page"))
    messages = session.get("messages", [])
    messages.append({"role": "user", "content": user_text})
    reply = f"קיבלתי: {user_text}"
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
    