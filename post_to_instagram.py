import os
import time
from playwright.sync_api import sync_playwright

def post_carousel(image_paths, caption):
    # جلب بيانات الحساب من GitHub Secrets
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")

    if not username or not password:
        raise ValueError("❌ يرجى التأكد من إضافة INSTAGRAM_USERNAME و INSTAGRAM_PASSWORD في GitHub Secrets.")

    print("⏳ جاري تشغيل المتصفح الآلي (Playwright)...")

    with sync_playwright() as p:
        # تشغيل المتصفح مع معلمات لمنع اكتشاف الأتمتة
        browser = p.chromium.launch(
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        # ضبط البيئة باللغة الإنجليزية لمنع اختلاف النصوص
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='en-US'
        )
        page = context.new_page()

        # 1. فتح صفحة تسجيل الدخول
        print("🔑 جاري فتح صفحة تسجيل الدخول...")
        page.goto("https://www.instagram.com/accounts/login/", wait_until="domcontentloaded")
        page.wait_for_timeout(4000)

        # قبول ملفات الكوكيز في حال ظهورها
        try:
            cookie_btn = page.locator("button:has-text('Allow all cookies'), button:has-text('Allow optional cookies'), button:has-text('Accept'), button:has-text('قبول')")
            if cookie_btn.count() > 0:
                cookie_btn.first.click()
                page.wait_for_timeout(2000)
        except Exception:
            pass

        # 2. تعبئة البيانات وتسجيل الدخول
        print("🔑 كتابة بيانات الدخول...")
        try:
            page.wait_for_selector("input[name='username']", timeout=20000)
            page.fill("input[name='username']", username)
            page.fill("input[name='password']", password)
            page.click("button[type='submit']")
            page.wait_for_timeout(7000)
        except Exception as e:
            print(f"❌ تعذر العثور على حقل الدخول: {e}")
            raise e

        # تخطي حفظ معلومات الدخول والإشعارات
        for btn_text in ["Not Now", "Not now", "ليس الآن", "Save Info", "Save info", "حفظ المعلومات"]:
            try:
                btn = page.locator(f"button:has-text('{btn_text}'), div[role='button']:has-text('{btn_text}')")
                if btn.count() > 0:
                    btn.first.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass

        # 3. فتح نافذة رفع منشور جديد
        print("📸 جاري اختيار الصور ورفعها...")
        try:
            create_btn = page.locator("svg[aria-label='New post'], svg[aria-label='منشور جديد'], svg[aria-label='New Post']")
            if create_btn.count() > 0:
                create_btn.first.click()
            else:
                page.goto("https://www.instagram.com/?select_post_type=1")
        except Exception:
            page.goto("https://www.instagram.com/?select_post_type=1")

        page.wait_for_timeout(3000)

        # 4. تحديد الملفات
        absolute_paths = [os.path.abspath(img) for img in image_paths]
        try:
            with page.expect_file_chooser(timeout=10000) as fc_info:
                select_btn = page.locator("button:has-text('Select from computer'), button:has-text('تحديد من الكمبيوتر')")
                if select_btn.count() > 0:
                    select_btn.first.click()
                else:
                    page.click("button", timeout=5000)
            file_chooser = fc_info.value
            file_chooser.set_files(absolute_paths)
        except Exception as e:
            print(f"❌ فشل رفع الصور: {e}")
            raise e

        page.wait_for_timeout(4000)

        # 5. الضغط على Next (التالي) مرتين
        print("➡️ متابعة الخطوات...")
        for _ in range(2):
            try:
                next_btn = page.locator("div[role='button']:has-text('Next'), button:has-text('Next'), div[role='button']:has-text('التالي')")
                if next_btn.count() > 0:
                    next_btn.first.click()
                    page.wait_for_timeout(3000)
            except Exception:
                pass

        # 6. كتابة النص
        print("✍️ إضافة شرح المنشور...")
        try:
            caption_box = page.locator("div[aria-label='Write a caption...'], div[aria-label='كتابة شرح...'], div[contenteditable='true']")
            caption_box.first.wait_for(timeout=10000)
            caption_box.first.fill(caption)
        except Exception as e:
            print(f"⚠️ لم يتمكن السكريبت من كتابة النص تلقائياً: {e}")

        page.wait_for_timeout(2000)

        # 7. الضغط على Share (مشاركة)
        print("🚀 جاري نشر المنشور...")
        try:
            share_btn = page.locator("div[role='button']:has-text('Share'), button:has-text('Share'), div[role='button']:has-text('مشاركة')")
            if share_btn.count() > 0:
                share_btn.first.click()
        except Exception as e:
            print(f"❌ فشل إرسال طلب المشاركة: {e}")
            raise e

        print("⏳ الانتظار لتأكيد النشر...")
        page.wait_for_timeout(12000)
        browser.close()
        print("✅ تم النشر على إنستغرام عبر المتصفح الآلي بنجاح!")
