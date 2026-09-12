import os
import glob
import sys

def get_caption() -> str:
    for path in ["output/caption.txt", "caption.txt", "daily_post/caption.txt"]:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read().strip()
    return "منشور يومي جديد!"


def get_images() -> list:
    for pattern in ["output/*.png", "daily_post/*.png", "*.png"]:
        images = sorted(glob.glob(pattern))
        if images:
            return images
    return []


def main():
    print("=" * 50)
    print("--- بدء عملية النشر الموحدة ---")
    print("=" * 50)

    caption     = get_caption()
    image_paths = get_images()

    if not image_paths:
        print("❌ لا توجد صور للنشر!")
        print("الملفات في المجلد الحالي:", os.listdir("."))
        for d in ["output", "daily_post"]:
            if os.path.exists(d):
                print(f"الملفات في {d}/:", os.listdir(d))
        sys.exit(1)

    print(f"📸 عدد الصور: {len(image_paths)}")
    print(f"📝 طول الكابشن: {len(caption)} حرف")

    results = {}

    # ── Instagram ────────────────────────────────────────────
    print("\n📸 [Instagram] جاري النشر...")
    try:
        import post_to_instagram
        post_to_instagram.post_carousel(image_paths, caption)
        results["instagram"] = "✅ نجح"
    except Exception as e:
        results["instagram"] = f"❌ فشل: {e}"
        print(f"❌ فشل انستغرام: {e}")

    # ── Telegram ─────────────────────────────────────────────
    print("\n✈️  [Telegram] جاري النشر...")
    try:
        import post_to_telegram
        post_to_telegram.post_album(image_paths, caption)
        results["telegram"] = "✅ نجح"
    except ImportError:
        results["telegram"] = "⚠️ ملف غير موجود"
        print("⚠️  post_to_telegram.py غير موجود، تم التخطي.")
    except Exception as e:
        results["telegram"] = f"❌ فشل: {e}"
        print(f"❌ فشل تلغرام: {e}")

    # ── LinkedIn ─────────────────────────────────────────────
    print("\n💼 [LinkedIn] جاري النشر...")
    # التحقق من وجود الـ Token قبل المحاولة
    if not os.environ.get("LINKEDIN_ACCESS_TOKEN"):
        results["linkedin"] = "⚠️ Token غير موجود في Secrets"
        print("⚠️  LINKEDIN_ACCESS_TOKEN غير موجود، تم التخطي.")
    else:
        try:
            import post_to_linkedin
            post_to_linkedin.post_content(image_paths, caption)
            results["linkedin"] = "✅ نجح"
        except ImportError:
            results["linkedin"] = "⚠️ ملف post_to_linkedin.py غير موجود"
            print("⚠️  post_to_linkedin.py غير موجود، تم التخطي.")
        except Exception as e:
            results["linkedin"] = f"❌ فشل: {e}"
            print(f"❌ فشل لينكد إن: {e}")

    # ── ملخص النتائج ─────────────────────────────────────────
    print("\n" + "=" * 50)
    print("--- ملخص النتائج ---")
    for platform, status in results.items():
        print(f"  {platform:12s}: {status}")
    print("=" * 50)

    # فشل الـ workflow فقط إذا فشلت جميع المنصات
    all_failed = all("❌" in s for s in results.values())
    if all_failed:
        print("\n❌ فشلت جميع المنصات!")
        sys.exit(1)


if __name__ == "__main__":
    main()
