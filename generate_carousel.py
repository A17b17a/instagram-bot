import asyncio
import json
import random
import os
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR   = Path("daily_post")
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "used_topics.json"))
SIZE         = 1080

TEACHER_NAME   = "أحمد الحيالي"
TEACHER_HANDLE = "@ahmed.hayali.iq"

# ════════════════════════════════════════════════════════════════
# الثيم الثابت — مستوحى من ملزمة AH
# خلفية فاتحة، نص كحلي، عناوين ذهبية، بوردر منقط
# ════════════════════════════════════════════════════════════════
NOTEBOOK_THEMES = [
    {   # الثيم الأساسي — الملزمة الكلاسيكية
        "name": "AH Classic",
        "bg":         "#f5f5f0",
        "card_bg":    "#ffffff",
        "border":     "#d4c5a9",
        "text":       "#1a1a2e",
        "title":      "#c8a84b",
        "accent":     "#1a1a2e",
        "badge_bg":   "#1a1a2e",
        "badge_text": "#c8a84b",
        "header_line":"#c8a84b",
    },
    {   # أزرق ملزمة — كحلي مع لمسة ذهبية
        "name": "AH Navy",
        "bg":         "#f0f2f8",
        "card_bg":    "#ffffff",
        "border":     "#b0bcd4",
        "text":       "#1a1a2e",
        "title":      "#c8a84b",
        "accent":     "#2c3e6b",
        "badge_bg":   "#2c3e6b",
        "badge_text": "#f0c040",
        "header_line":"#2c3e6b",
    },
    {   # ملزمة خضراء — للمحتوى العلمي
        "name": "AH Sage",
        "bg":         "#f2f5f0",
        "card_bg":    "#ffffff",
        "border":     "#a8c4a8",
        "text":       "#1a2e1a",
        "title":      "#c8a84b",
        "accent":     "#2e5e2e",
        "badge_bg":   "#2e5e2e",
        "badge_text": "#f0e0a0",
        "header_line":"#2e5e2e",
    },
    {   # ملزمة دافئة — للمحتوى التحفيزي
        "name": "AH Warm",
        "bg":         "#faf6f0",
        "card_bg":    "#ffffff",
        "border":     "#d4b896",
        "text":       "#2e1a0a",
        "title":      "#c8a84b",
        "accent":     "#8b4513",
        "badge_bg":   "#8b4513",
        "badge_text": "#fdecc8",
        "header_line":"#c8a84b",
    },
]

