import os
import json
import random
import urllib.request
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# 1. إعداد مفتاح API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. ضمان وجود خط عربي يدعم الرسم الصحيح
FONT_PATH = "Cairo-Bold.ttf"
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/cairo/static/Cairo-Bold.ttf"

def ensure_font():
    if not os.path.exists(FONT_PATH):
        print("جاري تحميل الخط العربي (Cairo)...")
        try:
            urllib.request.urlretrieve(FONT_URL, FONT_PATH)
            print("تم تحميل الخط بنجاح.")
        except Exception as e:
            print(f"فشل تحميل الخط: {e}")

ensure_font()

# 3. المراجع والأصناف الـ 6 المحددة
UNITS = [
    "الوحدة الأولى", "الوحدة الثانية", "الوحدة الثالثة", 
    "الوحدة الخامسة", "الوحدة السادسة", "الوحدة السابعة", "الأدب والكتاب"
]

CATEGORIES = [
    "قطع الكتاب والقصص الوزارية (Reading Passages & Stories)",
    "المفردات والإسقاطات والعبارات (Vocabulary & Context)",
    "هل تعلم؟ معلومات سريعة عن اللغة (Did You Know? English Facts)",
    "المرادفات والأضداد والاختصارات (Synonyms, Antonyms & Spelling)",
    "قواعد وشروح تفصيلية مع صيغ وزارية (Grammar Rules & Formulas)",
    "أخطاء شائعة والتعبير الصحيح (Common Mistakes & Idioms)"
]

selected_unit = random.choice(UNITS)
selected_category = random.choice(CATEGORIES)
seed_id = random.randint(10000, 99999)

# 4. صياغة البرومبت
PROMPT = f"""
أنت خبير صانع محتوى تعليمي لغة إنجليزية (منهج السادس إعدادي العراقي + إنجليزية عامة).

المطلوب: إنشاء منشور انستغرام فريد كلياً ومتجدد بناءً على المراجع التالية:
- المرجع/الوحدة: [{selected_unit}]
- الصنف المحدد اليوم: [{selected_category}]
- رمز التنوع العشوائي: #{seed_id}

تعليمات المحتوى:
- ابتكار موضوع محدد ودقيق جداً داخل الصنف المختار (وليس موضوعاً عاماً).
- إذا كان الصنف "هل تعلم؟" اجعل المحتوى معلومة غريبة أو مفيدة في اللغة.
- إذا كان "أخطاء شائعة" قارن بين الجملة الخاطئة والجملة الصحيحة مع الشرح.
- إذا كان "قواعد" اعطِ القاعدة مع مثال وزاري مترجم.

قم بتوليد كود JSON فقط وحصرياً بالهيكلية التالية بدون أي نص خارجي:

{{
  "caption": "اكتب هنا كابشن جذاب ومشوق للمنشور باللغة العربية مع إيموجيات وهاشتاقات مناسبة لطلاب السادس إعدادي مثل #سادس_إعدادي #انكليزي_سادس #وزاريات #العراق",
  "slides": [
    {{
      "badge": "بادج الصنف",
      "title": "العنوان الرئيسي",
      "content": "الشرح الأساسي"
    }},
    {{
      "badge": "التطبيق والأمثلة",
      "title": "تفاصيل الدرس",
      "content": "الشرح التفصيلي أو الأمثلة المترجمة"
    }},
    {{
      "badge": "اختبار سريع",
      "title": "سؤال اختباري وزاري",
      "quiz": {{
        "question": "نص السؤال هنا",
        "options": ["الخيار الأول", "الخيار الثاني", "الخيار الثالث"],
        "answer": "الخيار الصحيح"
      }}
    }},
    {{
      "badge": "الخاتمة",
      "title": "تابع الحساب للمزيد",
      "content": "اشترك للحصول على دروس يومية وتلخيصات شاملة"
    }}
  ]
}}
"""

def get_candidate_models():
    preferred_models = ["gemini-3.6-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    dynamic_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                dynamic_models.append(m.name)
    except Exception as e:
        print(f"تنبيه: تعذر جلب قائمة النماذج ديناميكياً: {e}")

    all_candidates = preferred_models + [m for m in dynamic_models if m not in preferred_models]
    return all_candidates

def generate_content():
    candidate_models = get_candidate_models()
    last_error = None

    for model_name in candidate_models:
        try:
            print(f"جاري تجربة النموذج: {model_name}...")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(PROMPT)
            print(f"تم التوليد بنجاح باستخدام النموذج: {model_name}")
            
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

    raise Exception(f"فشل التوليد مع جميع النماذج المتاحة. آخر خطأ: {last_error}")

def create_slide_image(slide_data, index, output_dir="daily_post"):
    os.makedirs(output_dir, exist_ok=True)
    img = Image.new("RGB", (1080, 1350), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # تحميل الخط بأحجام مختلفة
    try:
        font_badge = ImageFont.truetype(FONT_PATH, 26)
        font_title = ImageFont.truetype(FONT_PATH, 38)
        font_body = ImageFont.truetype(FONT_PATH, 28)
    except Exception:
        font_badge = font_title = font_body = ImageFont.load_default()

    draw.rectangle([40, 40, 1040, 1310], outline=(51, 65, 85), width=4)
    
    badge_text = slide_data.get("badge", "درس اليوم")
    title_text = slide_data.get("title", "")
    content_text = slide_data.get("content", "")
    
    # رسم البادج والعنوان
    draw.rectangle([80, 80, 500, 150], fill=(99, 102, 241))
    draw.text((100, 95), badge_text, font=font_badge, fill=(255, 255, 255))
    draw.text((80, 180), title_text, font=font_title, fill=(248, 250, 252))
    
    # رسم المحتوى
    if "quiz" in slide_data:
        quiz = slide_data["quiz"]
        draw.text((80, 300), f"سؤال: {quiz.get('question', '')}", font=font_body, fill=(226, 232, 240))
        y_offset = 400
        for opt in quiz.get("options", []):
            draw.text((100, y_offset), f"- {opt}", font=font_body, fill=(203, 213, 225))
            y_offset += 80
    else:
        draw.text((
