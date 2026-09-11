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
# هاشتاجات ثابتة تُضاف لكل منشور
# ════════════════════════════════════════════════════════════════
FIXED_HASHTAGS = (
    "#تعلم_الإنجليزية #تعليم_الإنجليزي #الإنجليزي #الإنجليزية "
    "#السادس_الإعدادي #الثالث_المتوسط #تعلم_ببساطة #أحمد_الحيالي "
    "#انجليزي_العراق #تعلم_اللغات"
)

# ════════════════════════════════════════════════════════════════
# Gemini API
# ════════════════════════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash-latest:generateContent?key={key}"
)

# ════════════════════════════════════════════════════════════════
# الثيمات — ملزمة AH: خلفية أغمق قليلاً، نصوص كحلية/سوداء
# ════════════════════════════════════════════════════════════════
NOTEBOOK_THEMES = [
    {   # Classic — رمادي دافئ
        "name": "AH Classic",
        "bg":          "#e8e6e0",
        "card_bg":     "#f9f8f5",
        "border":      "#c8b89a",
        "text":        "#1a1a1a",
        "title":       "#c8a84b",
        "header_name": "#0d0d0d",
        "header_handle":"#0d0d0d",
        "counter":     "#0d0d0d",
        "badge_bg":    "#1a1a2e",
        "badge_text":  "#c8a84b",
        "header_line": "#c8a84b",
        "footer_text": "#aaa098",
    },
    {   # Navy — أزرق كحلي فاتح
        "name": "AH Navy",
        "bg":          "#dde2ec",
        "card_bg":     "#f5f7fb",
        "border":      "#9aaac4",
        "text":        "#0d0d1a",
        "title":       "#c8a84b",
        "header_name": "#0d0d0d",
        "header_handle":"#0d0d0d",
        "counter":     "#0d0d0d",
        "badge_bg":    "#1e2d5e",
        "badge_text":  "#f0c040",
        "header_line": "#1e2d5e",
        "footer_text": "#9aaac4",
    },
    {   # Sage — أخضر زيتوني فاتح
        "name": "AH Sage",
        "bg":          "#dde6dd",
        "card_bg":     "#f5faf5",
        "border":      "#90b890",
        "text":        "#0d1a0d",
        "title":       "#c8a84b",
        "header_name": "#0d0d0d",
        "header_handle":"#0d0d0d",
        "counter":     "#0d0d0d",
        "badge_bg":    "#1e4a1e",
        "badge_text":  "#e8d888",
        "header_line": "#1e4a1e",
        "footer_text": "#90b890",
    },
    {   # Warm — بيج دافئ
        "name": "AH Warm",
        "bg":          "#ede5d8",
        "card_bg":     "#faf7f2",
        "border":      "#c4a882",
        "text":        "#1a0d00",
        "title":       "#c8a84b",
        "header_name": "#0d0d0d",
        "header_handle":"#0d0d0d",
        "counter":     "#0d0d0d",
        "badge_bg":    "#5c2e00",
        "badge_text":  "#fde8b8",
        "header_line": "#c8a84b",
        "footer_text": "#c4a882",
    },
]

# ════════════════════════════════════════════════════════════════
# البرومبت لـ Gemini
# ════════════════════════════════════════════════════════════════
def build_prompt(used_topics: list) -> str:
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "لا يوجد"
    return f"""أنت متخصص في إنشاء محتوى تعليمي إنجليزي للمنصات الاجتماعية.

المطلوب: اختر موضوعاً إنجليزياً تعليمياً وابتكر كاروسيل من 4 شرائح.

**معايير الموضوع:**
- مفيد لطلاب المراحل الدراسية العراقية (ابتدائي، متوسط، إعدادي) وكذلك لمن يطوّر إنجليزيته
- يتنوع بين: قواعد نحوية، مفردات، أخطاء شائعة، تراكيب مهمة، مهارات تواصل، نصائح تعلم
- لا تكرر أي موضوع من هذه القائمة:
{used_str}

**معايير اللغة والأسلوب:**
- اللغة: عربية فصيحة مبسطة وواضحة — رسمية ومفهومة، لا عامية
- الأسلوب: معلم محترف يقدم فائدة مباشرة وعملية
- ممنوع: "في هذا المنشور"، "ختاماً"، "شاركنا رأيك"، كلمات عامية
- الأمثلة الإنجليزية تُكتب بالإنجليزية والترجمة بالعربية

**الكابشن:** اكتب جملتين فقط تصفان فائدة المحتوى. لا هاشتاجات (تُضاف تلقائياً).

**صيغة الإجابة:** JSON فقط بدون أي نص خارجه:

{{
  "topic": "عنوان الموضوع بالعربي | English Title",
  "caption": "جملتان فقط عن فائدة المحتوى — بدون هاشتاجات",
  "slides": [
    {{
      "badge": "نص الـ badge القصير + إيموجي",
      "title": "عنوان الشريحة + إيموجي",
      "textAr": "محتوى الشريحة — واضح ومنظم"
    }},
    {{"badge":"...","title":"...","textAr":"..."}},
    {{"badge":"...","title":"...","textAr":"..."}},
    {{"badge":"...","title":"...","textAr":"..."}}
  ]
}}"""

