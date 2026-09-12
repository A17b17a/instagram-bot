import os
import json
import time
import random
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, ChallengeRequired, RateLimitError, ClientError
)

SESSION_FILE = Path("session.json")


def _build_client() -> Client:
    """
    بناء الـ Client مع إعدادات تقلل احتمال الحظر.
    """
    cl = Client()
    cl.delay_range = [2, 5]   # تأخير عشوائي بين كل طلب
    return cl


def _load_session(cl: Client, username: str, password: str) -> bool:
    """
    محاولة تحميل الـ session بالأولوية التالية:
      1. متغير بيئي INSTAGRAM_SESSION_JSON  (GitHub Secret)
      2. ملف session.json المحلي             (للتطوير)
    يرجع True إذا نجح، False إذا فشل.
    """
    session_data = os.environ.get("INSTAGRAM_SESSION_JSON", "").strip()

    # — المصدر 1: GitHub Secret —
    if session_data:
        try:
            settings = json.loads(session_data)
            cl.set_settings(settings)
            cl.login(username, password)
            print("🔑 تم تسجيل الدخول عبر INSTAGRAM_SESSION_JSON (Secret)")
            return True
        except Exception as e:
            print(f"⚠️  فشل تحميل الـ Secret session: {e}")

    # — المصدر 2: ملف محلي —
    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(username, password)
            print("🔑 تم تسجيل الدخول عبر session.json (ملف محلي)")
            return True
        except Exception as e:
            print(f"⚠️  فشل تحميل الـ session المحلي: {e}")

    return False


def _full_login(cl: Client, username: str, password: str):
    """
    تسجيل دخول كامل بالباسورد + حفظ الـ session.
    """
    print("🔐 تسجيل دخول كامل بالمعرف وكلمة المرور...")
    time.sleep(random.uniform(3, 7))   # تأخير قبل الدخول
    cl.login(username, password)
    _save_session(cl)


def _save_session(cl: Client):
    """
    حفظ الـ session في ملف محلي + طباعة JSON ليُنسخ إلى GitHub Secret.
    """
    settings = cl.get_settings()
    SESSION_FILE.write_text(
        json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    session_json = json.dumps(settings, ensure_ascii=False)
    print("\n" + "=" * 60)
    print("📋 SESSION JSON — انسخه إلى Secret: INSTAGRAM_SESSION_JSON")
    print(session_json)
    print("=" * 60 + "\n")


def post_carousel(image_paths: list, caption: str, max_retries: int = 3):
    """
    نشر كاروسيل مع:
      - إعادة استخدام الـ session لتجنب Rate Limit
      - إعادة المحاولة عند الفشل المؤقت
      - تأخيرات عشوائية لمحاكاة السلوك البشري
    """
    username = os.environ.get("INSTAGRAM_USERNAME")
    password = os.environ.get("INSTAGRAM_PASSWORD")

    if not username or not password:
        raise ValueError("❌ INSTAGRAM_USERNAME أو INSTAGRAM_PASSWORD غير موجودين في الأسرار")

    cl = _build_client()

    # — محاولة تحميل session موجود —
    session_loaded = _load_session(cl, username, password)
    if not session_loaded:
        _full_login(cl, username, password)

    # — تأخير عشوائي قبل النشر (يقلل احتمال الحظر) —
    delay = random.uniform(8, 20)
    print(f"⏳ انتظار {delay:.1f} ثانية قبل النشر...")
    time.sleep(delay)

    # — محاولات النشر مع Retry —
    for attempt in range(1, max_retries + 1):
        try:
            print(f"📤 محاولة النشر {attempt}/{max_retries}...")
            media = cl.album_upload(
                [str(p) for p in image_paths],
                caption=caption
            )
            # حفظ الـ session المحدَّث بعد النشر الناجح
            _save_session(cl)
            print(f"✅ نُشر بنجاح! Media ID: {media.pk}")
            return media

        except RateLimitError as e:
            wait = 60 * attempt   # 60 ثانية، 120، 180...
            print(f"⚠️  Rate Limit (محاولة {attempt}): {e}")
            if attempt < max_retries:
                print(f"⏳ انتظار {wait} ثانية...")
                time.sleep(wait)
            else:
                raise

        except LoginRequired:
            print("🔄 انتهت صلاحية الـ session، إعادة تسجيل الدخول...")
            _full_login(cl, username, password)
            time.sleep(random.uniform(5, 10))

        except ChallengeRequired as e:
            raise RuntimeError(
                f"❌ إنستغرام طلب تحقق (Challenge): {e}\n"
                "الحل: سجّل دخولك يدوياً مرة وأضف الـ session الجديد إلى Secret."
            )

        except ClientError as e:
            print(f"⚠️  خطأ Client (محاولة {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(30 * attempt)
            else:
                raise

        except Exception as e:
            print(f"⚠️  خطأ غير متوقع (محاولة {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(20)
            else:
                raise
