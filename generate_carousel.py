import asyncio
import json
import random
import os
import urllib.request
import urllib.error
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR   = Path("daily_post")
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "used_topics.json"))
SIZE         = 1080

TEACHER_NAME   = "أحمد الحيالي"
TEACHER_HANDLE = "@ahmed.hayali.iq"

# ════════════════════════════════════════════════════════════════
# Gemini API
# ════════════════════════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash-latest:generateContent?key={key}"
)

# ════════════════════════════════════════════════════════════════
# الثيمات — مستوحاة من ملزمة AH (فاتحة دائماً)
# ════════════════════════════════════════════════════════════════
NOTEBOOK_THEMES = [
    {
        "name": "AH Classic",
        "bg": "#f5f5f0", "card_bg": "#ffffff", "border": "#d4c5a9",
        "text": "#1a1a2e", "title": "#c8a84b", "accent": "#1a1a2e",
        "badge_bg": "#1a1a2e", "badge_text": "#c8a84b", "header_line": "#c8a84b",
    },
    {
        "name": "AH Navy",
        "bg": "#f0f2f8", "card_bg": "#ffffff", "border": "#b0bcd4",
        "text": "#1a1a2e", "title": "#c8a84b", "accent": "#2c3e6b",
        "badge_bg": "#2c3e6b", "badge_text": "#f0c040", "header_line": "#2c3e6b",
    },
    {
        "name": "AH Sage",
        "bg": "#f2f5f0", "card_bg": "#ffffff", "border": "#a8c4a8",
        "text": "#1a2e1a", "title": "#c8a84b", "accent": "#2e5e2e",
        "badge_bg": "#2e5e2e", "badge_text": "#f0e0a0", "header_line": "#2e5e2e",
    },
    {
        "name": "AH Warm",
        "bg": "#faf6f0", "card_bg": "#ffffff", "border": "#d4b896",
        "text": "#2e1a0a", "title": "#c8a84b", "accent": "#8b4513",
        "badge_bg": "#8b4513", "badge_text": "#fdecc8", "header_line": "#c8a84b",
    },
]

# ════════════════════════════════════════════════════════════════
# البرومبت الرئيسي لـ Gemini
# ════════════════════════════════════════════════════════════════
def build_prompt(used_topics: list) -> str:
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "لا يوجد"
    return f"""أنت مساعد متخصص في إنشاء محتوى تعليمي إنجليزي للمنصات الاجتماعية.

المطلوب: اختر موضوعاً إنجليزياً تعليمياً جديداً وابتكر محتوى كاروسيل من 4 شرائح.

**شروط الموضوع:**
- يجب أن يكون مفيداً لطلاب المراحل الدراسية العراقية (ابتدائي، متوسط، إعدادي) وأيضاً لمن يريد تطوير إنجليزيته عموماً
- يتنوع بين: قواعد نحوية، مفردات، أخطاء شائعة، تراكيب مهمة، مهارات محادثة، نصائح تعلم
- يمنع تكرار أي موضوع من القائمة التالية:
{used_str}

**شروط اللغة والأسلوب:**
- اللغة: عربية واضحة وسلسة (ليست فصحى متكلفة ولا عامية خالصة)
- الأسلوب: معلم خبير يشارك فائدة مباشرة وعملية
- يمنع منعاً باتاً: "في هذا المنشور"، "ختاماً"، "شاركنا رأيك"
- المحتوى العربي يُكتب بشكل واضح، والأمثلة الإنجليزية تُكتب بخط إنجليزي

**صيغة الإجابة:** JSON فقط، بدون أي نص خارجه، بهذا الشكل بالضبط:

{{
  "topic": "عنوان الموضوع بالعربي | English Title",
  "caption": "نص الكابشن مع الهاشتاجات (5-8 هاشتاقات مناسبة للمحتوى الإنجليزي والتعليمي)",
  "slides": [
    {{
      "badge": "نص الـ badge القصير + إيموجي",
      "title": "عنوان الشريحة + إيموجي",
      "textAr": "محتوى الشريحة — أسطر قصيرة واضحة مع الأمثلة الإنجليزية"
    }},
    {{
      "badge": "...",
      "title": "...",
      "textAr": "..."
    }},
    {{
      "badge": "...",
      "title": "...",
      "textAr": "..."
    }},
    {{
      "badge": "...",
      "title": "...",
      "textAr": "..."
    }}
  ]
}}

مهم جداً: أرجع JSON فقط، بدون ```json أو أي نص إضافي."""