# ════════════════════════════════════════════════════════════════
# مواضيع احتياطية (تُستخدم فقط إذا فشل Gemini)
# ════════════════════════════════════════════════════════════════
FALLBACK_TOPICS = [
    {
        "topic": "أخطاء شائعة | Make vs Do",
        "caption": "خطأ يقع فيه معظم متعلمي الإنجليزية عند استخدام Make وDo.\nتعرّف على القاعدة الصحيحة بأمثلة عملية واضحة.",
        "slides": [
            {"badge": "خطأ شائع ⚠️", "title": "Make أم Do؟ 🤔",
             "textAr": "هذا السؤال يُربك حتى المتقدمين.\n\nالقاعدة الأساسية:\n• Make = تصنع شيئاً أو تُنشئه\n• Do = تؤدي نشاطاً أو مهمة"},
            {"badge": "استخدام Make 📝", "title": "متى تستخدم Make؟",
             "textAr": "Make a mistake — يرتكب خطأ\nMake a decision — يتخذ قراراً\nMake a friend — يكوّن صداقة\nMake money — يكسب مالاً\nMake a phone call — يجري مكالمة"},
            {"badge": "استخدام Do 📝", "title": "متى تستخدم Do؟",
             "textAr": "Do homework — يؤدي الواجب\nDo exercise — يمارس الرياضة\nDo the dishes — يغسل الأطباق\nDo your best — يبذل قصارى جهده\nDo a course — يلتحق بدورة"},
            {"badge": "تطبيق 🎯", "title": "حل هذه الجمل",
             "textAr": "1. He ___ a big mistake yesterday.\n2. I need to ___ my homework now.\n3. She wants to ___ new friends.\n\nالإجابات: made / do / make"},
        ]
    },
    {
        "topic": "مفردات المشاعر | Feelings in English",
        "caption": "كلمة happy وحدها لا تكفي للتعبير عن مشاعرك بالإنجليزية.\nتعرّف على مفردات أدق وأكثر تعبيراً يستخدمها المتحدثون الأصليون.",
        "slides": [
            {"badge": "مفردات المشاعر 💭", "title": "تجاوز happy وsad! 🔄",
             "textAr": "المتحدث الأصلي لا يكتفي بكلمة happy أو sad.\n\nيستخدم كلمات أدق تحمل معنى أعمق وأكثر تعبيراً."},
            {"badge": "بدل Happy 😊", "title": "كلمات أقوى من Happy",
             "textAr": "Thrilled — سعيد جداً ومتحمس\nRelieved — مرتاح بعد قلق\nContent — راضٍ وهادئ\nGrateful — ممتنن\nExcited — متحمس جداً"},
            {"badge": "بدل Sad 😔", "title": "كلمات أدق من Sad",
             "textAr": "Disappointed — خذلان وإحباط\nFrustrated — محبط بسبب عقبة\nOverwhelmed — مثقول ومضغوط\nLonely — وحيد\nHeartbroken — حزين جداً"},
            {"badge": "تطبيق 🎯", "title": "استخدمها في جمل",
             "textAr": "بدلاً من: I am happy about my result\nقُل: I'm thrilled about my result!\n\nبدلاً من: I'm sad\nقُل: I'm a bit disappointed\n\nالفارق كبير في التعبير."},
        ]
    },
]

# ════════════════════════════════════════════════════════════════
# إدارة السجل
# ════════════════════════════════════════════════════════════════
def load_history() -> list:
    for src in [os.getenv("USED_TOPICS_JSON"), None]:
        if src is not None:
            try: return json.loads(src)
            except: continue
        if HISTORY_FILE.exists():
            try: return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            except: pass
    return []

def save_history(history: list):
    HISTORY_FILE.write_text(
        json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"📝 History saved ({len(history)} topics)")

# ════════════════════════════════════════════════════════════════
# استدعاء Gemini
# ════════════════════════════════════════════════════════════════
def call_gemini(prompt: str) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set")
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.85,
            "maxOutputTokens": 1500,
            "responseMimeType": "application/json",
        },
    }
    req = urllib.request.Request(
        GEMINI_URL.format(key=GEMINI_API_KEY),
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode())
    raw = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    raw = raw.strip("`").lstrip("json").strip()
    return json.loads(raw)

