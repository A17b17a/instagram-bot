import asyncio
import json
import random
import re
import os
import urllib.request
from pathlib import Path
from playwright.async_api import async_playwright

OUTPUT_DIR   = Path("daily_post")
HISTORY_FILE = Path(os.getenv("HISTORY_FILE", "used_topics.json"))
SIZE         = 1080

TEACHER_NAME   = "أحمد الحيالي"
TEACHER_HANDLE = "@ahmed.hayali.iq"

# ════════════════════════════════════════════════════════════════
# هاشتاجات ثابتة بدون همزات
# ════════════════════════════════════════════════════════════════
FIXED_HASHTAGS = (
    "#تعلم_الانجليزية #تعليم_الانجليزي #الانجليزي #الانجليزية "
    "#السادس_الاعدادي #الثالث_المتوسط #تعلم_ببساطة "
    "#احمد_الحيالي #احمد_موسى #انجليزي_العراق #تعلم_اللغات"
)

# ════════════════════════════════════════════════════════════════
# Gemini API
# ════════════════════════════════════════════════════════════════
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

# ════════════════════════════════════════════════════════════════
# الثيم الموحد للبراند (ألوان رسمية، تباين ممتاز، مظهر دفاتر مرتب)
# ════════════════════════════════════════════════════════════════
UNIFIED_THEME = {
    "bg":            "#e2e0d8",
    "card_bg":       "#ffffff",
    "border":        "#000000",
    "text":          "#111111",
    "title":         "#000000",
    "header_name":   "#000000",
    "header_handle": "#000000",
    "counter":       "#000000",
    "badge_bg":      "#000000",
    "badge_text":    "#ffffff",
    "divider":       "#000000",
    "footer_text":   "#000000",
    "highlight":     "#000000",
}

# ════════════════════════════════════════════════════════════════
# سلايد الاشتراك الثابت والموحد (الشكل القديم الأصلي)
# ════════════════════════════════════════════════════════════════
SUBSCRIBE_SLIDE = {
    "badge":  "تابعني",
    "title":  "استمر في التعلم معي",
    "textAr": (
        "اشترك في الحساب لمزيد من الشروحات والملاحظات اليومية.\n\n"
        "جميع روابط حساباتي تجدونها في بايو الحساب."
    ),
    "is_final": True
}

# ════════════════════════════════════════════════════════════════
# تنظيف الكابشن من رموز الماركداون
# ════════════════════════════════════════════════════════════════
def clean_caption_text(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    return text.strip()

# ════════════════════════════════════════════════════════════════
# بناء البرومبت لـ Gemini
# ════════════════════════════════════════════════════════════════
def build_prompt(used_topics: list) -> str:
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "لا يوجد"
    return f"""أنت أستاذ لغة إنجليزية محترف تشرح لطلاب المدارس العراقية والمبتدئين.

المطلوب: إنشاء محتوى تعليمي دسم وشامل من 4 شرائح.

قواعد مهمة جداً:
1. اختر موضوعاً يهم الطلاب (قواعد، فرق بين كلمتين، أخطاء شائعة، أزمنة).
2. لا تكرر أي موضوع من القائمة التالية:
{used_str}

3. هيكلة الشرائح:
   - الشريحة 1: المقدمة والقاعدة الأساسية الشاملة.
   - الشريحة 2: القسم الأول من القاعدة مع الشرح وأمثلة.
   - الشريحة 3: القسم الثاني من القاعدة مع الشرح وأمثلة.
   - الشريحة 4: بعنوان "أمثلة توضيحية" وتتضمن 3 جمل مع ترجمتها.

4. صيغة الجمل الإنجليزية:
   - ضع الكلمة/الجملة الإنجليزية ثم شارحة (—) ثم المعنى العربي، مثال: Make a mistake — يرتكب خطأ

صيغة الإجابة: JSON فقط:
{{
  "topic": "عنوان الموضوع",
  "caption": "عنوان المنشور الواضح\\n\\nتوضيح وملاحظة علمية شاملة عن الدرس تجعل الطالب يفهم القاعدة بسهولة.",
  "slides": [
    {{"badge": "مفهوم أساسي", "title": "عنوان الشريحة الأولى", "textAr": "الشرح العلمي..."}},
    {{"badge": "الحالة الأولى", "title": "عنوان الشريحة الثانية", "textAr": "الشرح التفصيلي..."}},
    {{"badge": "الحالة الثالثة", "title": "عنوان الشريحة الثالثة", "textAr": "الشرح التفصيلي..."}},
    {{"badge": "تطبيق", "title": "أمثلة توضيحية", "textAr": "1. He made a mistake — هو ارتكب خطأ\\n2. I do my homework — أنا أؤدي واجبي\\n3. She makes progress — هي تحقق تقدماً"}}
  ]
}}"""

FALLBACK_TOPICS = [
    {
        "topic": "الفرق بين Make و Do",
        "caption": "الفرق الدقيق بين الفعلين Make و Do في اللغة الإنجليزية\n\nكثيراً ما يقع الطلاب في خطأ التمييز بين Make و Do. القاعدة البسيطة هي أن Make تستخدم عند إيجاد أو إنتاج شيء جديد، بينما Do تُستخدم للأنشطة والمهام العامة.",
        "slides": [
            {
                "badge": "القاعدة العامة",
                "title": "الفرق بين Make و Do",
                "textAr": "الفعل Make يعني الصنع أو الإنشاء لشيء ملموس أو غير ملموس.\n\nالفعل Do يعني أداء مهمة، عمل، أو نشاط روتيني."
            },
            {
                "badge": "استخدام Make",
                "title": "متى نستخدم Make؟",
                "textAr": "نستخدم Make مع القرارات والأشياء المبتكرة:\n\nMake a decision — يتخذ قراراً\nMake a mistake — يرتكب خطأً\nMake money — يكسب مالاً"
            },
            {
                "badge": "استخدام Do",
                "title": "متى نستخدم Do؟",
                "textAr": "نستخدم Do مع المهام والأنشطة اليومية:\n\nDo homework — يؤدي الواجب البيتي\nDo business — يجري أعمالاً تجارية\nDo your best — تبذل قصارى جهدك"
            },
            {
                "badge": "تطبيق",
                "title": "أمثلة توضيحية",
                "textAr": "1. He made a big mistake yesterday — هو ارتكب خطأ كبيراً يوم أمس.\n2. I need to do my homework now — أحتاج إلى أداء واجبي الآن.\n3. She wants to make new friends — هي ترغب في تكوين صداقات."
            }
        ]
    }
]

def load_history() -> list:
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

def call_gemini(prompt: str) -> dict:
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set")

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 2000,
            "responseMimeType": "application/json",
        },
    }
    data = json.dumps(payload).encode("utf-8")
    url  = GEMINI_URL.format(key=GEMINI_API_KEY)
    req  = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    raw_text = result["candidates"][0]["content"]["parts"][0]["text"].strip()
    if raw_text.startswith("```"):
        raw_text = raw_text.split("```")[1]
        if raw_text.startswith("json"):
            raw_text = raw_text[4:]
    raw_text = raw_text.strip()

    return json.loads(raw_text)

