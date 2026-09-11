import os
import json
import random
import requests
from pathlib import Path
from playwright.sync_api import sync_playwright

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
OUTPUT_DIR = Path("daily_post")
OUTPUT_DIR.mkdir(exist_ok=True)
HISTORY_FILE = Path("used_topics.json")

# التصنيفات المطلوبة للتنويع اليومي
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
    {"bg": "#FFF5F5", "card_bg": "#FFFFFF", "primary": "#E53E3E", "text": "#2D3748"},
    {"bg": "#F0FFF4", "card_bg": "#FFFFFF", "primary": "#38A169", "text": "#2D3748"},
    {"bg": "#EBF8FF", "card_bg": "#FFFFFF", "primary": "#3182CE", "text": "#2D3748"},
    {"bg": "#FAF5FF", "card_bg": "#FFFFFF", "primary": "#805AD5", "text": "#2D3748"},
    {"bg": "#FFFAF0", "card_bg": "#FFFFFF", "primary": "#DD6B20", "text": "#2D3748"}
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
            valid_models = []
            for m in models:
                if "generateContent" in m.get("supportedGenerationMethods", []):
                    valid_models.append(m["name"].replace("models/", ""))
            return valid_models
        else:
            print(f"⚠️ Could not list models (Status {res.status_code}): {res.text}")
    except Exception as e:
        print(f"⚠️ Exception listing models: {e}")
    return []

def generate_content_with_gemini():
    if not GEMINI_API_KEY:
        raise ValueError("❌ GEMINI_API_KEY غير موجود في Secrets!")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": GEMINI_API_KEY
    }

    # جلب النماذج المدعومة والمتاحة لمفتاحك تلقائياً
    available_models = get_available_models(headers)
    fallback_models = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash-latest", "gemini-1.5-flash"]
    
    models_to_try = [m for m in available_models if "flash" in m] + available_models + fallback_models
    seen = set()
    models_to_try = [m for m in models_to_try if not (m in seen or seen.add(m))]

    history = load_history()
    category = random.choice(CATEGORIES)

    prompt = f"""
    أنت خبير في تدريس اللغة الإنجليزية وصانع محتوى تعليمي محترف.
    قم بإنشاء محتوى لكاروسيل إنستغرام (5 شرائح) من التصنيف التالي:
    التصنيف المطلوب: {category}

    المواضيع السابقة التي تم استخدامها (يمنع تكرارها كلياً):
    {json.dumps(history, ensure_ascii=False)}

    المطلوب رد بصيغة JSON فقط دون أي نصوص إضافية أو markdown:
    {{
      "topic_title": "عنوان الموضوع الرئيسي المختصر",
      "category_name": "{category}",
      "slides": [
        {{
          "slide_number": 1,
          "badge": "وسم الشريحة (مثلاً: القاعدة / هل تعلم / القصة)",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى الرئيسي بتنسيق HTML بسيط (استخدم <b> للتركيز)",
          "note": "ملاحظة أو مثال توضيحي"
        }},
        {{
          "slide_number": 2,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى الرئيسي",
          "note": "ملاحظة"
        }},
        {{
          "slide_number": 3,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى الرئيسي",
          "note": "ملاحظة"
        }},
        {{
          "slide_number": 4,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى الرئيسي",
          "note": "ملاحظة"
        }},
        {{
          "slide_number": 5,
          "badge": "وسم الشريحة",
          "title": "عنوان الشريحة",
          "content_html": "المحتوى الرئيسي",
          "note": "ملاحظة"
        }}
      ],
      "caption": "الكابشن الكامل للبوست باللغة العربية مع شرح مبسط وهاشتاغات عراقية وتعليمية مناسبة"
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
                res_json = res.json()
                raw_text = res_json['candidates'][0]['content']['parts'][0]['text']
                print(f"✅ Successfully generated using model: {model}")
                break
            else:
                last_error = f"Model {model} -> Status {res.status_code}: {res.text}"
        except Exception as e:
            last_error = f"Model {model} -> Exception: {e}"

    if not raw_text:
        raise Exception(f"❌ Failed to generate content via Gemini API. Last error: {last_error}")

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
                <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap" rel="stylesheet">
                <style>
                    * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Cairo', sans-serif; }}
                    body {{
                        width: 1080px; height: 1080px;
                        background-color: {theme['bg']};
                        display: flex; flex-direction: column;
                        justify-content: space-between; padding: 80px 60px;
                    }}
                    .header {{ display: flex; justify-content: space-between; align-items: center; }}
                    .badge {{ background: {theme['primary']}; color: white; padding: 10px 25px; border-radius: 30px; font-size: 24px; font-weight: bold; }}
                    .slide-num {{ font-size: 28px; color: #718096; font-weight: bold; }}
                    .card {{
                        background: {theme['card_bg']}; border-radius: 25px; padding: 50px;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.05); border-right: 12px solid {theme['primary']};
                        flex-grow: 1; margin: 40px 0; display: flex; flex-direction: column; justify-content: center;
                    }}
                    .title {{ font-size: 42px; color: {theme['primary']}; margin-bottom: 25px; font-weight: 900; }}
                    .content {{ font-size: 32px; color: {theme['text']}; line-height: 1.8; }}
                    .note {{ font-size: 26px; color: #4A5568; background: #EDF2F7; padding: 20px; border-radius: 15px; margin-top: 25px; }}
                    .footer {{ text-align: center; font-size: 24px; color: #A0AEC0; font-weight: bold; }}
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
            page.screenshot(path=str(OUTPUT_DIR / f"slide_{slide['slide_number']}.png"))

        browser.close()

if __name__ == "__main__":
    print("🤖 Requesting new unique topic from Gemini...")
    data = generate_content_with_gemini()
    print(f"✅ Generated Topic: {data['topic_title']} [{data['category_name']}]")
    render_slides_to_images(data)
