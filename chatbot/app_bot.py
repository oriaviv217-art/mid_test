"""ממשק הצ'אט. להרצה מהשורש: python -m streamlit run chatbot/app_bot.py"""
import streamlit as st

st.title("בוט תורים")

# הזיכרון של השיחה - שורד בין הודעה להודעה
if "messages" not in st.session_state:
    st.session_state.messages = []

# מציג את כל ההיסטוריה מחדש בכל ריצה
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# תיבת הקלט בתחתית המסך
user_text = st.chat_input("כתוב הודעה...")

if user_text:
    st.session_state.messages.append({"role": "user", "content": user_text})
    with st.chat_message("user"):
        st.write(user_text)

    reply = f"קיבלתי: {user_text}"   # זמני - כאן ייכנס הבוט האמיתי
    st.session_state.messages.append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)