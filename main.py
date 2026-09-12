import os
import glob
from post_to_telegram import send_telegram_album
from post_to_linkedin import post_to_linkedin
import post_to_instagram

def main():
    print("--- بدء عملية النشر الموحدة على جميع المنصات ---")

    # 1. قراءة الكابشن المولّد من Gemini
    caption_file = "output/caption.txt"
    if os.path.exists(caption_file):
        with open(caption_file, "r", encoding="utf-8") as f:
            caption = f.read()
    else:
        caption = "بوست يومي جديد حول تعلم اللغة الإنجليزية!"

    # 2. قراءة الصور المولّدة من مجلد output
    image_paths = sorted(glob.glob("output/*.png"))
    
    if not image_paths:
        print("❌ لم يتم العثور على صور في مجلد output!")
        return

    print(f"📸 تم العثور على {len(image_paths)} صور جاهزة للنشر.")

    # 3. النشر على Telegram كـ ألبوم صور + نص
    try:
        print("✈️ [Telegram] جاري نشر الألبوم...")
        send_telegram_album(image_paths, caption)
    except Exception as e:
        print(f"❌ [Telegram] خطأ: {e}")

    # 4. النشر على LinkedIn كـ منشور صور + نص
    try:
        print("💼 [LinkedIn] جاري نشر المنشور...")
        post_to_linkedin(caption, image_paths)
    except Exception as e:
        print(f"❌ [LinkedIn] خطأ: {e}")

    # 5. النشر على Instagram كـ Carousel
    try:
        print("📸 [Instagram] جاري نشر الكاروسيل...")
        if hasattr(post_to_instagram, 'post_carousel'):
            post_to_instagram.post_carousel(image_paths, caption)
        elif hasattr(post_to_instagram, 'upload_carousel'):
            post_to_instagram.upload_carousel(image_paths, caption)
        elif hasattr(post_to_instagram, 'publish'):
            post_to_instagram.publish(image_paths, caption)
        elif hasattr(post_to_instagram, 'main'):
            post_to_instagram.main()
        else:
            print("❌ [Instagram] تعذر العثور على دالة النشر في ملف post_to_instagram.py")
    except Exception as e:
        print(f"❌ [Instagram] خطأ: {e}")

    print("--- اكتملت عملية النشر بنجاح ---")

if __name__ == "__main__":
    main()
