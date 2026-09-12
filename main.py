import os
import glob
import post_to_telegram
import post_to_instagram

def main():
    print("--- بدء عملية النشر الموحدة ---")

    # 1. جلب النص (الكابشن)
    caption_file = "output/caption.txt"
    if os.path.exists(caption_file):
        with open(caption_file, "r", encoding="utf-8") as f:
            caption = f.read()
    elif os.path.exists("caption.txt"): # للبحث في المجلد الرئيسي أيضاً
        with open("caption.txt", "r", encoding="utf-8") as f:
            caption = f.read()
    else:
        caption = "بوست يومي جديد!"

    # 2. البحث عن الصور (الكاروسيل)
    # نجرب أولاً مجلد output
    image_paths = sorted(glob.glob("output/*.png"))
    
    # إذا لم نجدها في output، نبحث في المجلد الرئيسي
    if not image_paths:
        image_paths = sorted(glob.glob("*.png"))

    if not image_paths:
        print("❌ لا توجد صور للنشر إطلاقاً!")
        print("الملفات الموجودة حالياً في المجلد الرئيسي هي:")
        print(os.listdir("."))
        if os.path.exists("output"):
            print("الملفات الموجودة داخل مجلد output هي:")
            print(os.listdir("output"))
        return

    print(f"📸 تم العثور على {len(image_paths)} صور، مساراتها: {image_paths}")

    # 3. النشر على انستغرام
    print("\n📸 [Instagram] جاري النشر...")
    try:
        post_to_instagram.post_carousel(image_paths, caption)
        print("✅ تم النشر على انستغرام بنجاح!")
    except Exception as e:
        print(f"❌ فشل انستغرام: {e}")

    # 4. النشر على التلغرام
    print("\n✈️ [Telegram] جاري النشر...")
    try:
        post_to_telegram.post_album(image_paths, caption)
        print("✅ تم النشر على تلغرام بنجاح!")
    except Exception as e:
        print(f"❌ فشل تلغرام: {e}")

    # 5. النشر على لينكد إن (تخطي آمن إذا لم يوجد)
    print("\n💼 [LinkedIn] جاري التحقق من النشر...")
    try:
        import post_to_linkedin
        if hasattr(post_to_linkedin, 'post_content'):
            post_to_linkedin.post_content(image_paths, caption)
        elif hasattr(post_to_linkedin, 'main'):
            post_to_linkedin.main()
        print("✅ تم النشر على لينكد إن بنجاح!")
    except ImportError:
        print("⚠️ ملف لينكد إن غير موجود، تم التخطي بأمان.")
    except Exception as e:
        print(f"❌ فشل لينكد إن: {e}")

    print("\n--- اكتملت العملية ---")

if __name__ == "__main__":
    main()
