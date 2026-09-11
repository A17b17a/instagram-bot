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
# هاشتاجات ثابتة — بدون همزات
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
# الثيمات — حواف حادة، عناوين سوداء، خطوط فاصلة ومحيطة سوداء، ووسم أسود بأبيض
# ════════════════════════════════════════════════════════════════
NOTEBOOK_THEMES = [
    {
        "name": "Classic Beige",
        "bg":            "#e5e0d8",
        "card_bg":       "#f8f6f2",
        "border":        "#000000",
        "text":          "#1a1a1a",
        "title":         "#000000",
        "header_name":   "#000000",
        "header_handle": "#000000",
        "counter":       "#000000",
        "badge_bg":      "#000000",
        "badge_text":    "#ffffff",
        "divider":       "#000000",
        "footer_text":   "#000000",
        "highlight":     "#b8860b",
    },
    {
        "name": "Navy Blue",
        "bg":            "#d8dde8",
        "card_bg":       "#f2f4f8",
        "border":        "#000000",
        "text":          "#0d0d1a",
        "title":         "#000000",
        "header_name":   "#000000",
        "header_handle": "#000000",
        "counter":       "#000000",
        "badge_bg":      "#000000",
        "badge_text":    "#ffffff",
        "divider":       "#000000",
        "footer_text":   "#000000",
        "highlight":     "#b8860b",
    },
    {
        "name": "Forest Green",
        "bg":            "#d8e2d8",
        "card_bg":       "#f2f6f2",
        "border":        "#000000",
        "text":          "#0a180a",
        "title":         "#000000",
        "header_name":   "#000000",
        "header_handle": "#000000",
        "counter":       "#000000",
        "badge_bg":      "#000000",
        "badge_text":    "#ffffff",
        "divider":       "#000000",
        "footer_text":   "#000000",
        "highlight":     "#b8860b",
    },
    {
        "name": "Warm Terracotta",
        "bg":            "#e8ddd2",
        "card_bg":       "#faf7f2",
        "border":        "#000000",
        "text":          "#1a0d00",
        "title":         "#000000",
        "header_name":   "#000000",
        "header_handle": "#000000",
        "counter":       "#000000",
        "badge_bg":      "#000000",
        "badge_text":    "#ffffff",
        "divider":       "#000000",
        "footer_text":   "#000000",
        "highlight":     "#b8860b",
    },
]

# ════════════════════════════════════════════════════════════════
# سلايد الاشتراك الثابتة (المعدلة حسب الملاحظات)
# ════════════════════════════════════════════════════════════════
SUBSCRIBE_SLIDE = {
    "badge":  "تابعنا",
    "title":  "استمر في التعلم معنا",
    "textAr": (
        "اشترك في قنواتنا لمزيد من الشروحات والملاحظات اليومية.\n\n"
        "جميع روابط حساباتنا الرسمية تجدونها في وصف الحساب (البايو)."
    ),
}

