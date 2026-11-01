"""Get a background photo from Unsplash, with a generated gradient as a fallback."""

from dataclasses import dataclass
from datetime import date
from io import BytesIO
import random

from PIL import Image, ImageDraw, ImageFilter
import requests

UNSPLASH_API = "https://api.unsplash.com"
UTM = "utm_source=daily_scripture&utm_medium=referral"

# Rotated by day so the feed has variety.
SEARCH_TERMS = [
    "mountain sunrise",
    "calm ocean",
    "forest light",
    "clouds sky",
    "mountain lake",
    "wheat field",
    "starry night sky",
    "misty hills",
    "waterfall",
    "desert dunes",
    "meadow flowers",
    "sunset horizon",
]


@dataclass
class Background:
    image: Image.Image
    credit: str | None = None  # e.g. "Photo by Jane Doe on Unsplash"


def unsplash_photo(day: date, access_key: str, size: tuple[int, int]) -> Background:
    headers = {"Authorization": f"Client-ID {access_key}", "Accept-Version": "v1"}
    query = SEARCH_TERMS[day.toordinal() % len(SEARCH_TERMS)]
    resp = requests.get(
        f"{UNSPLASH_API}/photos/random",
        params={"query": query, "orientation": "portrait", "content_filter": "high"},
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    photo = resp.json()

    width, height = size
    img_url = f"{photo['urls']['raw']}&w={width}&h={height}&fit=crop&crop=entropy&fm=jpg&q=90"
    img = requests.get(img_url, timeout=60)
    img.raise_for_status()

    # Unsplash API guidelines: report a download whenever a photo is used.
    requests.get(photo["links"]["download_location"], headers=headers, timeout=30)

    user = photo["user"]
    credit = f"Photo by {user['name']} (@{user['username']}) on Unsplash"
    return Background(Image.open(BytesIO(img.content)).convert("RGB"), credit)


def gradient(day: date, size: tuple[int, int]) -> Background:
    """Soft two-color diagonal gradient with a light grain."""
    palettes = [
        ((24, 40, 72), (196, 120, 92)),
        ((18, 52, 59), (112, 160, 140)),
        ((44, 30, 70), (214, 160, 110)),
        ((20, 30, 48), (90, 120, 170)),
        ((60, 36, 40), (220, 170, 120)),
    ]
    rng = random.Random(day.toordinal())
    top, bottom = palettes[day.toordinal() % len(palettes)]
    width, height = size

    small = Image.new("RGB", (2, 2))
    small.putdata([top, top, bottom, bottom] if rng.random() < 0.5 else [top, bottom, top, bottom])
    img = small.resize(size, Image.BICUBIC)

    noise = Image.effect_noise(size, 18).convert("RGB")
    img = Image.blend(img, noise, 0.04)

    glow = Image.new("L", size, 0)
    ImageDraw.Draw(glow).ellipse(
        (width * 0.1, height * 0.15, width * 0.9, height * 0.75), fill=60
    )
    glow = glow.filter(ImageFilter.GaussianBlur(width // 5))
    img.paste(Image.new("RGB", size, (255, 240, 220)), mask=glow)
    return Background(img)


def get_background(day: date, size: tuple[int, int], unsplash_key: str | None) -> Background:
    if unsplash_key:
        try:
            return unsplash_photo(day, unsplash_key, size)
        except Exception as exc:  # never miss a day because of the photo
            print(f"Unsplash failed ({exc}); using a generated gradient instead.")
    return gradient(day, size)
