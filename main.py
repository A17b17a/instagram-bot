import os
import requests

# جلب الـ Access Token من متناغزات GitHub Secrets
ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN")

if not ACCESS_TOKEN:
    print("❌ خطأ: لم يتم العثور على LINKEDIN_ACCESS_TOKEN!")
    exit(1)

# 1. جلب معرف المستخدم (LinkedIn Person URN) تلقائياً
user_info_url = "https://api.linkedin.com/v2/userinfo"
headers_auth = {"Authorization": f"Bearer {ACCESS_TOKEN}"}

response_user = requests.get(user_info_url, headers=headers_auth)

if response_user.status_code != 200:
    print("❌ فشل في جلب معلومات المستخدم:", response_user.status_code, response_user.text)
    exit(1)

user_sub = response_user.json().get("sub")
author_urn = f"urn:li:person:{user_sub}"
print(f"✅ تم التعرف على حسابك بنجاح: {author_urn}")

# 2. نص المنشور المراد نشره
# (يمكنك تعديل النص هنا أو تطويره مستقبلاً ليجلب محتوى من AI أو ملف خارجي)
post_text = """🚀 Hello LinkedIn Community!

This post was generated and published automatically using Python & GitHub Actions!

#Python #Automation #GitHubActions #Tech"""

# 3. إرسال المنشور إلى LinkedIn API
post_url = "https://api.linkedin.com/v2/ugcPosts"
headers_post = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "X-Restli-Protocol-Version": "2.0.0"
}

post_body = {
    "author": author_urn,
    "lifecycleState": "PUBLISHED",
    "specificContent": {
        "com.linkedin.ugc.ShareContent": {
            "shareCommentary": {
                "text": post_text
            },
            "shareMediaCategory": "NONE"
        }
    },
    "visibility": {
        "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
    }
}

response = requests.post(post_url, headers=headers_post, json=post_body)

if response.status_code in [200, 201]:
    print("🎉 تم نشر المنشور بنجاح على حسابك في LinkedIn!")
else:
    print("❌ فشل النشر:", response.status_code, response.text)