def get_daily_topic() -> dict:
    history = load_history()

    if GEMINI_API_KEY:
        for attempt in range(1, 4):
            try:
                prompt     = build_prompt(history)
                topic_data = call_gemini(prompt)

                assert "topic" in topic_data
                assert "slides" in topic_data
                assert len(topic_data["slides"]) == 4

                clean_cap = clean_caption_text(topic_data.get("caption", ""))
                topic_data["caption"] = clean_cap + "\n\n" + FIXED_HASHTAGS

                history.append(topic_data["topic"])
                history = history[-60:]
                save_history(history)

                return topic_data
            except Exception as e:
                print(f"⚠️ Attempt {attempt} failed: {e}")

    chosen = dict(FALLBACK_TOPICS[0])
    clean_cap = clean_caption_text(chosen["caption"])
    chosen["caption"] = clean_cap + "\n\n" + FIXED_HASHTAGS

    history.append(chosen["topic"])
    history = history[-60:]
    save_history(history)
    return chosen

# ════════════════════════════════════════════════════════════════
# تنسيق محتوى النصوص وإدراج الخطوط
# ════════════════════════════════════════════════════════════════
def format_text_content(text_content):
    lines = text_content.split('\n')
    formatted_blocks = []

    for line in lines:
        s = line.strip()
        if not s:
            formatted_blocks.append('<div style="height:12px;"></div>')
            continue

        s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)

        if '—' in s:
            parts = s.split('—')
            en_part = parts[0].strip()
            ar_part = parts[1].strip()
            formatted_blocks.append(
                f'<div style="margin-bottom:16px; background:#f4f3ef; padding:12px 18px; border-right:5px solid #000; border-left:1px solid #ddd;">'
                f'  <div dir="ltr" style="text-align:left; font-size:28px; font-weight:800; color:#000; font-family:\'Cairo\', sans-serif;">{en_part}</div>'
                f'  <div dir="rtl" style="text-align:right; font-size:24px; font-weight:700; color:#222; margin-top:4px; font-family:\'Cairo\', sans-serif;">{ar_part}</div>'
                f'</div>'
            )
        else:
            has_ar = any('\u0600' <= c <= '\u06FF' for c in s)
            align, direction = ("right", "rtl") if has_ar else ("left", "ltr")
            formatted_blocks.append(
                f'<div style="text-align:{align}; direction:{direction}; font-family:\'Cairo\', sans-serif; '
                f'margin-bottom:14px; font-size:26px; line-height:1.6; font-weight:700; color:#111;">{s}</div>'
            )

    return "".join(formatted_blocks)

