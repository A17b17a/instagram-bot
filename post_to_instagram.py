import os
import json
import time
from pathlib import Path
from instagrapi import Client

USERNAME     = os.getenv("INSTAGRAM_USERNAME")
PASSWORD     = os.getenv("INSTAGRAM_PASSWORD")
SESSION_DATA = os.getenv("INSTAGRAM_SESSION_JSON")

OUTPUT_DIR   = Path("daily_post")
SESSION_FILE = Path("session.json")


# ─────────────────────────────────────────────────────────────
# تسجيل الدخول
# ─────────────────────────────────────────────────────────────
def get_client() -> Client:
    """
    أولوية:
    1. SESSION من GitHub Secret  (أسرع + أكثر أماناً من CAPTCHA)
    2. session.json محلي         (للتطوير على الحاسوب)
    3. تسجيل دخول بالباسورد      (آخر خيار)
    """
    cl = Client()
    
    # تعطيل رابط QE Expose القديم لتجنب خطأ 404
    cl.expose = lambda *args, **kwargs: True

    if SESSION_DATA:
        try:
            cl.set_settings(json.loads(SESSION_DATA))
            cl.login(USERNAME, PASSWORD)
            print("🔑 Logged in via GitHub Secret session.")
            return cl
        except Exception as e:
            print(f"⚠️  Secret session failed ({e}) — trying password login.")

    if SESSION_FILE.exists():
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            print("🔑 Logged in via local session.json.")
            return cl
        except Exception as e:
            print(f"⚠️  Local session failed ({e}) — trying password login.")

    print("🔐 Logging in with username & password...")
    cl.login(USERNAME, PASSWORD)
    return cl


# ─────────────────────────────────────────────────────────────
# حفظ الـ session في ملف (يلتقطه الـ workflow لاحقاً)
# ─────────────────────────────────────────────────────────────
def save_session(cl: Client):
    session_dict = cl.get_settings()
    SESSION_FILE.write_text(
        json.dumps(session_dict, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"💾 Session saved → {SESSION_FILE}")


# ─────────────────────────────────────────────────────────────
# النشر الرئيسي
# ─────────────────────────────────────────────────────────────
def upload_daily_carousel():
    if not USERNAME or not PASSWORD:
        raise ValueError("❌ INSTAGRAM_USERNAME or INSTAGRAM_PASSWORD not set!")

    cl = get_client()

    images = sorted(str(p) for p in OUTPUT_DIR.glob("slide_*.png"))
    caption_path = OUTPUT_DIR / "caption.txt"

    if not images:
        raise FileNotFoundError("❌ No slide_*.png found in daily_post/")
    if not caption_path.exists():
        raise FileNotFoundError("❌ caption.txt not found in daily_post/")

    caption = caption_path.read_text(encoding="utf-8")
    print(f"⏳ Uploading {len(images)} slides to Instagram…")
    time.sleep(3)   # تأخير بسيط لتفادي rate-limit

    media = cl.album_upload(images, caption=caption)
    print(f"🚀 Upload complete! Media PK: {media.pk}")

    # احفظ الـ session المحدَّث ليلتقطه الـ workflow
    save_session(cl)


if name == "main":
    upload_daily_carousel()