# ════════════════════════════════════════════════════════════════
# المواضيع — عامة ومتنوعة (لا علاقة بالمناهج الدراسية)
# ════════════════════════════════════════════════════════════════
LOCAL_TOPICS = [
    {
        "topic": "حقيقة علمية | النوم والذاكرة",
        "caption": "🧠 دماغك يشتغل وانت نايم!\n\nاعرف كيف النوم يأثر على ذاكرتك وتركيزك — معلومة تغير طريقة تفكيرك.\n\n#علم #دماغ #نوم #معلومة_تهمك #تطوير_ذات #أحمد_الحيالي",
        "slides": [
            {
                "badge": "علم وحقائق 🔬",
                "title": "النوم والذاكرة 🧠",
                "textAr": "هل تعلم أن دماغك لا يرتاح وأنت نايم؟\n\nبالعكس — هو يشتغل بشكل مكثف على ترتيب وحفظ كل اللي تعلمته خلال اليوم."
            },
            {
                "badge": "ماذا يحدث؟ 💡",
                "title": "3 مراحل مهمة 📋",
                "textAr": "1️⃣ الدماغ يراجع المعلومات الجديدة\n2️⃣ ينقلها من الذاكرة القصيرة للطويلة\n3️⃣ يربطها بمعلومات قديمة عندك أصلاً"
            },
            {
                "badge": "رقم مثير 📊",
                "title": "الأرقام لا تكذب 🎯",
                "textAr": "الشخص اللي ينام 7-8 ساعات يتذكر المعلومات بنسبة أعلى بـ 40% من اللي ينام أقل من 6 ساعات.\n\nالنوم مو كسل — هو استثمار."
            },
            {
                "badge": "تطبيق عملي ✅",
                "title": "وش تسوي اليوم؟ 🌙",
                "textAr": "• تعلّم شيء جديد قبل النوم مباشرة\n• لا تنظر للجوال آخر 30 دقيقة\n• اضمن 7 ساعات نوم على الأقل\n\nدماغك يشكرك الصبح! 🙌"
            }
        ]
    },
    {
        "topic": "مهارة إنجليزية | Collocations",
        "caption": "🗣️ السر الحقيقي وراء الإنجليزي الطبيعي!\n\nمو بس الكلمات — الكلمات اللي تجي مع بعض هي الفرق.\n\n#إنجليزي #تعلم_إنجليزي #مهارات_لغوية #أحمد_الحيالي #لغة_إنجليزية",
        "slides": [
            {
                "badge": "سر المتحدثين الأصليين 🔑",
                "title": "ليش إنجليزيتك تبدو غريبة؟ 🤔",
                "textAr": "المشكلة مو في قواعدك — هي في الـ Collocations!\n\nيعني: الكلمات اللي تجي مع بعض بشكل طبيعي."
            },
            {
                "badge": "أمثلة خاطئة ❌",
                "title": "أخطاء نسويها كلنا 😅",
                "textAr": "❌ Do a mistake → ✅ Make a mistake\n❌ Strong rain → ✅ Heavy rain\n❌ Do a photo → ✅ Take a photo\n❌ Big storm → ✅ Heavy storm"
            },
            {
                "badge": "أمثلة صحيحة ✅",
                "title": "تعلّم هالتراكيب 📝",
                "textAr": "✅ Make a decision (ياخذ قرار)\n✅ Pay attention (ينتبه)\n✅ Break a record (يكسر رقم)\n✅ Catch a cold (يصطاد برد)"
            },
            {
                "badge": "طريقة الحفظ 💡",
                "title": "كيف تتعلمها؟ 🎯",
                "textAr": "• ما تحفظ كلمة لوحدها — احفظها مع رفيقتها\n• اقرأ كثير بالإنجليزي وانتبه للتراكيب\n• استخدمها في جمل من حياتك اليومية"
            }
        ]
    },
    {
        "topic": "تطوير ذات | قاعدة الـ 2 دقيقة",
        "caption": "⏱️ إذا يجي بـ 2 دقيقة — سوّه الحين!\n\nقاعدة بسيطة غيّرت إنتاجية ملايين الناس حول العالم.\n\n#إنتاجية #تطوير_ذات #عادات #وقت #نجاح #أحمد_الحيالي",
        "slides": [
            {
                "badge": "إنتاجية 🚀",
                "title": "قاعدة الـ 2 دقيقة ⏱️",
                "textAr": "من كتاب Getting Things Done لـ David Allen:\n\n\"إذا كان الشيء يأخذ أقل من دقيقتين — سوّه الحين ولا تأجله.\""
            },
            {
                "badge": "ليش تشتغل؟ 🧠",
                "title": "السبب العلمي 🔬",
                "textAr": "تأجيل الأشياء الصغيرة يراكم ضغط نفسي في دماغك.\n\nكل مهمة صغيرة معلقة تاخذ جزء من طاقتك الذهنية — حتى لو ما تحس فيها."
            },
            {
                "badge": "تطبيق 📱",
                "title": "أمثلة من حياتك 🏠",
                "textAr": "• رد على رسالة مهمة → الحين\n• رتب مكتبك → الحين\n• اكتب الفكرة اللي جت لبالك → الحين\n• ادفع فاتورة صغيرة → الحين"
            },
            {
                "badge": "تحدي اليوم 🎯",
                "title": "جربها هالأسبوع 💪",
                "textAr": "طبّق القاعدة 7 أيام متتالية.\n\nراح تلاحظ إن قائمة مهامك تصغر، وإن طاقتك الذهنية ترتفع.\n\nالمهام الصغيرة هي اللي تسرق وقتك في الخفاء! 👀"
            }
        ]
    },
    {
        "topic": "حقيقة علمية | لماذا ننسى الأحلام؟",
        "caption": "💭 ليش تنسى حلمك بعد ثواني من الصحيان؟\n\nالجواب في علم الأعصاب — ومدهش أكثر مما تتوقع!\n\n#أحلام #علم_أعصاب #نوم #حقائق_علمية #أحمد_الحيالي",
        "slides": [
            {
                "badge": "سؤال يحيّر الجميع 🌙",
                "title": "ليش ننسى أحلامنا؟ 💭",
                "textAr": "تصحى من أجمل حلم في حياتك.\n\nتبلع ريقتك.\n\nراح!"
            },
            {
                "badge": "الجواب العلمي 🔬",
                "title": "ما يحدث في دماغك 🧠",
                "textAr": "الأحلام تصير في مرحلة REM النوم.\n\nفي هالمرحلة، مستوى النورأدرينالين (هرمون التركيز والذاكرة) ينخفض لأدنى مستوياته — لذلك الذاكرة لا تسجّل."
            },
            {
                "badge": "حقيقة مثيرة 💡",
                "title": "رقم يفاجئك 📊",
                "textAr": "الإنسان يحلم بين 4-6 أحلام كل ليلة.\n\nنتذكر فقط 5% منها — والباقي يختفي خلال أول 10 دقائق من الصحيان."
            },
            {
                "badge": "نصيحة 🎯",
                "title": "تبي تتذكر أحلامك؟ ✍️",
                "textAr": "• خلّي دفتر بجانب سريرك\n• اكتب الحلم فوراً قبل أي شيء ثاني\n• لا تحرك جسمك كثير لحظة الصحيان\n\nالحركة تمسح الحلم أسرع! 🏃"
            }
        ]
    },
    {
        "topic": "مهارة إنجليزية | أقوى 10 أفعال يومية",
        "caption": "💬 10 أفعال إنجليزية تحتاجها كل يوم — بالمعنى والمثال!\n\nاحفظهم وراح تلاحظ فرق فوري في حديثك.\n\n#إنجليزي #أفعال_إنجليزية #تعلم_إنجليزي #مفردات #أحمد_الحيالي",
        "slides": [
            {
                "badge": "مفردات يومية 📚",
                "title": "10 أفعال لازم تعرفها 🎯",
                "textAr": "هذي الأفعال تطلع في كل محادثة إنجليزية تقريباً.\n\nتعلّمها = تعلّمت نص المحادثة اليومية."
            },
            {
                "badge": "الأفعال 1-5 📝",
                "title": "القائمة الأولى 💬",
                "textAr": "• Figure out = يفهم / يكتشف\n• Run out of = ينتهي منه\n• Give up = يستسلم\n• Come up with = يبتكر فكرة\n• Look forward to = يتطلع لـ"
            },
            {
                "badge": "الأفعال 6-10 📝",
                "title": "القائمة الثانية 💬",
                "textAr": "• Deal with = يتعامل مع\n• Keep up with = يواكب\n• Put off = يأجل\n• Bring up = يذكر موضوع\n• Catch up = يلحق / يعوض"
            },
            {
                "badge": "تحدي الآن ⚡",
                "title": "استخدم واحد الحين! 🗣️",
                "textAr": "كوّن جملة بأي فعل من القائمة وحطها في التعليقات.\n\nمثال: I need to figure out how to improve my English!\n\nانتظرك 👇"
            }
        ]
    },
    {
        "topic": "تطوير ذات | قوة سؤال واحد",
        "caption": "❓ سؤال واحد يغير طريقة تفكيرك كلياً.\n\nاسأل نفسك اياه كل صبح وراح تشوف الفرق.\n\n#تفكير #تطوير_ذات #نجاح #عقلية #أحمد_الحيالي",
        "slides": [
            {
                "badge": "تطوير ذات 💡",
                "title": "سؤال يغير حياتك ❓",
                "textAr": "مو مبالغة — في علم النفس، الأسئلة اللي نسأل أنفسنا تحدد كيف نرى العالم وكيف نتصرف فيه."
            },
            {
                "badge": "السؤال السحري ✨",
                "title": "اسأل نفسك كل صبح 🌅",
                "textAr": "\"ما هو الشيء الواحد اللي لو سويته اليوم، يخلي كل شيء ثاني أسهل أو غير ضروري؟\"\n\nمن كتاب The ONE Thing."
            },
            {
                "badge": "ليش يشتغل؟ 🔬",
                "title": "الفكرة من الناحية العلمية 🧠",
                "textAr": "السؤال يجبر دماغك على الأولوية.\n\nبدل ما تفكر بـ 20 مهمة — تركز على الأهم.\n\nالتركيز على شيء واحد يرفع الإنجاز بشكل غير متوقع."
            },
            {
                "badge": "جربه الحين 🎯",
                "title": "تحدي الأسبوع 💪",
                "textAr": "سبعة أيام — كل صبح اسأل نفسك السؤال هذا.\n\nاكتب الجواب، وركز عليه.\n\nوأخبرنا وش تغير في تعليقاتك! 👇"
            }
        ]
    },
]

