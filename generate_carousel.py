import os
import json
import random
import textwrap
import urllib.request
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# 1. إعداد مفتاح API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. تحميل خط عربي يضمن ظهور الأحرف العربية بشكل صحيح (Cairo)
FONT_PATH = "Cairo-Bold.ttf"
FONT_URL = "https://raw.githubusercontent.com/google/fonts/main/ofl/cairo/static/Cairo-Bold.ttf"

def ensure_font():
    if not os.path.exists(FONT_PATH):
        print("جاري تحميل الخط العربي (Cairo)...")
        try:
            req = urllib.request.Request(
                FONT_URL, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(req) as response, open(FONT_PATH, 'wb') as out_file:
                out_file.write(response.read())
            print("تم تحميل الخط العربي بنجاح.")
        except Exception as e:
            print(f"تنبيه: تعذر تحميل الخط العربي تلقائياً: {e}")

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
- ابتكار موضوع محدد ودقيق جداً داخل الصنف المختار.
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
    
    # إعداد الخطوط
    try:
        font_badge = ImageFont.truetype(FONT_PATH, 28)
        font_title = ImageFont.truetype(FONT_PATH, 40)
        font_body = ImageFont.truetype(FONT_PATH, 30)
    except Exception:
        font_badge = font_title = font_body = ImageFont.load_default()

    # إطار داخلي للإنستغرام
    draw.rectangle([40, 40, 1040, 1310], outline=(51, 65, 85), width=4)
    
    badge_text = slide_data.get("badge", "درس اليوم")
    title_text = slide_data.get("title", "")
    content_text = slide_data.get("content", "")
    
    # رسم البادج
    draw.rectangle([80, 80, 520, 150], fill=(99, 102, 241))
    draw.text((100, 92), badge_text, font=font_badge, fill=(255, 255, 255))
    
    # رسم العنوان الرئيسي
    title_wrapped = textwrap.fill(title_text, width=35)
    draw.text((80, 180), title_wrapped, font=font_title, fill=(248, 250, 252))
    
    # رسم المحتوى أو الأسئلة
    if "quiz" in slide_data:
        quiz = slide_data["quiz"]
        question_text = textwrap.fill(f"سؤال: {quiz.get('question', '')}", width=40)
        draw.text((80, 320), question_text, font=font_body, fill=(226, 232, 240))
        
        y_offset = 480
        for opt in quiz.get("options", []):
            opt_text = textwrap.fill(f"- {opt}", width=40)
            draw.text((100, y_offset), opt_text, font=font_body, fill=(203, 213, 225))
            y_offset += 90
    else:
        content_wrapped = textwrap.fill(content_text, width=42)
        draw.text((80, 320), content_wrapped, font=font_body, fill=(203, 213, 225))
        
    file_path = os.path.join(output_dir, f"slide_{index + 1}.png")
    img.save(file_path)
    return file_path

def save_caption(caption_text, output_dir="daily_post"):
    os.makedirs(output_dir, exist_ok=True)
    file_path = os.path.join(output_dir, "caption.txt")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(caption_text)
    print(f"تم حفظ الكابشن في {file_path}")

def main():
    print(f"جاري التوليد لصنف [{selected_category}] - [{selected_unit}]...")
    data = generate_content()
    slides = data.get("slides", [])
    
    for idx, slide in enumerate(slides):
        create_slide_image(slide, idx, output_dir="daily_post")
    print("تم إنشاء الشرائح بنجاح.")

    caption_text = data.get("caption")
    if not caption_text:
        caption_text = f"📚 درس اليوم: {selected_category} - {selected_unit}\n\n#سادس_إعدادي #انكليزي_سادس #وزاريات"
    
    save_caption(caption_text, output_dir="daily_post")

if __name__ == "__main__":
    main()
