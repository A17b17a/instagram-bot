import os
import requests
from PIL import Image

def post_content(image_paths, caption):
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN")
    person_urn = os.environ.get("LINKEDIN_PERSON_URN")

    if not token or not person_urn:
        raise ValueError("❌ لم يتم العثور على LINKEDIN_ACCESS_TOKEN أو LINKEDIN_PERSON_URN")

    # 1. دمج الصور في ملف PDF واحد (مطلوب لعمل سلايدر في لينكد إن)
    pdf_path = "carousel.pdf"
    imgs = [Image.open(img).convert('RGB') for img in image_paths]
    # حفظ الصور كلها كصفحات في ملف الـ PDF
    imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])
    print("✅ تم تحويل الصور إلى ملف PDF بنجاح")

    headers = {
        "Authorization": f"Bearer {token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    # 2. تسجيل طلب رفع ملف (Document)
    register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    register_data = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
            "owner": person_urn,
            "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
        }
    }
    
    res = requests.post(register_url, headers=headers, json=register_data)
    res.raise_for_status()
    data = res.json()
    
    upload_url = data['value']['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
    asset_urn = data['value']['asset']

    # 3. رفع ملف الـ PDF فعلياً
    print("⏳ جاري رفع الملف إلى لينكد إن...")
    with open(pdf_path, 'rb') as f:
        upload_res = requests.post(upload_url, headers={"Authorization": f"Bearer {token}"}, data=f)
    upload_res.raise_for_status()
    print("✅ تم رفع الملف بنجاح!")

    # 4. إنشاء المنشور وربطه بالملف المرفوع
    post_url = "https://api.linkedin.com/v2/ugcPosts"
    post_data = {
        "author": person_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": caption},
                "shareMediaCategory": "DOCUMENT",
                "media": [
                    {
                        "status": "READY",
                        "media": asset_urn,
                        "title": {"text": "تصفح الصور"}
                    }
                ]
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
    }
    
    post_res = requests.post(post_url, headers=headers, json=post_data)
    post_res.raise_for_status()
    print("✅ تم النشر كسلايدر على LinkedIn بنجاح!")
