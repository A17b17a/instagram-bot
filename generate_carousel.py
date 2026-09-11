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
# مكتبة الثيمات الملونة (تُختار عشوائياً لكل منشور)
# ════════════════════════════════════════════════════════════════
THEMES = [
    # 1. ثيم سمائي (Sky Blue)
    {
        "bg":            "#e0f2fe",
        "card_bg":       "#ffffff",
        "border":        "#0284c7",
        "text":          "#0f172a",
        "title":         "#0369a1",
        "header_name":   "#0369a1",
        "header_handle": "#0284c7",
        "counter":       "#0369a1",
        "badge_bg":      "#0284c7",
        "badge_text":    "#ffffff",
        "divider":       "#0284c7",
        "footer_text":   "#0369a1",
    },
    # 2. ثيم بنفسجي الملكي (Purple)
    {
        "bg":            "#f3e8ff",
        "card_bg":       "#ffffff",
        "border":        "#7e22ce",
        "text":          "#1e1b4b",
        "title":         "#6b21a8",
        "header_name":   "#6b21a8",
        "header_handle": "#7e22ce",
        "counter":       "#6b21a8",
        "badge_bg":      "#7e22ce",
        "badge_text":    "#ffffff",
        "divider":       "#7e22ce",
        "footer_text":   "#6b21a8",
    },
    # 3. ثيم أخضر زمردي (Emerald Green)
    {
        "bg":            "#dcfce7",
        "card_bg":       "#ffffff",
        "border":        "#15803d",
        "text":          "#052e16",
        "title":         "#166534",
        "header_name":   "#166534",
        "header_handle": "#15803d",
        "counter":       "#166534",
        "badge_bg":      "#15803d",
        "badge_text":    "#ffffff",
        "divider":       "#15803d",
        "footer_text":   "#166534",
    },
    # 4. ثيم أصفر دافئ (Amber Yellow)
    {
        "bg":            "#fef3c7",
        "card_bg":       "#ffffff",
        "border":        "#d97706",
        "text":          "#451a03",
        "title":         "#b45309",
        "header_name":   "#b45309",
        "header_handle": "#d97706",
        "counter":       "#b45309",
        "badge_bg":      "#d97706",
        "badge_text":    "#ffffff",
        "divider":       "#d97706",
        "footer_text":   "#b45309",
    },
    # 5. ثيم أحمر عنابي (Crimson Red)
    {
        "bg":            "#fee2e2",
        "card_bg":       "#ffffff",
        "border":        "#dc2626",
        "text":          "#450a0a",
        "title":         "#b91c1c",
        "header_name":   "#b91c1c",
        "header_handle": "#dc2626",
        "counter":       "#b91c1c",
        "badge_bg":      "#dc2626",
        "badge_text":    "#ffffff",
        "divider":       "#dc2626",
        "footer_text":   "#b91c1c",
    },
    # 6. الثيم الكلاسيكي الرسمائي
    {
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
    }
]

FIXED_HASHTAGS = (
    "#تعلم_الانجليزية #تعليم_الانجليزي #الانجليزي #الانجليزية "
    "#السادس_الاعدادي #الثالث_المتوسط #تعلم_ببساطة "
    "#احمد_الحيالي #احمد_موسى #انجليزي_العراق #تعلم_اللغات"
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "gemini-1.5-flash:generateContent?key={key}"
)

SUBSCRIBE_SLIDE = {
    "badge":  "تابعني",
    "title":  "استمر في التعلم معي",
    "textAr": (
        "اشترك في الحساب لمزيد من الشروحات والملاحظات اليومية.\n\n"
        "جميع روابط حساباتي تجدونها في بايو الحساب."
    ),
    "is_final": True
}

def clean_caption_text(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'__(.*?)__', r'\1', text)
    text = re.sub(r'_(.*?)_', r'\1', text)
    return text.strip()

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

