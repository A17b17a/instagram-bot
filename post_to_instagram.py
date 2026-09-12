import os
from instagrapi import Client

def post_carousel(image_paths, caption):
    cl = Client()
    
    # تحميل الجلسة لتسجيل الدخول السريع
    session_json = os.environ.get("INSTAGRAM_SESSION_JSON")
    if session_json:
        with open("session.json", "w") as f:
            f.write(session_json)
        cl.load_settings("session.json")
    else:
        cl.login(os.environ.get("INSTAGRAM_USERNAME"), os.environ.get("INSTAGRAM_PASSWORD"))

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
