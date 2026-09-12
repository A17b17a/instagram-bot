import os
import requests

# ==========================================
# 1. نشر بوست على Instagram
# ==========================================
def post_to_instagram(image_path, caption):
    print("📸 [Instagram] جاري نشر البوست...")
    try:
        import post_to_instagram as insta_bot
        insta_bot.publish(image_path, caption)
        print("✅ [Instagram] تم النشر بنجاح!")
    except ImportError:
        print("⚠️ [Instagram] ملف post_to_instagram.py غير موجود، تم تجاوز المنصة.")
    except Exception as e:
        print(f"❌ [Instagram] خطأ أثناء النشر: {e}")

# ==========================================
# 2. نشر بوست على Telegram
# ==========================================
def post_to_telegram(image_path, caption):
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not bot_token or not chat_id:
        print("⚠️ [Telegram] تعذر النشر: بيانات TELEGRAM_BOT_TOKEN أو TELEGRAM_CHAT_ID غير متوفرة في Secrets.")
        return

    print("✈️ [Telegram] جاري نشر البوست...")
    
    if os.path.exists(image_path):
        url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
        with open(image_path, 'rb') as photo:
            res = requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'photo': photo})
    else:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        res = requests.post(url, data={'chat_id': chat_id, 'text': caption})

    if res.status_code == 200:
        print("✅ [Telegram] تم النشر بنجاح!")
    else:
        print(f"❌ [Telegram] خطأ أثناء النشر: {res.text}")

# ==========================================
# 3. نشر بوست على LinkedIn
# ==========================================
def post_to_linkedin(caption):
    access_token = os.getenv('LINKEDIN_ACCESS_TOKEN')
    if not access_token:
        print("⚠️ [LinkedIn] تعذر النشر: LINKEDIN_ACCESS_TOKEN غير موجود في Secrets.")
        return

    print("💼 [LinkedIn] جاري نشر البوست...")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }

    user_res = requests.get('https://api.linkedin.com/v2/userinfo', headers={'Authorization': f'Bearer {access_token}'})
    if user_res.status_code != 200:
        print(f"❌ [LinkedIn] خطأ في جلب بيانات الحساب: {user_res.text}")
        return
        
    person_urn = f"urn:li:person:{user_res.json().get('sub')}"

    post_payload = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": caption},
                "shareMediaCategory": "NONE"
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }

    res = requests.post("https://api.linkedin.com/v2/ugcPosts", headers=headers, json=post_payload)
    if res.status_code in [200, 201]:
        print("✅ [LinkedIn] تم النشر بنجاح!")
    else:
        print(f"❌ [LinkedIn] خطأ أثناء النشر: {res.text}")

# ==========================================
# التنفيذ المستقل (عزل كامل لكل منصة)
# ==========================================
if __name__ == "__main__":
    
    caption_text = "🚀 منشور جديد تم إرساله تلقائياً عبر نظام الأتمتة الموحد!\n\n#Automation #Python #Content"
    image_file = "post_image.png"

    print("--- بدء عملية النشر على جميع المنصات ---\n")

    try:
        post_to_instagram(image_file, caption_text)
    except Exception as e:
        print(f"❌ فشل التنفيذ لـ Instagram: {e}")

    try:
        post_to_telegram(image_file, caption_text)
    except Exception as e:
        print(f"❌ فشل التنفيذ لـ Telegram: {e}")

    try:
        post_to_linkedin(caption_text)
    except Exception as e:
        print(f"❌ فشل التنفيذ لـ LinkedIn: {e}")

    print("\n--- اكتملت عملية النشر ---")