# ════════════════════════════════════════════════════════════════
# البرومبت الرئيسي لـ Gemini مع إضافة كويز وتمييز الكلمات المفتاحية
# ════════════════════════════════════════════════════════════════
def build_prompt(used_topics: list) -> str:
    used_str = "\n".join(f"- {t}" for t in used_topics) if used_topics else "لا يوجد"
    return f"""أنت متخصص في إنشاء محتوى تعليمي إنجليزي للمنصات الاجتماعية.

المطلوب: اختر موضوعاً إنجليزياً تعليمياً وابتكر كاروسيل من 4 شرائح فقط.

معايير الموضوع:
- مفيد لطلاب المراحل الدراسية العراقية وكذلك لمن يطور إنجليزيته عموما
- يتنوع بين: قواعد نحوية، مفردات، اخطاء شائعة، تراكيب مهمة، نصائح تعلم
- لا تكرر اي موضوع من هذه القائمة:
{used_str}

معايير اللغة والأسلوب:
- عربية فصيحة مبسطة رسمية واضحة — لا عامية ابدا
- معلم محترف يقدم فائدة مباشرة وعملية
- يمنع تماماً استخدام أي إيموجي (Emoji)
- يمنع عبارات مثل: "في هذا المنشور"، "ختاماً"، "شاركنا رأيك"
- ضع الكلمات الإنجليزية الأساسية والأفعال المهمة في الشرائح بين نجمتين مضاعفتين مثل **make** أو **do** لتمييزها بصرياً.

معايير الكابشن (Caption):
- ضع عنواناً واضحاً للمنشور في السطر الأول.
- اتبع الجملة الرئيسية بفوائد المنشور.
- أضف سطرين في نهاية الكابشن يحتويان على سؤال اختباري (Quiz) قصير جداً متعلق بالدرس **بدون ذكر الإجابة**، واكتب تحته: "تجدون الإجابة الصحيحة في قناتنا على التيليجرام (الرابط في البايو)".

صيغة الاجابة: JSON فقط بدون أي نص خارجه:
{{
  "topic": "عنوان الموضوع | English Title",
  "caption": "عنوان المنشور الواضح\\nفائدة المنشور الشاملة.\\n\\nسؤال الكويز:\\nسؤال قصير جداً بدون إجابة؟\\nتجدون الإجابة الصحيحة في قناتنا على التيليجرام (الرابط في البايو).",
  "slides": [
    {{"badge": "نص قصير", "title": "عنوان الشريحة", "textAr": "المحتوى مع تمييز الأفعال والكلمات المفتاحية كـ **make** أو **do**"}},
    {{"badge": "...", "title": "...", "textAr": "..."}},
    {{"badge": "...", "title": "...", "textAr": "..."}},
    {{"badge": "...", "title": "...", "textAr": "..."}}
  ]
}}"""

# ════════════════════════════════════════════════════════════════
# مواضيع احتياطية
# ════════════════════════════════════════════════════════════════
FALLBACK_TOPICS = [
    {
        "topic": "اخطاء شائعة | Make vs Do",
        "caption": "الفرق بين Make و Do في اللغة الانجليزية\nخطأ يقع فيه معظم متعلمي الانجليزية عند استخدام الأفعال الأساسية.\n\nسؤال الكويز:\nChose the correct verb: He ___ a big mistake yesterday. (made / did)?\nتجدون الإجابة الصحيحة في قناتنا على التيليجرام (الرابط في البايو).",
        "slides": [
            {"badge": "خطأ شائع", "title": "Make ام Do؟",
             "textAr": "هذا السؤال يربك حتى المتقدمين.\n\nالقاعدة الاساسية:\n**Make** = تصنع شيئا او تنشئه\n**Do** = تؤدي نشاطا او مهمة"},
            {"badge": "استخدام Make", "title": "متى تستخدم Make؟",
             "textAr": "**Make a mistake** — يرتكب خطأ\n**Make a decision** — يتخذ قرارا\n**Make a friend** — يكون صداقة\n**Make money** — يكسب مالا"},
            {"badge": "استخدام Do", "title": "متى تستخدم Do؟",
             "textAr": "**Do homework** — يؤدي الواجب\n**Do exercise** — يمارس الرياضة\n**Do the dishes** — يغسل الاطباق\n**Do your best** — يبذل قصارى جهده"},
            {"badge": "تطبيق", "title": "حل هذه الجمل",
             "textAr": "1. He **made** a big mistake yesterday.\n2. I need to **do** my homework now.\n3. She wants to **make** new friends."},
        ]
    }
]

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
                print(f"🤖 Gemini attempt {attempt}/3...")
                prompt     = build_prompt(history)
                topic_data = call_gemini(prompt)

                assert "topic" in topic_data
                assert "slides" in topic_data
                assert len(topic_data["slides"]) == 4

                topic_data["caption"] = (
                    topic_data.get("caption", "").strip() + "\n\n" + FIXED_HASHTAGS
                )

                history.append(topic_data["topic"])
                history = history[-60:]
                save_history(history)

                print(f"✅ Generated: {topic_data['topic']}")
                return topic_data
            except Exception as e:
                print(f"⚠️ Attempt {attempt} failed: {e}")
    else:
        print("⚠️ GEMINI_API_KEY not set — using fallback")

    used_fallback = [h for h in history if any(f["topic"] == h for f in FALLBACK_TOPICS)]
    available     = [f for f in FALLBACK_TOPICS if f["topic"] not in used_fallback] or FALLBACK_TOPICS

    chosen = dict(random.choice(available))
    chosen["caption"] = chosen["caption"].strip() + "\n\n" + FIXED_HASHTAGS

    history.append(chosen["topic"])
    history = history[-60:]
    save_history(history)
    return chosen

