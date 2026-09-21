import os
import glob
import sys
import requests

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


def post_to_make(image_paths: list, caption: str):
    webhook_url = os.environ.get("WEBHOOK_URL")
    if not webhook_url:
        raise Exception("لم يتم العثور على WEBHOOK_URL في Secrets الخاص بـ GitHub!")

    print("📡 جاري إرسال البيانات والصور إلى Make Webhook...")
    
    data = {"caption": caption}
    files = {}
    
    # فتح الصورة الأولى لإرسالها مع الطلب
    if image_paths and os.path.exists(image_paths[0]):
        files = {"file": open(image_paths[0], "rb")}

    response = requests.post(webhook_url, data=data, files=files)

    if response.status_code in [200, 201, 204]:
        print("✅ تم إرسال البيانات بنجاح إلى Make!")
    else:
        raise Exception(f"فشل الإرسال إلى Make (كود الاستجابة: {response.status_code})")


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

    # ── Make (Instagram & Platforms) ─────────────────────────
    print("\n📸 [Make Webhook] جاري إرسال المحتوى...")
    try:
        post_to_make(image_paths, caption)
        results["make_webhook"] = "✅ نجح"
    except Exception as e:
        results["make_webhook"] = f"❌ فشل: {e}"
        print(f"❌ فشل الإرسال لـ Make: {e}")

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

    # ── ملخص النتائج ─────────────────────────────────────────
    print("\n" + "=" * 50)
    print("--- ملخص النتائج ---")
    for platform, status in results.items():
        print(f"  {platform:12s}: {status}")
    print("=" * 50)

    all_failed = all("❌" in s for s in results.values())
    if all_failed:
        print("\n❌ فشلت جميع المنصات!")
        sys.exit(1)


if __name__ == "__main__":
    main()
