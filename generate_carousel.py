import os
import json
import random
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# 1. إعداد مفتاح API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. المراجع والأصناف الـ 6 المحددة
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

# اختيار صنف ووحدة بشكل عشوائي تماماً لكل يوم
selected_unit = random.choice(UNITS)
selected_category = random.choice(CATEGORIES)
seed_id = random.randint(10000, 99999)

# 3. صياغة البرومبت
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

def generate_content():
    try:
        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        response = model.generate_content(PROMPT)
    except Exception:
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content(PROMPT)
        
    text = response.text.strip()
    
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    return json.loads(text.strip())

def create_slide_image(slide_data, index, output_dir="slides"):
    os.makedirs(output_dir, exist_ok=True)
    img = Image.new("RGB", (1080, 1350), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    draw.rectangle([40, 40, 1040, 1310], outline=(51, 65, 85), width=4)
    
    badge_text = slide_data.get("badge", "درس اليوم")
    title_text = slide_data.get("title", "")
    content_text = slide_data.get("content", "")
    
    draw.rectangle([80, 80, 450, 140], fill=(99, 102, 241))
    draw.text((100, 95), badge_text, fill=(255, 255, 255))
    
    draw.text((80, 180), title_text, fill=(248, 250, 252))
    
    if "quiz" in slide_data:
        quiz = slide_data["quiz"]
        draw.text((80, 300), f"سؤال: {quiz.get('question', '')}", fill=(226, 232, 240))
        y_offset = 400
        for opt in quiz.get("options", []):
            draw.text((100, y_offset), f"- {opt}", fill=(203, 213, 225))
            y_offset += 80
    else:
        draw.text((80, 300), content_text, fill=(203, 213, 225))
        
    file_path = os.path.join(output_dir, f"slide_{index + 1}.png")
    img.save(file_path)
    return file_path

def main():
    print(f"جاري التوليد لصنف [{selected_category}] - [{selected_unit}]...")
    data = generate_content()
    slides = data.get("slides", [])
    
    for idx, slide in enumerate(slides):
        create_slide_image(slide, idx)
    print("تم إنشاء الشرائح بنجاح.")

if __name__ == "__main__":
    main()