# ════════════════════════════════════════════════════════════════
# HTML السلايد — خط شبه رسمي (Cairo)، حواف حادة (0px)، تمييز ذهبي
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

        # استبدال التنسيق **كلمة** باللون الذهبي للكلمات المفتاحية
        s = re.sub(
            r'\*\*(.*?)\*\*',
            f'<span style="color:{theme["highlight"]}; font-weight:800;">\\1</span>',
            s
        )

        has_ar = any('\u0600' <= c <= '\u06FF' for c in s)
        align, direction = ("right", "rtl") if has_ar else ("left", "ltr")
        formatted += (
            f'<div style="text-align:{align};direction:{direction};'
            f'margin-bottom:16px;font-size:29px;line-height:1.75;'
            f'font-weight:700;color:{theme["text"]};">{s}</div>'
        )

    badge_html = (
        f'<div style="background:{theme["badge_bg"]};color:{theme["badge_text"]};'
        f'padding:8px 22px;border-radius:0px;font-size:21px;font-weight:800;'
        f'white-space:nowrap;flex-shrink:0;">{badge}</div>'
    ) if badge else ""

    return f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Cairo:wght@600;700;800;900&display=swap" rel="stylesheet">
<style>
* {{ box-sizing:border-box; margin:0; padding:0; }}
body {{
  width:1080px; height:1080px;
  background:{theme["bg"]};
  font-family:'Cairo', sans-serif;
  display:flex; flex-direction:column;
  padding:52px 58px 40px; overflow:hidden;
}}
.header {{
  display:flex; justify-content:space-between; align-items:center;
  padding-bottom:16px;
  border-bottom:3px solid {theme["divider"]};
  margin-bottom:28px;
}}
.teacher-name  {{ font-size:38px; font-weight:900; color:{theme["header_name"]}; }}
.teacher-handle{{ font-size:21px; font-weight:700; color:{theme["header_handle"]}; direction:ltr; text-align:right; margin-top:3px; }}
.slide-counter {{ font-size:30px; font-weight:800; color:{theme["counter"]}; direction:ltr; }}
.card {{
  flex:1; background:{theme["card_bg"]};
  border:3px solid {theme["border"]};
  border-radius:0px; padding:40px 46px;
  display:flex; flex-direction:column;
  box-shadow:none;
}}
.card-header {{
  display:flex; align-items:flex-start; justify-content:space-between; gap:14px;
  margin-bottom:26px; padding-bottom:20px;
  border-bottom:3px solid {theme["border"]};
}}
.card-title {{ font-size:42px; font-weight:900; color:{theme["title"]}; line-height:1.2; flex:1; }}
.card-body   {{ flex:1; display:flex; flex-direction:column; justify-content:center; }}
.footer {{
  margin-top:18px; padding-top:12px;
  border-top:3px solid {theme["border"]};
  text-align:center;
  font-size:19px; font-weight:800;
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
    <div class="card-body">{formatted}</div>
  </div>
  <div class="footer">ahmed.hayali.iq</div>
</body></html>"""

# ════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════
async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    data = get_daily_topic()
    theme = random.choice(NOTEBOOK_THEMES)

    all_slides   = data["slides"] + [SUBSCRIBE_SLIDE]
    total_slides = len(all_slides)

    print(f"🎨 Theme  : {theme['name']}")
    print(f"📌 Topic  : {data['topic']}")
    print(f"📊 Slides : {total_slides}")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
        )
        page = await browser.new_page(viewport={"width": SIZE, "height": SIZE})

        for i, slide in enumerate(all_slides):
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
    print("🎉 Done! All 5 slides generated successfully.")

if __name__ == "__main__":
    asyncio.run(main())
