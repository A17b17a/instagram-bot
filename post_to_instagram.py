import os
import time
from playwright.sync_api import sync_playwright

def post_carousel(image_paths, caption):
    # جلب بيانات الحساب من GitHub Secrets
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")

    if not username or not password:
        raise ValueError("❌ يرجى التأكد من إضافة INSTAGRAM_USERNAME و INSTAGRAM_PASSWORD في GitHub Secrets.")

    print("⏳ جاري تشغيل المتصفح الآلي (Playwright) وتجاوز حظر الـ IP...")

    with sync_playwright() as p:
        # تشغيل متصفح كروم بدون واجهة (Headless)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
        )
        page = context.new_page()

        # 1. تسجيل الدخول
        print("🔑 جاري فتح صفحة تسجيل الدخول...")
        page.goto("https://www.instagram.com/accounts/login/")
        page.wait_for_timeout(4000)

        # قبول الكوكيز إن ظهرت
        try:
            page.click("button:has-text('Allow all cookies')", timeout=3000)
        except Exception:
            pass

        page.fill("input[name='username']", username)
        page.fill("input[name='password']", password)
        page.click("button[type='submit']")
        page.wait_for_timeout(6000)

        # تخطي حفظ معلومات الدخول
        for text in ["Not Now", "ليس الآن", "Save Info", "حفظ المعلومات"]:
            try:
                page.click(f"button:has-text('{text}')", timeout=3000)
            except Exception:
                pass

        # 2. رفع صور السلايدر
        print("📸 جاري اختيار الصور ورفعها...")
        absolute_paths = [os.path.abspath(img) for img in image_paths]

        try:
            page.click("svg[aria-label='New post']", timeout=5000)
        except Exception:
            try:
                page.click("svg[aria-label='منشور جديد']", timeout=5000)
            except Exception:
                page.goto("https://www.instagram.com/?select_post_type=1")
                page.wait_for_timeout(3000)

        with page.expect_file_chooser() as fc_info:
            try:
                page.click("button:has-text('Select from computer')", timeout=5000)
            except Exception:
                page.click("button:has-text('تحديد من الكمبيوتر')", timeout=5000)

        file_chooser = fc_info.value
        file_chooser.set_files(absolute_paths)
        page.wait_for_timeout(4000)

        # 3. الضغط على Next (التالي)
        print("➡️ متابعة الخطوات...")
        for _ in range(2):
            try:
                page.click("div[role='button']:has-text('Next')", timeout=5000)
            except Exception:
                page.click("div[role='button']:has-text('التالي')", timeout=5000)
            page.wait_for_timeout(2000)

        # 4. كتابة النص والهاشتاغات
        print("✍️ إضافة شرح المنشور...")
        try:
            page.fill("div[aria-label='Write a caption...']", caption)
        except Exception:
            try:
                page.fill("div[aria-label='كتابة شرح...']", caption)
            except Exception:
                page.fill("div[contenteditable='true']", caption)

        page.wait_for_timeout(2000)

        # 5. الضغط على Share (مشاركة)
        print("🚀 جاري نشر المنشور...")
        try:
            page.click("div[role='button']:has-text('Share')", timeout=5000)
        except Exception:
            page.click("div[role='button']:has-text('مشاركة')", timeout=5000)

        print("⏳ الانتظار لتأكيد النشر...")
        page.wait_for_timeout(10000)
        browser.close()
        print("✅ تم النشر على إنستغرام عبر المتصفح الآلي بنجاح!")