صيغة الإجابة: JSON فقط:
{{
  "topic": "عنوان الموضوع",
  "caption": "عنوان المنشور الواضح\\n\\nتوضيح وملاحظة علمية شاملة عن الدرس تجعل الطالب يفهم القاعدة بسهولة.",
  "slides": [
    {{"badge": "القاعدة العامة", "title": "عنوان الموضوع", "textAr": "الشرح العلمي المباشر..."}},
    {{"badge": "الحالة الأولى", "title": "عنوان الشريحة الثانية", "textAr": "الشرح التفصيلي..."}},
    {{"badge": "الحالة الثانية", "title": "عنوان الشريحة الثالثة", "textAr": "الشرح التفصيلي..."}},
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

def format_text_content(text_content, centered=False, theme=None):
    lines = text_content.split('\n')
    formatted_blocks = []
    card_bg = theme["card_bg"] if theme else "#ffffff"

    for line in lines:
        s = line.strip()
        if not s:
            formatted_blocks.append('<div style="height:14px;"></div>')
            continue

        s = re.sub(r'\*\*(.*?)\*\*', r'\1', s)

        if '—' in s and not centered:
            parts = s.split('—')
            en_part = parts[0].strip()
            ar_part = parts[1].strip()
            formatted_blocks.append(
                f'<div style="margin-bottom:16px; background:#f8f9fa; padding:12px 18px; border-right:5px solid {theme["border"]}; border-left:1px solid #ddd;">'
                f'  <div dir="ltr" style="text-align:left; font-size:28px; font-weight:800; color:{theme["title"]};">{en_part}</div>'
                f'  <div dir="rtl" style="text-align:right; font-size:24px; font-weight:700; color:{theme["text"]}; margin-top:4px;">{ar_part}</div>'
                f'</div>'
            )
        else:
            align = "center" if centered else "right"
            direction = "rtl" if any('\u0600' <= c <= '\u06FF' for c in s) else "ltr"
            formatted_blocks.append(
                f'<div style="text-align:{align}; direction:{direction}; '
                f'margin-bottom:16px; font-size:28px; line-height:1.7; font-weight:700; color:{theme["text"]};">{s}</div>'
            )

    return "".join(formatted_blocks)

def build_slide_html(teacher_name, teacher_handle, title, badge,
                     text_content, current_index, total_slides, theme, is_first=False, is_final=False):
    
    header_html = f"""
    <div class="header">
      <div>
        <div class="teacher-name">{teacher_name}</div>
        <div class="teacher-handle">{teacher_handle}</div>
      </div>
      <div class="slide-counter">{current_index+1:02d} / {total_slides:02d}</div>
    </div>
    """

    if is_first:
        body_content = format_text_content(text_content, centered=True, theme=theme)
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{
  box-sizing: border-box; margin: 0; padding: 0;
  font-family: 'Cairo', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}
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
.intro-badge {{
  background:{theme["badge_bg"]}; color:{theme["badge_text"]};
  padding:6px 28px; font-size:22px; font-weight:800;
  margin-bottom:15px; display:inline-block;
}}
.card-title {{ font-size:44px; font-weight:900; color:{theme["title"]}; margin-bottom:20px; width:100%; }}
.divider-line {{ width:100%; height:3px; background:{theme["border"]}; margin-bottom:60px; }}
.card-body {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  width:100%; align-items:center;
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
  {header_html}
  <div class="card">
    <div class="intro-badge">{badge if badge else "الموضوع"}</div>
    <div class="card-title">{title}</div>
    <div class="divider-line"></div>
    <div class="card-body">
      {body_content}
    </div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

    if is_final:
        return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{
  box-sizing: border-box; margin: 0; padding: 0;
  font-family: 'Cairo', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}
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
  background:{theme["badge_bg"]}; color:{theme["badge_text"]};
  padding:6px 28px; font-size:22px; font-weight:800;
  margin-bottom:15px; display:inline-block;
}}
.card-title {{ font-size:42px; font-weight:900; color:{theme["title"]}; margin-bottom:20px; width:100%; }}
.divider-line {{ width:100%; height:3px; background:{theme["border"]}; margin-bottom:120px; }}
.card-body {{
  flex:1; display:flex; flex-direction:column; justify-content:center;
  font-size:28px; font-weight:800; line-height:1.8; color:{theme["text"]}; width:100%;
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
  {header_html}
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

    body_content = format_text_content(text_content, centered=False, theme=theme)
    badge_html = f'<div style="background:{theme["badge_bg"]}; color:{theme["badge_text"]}; padding:6px 20px; font-size:22px; font-weight:800; white-space:nowrap; flex-shrink:0;">{badge}</div>' if badge else ""

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{
  box-sizing: border-box; margin: 0; padding: 0;
  font-family: 'Cairo', -apple-system, BlinkMacSystemFont, sans-serif !important;
  -webkit-font-smoothing: antialiased;
  text-rendering: optimizeLegibility;
}}
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
  {header_html}
  <div class="card">
    <div class="card-header">
      <div class="card-title">{title}</div>
      {badge_html}
    </div>
    <div class="card-body">{body_content}</div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = get_daily_topic()
    
    # اختيار ثيم عشوائي ملون لكل منشور
    theme = random.choice(THEMES)

    all_slides   = data["slides"] + [SUBSCRIBE_SLIDE]
    total_slides = len(all_slides)

    print(f"📌 Generating topic: {data['topic']}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(all_slides):
            is_first = (i == 0)
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
                is_first=is_first,
                is_final=is_final
            )

            await page.set_content(html, wait_until="networkidle")
            await page.evaluate("document.fonts.ready")
            await asyncio.sleep(0.3)

            out_path = OUTPUT_DIR / f"slide_{i+1}.png"
            await page.screenshot(path=str(out_path))
            print(f"  ✅ slide_{i+1}.png rendered with dynamic color theme")

        await browser.close()

    (OUTPUT_DIR / "caption.txt").write_text(
        data.get("caption", ""), encoding="utf-8"
    )

if __name__ == "__main__":
    asyncio.run(main())
