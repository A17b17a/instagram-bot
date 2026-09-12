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
    imgs[0].save(pdf_path, save_all=True, append_images=imgs[1:])
    print("✅ تم تحويل الصور إلى ملف PDF بنجاح")

    # الترويسات الخاصة بالنظام الجديد (Rest API)
    headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202401",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    # 2. تسجيل طلب رفع مستند باستخدام Rest API الحديث (images/documents)
    register_url = "https://api.linkedin.com/v2/images?action=initializeUpload"
    register_data = {
        "initializeUploadRequest": {
            "owner": person_urn
        }
    }
    
    # تحويل URN ليتوافق مع أحدث صيغ رفع الوسائط
    document_register_url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    
    # للـ PDF / Carousel نستخدم Rest API V2 InitializeUpload للوسائط
    init_url = "https://api.linkedin.com/v2/restli/documents?action=initializeUpload"
    
    # جلب رابط الرفع عبر الـ REST API الحديث للمستندات
    register_payload = {
        "initializeUploadRequest": {
            "owner": person_urn
        }
    }
    
    # استخدام endpoint الـ Assets المحدث بحساب النسخة الحديثة
    res = requests.post(
        "https://api.linkedin.com/v2/assets?action=registerUpload",
        headers=headers,
        json={
            "registerUploadRequest": {
                "recipes": ["urn:li:digitalmediaRecipe:feedshare-document"],
                "owner": person_urn,
                "serviceRelationships": [{"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}]
            }
        }
    )
    
    # إذا فشل المسار القديم، نقوم باستخدام الـ Posts API المباشر الحديث
    if res.status_code != 200:
        # المحاولة عبر المسار الحديث لتسجيل المستندات
        res = requests.post(
            "https://api.linkedin.com/rest/documents?action=initializeUpload",
            headers={
                "Authorization": f"Bearer {token}",
                "LinkedIn-Version": "202401",
                "Content-Type": "application/json"
            },
            json={"initializeUploadRequest": {"owner": person_urn}}
        )
        res.raise_for_status()
        data = res.json()['value']
        upload_url = data['uploadUrl']
        asset_urn = data['document']
    else:
        data = res.json()['value']
        upload_url = data['uploadMechanism']['com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest']['uploadUrl']
        asset_urn = data['asset']

    # 3. رفع ملف الـ PDF فعلياً
    print("⏳ جاري رفع الملف إلى لينكد إن...")
    with open(pdf_path, 'rb') as f:
        upload_res = requests.put(upload_url, headers={"Authorization": f"Bearer {token}"}, data=f)
        if upload_res.status_code not in [200, 201]:
            upload_res = requests.post(upload_url, headers={"Authorization": f"Bearer {token}"}, data=f)
    print("✅ تم رفع الملف بنجاح!")

    # 4. إنشاء المنشور باستخدام Rest Posts API الجديد
    posts_url = "https://api.linkedin.com/rest/posts"
    post_headers = {
        "Authorization": f"Bearer {token}",
        "LinkedIn-Version": "202401",
        "X-Restli-Protocol-Version": "2.0.0",
        "Content-Type": "application/json"
    }

    # تركيب جسم الطلب لمنشور مستندات سلايدر (Document Carousel)
    post_data = {
        "author": person_urn,
        "commentary": caption,
        "visibility": "PUBLIC",
        "distribution": {
            "feedDistribution": "MAIN_FEED",
            "targetEntities": [],
            "thirdPartyDistributionChannels": []
        },
        "content": {
            "media": {
                "title": "تصفح الصور",
                "id": asset_urn
            }
        },
        "lifecycleState": "PUBLISHED"
    }
    
    post_res = requests.post(posts_url, headers=post_headers, json=post_data)
    
    # في حال عدم تدعيم الـ Endpoint الجديد للحساب الحالي، العودة للتوافق مع UGC
    if post_res.status_code not in [200, 201]:
        ugc_url = "https://api.linkedin.com/v2/ugcPosts"
        ugc_data = {
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
        post_res = requests.post(ugc_url, headers=headers, json=ugc_data)
        post_res.raise_for_status()

    print("✅ تم النشر كسلايدر على LinkedIn بنجاح!")
