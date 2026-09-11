import os
import json
import time
from pathlib import Path
from instagrapi import Client

USERNAME     = os.getenv("INSTAGRAM_USERNAME") or os.getenv("IG_USERNAME", "")
PASSWORD     = os.getenv("INSTAGRAM_PASSWORD") or os.getenv("IG_PASSWORD", "")
SESSION_DATA = os.getenv("INSTAGRAM_SESSION_JSON", "")

OUTPUT_DIR   = Path("daily_post")


def get_client() -> Client:
    cl = Client()
    cl.expose = lambda *args, **kwargs: True

    if SESSION_DATA.strip():
        try:
            session_dict = json.loads(SESSION_DATA.strip())
            cl.set_settings(session_dict)
            cl.login(USERNAME, PASSWORD)
            print("🔑 Logged in via GitHub Secret session.")
            return cl
        except Exception as e:
            print(f"⚠️ Secret session failed ({e}) — trying password login.")

    print("🔐 Logging in with username & password...")
    cl.login(USERNAME, PASSWORD)
    return cl


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
    print(f"⏳ Uploading {len(images)} slides to Instagram...")
    time.sleep(3)

    media = cl.album_upload(images, caption=caption)
    print(f"🚀 Upload complete! Media PK: {media.pk}")


if __name__ == "__main__":
    upload_daily_carousel()