# ════════════════════════════════════════════════════════════════
# مواضيع احتياطية (تُستخدم فقط إذا فشل Gemini)
# ════════════════════════════════════════════════════════════════
FALLBACK_TOPICS = [
    {
        "topic": "أخطاء شائعة | Make vs Do",
        "caption": "⚠️ Make أو Do — وين تستخدم كل واحدة؟\n\nغلطة يسويها 90% من متعلمي الإنجليزي. توقف عن التخمين!\n\n#إنجليزي #قواعد_إنجليزية #تعلم_إنجليزي #أحمد_الحيالي #انجليزي_عراق",
        "slides": [
            {"badge": "خطأ شائع ⚠️", "title": "Make أم Do؟ 🤔",
             "textAr": "هذا السؤال يحيّر حتى المتقدمين!\n\nالقاعدة الأساسية:\n• Make = تصنع شيئاً أو تخلقه\n• Do = تنفّذ نشاطاً أو مهمة"},
            {"badge": "استخدام Make 📝", "title": "متى تستخدم Make؟ ✅",
             "textAr": "Make a mistake (تغلط)\nMake a decision (تقرر)\nMake a friend (تصادق)\nMake money (تكسب)\nMake a phone call (تتصل)"},
            {"badge": "استخدام Do 📝", "title": "متى تستخدم Do؟ ✅",
             "textAr": "Do homework (تسوي واجب)\nDo exercise (تتمرن)\nDo the dishes (تغسل صحون)\nDo your best (تبذل قصارى)\nDo a course (تأخذ كورس)"},
            {"badge": "اختبر نفسك 🎯", "title": "حل هذه الجمل 💡",
             "textAr": "1. He ___ a big mistake yesterday.\n2. I need to ___ my homework now.\n3. She wants to ___ new friends.\n\nالأجوبة: made / do / make\n\nكيف كانت نتيجتك؟ 👇"},
        ]
    },
    {
        "topic": "مفردات مهمة | Feelings & Emotions",
        "caption": "💬 كيف تعبّر عن مشاعرك بالإنجليزي بطريقة طبيعية؟\n\nما يكفي تقول happy أو sad — في كلمات أقوى بكثير!\n\n#مفردات_إنجليزية #تعلم_إنجليزي #احساسات #أحمد_الحيالي",
        "slides": [
            {"badge": "مفردات المشاعر 💭", "title": "بدّل هالكلمات! 🔄",
             "textAr": "كلمة happy وحدها ما تكفي.\n\nالمتحدثون الأصليون يستخدمون كلمات أدق وأقوى لوصف مشاعرهم."},
            {"badge": "بدل Happy 😊", "title": "كلمات أقوى من Happy",
             "textAr": "• Thrilled = سعيد جداً ومتحمس\n• Relieved = مرتاح بعد قلق\n• Content = راضي وهادئ\n• Grateful = ممتنن\n• Excited = متحمس جداً"},
            {"badge": "بدل Sad 😔", "title": "كلمات أدق من Sad",
             "textAr": "• Disappointed = خذلان وإحباط\n• Frustrated = محبط بسبب عقبة\n• Overwhelmed = مثقول ومضغوط\n• Lonely = وحيد\n• Heartbroken = حزين جداً"},
            {"badge": "تطبيق 🗣️", "title": "استخدمها الحين! ✍️",
             "textAr": "بدل ما تقول: I am happy about my result\nقل: I'm thrilled about my result!\n\nبدل: I'm sad\nقل: I'm a bit disappointed\n\nالفرق كبير! 🎯"},
        ]
    },
]

# ════════════════════════════════════════════════════════════════
# إدارة سجل المواضيع
# ════════════════════════════════════════════════════════════════
def load_history() -> list:
    env_val = os.getenv("USED_TOPICS_JSON")
    if env_val:
        try:
            return json.loads(env_val)
        except Exception:
            pass
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []

def save_history(history: list):
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"📝 History saved ({len(history)} topics used)")

# ════════════════════════════════════════════════════════════════
# استدعاء Gemini API
# ════════════════════════════════════════════════════════════════
def call_gemini(prompt: str) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 1500,
            "responseMimeType": "application/json",
        },
    }
    data    = json.dumps(payload).encode("utf-8")
    url     = GEMINI_URL.format(key=GEMINI_API_KEY)
    req     = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    # تنظيف أي backticks إضافية
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    return json.loads(raw_text)