# ════════════════════════════════════════════════════════════════
# إدارة سجل المواضيع
# ════════════════════════════════════════════════════════════════
def load_history():
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
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"📝 Topics history saved: {history}")

def get_next_topic():
    history  = load_history()
    available = [t for t in LOCAL_TOPICS if t["topic"] not in history]
    if not available:
        history   = []
        available = LOCAL_TOPICS
    chosen = random.choice(available)
    history.append(chosen["topic"])
    save_history(history)
    return chosen

# ════════════════════════════════════════════════════════════════
# بناء HTML للسلايد — ثيم الملزمة
# ════════════════════════════════════════════════════════════════
def build_slide_html(teacher_name, teacher_handle, title, badge,
                     text_content, current_index, total_slides, theme):

    lines = text_content.split('\n')
    formatted_lines = ""
    for line in lines:
        line_str = line.strip()
        if not line_str:
            formatted_lines += '<div style="height:14px;"></div>'
            continue
        has_arabic  = any('\u0600' <= c <= '\u06FF' for c in line_str)
        has_english = any('a' <= c.lower() <= 'z' for c in line_str)
        if has_arabic:
            align, direction = "right", "rtl"
        elif has_english:
            align, direction = "left", "ltr"
        else:
            align, direction = "right", "rtl"

        formatted_lines += (
            f'<div style="text-align:{align};direction:{direction};'
            f'margin-bottom:18px;font-size:30px;line-height:1.7;'
            f'font-weight:600;color:{theme["text"]};">{line_str}</div>'
        )

    badge_html = (
        f'<div style="background:{theme["badge_bg"]};color:{theme["badge_text"]};'
        f'padding:6px 20px;border-radius:6px;font-size:22px;font-weight:700;'
        f'white-space:nowrap;">{badge}</div>'
    ) if badge else ''

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{
    width:1080px; height:1080px;
    background:{theme["bg"]};
    font-family:'Noto Sans Arabic','Arial',sans-serif;
    display:flex; flex-direction:column;
    padding:55px 60px; overflow:hidden;
  }}

  /* ─── Header ─── */
  .header {{
    display:flex; justify-content:space-between; align-items:center;
    padding-bottom:18px;
    border-bottom:3px solid {theme["header_line"]};
    margin-bottom:30px;
  }}
  .teacher-name {{
    font-size:38px; font-weight:800; color:{theme["accent"]};
    letter-spacing:-0.5px;
  }}
  .teacher-handle {{
    font-size:22px; font-weight:600; color:{theme["title"]};
    direction:ltr; text-align:right; margin-top:3px;
  }}
  .slide-counter {{
    font-size:32px; font-weight:800; color:{theme["title"]};
    direction:ltr; opacity:0.85;
    font-variant-numeric:tabular-nums;
  }}

  /* ─── Card ─── */
  .card {{
    flex:1; background:{theme["card_bg"]};
    border:2.5px dashed {theme["border"]};
    border-radius:20px; padding:44px 48px;
    display:flex; flex-direction:column;
    box-shadow:0 4px 20px rgba(0,0,0,0.06);
  }}
  .card-header {{
    display:flex; align-items:flex-start;
    justify-content:space-between; gap:16px;
    margin-bottom:30px;
    padding-bottom:22px;
    border-bottom:2px dashed {theme["border"]};
  }}
  .card-title {{
    font-size:44px; font-weight:900;
    color:{theme["title"]};
    line-height:1.2; flex:1;
  }}
  .card-body {{
    flex:1; display:flex; flex-direction:column; justify-content:center;
  }}

  /* ─── Footer line ─── */
  .footer-line {{
    margin-top:20px;
    padding-top:14px;
    border-top:2px solid {theme["border"]};
    display:flex; justify-content:center; align-items:center;
  }}
  .footer-text {{
    font-size:20px; font-weight:600; color:{theme["border"]};
    direction:ltr; letter-spacing:1px;
  }}
