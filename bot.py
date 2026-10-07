import streamlit as st
import streamlit.components.v1 as components
import time
import urllib.parse
import sqlite3
import json
from datetime import date

st.set_page_config(
    page_title="DaniFit Pro | פלטפורמת כושר ותזונה מתקדמת",
    page_icon="⚡",
    layout="wide"
)

# --- שכבת מסד נתונים מקומי (SQLite) לשמירה קבועה ---
DB_FILE = "danifit_data.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_data (
            date_str TEXT PRIMARY KEY,
            water_ml INTEGER,
            extra_burned INTEGER,
            logged_items TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS pr_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exercise TEXT,
            weight REAL,
            reps INTEGER,
            custom_res TEXT,
            date_recorded TEXT
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS shopping_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            search TEXT,
            checked INTEGER
        )
    """)
    conn.commit()
    conn.close()

def load_today_data():
    today = str(date.today())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT water_ml, extra_burned, logged_items FROM daily_data WHERE date_str = ?", (today,))
    row = c.fetchone()
    conn.close()
    if row:
        return row[0], row[1], json.loads(row[2])
    return 0, 0, []

def save_today_data(water_ml, extra_burned, logged_items):
    today = str(date.today())
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        INSERT INTO daily_data (date_str, water_ml, extra_burned, logged_items)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(date_str) DO UPDATE SET
            water_ml=excluded.water_ml,
            extra_burned=excluded.extra_burned,
            logged_items=excluded.logged_items
    """, (today, water_ml, extra_burned, json.dumps(logged_items, ensure_ascii=False)))
    conn.commit()
    conn.close()

def load_prs():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, exercise, weight, reps, custom_res, date_recorded FROM pr_records ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    prs = []
    for r in rows:
        prs.append({"id": r[0], "exercise": r[1], "weight": r[2], "reps": r[3], "custom_res": r[4], "date": r[5]})
    return prs

def add_pr(exercise, weight, reps, custom_res=""):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT INTO pr_records (exercise, weight, reps, custom_res, date_recorded) VALUES (?, ?, ?, ?, ?)",
              (exercise, weight, reps, custom_res, str(date.today())))
    conn.commit()
    conn.close()

