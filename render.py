"""Compose the verse onto the background as an Instagram-ready 4:5 image."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

SIZE = (1080, 1350)  # Instagram portrait 4:5
MARGIN_X = 120
MAX_TEXT_HEIGHT = 820
FONTS = Path(__file__).parent / "fonts"
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (240, 226, 200)


def _font(name: str, size: int, weight: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(FONTS / name), size)
    font.set_variation_by_axes([weight])
    return font


def _wrap(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    lines, current = [], ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if font.getlength(trial) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _fit_verse(text: str, max_width: int) -> tuple[ImageFont.FreeTypeFont, list[str], int]:
    """Largest font size (within reason) at which the verse fits the text area."""
    for size in range(68, 29, -2):
        font = _font("Lora.ttf", size, 500)
        lines = _wrap(text, font, max_width)
        line_height = int(size * 1.45)
        if len(lines) * line_height <= MAX_TEXT_HEIGHT:
            return font, lines, line_height
    return font, lines, line_height


def _prepare_background(img: Image.Image) -> Image.Image:
    img = ImageOps.fit(img.convert("RGB"), SIZE, Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(1.5))
    img = ImageEnhance.Brightness(img).enhance(0.62)

    # Vignette: darken toward the edges so the centered text pops.
    width, height = SIZE
    mask = Image.new("L", SIZE, 0)
    ImageDraw.Draw(mask).ellipse((-width * 0.25, -height * 0.1, width * 1.25, height * 1.1), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(220))
    dark = Image.new("RGB", SIZE, (0, 0, 0))
    return Image.composite(img, dark, mask)


def render_post(background: Image.Image, verse: str, reference: str, handle: str | None = None) -> Image.Image:
    img = _prepare_background(background)
    width, height = SIZE
    text_layer = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(text_layer)

    font, lines, line_height = _fit_verse(verse, width - 2 * MARGIN_X)
    ref_font = _font("Montserrat.ttf", 30, 600)
    ref_text = f"{reference}  ·  NLT".upper()
    rule_gap, ref_gap = 56, 40

    block_height = (len(lines) - 1) * line_height + font.size + rule_gap + ref_gap + 30
    y = (height - block_height) // 2

    for line in lines:
        draw.text((width / 2, y), line, font=font, fill=TEXT_COLOR, anchor="ma")
        y += line_height

    y += rule_gap - line_height + font.size  # tighten the gap after the last line
    draw.line((width / 2 - 40, y, width / 2 + 40, y), fill=ACCENT_COLOR, width=2)
    y += ref_gap
    _spaced_text(draw, (width / 2, y), ref_text, ref_font, tracking=4)

    if handle:
        handle_font = _font("Montserrat.ttf", 24, 500)
        draw.text((width / 2, height - 70), handle, font=handle_font, fill=(255, 255, 255, 170), anchor="ms")

    # Soft drop shadow behind all text for legibility on bright photos.
    shadow = Image.new("RGBA", SIZE, (0, 0, 0, 0))
    shadow.putalpha(text_layer.getchannel("A").point(lambda a: int(a * 0.7)))
    shadow = shadow.filter(ImageFilter.GaussianBlur(6))

    out = img.convert("RGBA")
    out.alpha_composite(shadow, (0, 3))
    out.alpha_composite(text_layer)
    return out.convert("RGB")


def _spaced_text(draw: ImageDraw.ImageDraw, center: tuple[float, float], text: str,
                 font: ImageFont.FreeTypeFont, tracking: int) -> None:
    """Draw letter-spaced text centered at `center` (Pillow has no tracking option)."""
    total = sum(font.getlength(ch) for ch in text) + tracking * (len(text) - 1)
    x, y = center[0] - total / 2, center[1]
    for ch in text:
        draw.text((x, y), ch, font=font, fill=ACCENT_COLOR, anchor="la")
        x += font.getlength(ch) + tracking
