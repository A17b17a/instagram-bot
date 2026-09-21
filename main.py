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


def upload_image(file_path: str) -> str:
    """رفع الصورة تلقائياً للحصول على رابط مباشر قابل للنشر على إنستغرام"""
    url = "https://catbox.moe/user/api.php"
    data = {"reqtype": "fileupload"}
    
    with open(file_path, "rb") as f:
        res = requests.post(url, data=data, files={"fileToUpload": f}, timeout=30)
    
    if res.status_code == 200 and res.text.startswith("http"):
        return res.text.strip()
    else:
        raise Exception(f"فشل رفع الصورة {file_path}: {res.text}")


def post_to_make(image_paths: list, caption: str):
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL") or os.environ.get("WEBHOOK_URL")
    
    if not webhook_url:
        raise Exception("لم يتم العثور على MAKE_WEBHOOK_URL في Secrets الخاص بـ GitHub!")

    print("📤 جاري رفع الصور الموالدة للحصول على روابط مباشرة...")
    image_urls = []
    for idx, img_path in enumerate(image_paths):
        print(f"   - رفع الصورة [{idx + 1}/{len(image_paths)}]: {img_path}")
        url = upload_image(img_path)
        image_urls.append(url)

    print("📡 جاري إرسال البيانات والروابط الخمسة إلى Make Webhook...")
    
    # تجهيز حزمة البيانات بـ JSON لـ Make.com
    payload = {
        "caption": caption
    }
    
    # إرسال روابط الصور كـ image_1, image_2, image_3, image_4, image_5
    for i, url in enumerate(image_urls):
        payload[f"image_{i+1}"] = url

    response = requests.post(webhook_url, json=payload, timeout=30)

    if response.status_code in [200, 201, 204]:
        print("✅ تم إرسال البيانات والروابط بنجاح إلى Make!")
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

    # ── Make (Instagram Carousel) ─────────────────────────────
    print("\n📸 [Make Webhook] جاري رفع الصور وإرسال المحتوى...")
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
