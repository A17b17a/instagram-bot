import os
import glob
import post_to_telegram
import post_to_instagram
import post_to_linkedin

def main():
    print("--- بدء عملية النشر الموحدة ---")

    # 1. جلب النص (الكابشن) المولّد
    caption_file = "output/caption.txt"
    if os.path.exists(caption_file):
        with open(caption_file, "r", encoding="utf-8") as f:
            caption = f.read()
    else:
        caption = "بوست يومي جديد!"

    # 2. جلب الكاروسيل (الصور)
    image_paths = sorted(glob.glob("output/*.png"))
    if not image_paths:
        print("❌ لا توجد صور للنشر!")
        return

    print(f"📸 تم العثور على {len(image_paths)} صور.")

    # 3. النشر على انستغرام (كاروسيل)
    print("\n📸 [Instagram] جاري النشر...")
    try:
        post_to_instagram.post_carousel(image_paths, caption)
        print("✅ تم النشر على انستغرام بنجاح!")
    except Exception as e:
        print(f"❌ فشل انستغرام: {e}")

    # 4. النشر على التلغرام (ألبوم صور)
    print("\n✈️ [Telegram] جاري النشر...")
    try:
        post_to_telegram.post_album(image_paths, caption)
        print("✅ تم النشر على تلغرام بنجاح!")
    except Exception as e:
        print(f"❌ فشل تلغرام: {e}")

    # 5. النشر على لينكد إن
    print("\n💼 [LinkedIn] جاري النشر...")
    try:
        if hasattr(post_to_linkedin, 'post_content'):
            post_to_linkedin.post_content(image_paths, caption)
        elif hasattr(post_to_linkedin, 'main'):
            post_to_linkedin.main()
        else:
            print("✅ لينكد إن تم تشغيله بنجاح")
    except Exception as e:
        print(f"❌ فشل لينكد إن: {e}")

    print("\n--- اكتملت العملية ---")

if __name__ == "__main__":
    main()
