import asyncio
import json
import random
import os
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR = Path("daily_post")
# ✅ تغيير: HISTORY_FILE يُقرأ من متغير بيئي أو يُحفظ محلياً
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "used_topics.json"))
SIZE = 1080

TEACHER_NAME = "أحمد الحيالي"
TEACHER_HANDLE = "@Ahmed.hayali.iq"

THEMES = [
    {
        "name": "Classic Slate",
        "bg": "#f8fafc",
        "card_bg": "#ffffff",
        "border": "#cbd5e1",
        "text": "#1e293b",
        "title": "#0f172a",
        "accent": "#2563eb",
        "badge_bg": "#e0f2fe",
        "badge_text": "#0284c7"
    },
    {
        "name": "Emerald Mint",
        "bg": "#f0fdf4",
        "card_bg": "#ffffff",
        "border": "#a7f3d0",
        "text": "#064e3b",
        "title": "#022c22",
        "accent": "#059669",
        "badge_bg": "#d1fae5",
        "badge_text": "#047857"
    },
    {
        "name": "Warm Sunset",
        "bg": "#fffbeb",
        "card_bg": "#ffffff",
        "border": "#fde68a",
        "text": "#78350f",
        "title": "#451a03",
        "accent": "#d97706",
        "badge_bg": "#fef3c7",
        "badge_text": "#b45309"
    },
    {
        "name": "Purple Modern",
        "bg": "#faf5ff",
        "card_bg": "#ffffff",
        "border": "#e9d5ff",
        "text": "#581c87",
        "title": "#3b0764",
        "accent": "#9333ea",
        "badge_bg": "#f3e8ff",
        "badge_text": "#7e22ce"
    },
    {
        "name": "Dark Mode Elegance",
        "bg": "#0f172a",
        "card_bg": "#1e293b",
        "border": "#334155",
        "text": "#f8fafc",
        "title": "#ffffff",
        "accent": "#38bdf8",
        "badge_bg": "#1e3a8a",
        "badge_text": "#93c5fd"
    }
]

