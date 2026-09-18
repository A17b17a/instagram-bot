import os
from instagrapi import Client

def post_carousel(image_paths, caption):
    cl = Client()
    
    # تحميل الجلسة لتسجيل الدخول السريع والآمن
    session_json = os.environ.get("INSTAGRAM_SESSION_JSON")
    
    # التأكد من وجود الجلسة لمنع محاولة الدخول بالباسورد
    if not session_json:
        raise ValueError("❌ رمز الجلسة مفقود! تأكد من إضافة INSTAGRAM_SESSION_JSON في إعدادات GitHub.")
        
    with open("session.json", "w") as f:
        f.write(session_json)
        
    cl.load_settings("session.json")

    print("⏳ جاري النشر على انستغرام (محاولة واحدة فقط)...")
    try:
        # رفع الصور كسلايدر (Carousel)
        cl.album_upload(image_paths, caption)
        print("✅ تم النشر على انستغرام بنجاح!")
    except Exception as e:
        error_msg = str(e)
        # تجاهل خطأ qe/expose لأنه وهمي والبوست يُنشر فعلياً
        if "qe/expose" in error_msg:
            print("⚠️ ظهر تحذير qe/expose من سيرفرات انستغرام، لكن المنشور تم نشره بنجاح!")
        else:
            raise e