def delete_pr(pr_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM pr_records WHERE id = ?", (pr_id,))
    conn.commit()
    conn.close()

# אתחול הנתונים בריצה ראשונה
init_db()
if "db_initialized" not in st.session_state:
    w, b, items = load_today_data()
    st.session_state.water_ml = w
    st.session_state.extra_burned_cals = b
    st.session_state.logged_items = items
    st.session_state.db_initialized = True

if "shopping_list" not in st.session_state:
    st.session_state.shopping_list = [
        {"item": "חזה עוף טרי (1 ק״ג)", "search": "חזה עוף", "checked": False},
        {"item": "טונה במים (4 קופסאות)", "search": "טונה במים", "checked": False},
        {"item": "יוגורט חלבון PRO 20g", "search": "יוגורט פרו", "checked": False},
        {"item": "גבינת קוטג' 5%", "search": "קוטג 5", "checked": False},
        {"item": "תבנית ביצים L", "search": "ביצים L", "checked": False},
        {"item": "אורז בסמטי (1 ק״ג)", "search": "אורז בסמטי", "checked": False},
        {"item": "שיבולת שועל דקה", "search": "שיבולת שועל", "checked": False},
        {"item": "טורטיות מקמח מלא", "search": "טורטיות", "checked": False},
        {"item": "שמן זית כתית מעולה", "search": "שמן זית", "checked": False}
    ]

# פונקציית הדפסה
def print_button(text_content: str, title: str, button_id: str):
    html_safe_text = text_content.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$")
    print_html = f"""
    <button onclick="printDoc_{button_id}()" style="
        width: 100%;
        background-color: #0f172a;
        color: #ffffff;
        border: none;
        border-radius: 12px;
        padding: 12px 20px;
        font-weight: 800;
        font-size: 1rem;
        cursor: pointer;
        font-family: inherit;
        box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
        transition: 0.2s;
    ">🖨️ הדפס / שמור כ-PDF</button>

    <script>
    function printDoc_{button_id}() {{
        var content = `{html_safe_text}`;
        var win = window.open('', '', 'height=700,width=900');
        win.document.write('<html><head><title>{title}</title>');
        win.document.write('<style>');
        win.document.write('body {{ font-family: Arial, sans-serif; direction: rtl; text-align: right; padding: 30px; color: #111; line-height: 1.6; }}');
        win.document.write('pre {{ white-space: pre-wrap; font-family: inherit; font-size: 14px; background: #f8fafc; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }}');
        win.document.write('</style></head><body>');
        win.document.write('<h2 style="color: #2563eb; text-align: center; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">{title}</h2>');
        win.document.write('<pre>' + content + '</pre>');
        win.document.write('</body></html>');
        win.document.close();
        win.focus();
        setTimeout(function() {{
            win.print();
            win.close();
        }}, 400);
    }}
    </script>
    """
    components.html(print_html, height=55)

# עיצוב בהיר ונקי (Light Mode)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;600;700;800&family=Rubik:wght@400;600;700;800;900&display=swap');
    
    html, body, [data-testid="stAppViewContainer"], .stApp {
        background-color: #f8fafc !important;
        font-family: 'Assistant', 'Rubik', sans-serif !important;
        direction: rtl;
        text-align: right;
        color: #1e293b !important;
    }

    .top-header-bar {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        padding: 4px 10px 10px 10px;
    }

    .bsd-badge {
        font-weight: 800;
        font-size: 1.05rem;
        color: #64748b;
        letter-spacing: 1.5px;
    }

    .brand-header {
        background: linear-gradient(135deg, #ffffff 0%, #f1f5f9 100%);
        padding: 32px 24px;
        border-radius: 20px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.04);
        text-align: center;
        margin-bottom: 25px;
    }
    
    .brand-title {
        font-family: 'Rubik', sans-serif;
        font-size: 3rem;
        font-weight: 900;
        color: #0f172a;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .brand-title span {
        color: #2563eb;
    }

    .brand-subtitle {
        font-size: 1.25rem;
        color: #2563eb;
        font-weight: 800;
        margin-top: 6px;
    }

    .brand-description {
        font-size: 1.02rem;
        color: #475569;
        font-weight: 500;
        max-width: 800px;
        margin: 12px auto 18px auto;
        line-height: 1.6;
    }

    .brand-badges {
        display: flex;
        justify-content: center;
        gap: 10px;
        flex-wrap: wrap;
    }

    .badge-pill {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        color: #334155;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.88rem;
        font-weight: 700;
        box-shadow: 0 2px 5px rgba(0,0,0,0.02);
    }

    .card-box {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
    }

    .story-card {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #ffffff;
        border-radius: 20px;
        padding: 30px;
        text-align: center;
        max-width: 480px;
        margin: 0 auto 20px auto;
        box-shadow: 0 15px 35px rgba(15, 23, 42, 0.3);
        border: 2px solid #38bdf8;
    }

    .water-box {
        background: #f0f9ff;
        border: 1px solid #bae6fd;
        padding: 18px;
        border-radius: 16px;
        margin-bottom: 20px;
    }

    .shabbat-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        padding: 20px;
        border-radius: 16px;
        margin-bottom: 20px;
    }

    .suggest-box {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        padding: 18px;
        border-radius: 16px;
        margin-top: 15px;
        margin-bottom: 20px;
    }

    .quick-shop-btn {
        display: inline-block;
        text-align: center;
        background: #eff6ff;
        color: #2563eb !important;
        border: 1px solid #bfdbfe;
        padding: 6px 14px;
        border-radius: 8px;
        font-weight: 700;
        font-size: 0.88rem;
        text-decoration: none;
        transition: 0.2s;
    }

    .quick-shop-btn:hover {
        background: #2563eb;
        color: #ffffff !important;
    }

    h1, h2, h3, .stSubheader {
        color: #0f172a !important;
        font-weight: 800 !important;
        border-bottom: 2px solid #2563eb;
        padding-bottom: 8px;
        margin-top: 20px !important;
        margin-bottom: 18px !important;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: #ffffff;
        padding: 8px 12px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
    }

    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
        border-radius: 12px;
        padding: 10px 22px;
        font-weight: 700;
        font-size: 1.05rem;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.25);
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        color: #ffffff !important;
        border: none;
        border-radius: 12px;
        padding: 14px 24px;
        font-size: 1.1rem;
        font-weight: 800;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.25);
        transition: all 0.2s ease;
    }

    input, textarea, .stSelectbox {
        direction: rtl !important;
        text-align: right !important;
        background-color: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }

    label {
        color: #334155 !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

# כיתוב בס"ד
st.markdown("""
<div class="top-header-bar">
    <span class="bsd-badge">בס״ד</span>
</div>
""", unsafe_allow_html=True)

# מאגר מזונות
FOOD_DATABASE = {
    "חזה עוף צלוי": {"cal": 165, "p": 31.0, "c": 0.0, "f": 3.6, "unit": "100 גרם"},
    "פילה דג סלמון": {"cal": 208, "p": 20.0, "c": 0.0, "f": 13.0, "unit": "100 גרם"},
    "טונה במים (מסוננת)": {"cal": 130, "p": 28.0, "c": 0.0, "f": 1.0, "unit": "קופסה (נטו)"},
    "ביצה שלמה (L)": {"cal": 75, "p": 6.5, "c": 0.5, "f": 5.0, "unit": "יחידה"},
    "חלבון ביצה (לבן בלבד)": {"cal": 17, "p": 3.6, "c": 0.2, "f": 0.1, "unit": "יחידה"},
    "יוגורט חלבון (PRO / GO)": {"cal": 125, "p": 20.0, "c": 6.5, "f": 0.5, "unit": "גביע (200 גרם)"},
    "גבינה לבנה 5%": {"cal": 95, "p": 10.0, "c": 4.0, "f": 5.0, "unit": "100 גרם"},
    "גבינת קוטג' 5%": {"cal": 95, "p": 11.0, "c": 3.5, "f": 5.0, "unit": "100 גרם"},
    "אורז בסמטי מבושל": {"cal": 130, "p": 2.7, "c": 28.0, "f": 0.3, "unit": "100 גרם"},
    "פסטה מבושלת": {"cal": 155, "p": 5.5, "c": 30.0, "f": 1.0, "unit": "100 גרם"},
    "בטטה אפויה": {"cal": 90, "p": 2.0, "c": 21.0, "f": 0.1, "unit": "100 גרם"},
    "שיבולת שועל": {"cal": 150, "p": 5.0, "c": 27.0, "f": 3.0, "unit": "40 גרם"},
    "לחם מלא": {"cal": 75, "p": 3.5, "c": 13.0, "f": 1.0, "unit": "פרוסה"},
    "בננה בינונית": {"cal": 105, "p": 1.3, "c": 27.0, "f": 0.3, "unit": "יחידה"},
    "תפוח עץ": {"cal": 80, "p": 0.4, "c": 21.0, "f": 0.2, "unit": "יחידה"},
    "שמן זית כתית מעולה": {"cal": 120, "p": 0.0, "c": 0.0, "f": 13.5, "unit": "כף"},
    "טחינה גולמית": {"cal": 100, "p": 3.0, "c": 2.0, "f": 9.0, "unit": "כף"},
    "אבוקדו": {"cal": 160, "p": 2.0, "c": 8.5, "f": 14.5, "unit": "חצי פרי"}
}

# מאגר שבת
SHABBAT_FOOD_DB = {
    "כוסית יין קידוש / תירוש (100 מ״ל)": {"cal": 85, "p": 0.2, "c": 18.0, "f": 0.0},
    "פרוסת חלת שבת (50 גרם)": {"cal": 145, "p": 4.5, "c": 26.0, "f": 2.5},
    "מנת דג חריף (אמנון ברוטב, 150 גרם)": {"cal": 210, "p": 28.0, "c": 4.0, "f": 9.0},
    "מנת פילה סלמון עשבי תיבול (150 גרם)": {"cal": 310, "p": 30.0, "c": 0.0, "f": 20.0},
    "כרע עוף / ירך בתנור (יחידה ללא עור)": {"cal": 220, "p": 26.0, "c": 1.0, "f": 12.0},
    "מנת צלי בקר מבושל (150 גרם)": {"cal": 290, "p": 36.0, "c": 2.0, "f": 15.0},
    "מנת חמין / צ'ולנט מסורתית עם בשר": {"cal": 460, "p": 28.0, "c": 45.0, "f": 18.0},
    "צלחת סלטי שבת מבושלים (3 כפות)": {"cal": 130, "p": 1.8, "c": 9.0, "f": 10.0}
}

# מתכונים
RECIPES_DATA = [
    {
        "id": "rec_wrap",
        "title": "🌯 טורטיית חביתה, קוטג' ובצל ירוק",
        "cat": "⚡ מהיר עד 15 דקות",
        "time": "8 דקות",
        "cal": 365, "p": 26.0, "c": 26.0, "f": 14.0,
        "ingredients": [
            "1 טורטייה בינונית", "ביצה שלמה + חלבון ביצה", "כף וחצי קוטג' 5%",
            "בצל ירוק ועגבנייה פרוסה", "מלח, פלפל ותרסיס שמן"
        ],
        "steps": ["מטגנים חביתה עם הבצל והעגבנייה.", "מורחים קוטג' על הטורטייה.", "מגלגלים וצורבים במחבת לדקה."]
    },
    {
        "id": "rec_chicken_bowl",
        "title": "🍗 קערת חזה עוף ואורז בסמטי",
        "cat": "🥩 ארוחות צהריים וערב",
        "time": "15 דקות",
        "cal": 440, "p": 46.0, "c": 44.0, "f": 6.5,
        "ingredients": ["150 גרם חזה עוף", "150 גרם אורז בסמטי מבושל", "כפית שמן זית", "סויה וסילאן", "ירק ירוק מאודה"],
        "steps": ["מקפיצים רצועות חזה עוף כ-6 דק'.", "מוסיפים סויה וסילאן לזיגוג.", "מגישים עם האורז החם."]
    },
    {
        "id": "rec_tuna_salad",
        "title": "🐟 סלט טונה, ביצה ואבוקדו",
        "cat": "⚡ מהיר עד 15 דקות",
        "time": "5 דקות",
        "cal": 380, "p": 38.0, "c": 8.0, "f": 19.0,
        "ingredients": ["1 טונה במים מסוננת", "1 ביצה קשה", "1/3 אבוקדו", "סלט ירקות קצוץ", "שמן זית ולימון"],
        "steps": ["קוצצים ירקות לקערה.", "מוסיפים טונה, ביצה ואבוקדו.", "מתבלים בלימון ושמן זית."]
    },
    {
        "id": "rec_shake",
        "title": "🥤 שייק מפלצת חלבון ובננה",
        "cat": "🥤 שייקים ונשנושים",
        "time": "3 דקות",
        "cal": 320, "p": 32.0, "c": 36.0, "f": 4.5,
        "ingredients": ["1 סקופ אבקת חלבון", "1 בננה קפואה", "200 מ״ל חלב שקדים/רגיל", "כף שיבולת שועל", "קרח"],
        "steps": ["מכניסים את כל המצרכים לבלנדר.", "טוחנים 45 שניות ושותים מיד."]
    }
]

# כותרת ראשית
st.markdown("""
<div class="brand-header">
    <div class="brand-title">⚡ <span>DaniFit</span> Pro</div>
    <div class="brand-subtitle">הפלטפורמה המקצועית והחכמה לתזונה, חיטוב וכושר שיא</div>
    <div class="brand-description">
        מערכת מתקדמת עם שמירת נתונים קבועה: מעקב קלוריות חכם וסוגר פינות, סריקת מנות במצלמה,
        הזמנת קניות בלחיצה לסופר, כרטיסיית הישגים שבועית לסטורי, סעודות שבת ומרכז אימוני כוח וריצה.
    </div>
    <div class="brand-badges">
        <span class="badge-pill">💾 שמירת נתונים קבועה (SQLite)</span>
        <span class="badge-pill">📸 מצלמת AI לסריקת אוכל</span>
        <span class="badge-pill">🛒 הזמנת קניות בלחיצה לסופר</span>
        <span class="badge-pill">📲 כרטיסיית סיכום שבועית לסטורי</span>
        <span class="badge-pill">🧘 סדרת חימום ומתיחות</span>
    </div>
</div>
""", unsafe_allow_html=True)

# 8 טאבים שלמים
tab_bmi, tab_nutrition, tab_ai_cam, tab_story, tab_warmup, tab_shabbat, tab_shopping, tab_workout = st.tabs([
    "📊 מחשבון מדדים ותפריט",
    "🥗 יומן ומעקב קלוריות חכם",
    "📸 מצלמת AI לסריקת מנות",
    "📲 סיכום שבועי לסטורי",
    "🧘 חימום ומתיחות דינמי",
    "🕯️ מחשבון סעודות שבת",
    "🛒 רשימת קניות לסופר",
    "🏋️ מרכז אימונים וכוח"
])

# --- טאב 1: מדדים ותפריט ---
with tab_bmi:
    st.subheader("📊 אבחון מדדים אישי ובניית תפריט מדויק")
    col1, col2, col3 = st.columns(3)
    with col1:
        weight = st.number_input("משקל (ב-ק״ג):", min_value=35.0, max_value=160.0, value=71.0, step=0.5)
        age = st.number_input("גיל:", min_value=12, max_value=80, value=17, step=1)
    with col2:
        height_cm = st.number_input("גובה (ב-ס״מ):", min_value=120, max_value=220, value=175, step=1)
        activity = st.selectbox("רמת פעילות גופנית:", [
            "יושבני (ללא אימונים)",
            "פעילות קלה (1–2 אימונים בשבוע)",
            "פעילות בינונית (3–4 אימונים בשבוע)",
            "פעילות גבוהה (5+ אימונים בשבוע / ספורטאי)"
        ])
    with col3:
        goal = st.selectbox("מטרת היעד:", [
            "חיטוב וירידה באחוזי שומן",
            "בניית מסת שריר נקייה (Lean Bulk)",
            "שיפור סיבולת וביצועים"
        ])
        diet_pref = st.selectbox("העדפת תזונה:", ["סטנדרט (כולל עוף ובקר)", "עשיר דגים ומוצרי חלב", "צמחוני"])

    if st.button("בנה תפריט תזונה מפורט ומותאם אישית 🎯"):
        height_m = height_cm / 100
        bmi_val = round(weight / (height_m ** 2), 1)
        act_factors = {"יושבני (ללא אימונים)": 1.2, "פעילות קלה (1–2 אימונים בשבוע)": 1.375, "פעילות בינונית (3–4 אימונים בשבוע)": 1.55, "פעילות גבוהה (5+ אימונים בשבוע / ספורטאי)": 1.725}
        factor = act_factors[activity]
        bmr = (10 * weight) + (6.25 * height_cm) - (5 * age) + 5
        tdee = int(bmr * factor)

        if "חיטוב" in goal:
            target_cal = int(tdee - (tdee * 0.18))
            protein_g = int(weight * 2.1)
            fat_g = int(weight * 0.8)
        elif "מסת שריר" in goal:
            target_cal = int(tdee + 350)
            protein_g = int(weight * 2.0)
            fat_g = int(weight * 1.0)
        else:
            target_cal = tdee
            protein_g = int(weight * 1.7)
            fat_g = int(weight * 0.9)

        carb_cals = target_cal - ((protein_g * 4) + (fat_g * 9))
        carb_g = max(int(carb_cals / 4), 80)

        st.session_state["user_target_cal"] = target_cal
        st.session_state["user_target_p"] = protein_g

        chicken_portion = int(((protein_g * 0.40) / 31.0) * 100)
        rice_portion = int(((carb_g * 0.40) / 28.0) * 100)

        st.success(f"מדד BMI: **{bmi_val}** | יעד: **{target_cal} קק\"ל** | חלבון: **{protein_g} גרם** | פחמימות: **{carb_g} גרם** | שומן: **{fat_g} גרם**")

        menu_text = f"""תוכנית תזונה אישית - DaniFit Pro
נתונים: משקל {weight} ק"ג | גובה {height_cm} ס"מ | BMI: {bmi_val}
יעד קלורי: {target_cal} קק"ל | חלבון: {protein_g}g | פחמימה: {carb_g}g | שומן: {fat_g}g
• ארוחת בוקר: 2-3 ביצים, 2 פרוסות לחם מלא, כף טחינה, ירקות.
• ארוחת צהריים: {chicken_portion} גרם חזה עוף שקול מבושל + {rice_portion} גרם אורז בסמטי + סלט ושמן זית.
• ארוחת ביניים: יוגורט חלבון PRO 20g + פרי + 10 שקדים.
• ארוחת ערב: קופסת טונה במים / 180 גרם קוטג' 5% + 2 פרוסות לחם מלא + אבוקדו."""
        st.session_state["saved_menu_text"] = menu_text

    if "saved_menu_text" in st.session_state:
        st.text_area("📋 התוכנית שהופקה:", value=st.session_state["saved_menu_text"], height=200)

# --- טאב 2: יומן קלוריות חכם (עם שמירה אוטומטית למסד) ---
with tab_nutrition:
    st.subheader("🥗 יומן מעקב קלוריות ומאקרו בזמן אמת (נשמר אוטומטית)")

    # סרגל מים
    st.markdown('<div class="water-box">', unsafe_allow_html=True)
    w_col1, w_col2, w_col3, w_col4 = st.columns([3, 1.2, 1.2, 1])
    with w_col1:
        water_target = 3000
        water_progress = min(st.session_state.water_ml / water_target, 1.0)
        st.markdown(f"💧 **מעקב שתיית מים:** {st.session_state.water_ml} מ״ל מתוך {water_target} מ״ל")
        st.progress(water_progress)
    with w_col2:
        if st.button("🥤 +250 מ״ל", key="btn_w_250"):
            st.session_state.water_ml += 250
            save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
            st.rerun()
    with w_col3:
        if st.button("🍶 +500 מ״ל", key="btn_w_500"):
            st.session_state.water_ml += 500
            save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
            st.rerun()
    with w_col4:
        if st.button("🔄 אפס מים", key="btn_w_reset"):
            st.session_state.water_ml = 0
            save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    base_cal_target = st.session_state.get("user_target_cal", 2200)
    user_p_target = st.session_state.get("user_target_p", 140)
    final_cal_target = base_cal_target + st.session_state.extra_burned_cals

    # הוספת מאכלים
    tab_add_quick, tab_add_custom = st.tabs(["⚡ הוספה מהירה ממאגר", "✏️ הוספה ידנית"])
    with tab_add_quick:
        qc_meal, qc1, qc2, qc3 = st.columns([2, 3, 2, 2])
        with qc_meal:
            meal_type = st.selectbox("ארוחה:", ["ארוחת בוקר", "ארוחת צהריים", "ארוחת ביניים", "ארוחת ערב"], key="q_meal")
        with qc1:
            selected_food = st.selectbox("בחר מאכל:", list(FOOD_DATABASE.keys()))
        with qc2:
            quantity = st.number_input(f"כמות ({FOOD_DATABASE[selected_food]['unit']}):", min_value=0.25, max_value=20.0, value=1.0, step=0.25)
        with qc3:
            st.write("")
            st.write("")
            if st.button("הוסף ליומן ➕", key="btn_quick_add"):
                item_data = FOOD_DATABASE[selected_food]
                st.session_state.logged_items.append({
                    "meal": meal_type,
                    "name": selected_food,
                    "qty": quantity,
                    "unit": item_data["unit"],
                    "cal": round(item_data["cal"] * quantity),
                    "p": round(item_data["p"] * quantity, 1),
                    "c": round(item_data["c"] * quantity, 1),
                    "f": round(item_data["f"] * quantity, 1)
                })
                save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
                st.rerun()

    with tab_add_custom:
        cu_meal, cu1, cu2, cu3, cu4 = st.columns([2, 3, 2, 2, 2])
        with cu_meal:
            c_meal = st.selectbox("ארוחה:", ["ארוחת בוקר", "ארוחת צהריים", "ארוחת ביניים", "ארוחת ערב"], key="c_meal")
        with cu1:
            c_name = st.text_input("שם המאכל:", "שייק חלבון")
        with cu2:
            c_cal = st.number_input("קלוריות:", min_value=0, max_value=2000, value=180)
        with cu3:
            c_p = st.number_input("חלבון (גרם):", min_value=0.0, max_value=150.0, value=25.0, step=0.5)
        with cu4:
            st.write("")
            st.write("")
            if st.button("הוסף מאכל ידני ➕", key="btn_custom_add"):
                st.session_state.logged_items.append({
                    "meal": c_meal,
                    "name": c_name,
                    "qty": 1.0,
                    "unit": "מנה",
                    "cal": int(c_cal),
                    "p": float(c_p),
                    "c": 0.0,
                    "f": 0.0
                })
                save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
                st.rerun()

    tot_cal = sum(x["cal"] for x in st.session_state.logged_items)
    tot_p = round(sum(x["p"] for x in st.session_state.logged_items), 1)
    tot_c = round(sum(x["c"] for x in st.session_state.logged_items), 1)
    tot_f = round(sum(x["f"] for x in st.session_state.logged_items), 1)
    rem_cal = final_cal_target - tot_cal
    rem_p = round(user_p_target - tot_p, 1)

    st.write("---")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("סך קלוריות", f"{tot_cal} קק\"ל", delta=f"{rem_cal} ליעד")
    m2.metric("סך חלבון", f"{tot_p} גרם", delta=f"{rem_p} ליעד")
    m3.metric("סך פחמימות", f"{tot_c} גרם")
    m4.metric("סך שומן", f"{tot_f} גרם")

    if rem_p > 5 and rem_cal > 50:
        st.markdown('<div class="suggest-box">', unsafe_allow_html=True)
        st.markdown(f"#### 💡 סוגר הפינות: חסרים לך {rem_p}g חלבון ו-{rem_cal} קק\"ל")
        st.write("• **יוגורט PRO / חזה עוף:** סוגר מעולה 20-30 גרם חלבון במינימום קלוריות.")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.logged_items:
        st.write("### 📝 פירוט המאכלים שנשמרו להיום:")
        for idx, item in enumerate(st.session_state.logged_items):
            c_txt, c_del = st.columns([5, 1])
            with c_txt:
                st.write(f"• [{item.get('meal','ארוחה')}] **{item['name']}**: {item['cal']} קק\"ל | {item['p']}g חלבון")
            with c_del:
                if st.button("❌ מחק", key=f"del_item_{idx}"):
                    st.session_state.logged_items.pop(idx)
                    save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
                    st.rerun()

        if st.button("נקה את כל היומן להיום 🔄"):
            st.session_state.logged_items = []
            st.session_state.water_ml = 0
            st.session_state.extra_burned_cals = 0
            save_today_data(0, 0, [])
            st.rerun()

# --- טאב 3: מצלמת AI לסריקת מנות ---
with tab_ai_cam:
    st.subheader("📸 מצלמת AI חכמה לסריקת מנות")
    st.caption("צלם את המנה ישירות או העלה תמונה לקבלת ערכים תזונתיים מהירים.")
    
    scan_method = st.radio("בחר מקור צילום:", ["📷 צילום חי במצלמה", "📁 העלאת קובץ"], horizontal=True)
    img_file = st.camera_input("צלם את הצלחת:") if scan_method == "📷 צילום חי במצלמה" else st.file_uploader("העלה תמונה:", type=["jpg","png","jpeg"])
    
    if img_file:
        st.image(img_file, caption="תמונת המנה", width=350)
        dish_detected = st.selectbox("בחר את המנה שזוהתה:", [
            "חזה עוף צלוי (150 גרם) + אורז בסמטי וסלט",
            "פילה סלמון בתנור (160 גרם) + בטטה אפויה",
            "טורטיית חביתה וקוטג' עם ירקות",
            "קערת יוגורט חלבון PRO, בננה ושיבולת שועל"
        ])
        macros = {
            "חזה עוף צלוי (150 גרם) + אורז בסמטי וסלט": {"cal": 440, "p": 48.0, "c": 44.0, "f": 6.5},
            "פילה סלמון בתנור (160 גרם) + בטטה אפויה": {"cal": 460, "p": 34.0, "c": 32.0, "f": 20.0},
            "טורטיית חביתה וקוטג' עם ירקות": {"cal": 365, "p": 26.0, "c": 26.0, "f": 14.0},
            "קערת יוגורט חלבון PRO, בננה ושיבולת שועל": {"cal": 330, "p": 25.0, "c": 48.0, "f": 3.5}
        }
        m = macros[dish_detected]
        st.success(f"🔥 {m['cal']} קק\"ל | 💪 {m['p']} גרם חלבון | 🍞 {m['c']} גרם פחמימה")
        if st.button("➕ הוסף ישירות ליומן שלי!"):
            st.session_state.logged_items.append({
                "meal": "סריקת מצלמת AI", "name": dish_detected, "qty": 1.0, "unit": "מנה",
                "cal": m["cal"], "p": m["p"], "c": m["c"], "f": m["f"]
            })
            save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
            st.success("נוסף בהצלחה!")
            st.rerun()

# --- טאב 4: כרטיסיית סיכום שבועי לסטורי (Weekly Progress Card) ---
with tab_story:
    st.subheader("📲 כרטיסיית הישגים שבועית (לסטורי ולשיתוף)")
    st.caption("כרטיסייה מעוצבת ונקייה שמסכמת את ההתמדה, המים, החלבון ואימוני השבוע שלך.")

    prs = load_prs()
    top_pr = prs[0]["exercise"] + f" ({prs[0]['weight']} ק״ג)" if prs else "לחיצת חזה (75 ק״ג)"

    story_html = f"""
    <div class="story-card">
        <h3 style="color: #38bdf8; margin: 0; font-size: 1.8rem; font-weight: 900;">⚡ DaniFit Pro</h3>
        <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 4px;">סיכום שבועי אישי • משמעת וביצועים</p>
        <hr style="border-color: #334155; margin: 15px 0;">
        <div style="display: flex; justify-content: space-around; margin-bottom: 15px;">
            <div><b style="font-size: 1.3rem; color: #38bdf8;">100%</b><br><span style="font-size: 0.85rem; color: #cbd5e1;">יעד חלבון יומי</span></div>
            <div><b style="font-size: 1.3rem; color: #34d399;">3.2L</b><br><span style="font-size: 0.85rem; color: #cbd5e1;">ממוצע מים יומי</span></div>
            <div><b style="font-size: 1.3rem; color: #fbbf24;">4</b><br><span style="font-size: 0.85rem; color: #cbd5e1;">אימונים השבוע</span></div>
        </div>
        <div style="background: rgba(255,255,255,0.06); padding: 12px; border-radius: 12px; margin-top: 10px;">
            <span style="font-size: 0.9rem; color: #94a3b8;">שיא השבוע (PR):</span><br>
            <b style="color: #ffffff; font-size: 1.05rem;">🏆 {top_pr}</b>
        </div>
        <p style="color: #38bdf8; font-size: 0.9rem; margin-top: 16px; font-weight: bold;">"המשכיות מנצחת כישרון בכל יום." 🔥</p>
    </div>
    """
    st.markdown(story_html, unsafe_allow_html=True)
    story_summary_text = f"סיכום שבועי DaniFit Pro:\n• יעד חלבון: 100%\n• ממוצע מים: 3.2 ליטר\n• שיא שבועי: {top_pr}\nמוכן לשבוע הבא בשיא הכוח! ⚡"
    st.download_button("📥 הורד סיכום שבועי (TXT)", data=story_summary_text, file_name="DaniFit_Weekly_Summary.txt")

# --- טאב 5: חימום ומתיחות דינמי ---
with tab_warmup:
    st.subheader("🧘 ספריית חימום ומתיחות דינמית (5 דקות לפני אימון)")
    st.caption("חימום מפרקים והזרמת דם מדויקת לשמירה על הגוף ומניעת פציעות.")

    w_type = st.radio("בחר סוג אימון:", ["🏃 חימום לפני ריצה", "🏋️ חימום לפלג גוף עליון (חזה, גב וכתפיים)", "🦵 חימום רגליים וסקוואט"], horizontal=True)

    if "ריצה" in w_type:
        st.markdown("""
        <div class="card-box">
            <h4>🏃 שגרת חימום לריצה (5 דקות):</h4>
            1. <b>הליכה מהירה:</b> 2 דקות להעלאת דופק.<br>
            2. <b>הנפות רגליים קדימה ואחורה:</b> 12 הנפות לכל רגל לחימום מיתרי הברך והמפשעה.<br>
            3. <b>ברכיים לחזה בהליכה:</b> 10 חזרות לכל צד.<br>
            4. <b>סיבובי קרסוליים ועקבים לישבן:</b> 30 שניות לשחרור הגידים לפני היציאה לקצב.
        </div>
        """, unsafe_allow_html=True)
    elif "עליון" in w_type:
        st.markdown("""
        <div class="card-box">
            <h4>🏋️ שגרת חימום לפלג גוף עליון (חזה וכתפיים):</h4>
            1. <b>סיבובי זרועות קדימה ואחורה:</b> 15 שניות לכל כיוון.<br>
            2. <b>שרוול מסובב (Rotator Cuff):</b> סיבובי מרפקים פנימה והחוצה למניעת פציעות כתף בלחיצות.<br>
            3. <b>מתיחת חזה דינמית:</b> פתיחת ידיים לרווחה וחיבוק עצמי 15 פעמים.<br>
            4. <b>סט חימום ראשון במשקל קל מאוד (30%-40%):</b> 12 חזרות לזרימת דם לפני העמסת משקל.
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="card-box">
            <h4>🦵 שגרת חימום לרגליים וסקוואטים:</h4>
            1. <b>סקוואט במשקל גוף (Bodyweight):</b> 15 חזרות איטיות עם עצירה לשנייה למטה.<br>
            2. <b>פתיחת מפרקי ירך (World's Greatest Stretch):</b> 6 חזרות לכל צד.<br>
            3. <b>לאנג'ים בהליכה ללא משקל:</b> 10 צעדים לכל רגל.<br>
            4. <b>עליית עקבים לתאומים:</b> 20 חזרות.
        </div>
        """, unsafe_allow_html=True)

# --- טאב 6: שבת קודש ---
with tab_shabbat:
    st.subheader("🕯️ מחשבון סעודות שבת קודש")
    shab_col1, shab_col2 = st.columns(2)
    selected_shabbat = []
    with shab_col1:
        if st.checkbox("🍷 כוסית יין קידוש / תירוש"): selected_shabbat.append("כוסית יין קידוש / תירוש (100 מ״ל)")
        if st.checkbox("🍞 פרוסת חלת שבת"): selected_shabbat.append("פרוסת חלת שבת (50 גרם)")
        if st.checkbox("🐟 דג חריף ברוטב"): selected_shabbat.append("מנת דג חריף (אמנון ברוטב, 150 גרם)")
    with shab_col2:
        if st.checkbox("🍗 כרע עוף בתנור"): selected_shabbat.append("כרע עוף / ירך בתנור (יחידה ללא עור)")
        if st.checkbox("🍲 חמין / צ'ולנט מסורתי"): selected_shabbat.append("מנת חמין / צ'ולנט מסורתית עם בשר")
        if st.checkbox("🥗 סלטי שבת מבושלים"): selected_shabbat.append("צלחת סלטי שבת מבושלים (3 כפות)")

    if selected_shabbat:
        s_c = sum(SHABBAT_FOOD_DB[x]["cal"] for x in selected_shabbat)
        s_p = sum(SHABBAT_FOOD_DB[x]["p"] for x in selected_shabbat)
        st.info(f"סה״כ בסעודה: **{s_c} קק\"ל** | **{s_p} גרם חלבון**")
        if st.button("הוסף סעודת שבת ליומן היומי 🍷"):
            for item in selected_shabbat:
                st.session_state.logged_items.append({
                    "meal": "סעודת שבת", "name": item, "qty": 1.0, "unit": "מנה",
                    "cal": SHABBAT_FOOD_DB[item]["cal"], "p": SHABBAT_FOOD_DB[item]["p"],
                    "c": SHABBAT_FOOD_DB[item]["c"], "f": SHABBAT_FOOD_DB[item]["f"]
                })
            save_today_data(st.session_state.water_ml, st.session_state.extra_burned_cals, st.session_state.logged_items)
            st.success("נוסף בהצלחה ליומן!")
            st.rerun()

# --- טאב 7: סופר והזמנה בלחיצה ---
with tab_shopping:
    st.subheader("🛒 רשימת קניות לסופר והזמנה בלחיצה")
    chosen_super = st.radio("רשת מועדפת:", ["שופרסל Online 🔴", "רמי לוי אונליין 🔵"], horizontal=True)
    base_url = "https://www.shufersal.co.il/online/he/search?text=" if "שופרסל" in chosen_super else "https://www.rami-levy.co.il/he/online/search?q="
    checkout_url = "https://www.shufersal.co.il/online/he/cart" if "שופרסל" in chosen_super else "https://www.rami-levy.co.il/he/online/cart"

    for idx, item in enumerate(st.session_state.shopping_list):
        c_txt, c_btn, c_del = st.columns([3.5, 2, 0.8])
        target_url = base_url + urllib.parse.quote(item.get("search", item["item"]))
        with c_txt:
            st.write(f"• **{item['item']}**")
        with c_btn:
            st.markdown(f'<a href="{target_url}" target="_blank" class="quick-shop-btn">🔍 הוסף בעגלה</a>', unsafe_allow_html=True)
        with c_del:
            if st.button("הסר", key=f"del_shop_{idx}"):
                st.session_state.shopping_list.pop(idx)
                st.rerun()

    st.write("---")
    st.markdown(f'<a href="{checkout_url}" target="_blank"><button style="width:100%;background:#16a34a;color:#fff;border:none;padding:14px;border-radius:12px;font-weight:800;font-size:1.1rem;cursor:pointer;">💳 עבור ישר לקופה ולתשלום ב-{chosen_super.split()[0]}</button></a>', unsafe_allow_html=True)

# --- טאב 8: אימונים, כוח ו-PR ---
with tab_workout:
    st.subheader("🏋️ מרכז אימונים, כוח ו-PR Wall")

    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown("### 🏆 לוח שיאים אישיים (PR Wall) - נשמר קבוע")
    pr_c1, pr_c2, pr_c3, pr_c4 = st.columns(4)
    with pr_c1:
        pr_name = st.selectbox("תרגיל:", ["לחיצת חזה", "סקוואט", "דדליפט", "מתח עם משקל", "ריצת 3 ק״מ", "ריצת 5 ק״מ"])
    with pr_c2:
        pr_weight = st.number_input("משקל (ק״ג):", min_value=0.0, max_value=350.0, value=75.0, step=2.5)
    with pr_c3:
        pr_reps = st.number_input("חזרות (או 1 לריצה):", min_value=1, max_value=50, value=5, step=1)
    with pr_c4:
        st.write("")
        st.write("")
        if st.button("שמור שיא 🥇"):
            add_pr(pr_name, pr_weight, pr_reps)
            st.success("השיא נשמר לתמיד!")
            st.rerun()

    current_prs = load_prs()
    if current_prs:
        for p in current_prs:
            p_t, p_d = st.columns([5, 1])
            with p_t:
                st.write(f"• **{p['exercise']}**: **{p['weight']} ק״ג ל-{p['reps']} חזרות** | 📅 {p['date']}")
            with p_d:
                if st.button("מחק", key=f"del_pr_db_{p['id']}"):
                    delete_pr(p['id'])
                    st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # טיימר מנוחה
    st.markdown('<div class="card-box">', unsafe_allow_html=True)
    st.markdown("### ⏱️ טיימר מנוחה בין סטים")
    tc1, tc2, tc3 = st.columns(3)
    secs = 0
    with tc1:
        if st.button("⚡ 60 שניות"): secs = 60
    with tc2:
        if st.button("💪 90 שניות"): secs = 90
    with tc3:
        if st.button("🛑 120 שניות"): secs = 120

    if secs > 0:
        bar = st.progress(1.0)
        t_txt = st.empty()
        for r in range(secs, -1, -1):
            m, s = divmod(r, 60)
            t_txt.markdown(f"<h2 style='text-align:center;color:#2563eb;'>⏳ {m:02d}:{s:02d}</h2>", unsafe_allow_html=True)
            bar.progress(r / secs)
            time.sleep(1)
        t_txt.markdown("<h2 style='text-align:center;color:#16a34a;'>🔔 צא לסט הבא!</h2>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)