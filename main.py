import os
import glob
import sys
import requests
import subprocess
import time

# بيانات المستودع الخاص بك على GitHub
GITHUB_REPO = "A17b17a/instagram-bot"
BRANCH = "main"

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


def push_images_to_github():
    """رفع الصور الموالدة إلى مستودع GitHub مباشرةً للحصول على روابط مستقرة"""
    try:
        print("📦 جاري رفع الصور الموالدة إلى مستودع GitHub...")
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], check=False)
        subprocess.run(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"], check=False)
        subprocess.run(["git", "add", "output/"], check=False)
        subprocess.run(["git", "commit", "-m", "Upload generated carousel images [skip ci]"], check=False)
        subprocess.run(["git", "push"], check=False)
        print("✅ تم رفع الصور على GitHub بنجاح!")
    except Exception as e:
        print(f"⚠️ تنبيه Git: {e}")


def post_to_make(image_paths: list, caption: str):
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL") or os.environ.get("WEBHOOK_URL")
    
    if not webhook_url:
        raise Exception("لم يتم العثور على MAKE_WEBHOOK_URL في Secrets الخاص بـ GitHub!")

    # رفع الصور لـ GitHub أولاً
    push_images_to_github()

    timestamp = int(time.time())
    image_urls = []
    
    print("🔗 جاري تحويل مسارات الصور إلى روابط GitHub المباشرة...")
    for img_path in image_paths:
        # تنظيف المسار
        clean_path = img_path.replace("\\", "/")
        # بناء رابط Raw مباشر من GitHub
        raw_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{BRANCH}/{clean_path}?v={timestamp}"
        image_urls.append(raw_url)
        print(f"   - رابط الصورة: {raw_url}")

    print("📡 جاري إرسال الروابط والكابشن إلى Make Webhook...")
    
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
    print("--- بدء عملية النشر الموحدة عبر GitHub Direct ---")
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
    print("\n📸 [Make Webhook] جاري التجهيز والإرسال...")
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
