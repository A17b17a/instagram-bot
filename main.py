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
    # تم تحديث الأنماط للبحث عن صور JPG المناسبة لإنستغرام
    for pattern in ["output/*.jpg", "output/*.jpeg", "daily_post/*.jpg", "*.jpg", "output/*.png"]:
        images = sorted(glob.glob(pattern))
        if images:
            return images
    return []


def upload_image(file_path: str) -> str:
    """رفع الصورة تلقائياً للحصول على رابط مباشر مع سيرفرات احتياطية وهيدرات حقيقية"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    # 1. المحاولة الأولى: سيرفر Tmpfiles المباشر
    try:
        url = "https://tmpfiles.org/api/v1/upload"
        with open(file_path, "rb") as f:
            res = requests.post(url, files={"file": f}, headers=headers, timeout=20)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                raw_url = data["data"]["url"]
                return raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    except Exception:
        pass

    # 2. المحاولة الثانية: سيرفر Catbox مع هيدر متصفح
    try:
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}
        with open(file_path, "rb") as f:
            res = requests.post(url, data=data, files={"fileToUpload": f}, headers=headers, timeout=30)
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception:
        pass

    # 3. المحاولة الثالثة: سيرفر Litterbox الاحتياطي
    try:
        url = "https://litterbox.catbox.moe/resources/internals/api.php"
        data = {"reqtype": "fileupload", "time": "1h"}
        with open(file_path, "rb") as f:
            res = requests.post(url, data=data, files={"fileToUpload": f}, headers=headers, timeout=30)
        if res.status_code == 200 and res.text.startswith("http"):
            return res.text.strip()
    except Exception:
        pass

    raise Exception(f"تعذر رفع الصورة {file_path} على كافة السيرفرات")


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
    
    payload = {
        "caption": caption
    }
    
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