def build_slide_html(teacher_name, teacher_handle, title, badge,
                     text_content, current_index, total_slides, theme, is_final=False):
    
    if is_final:
        # التصميم الاصلي والتطابق التام للسلايد الخامس (الاشتراك)
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; font-family:'Cairo', sans-serif !important; }}
body {{
  width:1080px; height:1080px;
  background:{theme["bg"]};
  color:{theme["text"]};
  display:flex; flex-direction:column;
  padding:50px 55px 35px; overflow:hidden;
}}
.header {{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:14px;
  border-bottom:3px solid {theme["divider"]};
  margin-bottom:24px;
}}
.teacher-name  {{ font-size:36px; font-weight:900; color:{theme["header_name"]}; }}
.teacher-handle{{ font-size:20px; font-weight:700; color:{theme["header_handle"]}; direction:ltr; text-align:right; margin-top:2px; }}
.slide-counter {{ font-size:28px; font-weight:800; color:{theme["counter"]}; direction:ltr; }}
.card {{
  flex:1; background:{theme["card_bg"]};
  border:3px solid {theme["border"]};
  padding:50px 42px;
  display:flex; flex-direction:column;
  align-items:center; text-align:center;
}}
.subscribe-badge {{
  background:#000; color:#fff;
  padding:6px 28px; font-size:22px; font-weight:800;
  margin-bottom:15px; display:inline-block;
}}
.card-title {{ font-size:42px; font-weight:900; color:#000; margin-bottom:20px; width:100%; }}
.divider-line {{ width:100%; height:3px; background:#000; margin-bottom:120px; }}
.card-body {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  font-size:28px; font-weight:800; line-height:1.8; color:#000; width:100%;
}}
.footer {{
  margin-top:16px; padding-top:10px;
  border-top:3px solid {theme["border"]};
  text-align:center;
  font-size:18px; font-weight:800;
  color:{theme["footer_text"]}; direction:ltr; letter-spacing:.8px;
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
    <div class="subscribe-badge">تابعني</div>
    <div class="card-title">{title}</div>
    <div class="divider-line"></div>
    <div class="card-body">
      <p style="margin-bottom:20px;">اشترك في الحساب لمزيد من الشروحات والملاحظات اليومية.</p>
      <p>جميع روابط حساباتي تجدونها في بايو الحساب.</p>
    </div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

    # الشرائح التعليمية 1 - 4
    body_content = format_text_content(text_content)
    badge_html = f'<div style="background:{theme["badge_bg"]}; color:{theme["badge_text"]}; padding:6px 20px; font-size:22px; font-weight:800; white-space:nowrap; flex-shrink:0;">{badge}</div>' if badge else ""

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; font-family:'Cairo', sans-serif !important; }}
body {{
  width:1080px; height:1080px;
  background:{theme["bg"]};
  color:{theme["text"]};
  display:flex; flex-direction:column;
  padding:50px 55px 35px; overflow:hidden;
}}
.header {{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:14px;
  border-bottom:3px solid {theme["divider"]};
  margin-bottom:24px;
}}
.teacher-name  {{ font-size:36px; font-weight:900; color:{theme["header_name"]}; }}
.teacher-handle{{ font-size:20px; font-weight:700; color:{theme["header_handle"]}; direction:ltr; text-align:right; margin-top:2px; }}
.slide-counter {{ font-size:28px; font-weight:800; color:{theme["counter"]}; direction:ltr; }}
.card {{
  flex:1; background:{theme["card_bg"]};
  border:3px solid {theme["border"]};
  padding:38px 42px;
  display:flex; flex-direction:column;
}}
.card-header {{
  display:flex; align-items:center; justify-content:space-between; gap:16px;
  margin-bottom:24px; padding-bottom:16px;
  border-bottom:3px solid {theme["border"]}; width: 100%;
}}
.card-title {{ font-size:40px; font-weight:900; color:{theme["title"]}; line-height:1.2; flex:1; }}
.card-body   {{ flex:1; display:flex; flex-direction:column; justify-content:center; width:100%; }}
.footer {{
  margin-top:16px; padding-top:10px;
  border-top:3px solid {theme["border"]};
  text-align:center;
  font-size:18px; font-weight:800;
  color:{theme["footer_text"]}; direction:ltr; letter-spacing:.8px;
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
    <div class="card-body">{body_content}</div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

# ════════════════════════════════════════════════════════════════
# التشغيل الرئيسي
# ════════════════════════════════════════════════════════════════
async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = get_daily_topic()
    theme = UNIFIED_THEME

    all_slides   = data["slides"] + [SUBSCRIBE_SLIDE]
    total_slides = len(all_slides)

    print(f"📌 Generating topic: {data['topic']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(all_slides):
            is_final = slide.get("is_final", False)
            html = build_slide_html(
                teacher_name=TEACHER_NAME,
                teacher_handle=TEACHER_HANDLE,
                title=slide.get("title", ""),
                badge=slide.get("badge", ""),
                text_content=slide.get("textAr", ""),
                current_index=i,
                total_slides=total_slides,
                theme=theme,
                is_final=is_final
            )
            await page.set_content(html, wait_until="domcontentloaded")
            # ضمان تحميل الخط كاملاً قبل الالتقاط
            await page.evaluate("document.fonts.ready")
            out_path = OUTPUT_DIR / f"slide_{i+1}.png"
            await page.screenshot(path=str(out_path))
            print(f"  ✅ slide_{i+1}.png")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(
        data.get("caption", ""), encoding="utf-8"
    )
    print("🎉 All slides generated successfully with Cairo font & unified design!")

if __name__ == "__main__":
    asyncio.run(main())
