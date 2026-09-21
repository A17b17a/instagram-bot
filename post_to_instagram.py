import os
import requests

def post_carousel(image_paths, caption):
    # جلب رابط الـ Webhook من GitHub Secrets
    webhook_url = os.environ.get("MAKE_WEBHOOK_URL")

    if not webhook_url:
        print("⚠️ لم يتم ضبط MAKE_WEBHOOK_URL في GitHub Secrets.")
        return

    print("🚀 جاري إرسال البيانات إلى Make/Pipedream للنشر على إنستغرام...")

    # تجهيز البيانات (النص والروابط)
    payload = {
        "caption": caption,
        "images": image_paths  # أو روابط الصور المباشرة
    }

    try:
        response = requests.post(webhook_url, json=payload, timeout=30)
        if response.status_code == 200:
            print("✅ تم إرسال المنشور إلى Webhook بنجاح للنشر الآلي!")
        else:
            print(f"❌ فشل الإرسال إلى Webhook: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ حدث خطأ أثناء الاتصال بـ Webhook: {e}")