LOCAL_TOPICS = [
    {
        "topic": "قصة قصيرة ومعنى 📖 | The Wise Old Man",
        "caption": "📌 قصة قصيرة ممتعة لتقوية القراءة والاستماع والكلمات! 📖\n\nاقرأ القصة وتعلّم مفردات جديدة بسهولة.\n\nاحفظ البطاقات عندك للمراجعة! 📌\n#قصص_إنجليزية #تعلم_الإنجليزي #مفردات #أحمد_الحيالي",
        "slides": [
            {
                "badge": "قصة مترجمة 📖",
                "title": "الرجل العجوز الحكيم 👴",
                "textAr": "An old man lived in the village.\n(عاش رجل عجوز في القرية).\n\nHe was always complaining and the whole village was tired of him.\n(كان يتذمر دائماً والقرية بأكملها تعبت منه)."
            },
            {
                "badge": "الجزء الثاني 📖",
                "title": "تحول مفاجئ ⚡",
                "textAr": "One day, when he turned 80, something miraculous happened.\n(في أحد الأيام، عندما بلغ الـ 80، حدث شيء معجزة).\n\nHe stopped complaining and was smiling all day.\n(توقف عن التذمر وكان يبتسم طوال اليوم)."
            },
            {
                "badge": "الحكمة 💡",
                "title": "العبرة من القصة 🌟",
                "textAr": "Villagers asked: What happened to you?\nHe said: Nothing, I just decided to enjoy life instead of chasing happiness.\n(قال: قررت الاستمتاع بالحياة بدلاً من مطاردة السعادة)."
            },
            {
                "badge": "مفردات القصة 📝",
                "title": "كلمات جديدة 🎯",
                "textAr": "• Complain ➔ يتذمر\n• Miracle ➔ معجزة\n• Chase ➔ يطارد / يلاحق\n• Village ➔ قرية"
            }
        ]
    },
    {
        "topic": "كلمات متشابهة ⚠️ | Their vs There vs They're",
        "caption": "📌 الفرق بين ثلاث كلمات تنطق بنفس الشكل تماماً! ⚠️\n\nتوقف عن الخطأ في كتابتها بعد اليوم.\n\nشاركه مع صديقك المهتم! 🎯\n#كلمات_إنجليزية #جرامر #أحمد_الحيالي",
        "slides": [
            {
                "badge": "تشابه باللفظ 🔊",
                "title": "There / Their / They're",
                "textAr": "الثلاث كلمات لها نفس النطق تماماً، لكن المعنى والاستخدام مختلف كلياً!"
            },
            {
                "badge": "الأولى والثانية 📝",
                "title": "الفرق بالتفصيل 💡",
                "textAr": "1️⃣ There = هناك (للمكان)\n• Sit over there. (اجلس هناك).\n\n2️⃣ Their = ملكهم (للملكية)\n• Their house is big. (بيتكُم كبير)."
            },
            {
                "badge": "الثالثة 📝",
                "title": "الكلمة الثالثة 🌟",
                "textAr": "3️⃣ They're = هم يكونون (اختصار They are)\n• They're happy. (هم سعيدون)."
            },
            {
                "badge": "تحدي سريع 🎯",
                "title": "اختبر نفسك 💡",
                "textAr": "سؤال: اختر الكلمة الصحيحة:\n(___ going to the park)\n\nالجواب الصحيح: They're"
            }
        ]
    },
    {
        "topic": "أهم المعاكسات 🔄 | Antonyms in English",
        "caption": "📌 ضاعف حصيلتك اللغوية بتعلم الكلمة وعكسها! 🔄\n\nطريقة سريعة لحفظ الكلمات وسهولة استذكارها.\n\nاحفظ المنشور عندك! 📌\n#مفردات_إنجليزية #معاكسات #أحمد_الحيالي",
        "slides": [
            {
                "badge": "المعاكسات 🔄",
                "title": "أهم الصفات وعكسها 🎯",
                "textAr": "تعلم الكلمة وعكسها يساعدك على التحدث بطلاقة وتذكر المفردات بسرعة."
            },
            {
                "badge": "القائمة الأولى 📝",
                "title": "الصفات اليومية 💬",
                "textAr": "• Ancient (قديم جداً) ✖️ Modern (حديث)\n• Generous (كريم) ✖️ Stingy (بخيل)\n• Brave (شجاع) ✖️ Coward (جبان)"
            },
            {
                "badge": "القائمة الثانية 📝",
                "title": "صفات الحالات 🌟",
                "textAr": "• Complex (معقد) ✖️ Simple (بسيط)\n• Temporary (مؤقت) ✖️ Permanent (دائم)\n• Polite (مهذب) ✖️ Rude (وقح)"
            },
            {
                "badge": "تطبيقي 🎯",
                "title": "تحدي الكلمات 💡",
                "textAr": "سؤال: ما هو عكس كلمة (Dangerous - خطير)؟\n\nالجواب الصحيح: Safe (آمن)"
            }
        ]
    }
]

def load_history():
    # ✅ تغيير: يقرأ من متغير بيئي USED_TOPICS_JSON أولاً (لـ GitHub Actions)
    env_history = os.getenv("USED_TOPICS_JSON")
    if env_history:
        try:
            return json.loads(env_history)
        except Exception:
            return []
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(history):
    # ✅ تغيير: يحفظ الـ JSON في ملف لتلتقطه GitHub Actions وتحدّث الـ secret
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"📝 History saved: {history}")

def get_next_topic():
    history = load_history()
    available = [t for t in LOCAL_TOPICS if t["topic"] not in history]
    if not available:
        history = []
        available = LOCAL_TOPICS
    chosen = random.choice(available)
    history.append(chosen["topic"])
    save_history(history)
    return chosen

