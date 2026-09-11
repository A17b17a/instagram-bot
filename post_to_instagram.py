import os
import json
import time
from pathlib import Path
from instagrapi import Client

USERNAME     = os.getenv("INSTAGRAM_USERNAME") or os.getenv("IG_USERNAME", "")
PASSWORD     = os.getenv("INSTAGRAM_PASSWORD") or os.getenv("IG_PASSWORD", "")
SESSION_DATA = os.getenv("INSTAGRAM_SESSION_JSON", "")

OUTPUT_DIR   = Path("daily_post")
SESSION_FILE = Path("ig_session.json")


def get_client() -> Client:
    cl = Client()
    
    # تعطيل رابط QE Expose المعطل من إنستغرام لمنع خطأ 404
    cl.expose = lambda *args, **kwargs: True

    # 1️⃣ استخدام الجلسة من GitHub Secret
    if SESSION_DATA.strip():
        try:
            session_dict = json.loads(SESSION_DATA.strip())
            cl.set_settings(session_dict)
            cl.login(USERNAME, PASSWORD)
            print("🔑 Logged in via GitHub Secret session.")
            return cl
        except Exception as e:
            print(f"⚠️ Secret session failed ({e}) — trying local session or password.")

    # 2️⃣ استخدام ملف الجلسة المحلي (إذا كان غير فارغ)
    if SESSION_FILE.exists() and SESSION_FILE.stat().st_size > 0:
        try:
            cl.load_settings(SESSION_FILE)
            cl.login(USERNAME, PASSWORD)
            print(f"🔑 Logged in via {SESSION_FILE}.")
            return cl
        except Exception as e:
            print(f"⚠️ Local session failed ({e}) — trying password login.")

    # 3️⃣ تسجيل الدخول بكلمة السر واسم المستخدم
    print("🔐 Logging in with username & password...")
    cl.login(USERNAME, PASSWORD)
    return cl


def save_session(cl: Client):
    try:
        session_dict = cl.get_settings()
        SESSION_FILE.write_text(
            json.dumps(session_dict, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        print(f"💾 Session saved → {SESSION_FILE}")
    except Exception as e:
        print(f"⚠️ Could not save session: {e}")


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
    print(f"⏳ Uploading {len(images)} slides to Instagram (Carousel only)…")
    time.sleep(3)

    media = cl.album_upload(images, caption=caption)
    print(f"🚀 Upload complete! Media PK: {media.pk}")

    # حفظ الجلسة المحدثة للاستخدام المستقبلي
    save_session(cl)


if __name__ == "__main__":
    upload_daily_carousel()
