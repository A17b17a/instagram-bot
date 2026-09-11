import os
from pathlib import Path
from instagrapi import Client
from instagrapi.types import StoryMedia

# ════════════════════════════════════════════════════════════════
# إعدادات الحساب والمجلدات
# ════════════════════════════════════════════════════════════════
USERNAME = os.getenv("IG_USERNAME", "ahmed.hayali.iq")
PASSWORD = os.getenv("IG_PASSWORD", "Ah.mu2086!.ah")

DAILY_POST_DIR = Path("daily_post")

def main():
    if not DAILY_POST_DIR.exists():
        print("❌ مجلد daily_post غير موجود! قم بتشغيل سكريبت إنشاء التصاميم أولاً.")
        return

    # جلب جميع الشرائح المجهزة مرتبة
    slides = sorted([str(p) for p in DAILY_POST_DIR.glob("slide_*.png")])
    caption_file = DAILY_POST_DIR / "caption.txt"
    
    if not slides:
        print("❌ لم يتم العثور على أي صور داخل مجلد daily_post")
        return

    caption = caption_file.read_text(encoding="utf-8") if caption_file.exists() else ""

    print(f"🔄 جاري تسجيل الدخول إلى حساب: {USERNAME}...")
    cl = Client()
    
    # إدارة الجلسة لمنع الحظر
    session_file = Path("ig_session.json")
    if session_file.exists():
        cl.load_settings(session_file)
        cl.login(USERNAME, PASSWORD)
    else:
        cl.login(USERNAME, PASSWORD)
        cl.dump_settings(session_file)

    # 1️⃣ نشر المنشور الرئيسي (Carousel)
    print(f"📸 جاري نشر الكاروسيل ({len(slides)} شرائح)...")
    post_media = cl.album_upload(
        paths=slides,
        caption=caption
    )
    print(f"✅ تم نشر المنشور بنجاح! ID المنشور: {post_media.pk}")

    # 2️⃣ تجهيز ملصق المشاركة التفاعلي الموجه للمنشور
    print("📲 جاري إنشاء الستوري وإضافة ملصق التوجيه التفاعلي للمنشور...")
    
    # ملصق يحيل المتابع مباشرة للمنشور
    post_sticker = StoryMedia(
        media_pk=post_media.pk,  # ربط الستوري بمعرف المنشور الجديد
        x=0.5,                   # الموضع الأفقي (المنتصف)
        y=0.5,                   # الموضع العمودي (المنتصف)
        width=0.7,               # حجم الملصق بالنسبة للشاشة
        height=0.7
    )

    # رفع الشريحة الأولى كخلفية للستوري مع دمج الملصق التفاعلي فوقها
    cl.photo_upload_to_story(
        path=slides[0],
        stickers=[post_sticker]
    )
    
    print("🎉 تم نشر الستوري بنجاح! عند الضغط عليها ستنقل المتابع فوراً إلى البوست.")

if __name__ == "__main__":
    main()
