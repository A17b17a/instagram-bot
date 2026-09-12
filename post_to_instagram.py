import os
from instagrapi import Client

def post_carousel(image_paths, caption):
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        raise ValueError("بيانات الانستغرام غير موجودة في الأسرار")

    cl = Client()
    cl.login(username, password)
    
    # رفع الصور على شكل كاروسيل متسلسل مع النص
    cl.album_upload(image_paths, caption)
