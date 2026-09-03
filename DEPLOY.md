# הוראות פריסה — בוט תורים

## הרצה מקומית

דורש שני תהליכים נפרדים, כל אחד בטרמינל/חלון משלו, שניהם מריצים
מתיקיית השורש של הפרויקט (חשוב: לא מתוך `chatbot`, אחרת ה-DB לא יימצא).

**1. שכבת ה-API** (פורט 5001):
```bash
python chatbot/api.py
```

**2. ממשק הצ'אט** (פורט 5002):
```bash
python chatbot/web.py
```

פותחים דפדפן בכתובת `http://127.0.0.1:5002`.

### הכנת נתונים (פעם ראשונה בלבד, על DB חדש)

```bash
python -c "from db import init_db; init_db()"
python -c "from seed_data import seed_if_empty; seed_if_empty()"
python chatbot/setup_final_data.py
```

הסקריפט השלישי מוסיף עמודת `national_id`, ממלא תעודות זהות,
ומוסיף את לקוחות הבדיקה (רותם מירון, רותם שרעבי, עדי כרמלי).
בטוח להרצה חוזרת — לא משכפל נתונים.

### משתני סביבה

צריך קובץ `chatbot/.env` (לא נכנס לגיט) עם שורה אחת:

בלעדיו הבוט ממשיך לעבוד, רק בלי שכבת ה-NLU (נופל על חילוץ בקוד).





---

## פריסה לשרת (PythonAnywhere)

הפריסה **אינה** אוטומטית. תהליך משיכה ידני מגיטהאב, לפי הצורך.

### התקנה ראשונית

**1. Bash console חדש**, ואז:
```bash
git clone -b Final_Project_Financial_Advirosy https://github.com/oriaviv217-art/mid_test.git
cd mid_test
```

**2. התקנת חבילות:**
```bash
pip install --user -r requirements.txt
pip install --user requests google-genai python-dotenv
```

**3. בניית ה-DB** (הוא לא נכנס לגיט):
```bash
python3.13 -c "from db import init_db; init_db()"
python3.13 -c "from seed_data import seed_if_empty; seed_if_empty()"
python3.13 chatbot/setup_final_data.py
```

**4. יצירת `.env`** (הקובץ לא נכנס לגיט, צריך ליצור בכל שרת חדש):
```bash
nano chatbot/.env
```
שורה אחת: `GEMINI_API_KEY=<המפתח>`. שמירה: `Ctrl+O`, Enter, `Ctrl+X`.

### הגדרת ה-Web App

בחשבון החינמי יש אפליקציית web אחת בלבד. הבוט רץ ב-**מצב LOCAL**:
`api_client.py` קורא ישירות לפונקציות פייתון במקום דרך HTTP,
כך שלא צריך שני שרתים נפרדים.

**1.** לשונית **Web** בדשבורד ← **Add a new web app** ← **Manual configuration** ← **Python 3.13**

**2.** תחת "Code", לעדכן:
- Source code: `/home/<username>/mid_test`
- Working directory: `/home/<username>/mid_test`

**3.** לערוך את קובץ ה-WSGI (הקישור תחת "WSGI configuration file"),
למחוק את התוכן ולהדביק:

```python
import sys
import os

path = '/home/<username>/mid_test'
if path not in sys.path:
    sys.path.insert(0, path)

chatbot_path = '/home/<username>/mid_test/chatbot'
if chatbot_path not in sys.path:
    sys.path.insert(0, chatbot_path)

os.environ['USE_LOCAL_API'] = '1'
os.chdir(path)

from web import app as application  # noqa
```

(להחליף `<username>` בשם המשתמש האמיתי בפייתון-אנווייר.)

**4.** Save, ואז לחזור ללשונית Web וללחוץ **Reload**.

### עדכון קוד קיים (אחרי push לגיטהאב)

**Bash console**, בתוך `mid_test`:
```bash
git pull
```

אם קובץ ספציפי נערך גם ידנית בשרת ומונע merge:
```bash
git checkout -- <path/to/file>
git pull
```

לאחר משיכת קוד חדש — חובה **Reload** בלשונית Web כדי שהשינוי ייכנס לתוקף.

### בדיקה שהכל עובד

```bash
cd chatbot
USE_LOCAL_API=1 python3.13 test_client.py
python3.13 test_nlu.py
```

ובדפדפן: `https://<username>.pythonanywhere.com`

---

## נקודות תקלה נפוצות

| תסמין | סיבה | פתרון |
|---|---|---|
| `sqlite3.OperationalError: no such table` | הורצה פקודה מתוך `chatbot/` במקום מהשורש | לחזור לשורש הפרויקט |
| NLU מחזיר `None` תמיד | מפתח Gemini לא נטען, או שם מודל לא קיים | לבדוק `chatbot/.env`, ולעדכן `MODEL` ב-`nlu.py` לפי `client.models.list()` |
| שגיאת 404 על מודל Gemini | גוגל הפסיקה לתמוך בשם המודל | לעדכן את `MODEL` ב-`chatbot/nlu.py` |
| שגיאת 503 מ-Gemini | עומס זמני בצד גוגל | לא תקלה בקוד — הבוט נופל אוטומטית לחילוץ בקוד |
| הכתובת הציבורית לא עולה | שכחו Reload אחרי שינוי קוד/WSGI | ללחוץ Reload בלשונית Web |