# ════════════════════════════════════════════════════════════════
# الحصول على الموضوع اليومي
# ════════════════════════════════════════════════════════════════
def get_daily_topic() -> dict:
    history = load_history()

    # ── محاولة Gemini (3 محاولات) ──
    if GEMINI_API_KEY:
        for attempt in range(1, 4):
            try:
                print(f"🤖 Gemini attempt {attempt}/3...")
                prompt    = build_prompt(history)
                topic_data = call_gemini(prompt)

                # التحقق من البنية
                assert "topic" in topic_data
                assert "slides" in topic_data
                assert len(topic_data["slides"]) == 4
                for s in topic_data["slides"]:
                    assert "title" in s and "textAr" in s

                # حفظ العنوان في السجل
                history.append(topic_data["topic"])
                # احتفظ بآخر 60 موضوع فقط (شهرين)
                if len(history) > 60:
                    history = history[-60:]
                save_history(history)

                print(f"✅ Gemini generated: {topic_data['topic']}")
                return topic_data

            except Exception as e:
                print(f"⚠️  Gemini attempt {attempt} failed: {e}")
    else:
        print("⚠️  GEMINI_API_KEY not set — using fallback topics")

    # ── Fallback: المواضيع الاحتياطية ──
    print("📦 Using fallback topic...")
    used_fallback = [h for h in history if any(f["topic"] == h for f in FALLBACK_TOPICS)]
    available     = [f for f in FALLBACK_TOPICS if f["topic"] not in used_fallback]
    if not available:
        available = FALLBACK_TOPICS

    chosen = random.choice(available)
    history.append(chosen["topic"])
    if len(history) > 60:
        history = history[-60:]
    save_history(history)
    return chosen

# ════════════════════════════════════════════════════════════════
# HTML للسلايد — ثيم الملزمة
# ════════════════════════════════════════════════════════════════
def build_slide_html(teacher_name, teacher_handle, title, badge,
                     text_content, current_index, total_slides, theme):
    lines = text_content.split('\n')
    formatted = ""
    for line in lines:
        s = line.strip()
        if not s:
            formatted += '<div style="height:12px;"></div>'
            continue
        has_ar = any('\u0600' <= c <= '\u06FF' for c in s)
        align, direction = ("right", "rtl") if has_ar else ("left", "ltr")
        formatted += (
            f'<div style="text-align:{align};direction:{direction};'
            f'margin-bottom:16px;font-size:29px;line-height:1.75;'
            f'font-weight:600;color:{theme["text"]};">{s}</div>'
        )

    badge_html = (
        f'<div style="background:{theme["badge_bg"]};color:{theme["badge_text"]};'
        f'padding:7px 20px;border-radius:6px;font-size:21px;font-weight:700;'
        f'white-space:nowrap;flex-shrink:0;">{badge}</div>'
    ) if badge else ""

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head><meta charset="UTF-8">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  width:1080px; height:1080px;
  background:{theme["bg"]};
  font-family:'Noto Sans Arabic','Noto Naskh Arabic','Arial',sans-serif;
  display:flex; flex-direction:column;
  padding:52px 58px 40px; overflow:hidden;
}}
.header {{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:16px;
  border-bottom:3px solid {theme["header_line"]};
  margin-bottom:28px;
}}
.teacher-name  {{ font-size:36px; font-weight:800; color:{theme["accent"]}; }}
.teacher-handle{{ font-size:21px; font-weight:600; color:{theme["title"]}; direction:ltr; text-align:right; margin-top:3px; }}
.slide-counter {{ font-size:30px; font-weight:800; color:{theme["title"]}; direction:ltr; opacity:.85; }}
.card {{
  flex:1; background:{theme["card_bg"]};
  border:2.5px dashed {theme["border"]};
  border-radius:18px; padding:40px 46px;
  display:flex; flex-direction:column;
  box-shadow:0 4px 18px rgba(0,0,0,0.06);
}}
.card-header {{
  display:flex; align-items:flex-start; justify-content:space-between; gap:14px;
  margin-bottom:26px; padding-bottom:20px;
  border-bottom:2px dashed {theme["border"]};
}}
.card-title {{ font-size:42px; font-weight:900; color:{theme["title"]}; line-height:1.2; flex:1; }}
.card-body   {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
.footer {{
  margin-top:18px; padding-top:12px;
  border-top:2px solid {theme["border"]};
  text-align:center;
  font-size:19px; font-weight:600;
  color:{theme["border"]}; direction:ltr; letter-spacing:.8px;
}}
</style></head>
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
    <div class="card-body">{formatted}</div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data         = get_daily_topic()
    theme        = random.choice(NOTEBOOK_THEMES)
    total_slides = len(data["slides"])

    print(f"🎨 Theme  : {theme['name']}")
    print(f"📌 Topic  : {data['topic']}")
    print(f"📊 Slides : {total_slides}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(data["slides"]):
            html = build_slide_html(
                teacher_name=TEACHER_NAME,
                teacher_handle=TEACHER_HANDLE,
                title=slide.get("title", ""),
                badge=slide.get("badge", ""),
                text_content=slide.get("textAr", ""),
                current_index=i,
                total_slides=total_slides,
                theme=theme,
            )
            await page.set_content(html, wait_until="domcontentloaded")
            out_path = OUTPUT_DIR / f"slide_{i+1}.png"
            await page.screenshot(path=str(out_path))
            print(f"  ✅ slide_{i+1}.png")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(
        data.get("caption", ""), encoding="utf-8"
    )
    print("🎉 Done! All slides generated.")

if __name__ == "__main__":
    asyncio.run(main())