def build_slide_html(teacher_name, teacher_handle, title, badge, text_content,
                     current_index, total_slides, theme):
    lines = text_content.split('\n')
    formatted_lines = ""
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
        is_english = (
            any('a' <= c.lower() <= 'z' for c in line_str)
            and not any('\u0600' <= c <= '\u06FF' for c in line_str)
        )
        align = "left" if is_english else "right"
        direction = "ltr" if is_english else "rtl"
        formatted_lines += (
            f'<div style="text-align:{align};direction:{direction};'
            f'margin-bottom:22px;font-size:32px;line-height:1.6;'
            f'font-weight:700;color:{theme["text"]};">{line_str}</div>'
        )

    current_str = f"{current_index + 1:02d}"
    total_str = f"{total_slides:02d}"
    badge_html = (
        f'<div class="badge" style="background:{theme["badge_bg"]};'
        f'color:{theme["badge_text"]};">{badge}</div>'
    ) if badge else ''

    # ✅ تغيير: الخط محلي (Noto Sans Arabic) بدلاً من Google Fonts
    # يُضاف في GitHub Actions كـ apt package ويُشار إليه مباشرة
    return f"""
    <!DOCTYPE html>
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <style>
            @font-face {{
                font-family: 'Cairo';
                src: local('Cairo'), local('NotoSansArabic');
            }}
            * {{ box-sizing:border-box; margin:0; padding:0; }}
            body {{
                width:1080px; height:1080px;
                background-color:{theme["bg"]};
                font-family:'Cairo','Noto Sans Arabic','Arial',sans-serif;
                display:flex; flex-direction:column;
                padding:60px; overflow:hidden;
            }}
            .header {{
                display:flex; justify-content:space-between;
                align-items:center; width:100%; margin-bottom:35px;
            }}
            .teacher-info {{ display:flex; flex-direction:column; text-align:right; }}
            .teacher-name {{ font-size:44px; font-weight:800; color:{theme["title"]}; line-height:1.1; }}
            .teacher-handle {{ font-size:26px; font-weight:700; color:{theme["accent"]}; direction:ltr; text-align:right; margin-top:4px; }}
            .slide-counter {{ font-size:36px; font-weight:800; color:{theme["accent"]}; letter-spacing:2px; direction:ltr; opacity:0.8; }}
            .card {{
                flex:1; background:{theme["card_bg"]};
                border:3px dashed {theme["border"]};
                border-radius:32px; padding:50px;
                display:flex; flex-direction:column; justify-content:flex-start;
                box-shadow:0 10px 30px rgba(0,0,0,0.04);
            }}
            .card-header {{
                display:flex; align-items:center; justify-content:space-between;
                margin-bottom:35px; border-bottom:2px solid {theme["bg"]};
                padding-bottom:20px;
            }}
            .card-title {{ font-size:40px; font-weight:800; color:{theme["title"]}; }}
            .badge {{ padding:8px 22px; border-radius:50px; font-size:24px; font-weight:700; }}
            .card-body {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="teacher-info">
                <div class="teacher-name">{teacher_name}</div>
                <div class="teacher-handle">{teacher_handle}</div>
            </div>
            <div class="slide-counter">{current_str} / {total_str}</div>
        </div>
        <div class="card">
            <div class="card-header">
                <div class="card-title">{title}</div>
                {badge_html}
            </div>
            <div class="card-body">
                {formatted_lines}
            </div>
        </div>
    </body>
    </html>
    """

async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = get_next_topic()
    theme = random.choice(THEMES)
    total_slides = len(data["slides"])

    async with async_playwright() as p:
        # ✅ تغيير: --no-sandbox ضروري في بيئة GitHub Actions (Linux container)
        browser = await p.chromium.launch(args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(data["slides"]):
            html_content = build_slide_html(
                teacher_name=TEACHER_NAME,
                teacher_handle=TEACHER_HANDLE,
                title=slide.get("title", ""),
                badge=slide.get("badge", ""),
                text_content=slide.get("textAr", ""),
                current_index=i,
                total_slides=total_slides,
                theme=theme
            )
            await page.set_content(html_content, wait_until="domcontentloaded")
            # ✅ تغيير: domcontentloaded بدلاً من networkidle لأنه لا يوجد اتصال خارجي
            out_path = OUTPUT_DIR / f"slide_{i + 1}.png"
            await page.screenshot(path=str(out_path))
            print(f"✅ Saved: {out_path}")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(data["caption"], encoding="utf-8")
    print("🎨 All slides generated successfully!")

if __name__ == "__main__":
    asyncio.run(main())
