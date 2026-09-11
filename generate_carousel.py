import os
import json
import random
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont

# 1. إعداد مفتاح API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# 2. مصفوفات التوليد اللانهائي والعشوائي
UNITS = [
    "الوحدة الأولى", "الوحدة الثانية", "الوحدة الثالثة", 
    "الوحدة الخامسة", "الوحدة السادسة", "الوحدة السابعة", "الأدب الكلي"
]

CATEGORIES = [
    "قواعد وشروح تفصيلية مع الصيغ (Grammar Rules & Formulas)",
    "قطع الكتاب والقصص والأسئلة الوزارية (Passages & Literature)",
    "المفردات، الإسقاطات، والبادئات المعاكسة (Vocab, Prefixes & Phrasal Verbs)",
    "الأخطاء الشائعة والتعبير اليومي (Common Mistakes & Daily Idioms)",
    "المرادفات والأضداد والاختصارات الإملائية (Synonyms & Antonyms)"
]

# اختيار محاور عشوائية في كل مرة يشتغل فيها البوت
selected_unit = random.choice(UNITS)
selected_category = random.choice(CATEGORIES)
seed_id = random.randint(10000, 99999)

# 3. صياغة البرومبت المتجدد تلقائياً
PROMPT = f"""
أنت خبير ومصمم محتوى تعليمي للغة الإنجليزية (منهج السادس إعدادي العراقي + الإنجليزية العامة).

المطلوب: ابتكار درس فريد وجديد تماماً ضمن:
- القسم: [{selected_unit}]
- التصنيف: [{selected_category}]
- معرف التنوع: #{seed_id}

قم بتوليد كود JSON فقط وحصرياً، بدون أي نص إضافي أو شرح خارج الكود، بالهيكلية التالية:

{{
  "slides": [
    {{
      "badge": "بادج الشريحة (مثلاً: قواعد / قصة اليوم / أخطاء شائعة)",
      "title": "العنوان الرئيسي بالعربي والإنجليزية",
      "content": "الشرح الأساسي والتمهيد للموضوع"
    }},
    {{
      "badge": "التطبيق والأمثلة",
      "title": "القاعدة أو الأمثلة الوزارية",
      "content": "تفاصيل القاعدة أو الأمثلة المترجمة بشكل منظم"
    }},
    {{
      "badge": "اختبار سريع",
      "title": "سؤال وزاري / اختباري",
      "quiz": {{
        "question": "نص السؤال هنا",
        "options": ["الخيار الأول", "الخيار الثاني", "الخيار الثالث"],
        "answer": "الخيار الصحيح المطابق تماماً لأحد الخيارات أعلاه"
      }}
    }},
    {{
      "badge": "الخاتمة",
      "title": "اشترك للمزيد من الدروس",
      "content": "تابع الحساب للحصول على شروحات يومية وتلخيصات وزارية"
    }}
  ]
}}
"""

def generate_content():
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(PROMPT)
    text = response.text.strip()
    
    # تنظيف النص للحصول على JSON صافي
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
        
    return json.loads(text.strip())

def create_slide_image(slide_data, index, output_dir="slides"):
    os.makedirs(output_dir, exist_ok=True)
    
    # إنشاء صورة بحجم إعلانات انستغرام (1080x1350)
    img = Image.new("RGB", (1080, 1350), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)
    
    # رسم الخلفية والشهاب التصميمي
    draw.rectangle([40, 40, 1040, 1310], outline=(51, 65, 85), width=4)
    
    # كتابة النصوص (البادج، العنوان، المحتوى)
    badge_text = slide_data.get("badge", "درس اليوم")
    title_text = slide_data.get("title", "")
    content_text = slide_data.get("content", "")
    
    # رسم البادج
    draw.rectangle([80, 80, 400, 140], fill=(99, 102, 241))
    draw.text((100, 95), badge_text, fill=(255, 255, 255))
    
    # رسم العنوان
    draw.text((80, 180), title_text, fill=(248, 250, 252))
    
    # رسم المحتوى أو الاختبار
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
    print("جاري توليد المحتوى العشوائي بواسطة الذكاء الاصطناعي...")
    data = generate_content()
    
    slides = data.get("slides", [])
    print(f"تم توليد {len(slides)} شرائح بنجاح.")
    
    for idx, slide in enumerate(slides):
        path = create_slide_image(slide, idx)
        print(f"تم إنشاء الصورة: {path}")

if __name__ == "__main__":
    main()
