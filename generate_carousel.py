import os
import json
import random
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path("used_topics.json")

CATEGORIES = [
    "منهج السادس إعدادي (العراق - قواعد، قطع، إسقاطات، أو إملاء)",
    "منهج الثالث متوسط (العراق - قطع، قواعد، أو مفردات)",
    "هل تعلم؟ (معلومات لغوية نادرة وعجيبة عن اللغة الإنجليزية)",
    "قصة قصيرة جداً ومفيدة مع معاني المفردات وتوضيح النطق",
    "أخطاء شائعة وتصحيحها (Common Mistakes in English)",
    "مرادفات وأضداد (Synonyms & Antonyms) مع أمثلة",
    "قواعد اللغة الإنجليزية (Grammar Rules Explained)",
    "مفردات ومصطلحات يومية (Daily Idioms & Expressions)",
    "جمل وتراكيب جاهزة للمحادثة اليومية (Daily Conversations)",
    "قطع خارجية وقراءة واستيعاب (Reading Comprehension)"
]

COLOR_THEMES = [
    {"bg": "#F8FAFC", "card_bg": "#FFFFFF", "primary": "#2563EB", "accent": "#EFF6FF", "text": "#1E293B", "border": "#3B82F6"},
    {"bg": "#FDF2F2", "card_bg": "#FFFFFF", "primary": "#DC2626", "accent": "#FEF2F2", "text": "#1E293B", "border": "#EF4444"},
    {"bg": "#F0FDF4", "card_bg": "#FFFFFF", "primary": "#16A34A", "accent": "#F0FDF4", "text": "#1E293B", "border": "#22C55E"},
    {"bg": "#FAF5FF", "card_bg": "#FFFFFF", "primary": "#9333EA", "accent": "#FAF5FF", "text": "#1E293B", "border": "#A855F7"},
    {"bg": "#FFFBEB", "card_bg": "#FFFFFF", "primary": "#D97706", "accent": "#FFFBEB", "text": "#1E293B", "border": "#F59E0B"}
]

def load_history():
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_history(history):
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")

def get_available_models(headers):
    url = "https://generativelanguage.googleapis.com/v1beta/models"
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            models = res.json().get("models", [])
            return [m["name"].replace("models/", "") for m in models if "generateContent" in m.get("supportedGenerationMethods", [])]
    except Exception:
        pass
    return []

def generate_content_with_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY غير موجود في Secrets!")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    available_models = get_available_models(headers)
    fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash"]
    models_to_try = [m for m in available_models if "flash" in m] + available_models + fallback_models
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    history = load_history()
    category = random.choice(CATEGORIES)

    prompt = f"""
    أنت أستاذ وخبير تدريس لغة إنجليزية محترف جداً وصانع محتوى تعليمي.
    قم بإنشاء محتوى لكاروسيل إنستغرام (5 شرائح) للتصنيف التالية:
    التصنيف: {category}

    المواضيع السابقة (يمنع التكرار):
    {json.dumps(history, ensure_ascii=False)}

    شروط صارمة للمحتوى والإملاء:
    1. اكتب بلغة عربية فصيحة ومفهومة وسليمة 100% بدون أي أخطاء إملائية أو مطبعية أو كلمات مبتورة.
    2. تأكد من أن كل العبارات الإنجليزية مكتوبة بشكل صحيح وموضوعة داخل وسم <span dir="ltr"> الجملة الإنجليزية </span> لكي لا تختلط باللغة العربية.
    3. الرد يكون JSON فقط بدون أية نصوص خارجية أو markdown.

    شكل الـ JSON المطلوب:
    {{
      "topic_title": "عنوان الموضوع المختصر والواضح",
      "category_name": "{category}",
      "slides": [
        {{
          "slide_number": 1,
          "badge": "وسم الشريحة (مثلاً: تعبير شائع / قاعدة / سؤال)",
          "title": "العنوان الرئيسي للشريحة",
          "content_html": "المحتوى الشارح مع وضع الكلمات المفتاحية بين <b> والعبارات الإنجليزية داخل <span dir='ltr'>...</span>",
          "note": "مثال توضيحي أو ترجمة معتمدة"
        }},
        {{
          "slide_number": 2,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى",
          "note": "ملاحظة أو مثال"
        }},
        {{
          "slide_number": 3,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى",
          "note": "ملاحظة أو مثال"
        }},
        {{
          "slide_number": 4,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى",
          "note": "ملاحظة أو مثال"
        }},
        {{
          "slide_number": 5,
          "badge": "تحدي التفاعل",
          "title": "دورك تجاوب!",
          "content_html": "سؤال أو اختريات للتفاعل بالتعليقات",
          "note": "احفظ البوست حتى ترجعله وشاركه ويا أصدقائك!"
        }}
      ],
      "caption": "الكابشن الكامل للبوست باللغة العربية مع شرح مبسط وهاشتاغات تعليمية وعراقية مناسبة"
    }}
    """

    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    raw_text = None
    last_error = None

    for model in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=30)
            if res.status_code == 200:
                raw_text = res.json()['candidates'][0]['content']['parts'][0]['text']
                break
            else:
                last_error = f"Model {model} -> Status {res.status_code}"
        except Exception as e:
            last_error = str(e)

    if not raw_text:
        raise Exception(f"❌ Failed to generate content via Gemini API: {last_error}")

    cleaned_text = raw_text.replace("```json", "").replace("```", "").strip()
    content = json.loads(cleaned_text)

    history.append(content["topic_title"])
    save_history(history)

    return content

