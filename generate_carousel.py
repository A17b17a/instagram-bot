import os
import json
import random
import google.generativeai as genai
from playwright.sync_api import sync_playwright

# 1. إعداد مفتاح Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. مراجع منهج السادس الإعدادي العراقي
UNITS = [
    "الوحدة الأولى (Zaid Tariq / Grammar / Vocabulary)",
    "الوحدة الثانية (Police Officers / Must & Have to / Abbreviations)",
    "الوحدة الثالثة (If Conditionals / Regret / Definitions)",
    "الوحدة الخامسة (Present Perfect / Travel / Sightseeing)",
    "الوحدة السادسة (Banking / Passive Voice / Cheques)",
    "الوحدة السابعة (Future tenses / Conference Interpreter)",
    "الأدب (قصة الأرجوحة The Swing & الكناري The Canary)"
]

CATEGORIES = [
    "قطع الكتاب والقصص (Reading Passages)",
    "المفردات والإسقاطات والتوصيلات (Vocabulary & Matching)",
    "القواعد والملاحظات الوزارية (Grammar Rules)",
    "الإملاء والاختصارات والتصاريف (Spelling & Abbreviations)",
    "أسئلة وزارية مكررة واختبارات (Ministerial Questions)"
]

selected_unit = random.choice(UNITS)
selected_category = random.choice(CATEGORIES)
seed_id = random.randint(10000, 99999)

# 3. البرومبت المخصص لمنهج السادس الإعدادي العراقي
PROMPT = f"""
أنت أستاذ وخبير متخصص بـ (منهج اللغة الإنجليزية للصف السادس الإعدادي العراقي).
قم بإنشاء درس تعليمي دقيق ومطابق للمنهج الوزاري العراقي حصراً.

التركيز اليوم على: [{selected_unit}]
الصنف: [{selected_category}]
رمز التنوع العشوائي: #{seed_id}

تعليمات المحتوى:
1. اختر موضوعاً وزارياً حقيقياً ومحدداً من المنهج.
2. اكتب المحتوى بلغة عربية وإنجليزية واضحة ومبسطة للطلاب.
3. التوليد يكون كود JSON فقط وحصرياً دون أي مقدمات أو مؤخرات:

{{
  "caption": "اكتب هنا كابشن مشوق للمنشور يوضح درس اليوم مع هاشتاقات المنهج العراقي #سادس_إعدادي #انكليزي_سادس #وزاريات #العراق",
  "slides": [
    {{
      "badge": "درس اليوم",
      "title": "العنوان الرئيسي للدرس",
      "content": "شرح مبسط ومباشر للنقطة الوزارية المهمة"
    }},
    {{
      "badge": "صيغ وزارية",
      "title": "كيف يأتي في الامتحان؟",
      "content": "أمثلة وزاريّة مترجمة مع إبيان طريقة الحل"
    }},
    {{
      "badge": "اختبار سريع",
      "title": "اختبر نفسك",
      "content": "سؤال وزاري مهم وتطلب من الطالب كتابة الحل في التعليقات"
    }},
    {{
      "badge": "نصيحة امتحانية",
      "title": "احفظ المنشور",
      "content": "احفظ هذا البوست للمراجعة السريعة قبل الامتحان وشاركه مع زملائك!"
    }}
  ]
}}
"""

# قالب HTML القديم بتصميم أنيق ودعم كامل للغة العربية (خط تجوال)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@500;700;900&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: 'Tajawal', sans-serif; }}
  body {{
    width: 1080px;
    height: 1350px;
    background: #0f172a;
    color: #f8fafc;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 70px;
    position: relative;
  }}
  .card {{
    background: #1e293b;
    border: 3px solid #334155;
    border-radius: 32px;
    padding: 60px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }}
  .badge {{
    align-self: flex-start;
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
    color: #ffffff;
    padding: 14px 32px;
    border-radius: 50px;
    font-size: 28px;
    font-weight: 700;
    margin-bottom: 40px;
  }}
  .title {{
    font-size: 50px;
    font-weight: 900;
    color: #ffffff;
    line-height: 1.4;
    margin-bottom: 35px;
    border-right: 8px solid #6366f1;
    padding-right: 24px;
  }}
  .content {{
    font-size: 34px;
    line-height: 1.8;
    color: #cbd5e1;
    white-space: pre-wrap;
    flex-grow: 1;
    margin-top: 10px;
  }}
  .footer {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-top: 2px solid #334155;
    padding-top: 30px;
    font-size: 26px;
    color: #94a3b8;
  }}
  .brand {{
    font-weight: 700;
    color: #818cf8;
  }}
</style>
</head>
<body>
  <div class="card">
    <div>
      <div class="badge">{badge}</div>
      <div class="title">{title}</div>
      <div class="content">{content}</div>
    </div>
    <div class="footer">
      <span class="brand">@ahmed.hayali.iq</span>
      <span>إنجليزي السادس الإعدادي 📚</span>
    </div>
  </div>
</body>
</html>
"""

def get_candidate_models():
    preferred_models = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    dynamic_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                dynamic_models.append(m.name)
    except Exception as e:
        print(f"تنبيه: تعذر جلب قائمة النماذج: {e}")

    return preferred_models + [m for m in dynamic_models if m not in preferred_models]

def generate_content():
    candidate_models = get_candidate_models()
    last_error = None

    for model_name in candidate_models:
        try:
            print(f"جاري التوليد باستخدام: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(PROMPT)
            
            text = response.text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
                
            return json.loads(text.strip())
        except Exception as e:
            print(f"فشلت المحاولة مع {model_name}: {e}")
            last_error = e

    raise Exception(f"فشل التوليد: {last_error}")

def render_slides_with_playwright(slides_data, output_dir="daily_post"):
    os.makedirs(output_dir, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        
        for idx, slide in enumerate(slides_data):
            html_content = HTML_TEMPLATE.format(
                badge=slide.get("badge", "درس اليوم"),
                title=slide.get("title", ""),
                content=slide.get("content", "")
            )
            page.set_content(html_content)
            page.wait_for_timeout(600)  # انتظار تحميل الخطوط
            file_path = os.path.join(output_dir, f"slide_{idx + 1}.png")
            page.screenshot(path=file_path)
            print(f"تم إنشاء الشريحة: {file_path}")
            
        browser.close()

def save_caption(caption_text, output_dir="daily_post"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "caption.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(caption_text)

def main():
    print(f"توليد منشور جديد لـ [{selected_unit}]...")
    data = generate_content()
    slides = data.get("slides", [])
    
    render_slides_with_playwright(slides)
    
    caption_text = data.get("caption", f"📚 درس اليوم - {selected_unit}\n#سادس_إعدادي")
    save_caption(caption_text)
    print("تمت العملية بنجاح!")

if __name__ == "__main__":
    main()
