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
    for pattern in ["output/*.jpg", "output/*.jpeg", "daily_post/*.jpg", "*.jpg", "output/*.png"]:
        images = sorted(glob.glob(pattern))
        if images:
            return images
    return []


def upload_image(file_path: str) -> str:
    """رفع الصورة على سيرفرات سريعة ومفتوحة لسيرفرات إنستغرام وفيسبوك"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # 1. سيرفر Catbox (الأفضل والأضمن والمفتوح لسيرفرات فيسبوك وإنستغرام)
    try:
        url = "https://catbox.moe/user/api.php"
        data = {"reqtype": "fileupload"}
        with open(file_path, "rb") as f:
            res = requests.post(url, data=data, files={"fileToUpload": f}, headers=headers, timeout=30)
        if res.status_code == 200 and res.text.startswith("http"):
            direct_url = res.text.strip()
            print(f"      🔗 تم الرفع بنجاح (Catbox): {direct_url}")
            return direct_url
    except Exception as e:
        print(f"      ⚠️ فشل Catbox: {e}")

    # 2. سيرفر Pixeldrain (احتياطي)
    try:
        url = "https://pixeldrain.com/api/file"
        with open(file_path, "rb") as f:
            res = requests.post(url, files={"file": f}, headers=headers, timeout=30)
        if res.status_code in [200, 201]:
            data = res.json()
            if data.get("success"):
                file_id = data.get("id")
                direct_url = f"https://pixeldrain.com/api/file/{file_id}"
                print(f"      🔗 تم الرفع بنجاح (Pixeldrain): {direct_url}")
                return direct_url
    except Exception as e:
        print(f"      ⚠️ فشل Pixeldrain: {e}")

    # 3. سيرفر FreeImage (احتياطي ثاني)
    try:
        url = "https://freeimage.host/api/1/upload"
        params = {
            "key": "6d207e6418357803d36c09f476b8bcbf",
            "action": "upload",
            "format": "json"
        }
        with open(file_path, "rb") as f:
            res = requests.post(url, data=params, files={"source": f}, headers=headers, timeout=30)
        if res.status_code == 200:
            data = res.json()
            if data.get("status_code") == 200:
                direct_url = data["image"]["url"]
                print(f"      🔗 تم الرفع بنجاح (FreeImage): {direct_url}")
                return direct_url
    except Exception as e:
        print(f"      ⚠️ فشل FreeImage: {e}")

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