def get_daily_topic() -> dict:
    history = load_history()
    if GEMINI_API_KEY:
        for attempt in range(1, 4):
            try:
                print(f"🤖 Gemini attempt {attempt}/3...")
                data = call_gemini(build_prompt(history))
                assert "topic" in data and "slides" in data
                assert len(data["slides"]) == 4
                # أضف الهاشتاجات الثابتة للكابشن
                data["caption"] = data.get("caption", "").strip() + "\n\n" + FIXED_HASHTAGS
                history.append(data["topic"])
                if len(history) > 60:
                    history = history[-60:]
                save_history(history)
                print(f"✅ Topic: {data['topic']}")
                return data
            except Exception as e:
                print(f"⚠️  Attempt {attempt} failed: {e}")
    else:
        print("⚠️  No GEMINI_API_KEY — using fallback")

    # Fallback
    used = set(history)
    available = [f for f in FALLBACK_TOPICS if f["topic"] not in used] or FALLBACK_TOPICS
    chosen = random.choice(available)
    chosen = dict(chosen)
    chosen["caption"] = chosen["caption"].strip() + "\n\n" + FIXED_HASHTAGS
    history.append(chosen["topic"])
    if len(history) > 60:
        history = history[-60:]
    save_history(history)
    return chosen

# ════════════════════════════════════════════════════════════════
# HTML السلايد
# ════════════════════════════════════════════════════════════════
def build_slide_html(teacher_name, teacher_handle, title, badge,
                     text_content, current_index, total_slides, theme):
    lines = text_content.split('\n')
    formatted = ""
    for line in lines:
        s = line.strip()
        if not s:
            formatted += '<div style="height:10px;"></div>'
            continue
        has_ar = any('\u0600' <= c <= '\u06FF' for c in s)
        align  = "right" if has_ar else "left"
        dirn   = "rtl"   if has_ar else "ltr"
        formatted += (
            f'<div style="text-align:{align};direction:{dirn};'
            f'margin-bottom:15px;font-size:28px;line-height:1.8;'
            f'font-weight:600;color:{theme["text"]};">{s}</div>'
        )

    badge_html = (
        f'<div style="background:{theme["badge_bg"]};color:{theme["badge_text"]};'
        f'padding:7px 18px;border-radius:6px;font-size:20px;font-weight:700;'
        f'white-space:nowrap;flex-shrink:0;">{badge}</div>'
    ) if badge else ""

    # إيموجيات الأرقام بدل الأيقونات
    num_emojis = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
    slide_emoji = num_emojis[current_index] if current_index < len(num_emojis) else f"{current_index+1}"

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
  padding:52px 58px 38px;
  overflow:hidden;
}}
.header {{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:14px;
  border-bottom:3px solid {theme["header_line"]};
  margin-bottom:26px;
}}
.teacher-name {{
  font-size:38px; font-weight:900;
  color:{theme["header_name"]};
  letter-spacing:-0.3px;
}}
.teacher-handle {{
  font-size:21px; font-weight:700;
  color:{theme["header_handle"]};
  direction:ltr; text-align:right; margin-top:2px;
}}
.slide-counter {{
  font-size:28px; font-weight:800;
  color:{theme["counter"]};
  direction:ltr;
}}
.card {{
  flex:1;
  background:{theme["card_bg"]};
  border:2.5px dashed {theme["border"]};
  border-radius:18px; padding:38px 44px;
  display:flex; flex-direction:column;
  box-shadow:0 6px 24px rgba(0,0,0,0.09);
}}
.card-header {{
  display:flex; align-items:flex-start;
  justify-content:space-between; gap:14px;
  margin-bottom:24px; padding-bottom:18px;
  border-bottom:2px dashed {theme["border"]};
}}
.card-title {{
  font-size:40px; font-weight:900;
  color:{theme["title"]};
  line-height:1.2; flex:1;
}}
.card-body {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
}}
.footer {{
  margin-top:16px; padding-top:10px;
  border-top:1.5px solid {theme["border"]};
  text-align:center;
  font-size:18px; font-weight:600;
  color:{theme["footer_text"]}; direction:ltr; letter-spacing:.6px;
}}
</style></head>
<body>
  <div class="header">
    <div>
      <div class="teacher-name">{teacher_name}</div>
      <div class="teacher-handle">{teacher_handle}</div>
    </div>
    <div class="slide-counter">{slide_emoji} {current_index+1:02d} / {total_slides:02d}</div>
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

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(data["slides"]):
            html = build_slide_html(
                teacher_name=TEACHER_NAME,
                teacher_handle=TEACHER_HANDLE,
                title=slide.get("title",""),
                badge=slide.get("badge",""),
                text_content=slide.get("textAr",""),
                current_index=i,
                total_slides=total_slides,
                theme=theme,
            )
            await page.set_content(html, wait_until="domcontentloaded")
            out_path = OUTPUT_DIR / f"slide_{i+1}.png"
            await page.screenshot(path=str(out_path))
            print(f"  ✅ slide_{i+1}.png")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(data.get("caption",""), encoding="utf-8")
    print("🎉 Done!")

if __name__ == "__main__":
    asyncio.run(main())