</style>
</head>
<body>
  <div class="header">
    <div>
      <div class="teacher-name">{teacher_name}</div>
      <div class="teacher-handle">{teacher_handle}</div>
    </div>
    <div class="slide-counter">{current_index+1:02d} / {total_slides:02d}</div>
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

  <div class="footer-line">
    <div class="footer-text">ahmed.hayali.iq</div>
  </div>
</body>
</html>"""


# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data        = get_next_topic()
    theme       = random.choice(NOTEBOOK_THEMES)
    total_slides = len(data["slides"])

    print(f"🎨 Theme: {theme['name']}")
    print(f"📌 Topic: {data['topic']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox",
                  "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(data["slides"]):
            html = build_slide_html(
                teacher_name   = TEACHER_NAME,
                teacher_handle = TEACHER_HANDLE,
                title          = slide.get("title", ""),
                badge          = slide.get("badge", ""),
                text_content   = slide.get("textAr", ""),
                current_index  = i,
                total_slides   = total_slides,
                theme          = theme,
            )
            await page.set_content(html, wait_until="domcontentloaded")
            out_path = OUTPUT_DIR / f"slide_{i+1}.png"
            await page.screenshot(path=str(out_path))
            print(f"  ✅ slide_{i+1}.png saved")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(data["caption"], encoding="utf-8")
    print("🎉 All slides generated!")

if __name__ == "__main__":
    asyncio.run(main())
