"""
النشر على LinkedIn عبر API مباشرة (بدون ملفات محلية).
المتغيرات المطلوبة في GitHub Secrets:
  LINKEDIN_ACCESS_TOKEN   — Access Token من LinkedIn Developer App
  LINKEDIN_PERSON_URN     — مثال: urn:li:person:XXXXXXXX
                            (احصل عليه من: https://api.linkedin.com/v2/userinfo)
"""
import os
import json
import urllib.request
import urllib.error
from pathlib import Path

API_BASE = "https://api.linkedin.com/v2"


def _get_credentials():
    token = os.environ.get("LINKEDIN_ACCESS_TOKEN", "").strip()
    urn   = os.environ.get("LINKEDIN_PERSON_URN", "").strip()

    if not token:
        raise ValueError("❌ LINKEDIN_ACCESS_TOKEN غير موجود في الأسرار")
    if not urn:
        raise ValueError("❌ LINKEDIN_PERSON_URN غير موجود في الأسرار")
    return token, urn


def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }


def _register_image(token: str, urn: str) -> tuple[str, str]:
    """تسجيل صورة واحدة والحصول على رابط الرفع و asset URN."""
    payload = {
        "registerUploadRequest": {
            "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
            "owner": urn,
            "serviceRelationships": [{
                "relationshipType": "OWNER",
                "identifier": "urn:li:userGeneratedContent"
            }]
        }
    }
    req = urllib.request.Request(
        f"{API_BASE}/assets?action=registerUpload",
        data=json.dumps(payload).encode(),
        headers=_headers(token),
        method="POST",
    )
    with urllib.request.urlopen(req) as r:
        data = json.loads(r.read())

    upload_url = data["value"]["uploadMechanism"][
        "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
    ]["uploadUrl"]
    asset_urn  = data["value"]["asset"]
    return upload_url, asset_urn


def _upload_image(upload_url: str, token: str, image_path: str):
    """رفع ملف الصورة إلى الرابط المسجَّل."""
    with open(image_path, "rb") as f:
        image_data = f.read()
    req = urllib.request.Request(
        upload_url,
        data=image_data,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type":  "image/png",
        },
        method="PUT",
    )
    with urllib.request.urlopen(req):
        pass   # 201 Created


def post_content(image_paths: list, caption: str):
    """
    نشر على LinkedIn:
      - صورة واحدة إذا كان image_paths فيه عنصر واحد
      - أول صورة فقط إذا كان كاروسيل (LinkedIn لا يدعم ألبوم API مجاناً)
      - النص (caption) كـ commentary
    """
    token, urn = _get_credentials()

    # LinkedIn يدعم صورة واحدة فقط في المنشور العادي عبر API
    image_to_use = str(image_paths[0]) if image_paths else None

    if image_to_use and Path(image_to_use).exists():
        print(f"   ⬆️  رفع الصورة: {image_to_use}")
        upload_url, asset_urn = _register_image(token, urn)
        _upload_image(upload_url, token, image_to_use)
        print(f"   ✅ الصورة جاهزة: {asset_urn}")

        payload = {
            "author":          urn,
            "lifecycleState":  "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": caption[:3000]},
                    "shareMediaCategory": "IMAGE",
                    "media": [{
                        "status":      "READY",
                        "description": {"text": caption[:200]},
                        "media":        asset_urn,
                        "title":        {"text": "منشور يومي"},
                    }]
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }
    else:
        # نشر نصي فقط إذا لم تكن هناك صورة
        print("   ℹ️  لا توجد صورة — نشر نصي فقط")
        payload = {
            "author":          urn,
            "lifecycleState":  "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary":    {"text": caption[:3000]},
                    "shareMediaCategory": "NONE",
                }
            },
            "visibility": {
                "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
            }
        }

    req = urllib.request.Request(
        f"{API_BASE}/ugcPosts",
        data=json.dumps(payload).encode(),
        headers=_headers(token),
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
            print(f"   ✅ نُشر على LinkedIn: {result.get('id','')}")
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"❌ LinkedIn API error {e.code}: {body}")
