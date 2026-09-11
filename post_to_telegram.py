import os
import json
from pathlib import Path
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
POST_DIR = Path("daily_post")

def post_to_telegram():
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ لم يتم تحديد TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID. تم تخطي النشر على تليكرام.")
        return

    # قراءة النص/الكابشن
    caption_file = POST_DIR / "caption.txt"
    caption = caption_file.read_text(encoding="utf-8") if caption_file.exists() else ""

    # جمع صور الشرائح
    slide_files = sorted(list(POST_DIR.glob("slide_*.png")))
    if not slide_files:
        print("❌ لم يتم العثور على أي صور للنشر على تليكرام.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMediaGroup"

    media = []
    files = {}

    for idx, slide_path in enumerate(slide_files):
        attach_name = f"photo_{idx}"
        media_item = {
            "type": "photo",
            "media": f"attach://{attach_name}"
        }
        # إضافة الكابشن مع الصورة الأولى فقط
        if idx == 0 and caption:
            media_item["caption"] = caption

        media.append(media_item)
        files[attach_name] = (slide_path.name, open(slide_path, "rb"), "image/png")

    data = {
        "chat_id": TELEGRAM_CHAT_ID,
        "media": json.dumps(media, ensure_ascii=False)
    }

    print(f"⏳ جاري نشر {len(slide_files)} شرائح على قناة التليكرام ({TELEGRAM_CHAT_ID})...")
    
    try:
        response = requests.post(url, data=data, files=files, timeout=60)
        res_json = response.json()
        if res_json.get("ok"):
            print("🚀 تم النشر بنجاح على قناة التليكرام!")
        else:
            print(f"❌ فشل النشر على تليكرام: {res_json.get('description')}")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الاتصال بتليكرام: {e}")
    finally:
        for f in files.values():
            f[1].close()

if __name__ == "__main__":
    post_to_telegram()
