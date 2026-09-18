import os
import requests
import json

def post_album(image_paths, caption):
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        raise ValueError("بيانات التلغرام غير موجودة في الأسرار")

    url = f"https://api.telegram.org/bot{bot_token}/sendMediaGroup"
    
    media = []
    files = {}
    
    # تجهيز الصور لترسل كألبوم واحد
    for i, img_path in enumerate(image_paths):
        file_key = f"photo{i}"
        media.append({
            "type": "photo",
            "media": f"attach://{file_key}",
            "caption": caption if i == 0 else "" # وضع النص في الصورة الأولى فقط
        })
        files[file_key] = open(img_path, 'rb')
        
    data = {"chat_id": chat_id, "media": json.dumps(media)}
    response = requests.post(url, data=data, files=files)
    
    # إغلاق الملفات لتجنب الأخطاء
    for f in files.values():
        f.close()
        
    if not response.ok:
        raise Exception(response.text)