def render_slides_to_images(content):
    theme = random.choice(COLOR_THEMES)
    
    (OUTPUT_DIR / "caption.txt").write_text(content["caption"], encoding="utf-8")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1080})

        for slide in content["slides"]:
            html_content = f"""
            <!DOCTYPE html>
            <html lang="ar" dir="rtl">
            <head>
                <meta charset="UTF-8">
                <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&family=Poppins:wght@500;700&display=swap" rel="stylesheet">
                <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
                    body {{
                        width: 1080px; height: 1080px;
                        background-color: {theme['bg']};
                        font-family: 'Cairo', sans-serif;
                        display: flex; flex-direction: column;
                        justify-content: space-between;
                        padding: 70px;
                    }}
                    .header {{
                        display: flex; justify-content: space-between; align-items: center;
                    }}
                    .badge {{
                        background: {theme['primary']}; color: #FFFFFF;
                        padding: 12px 28px; border-radius: 50px;
                        font-size: 24px; font-weight: 700;
                    }}
                    .slide-num {{
                        font-size: 26px; color: #64748B; font-weight: 700;
                        font-family: 'Poppins', sans-serif;
                    }}
                    .card {{
                        background: {theme['card_bg']};
                        border-radius: 32px;
                        padding: 60px 50px;
                        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.06);
                        border-right: 12px solid {theme['border']};
                        flex-grow: 1;
                        margin: 35px 0;
                        display: flex; flex-direction: column; justify-content: center;
                        gap: 25px;
                    }}
                    .title {{
                        font-size: 44px; color: {theme['primary']};
                        font-weight: 900; line-height: 1.3;
                    }}
                    .content {{
                        font-size: 32px; color: {theme['text']};
                        line-height: 1.8; font-weight: 600;
                    }}
                    .content b {{
                        color: {theme['primary']};
                    }}
                    .content span[dir="ltr"], [dir="ltr"] {{
                        font-family: 'Poppins', sans-serif;
                        direction: ltr; display: inline-block;
                        color: #0F172A; font-weight: 700;
                    }}
                    .note {{
                        font-size: 26px; color: #334155;
                        background: {theme['accent']};
                        padding: 22px 28px; border-radius: 20px;
                        border-left: 6px solid {theme['border']};
                        line-height: 1.6; font-weight: 600;
                    }}
                    .footer {{
                        text-align: center; font-size: 26px; color: #94A3B8;
                        font-weight: 700; letter-spacing: 0.5px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <span class="badge">{slide['badge']}</span>
                    <span class="slide-num">0{slide['slide_number']} / 05</span>
                </div>
                <div class="card">
                    <h2 class="title">{slide['title']}</h2>
                    <div class="content">{slide['content_html']}</div>
                    {f'<div class="note">{slide["note"]}</div>' if slide.get("note") else ''}
                </div>
                <div class="footer">أحمد الحيالي | ahmed.hayali.iq</div>
            </body>
            </html>
            """
            
            page.set_content(html_content)
            # تم تحويل نوع الحفظ إلى JPEG
            page.screenshot(
                path=str(OUTPUT_DIR / f"slide_{slide['slide_number']}.jpg"),
                type="jpeg",
                quality=95
            )

        browser.close()

if __name__ == "__main__":
    print("🤖 Generating formatted carousel content with Gemini...")
    data = generate_content_with_gemini()
    print(f"✅ Topic Generated: {data['topic_title']} [{data['category_name']}]")
    render_slides_to_images(data)
