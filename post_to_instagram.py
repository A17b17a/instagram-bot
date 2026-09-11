import os
import json
from pathlib import Path
from instagrapi import Client
from instagrapi.types import StoryMedia

# إصلاح خلل خاصية extra في StoryMedia لضمان عمل الستوري
StoryMedia.extra = property(lambda self: {})

USERNAME = os.getenv("INSTAGRAM_USERNAME") or os.getenv("IG_USERNAME", "")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD") or os.getenv("IG_PASSWORD", "")
SESSION_ENV = os.getenv("INSTAGRAM_SESSION_JSON", "")

SESSION_FILE = Path("ig_session.json")
DAILY_POST_DIR = Path("daily_post")

def main():
    if not DAILY_POST_DIR.exists():
        print("❌ مجلد daily_post غير موجود!")
        return

    slides = sorted([str(p) for p in DAILY_POST_DIR.glob("slide_*.png")])
    caption_file = DAILY_POST_DIR / "caption.txt"
    caption = caption_file.read_text(encoding="utf-8") if caption_file.exists() else ""

    cl = Client()
    
    # تجاوز رابط التتبع المعطل من إنستغرام
    cl.expose = lambda *args, **kwargs: True

    logged_in = False

    # 1️⃣ تسجيل الدخول عبر الجلسة
    if SESSION_ENV.strip():
        try:
            session_str = SESSION_ENV.strip()
            if not session_str.startswith("{"):
                print("🔄 جاري تسجيل الدخول باستخدام sessionid...")
                cl.login_by_sessionid(session_str)
                logged_in = True
            else:
                print("🔄 جاري تحميل الجلسة من متغير INSTAGRAM_SESSION_JSON...")
                session_data = json.loads(session_str)
                with open(SESSION_FILE, "w", encoding="utf-8") as f:
                    json.dump(session_data, f)
                cl.load_settings(SESSION_FILE)
                cl.login(USERNAME, PASSWORD)
                logged_in = True
            print("✅ تم تسجيل الدخول بنجاح عبر الجلسة!")
        except Exception as e:
            print(f"⚠️ فشل تسجيل الدخول بمتغير الجلسة: {e}")

    # 2️⃣ تسجيل الدخول بملف الجلسة
    if not logged_in and SESSION_FILE.exists():
        try:
            print("🔄 جاري تحميل الجلسة من ملف ig_session.json...")
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            logged_in = True
            print("✅ تم تسجيل الدخول عبر ملف الجلسة بنجاح!")
        except Exception as e:
            print(f"⚠️ فشل تحميل ملف الجلسة: {e}")

    # 3️⃣ تسجيل الدخول المباشر
    if not logged_in:
        print("🔄 محاولة تسجيل الدخول المباشر بكلمة السر...")
        cl.login(USERNAME, PASSWORD)

    # 📸 نشر الكاروسيل
    print(f"📸 جاري نشر الكاروسيل ({len(slides)} شرائح)...")
    post_media = cl.album_upload(paths=slides, caption=caption)
    print(f"✅ تم نشر الكاروسيل بنجاح! ID: {post_media.pk}")

    # 📲 نشر الستوري التفاعلي
    print("📲 جاري نشر الستوري مع ملصق التوجيه التفاعلي...")
    try:
        post_sticker = StoryMedia(
            media_pk=post_media.pk,
            x=0.5, y=0.5, width=0.6, height=0.6
        )
        cl.photo_upload_to_story(path=slides[0], stickers=[post_sticker])
        print("🎉 تم نشر الستوري بنجاح مع زر التوجيه للمنشور!")
    except Exception as e:
        print(f"⚠️ تعذر نشر الستوري بالملصق التفاعلي: {e}")
        # محاولة نشر الستوري كصورة عادية إذا فشل الملصق
        try:
            cl.photo_upload_to_story(path=slides[0])
            print("🎉 تم نشر الستوري كصورة عادية بنجاح!")
        except Exception as err:
            print(f"❌ فشل نشر الستوري بالكامل: {err}")

if __name__ == "__main__":
    main()
