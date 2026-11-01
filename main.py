"""Daily NLT scripture post for Instagram.

    python main.py render  [--date YYYY-MM-DD]                -> posts/<date>.jpg + posts/<date>.json
    python main.py publish [--date YYYY-MM-DD] --image-url URL -> posts the rendered image to Instagram
    python main.py refresh-token                              -> prints a refreshed Instagram token

Settings come from environment variables (GitHub secrets/variables in the workflow):
    NLT_API_KEY          free key from https://api.nlt.to (falls back to the rate-limited demo key)
    UNSPLASH_ACCESS_KEY  free key from https://unsplash.com/developers (falls back to gradients)
    IG_USER_ID, IG_ACCESS_TOKEN   Instagram API credentials (publish only)
    TIMEZONE             decides what "today" is, e.g. America/Chicago (default America/New_York)
    IG_HANDLE            optional, printed small at the bottom of the image
    HASHTAGS             optional, overrides the default hashtags
"""

import argparse
from datetime import date, datetime
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from background import get_background
from render import SIZE, render_post
import instagram
import scripture

POSTS_DIR = Path(__file__).parent / "posts"
DEFAULT_HASHTAGS = "#dailyverse #bibleverse #scripture #NLT #faith #jesus #christian #godisgood"
NLT_CREDIT = (
    "Scripture quotations are taken from the Holy Bible, New Living Translation, "
    "copyright ©1996, 2004, 2015 by Tyndale House Foundation. Used by permission of "
    "Tyndale House Publishers, Carol Stream, Illinois 60188. All rights reserved."
)


def today() -> date:
    return datetime.now(ZoneInfo(os.environ.get("TIMEZONE") or "America/New_York")).date()


def build_caption(verse: str, reference: str, photo_credit: str | None) -> str:
    parts = [f"{verse}\n— {reference} (NLT)", os.environ.get("HASHTAGS") or DEFAULT_HASHTAGS, NLT_CREDIT]
    if photo_credit:
        parts.append(photo_credit)
    return "\n\n".join(parts)


def render(day: date) -> Path:
    reference = scripture.reference_for(day)
    verse = scripture.fetch_nlt(reference, os.environ.get("NLT_API_KEY") or "TEST")
    print(f"{day}: {reference} — {verse}")

    background = get_background(day, SIZE, os.environ.get("UNSPLASH_ACCESS_KEY"))
    image = render_post(background.image, verse, reference, os.environ.get("IG_HANDLE"))

    POSTS_DIR.mkdir(exist_ok=True)
    image_path = POSTS_DIR / f"{day}.jpg"
    image.save(image_path, "JPEG", quality=92, optimize=True)
    meta = {
        "date": str(day),
        "reference": reference,
        "verse": verse,
        "photo_credit": background.credit,
        "caption": build_caption(verse, reference, background.credit),
        "media_id": None,
    }
    (POSTS_DIR / f"{day}.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Saved {image_path}")
    return image_path


def publish(day: date, image_url: str) -> None:
    meta_path = POSTS_DIR / f"{day}.json"
    meta = json.loads(meta_path.read_text())
    if meta.get("media_id"):
        print(f"Already posted for {day} (media {meta['media_id']}); skipping.")
        return
    # strip(): pasted secrets often carry a stray space or newline
    media_id = instagram.publish_image(
        os.environ["IG_USER_ID"].strip(), os.environ["IG_ACCESS_TOKEN"].strip(), image_url, meta["caption"]
    )
    meta["media_id"] = media_id
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    print(f"Published {day} to Instagram: media {media_id}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["render", "publish", "already-posted", "refresh-token"])
    parser.add_argument("--date", help="YYYY-MM-DD (default: today in TIMEZONE)")
    parser.add_argument("--image-url", help="public URL of the rendered JPEG (publish only)")
    args = parser.parse_args()
    day = date.fromisoformat(args.date) if args.date else today()

    if args.command == "render":
        render(day)
    elif args.command == "publish":
        if not args.image_url:
            parser.error("publish needs --image-url")
        publish(day, args.image_url)
    elif args.command == "already-posted":
        meta_path = POSTS_DIR / f"{day}.json"
        posted = meta_path.exists() and bool(json.loads(meta_path.read_text()).get("media_id"))
        print("true" if posted else "false")
    elif args.command == "refresh-token":
        print(instagram.refresh_token(os.environ["IG_ACCESS_TOKEN"].strip()))


if __name__ == "__main__":
    main()
