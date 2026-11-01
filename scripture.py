"""Pick the day's verse and fetch its NLT text from Tyndale's NLT API (api.nlt.to)."""

from datetime import date
from html.parser import HTMLParser
from pathlib import Path
import re

import requests

VERSES_FILE = Path(__file__).parent / "verses.txt"
NLT_API_URL = "https://api.nlt.to/api/passages"

# Elements in the API's HTML that aren't part of the verse text itself.
SKIP_CLASSES = {"vn", "a-tn", "tn", "chapter-number", "subhead", "psa-title", "bk_ch_vs_header"}
SKIP_TAGS = {"h2", "h3", "h4", "head", "title"}
VOID_TAGS = {"br", "link", "meta", "img", "hr", "wbr"}  # never get an end tag


def load_references() -> list[str]:
    lines = VERSES_FILE.read_text().splitlines()
    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def reference_for(day: date) -> str:
    """Line N of verses.txt is used on day N of the year."""
    refs = load_references()
    return refs[(day.timetuple().tm_yday - 1) % len(refs)]


class _VerseTextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0  # >0 while inside an element we're skipping
        self.small_caps_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in VOID_TAGS:
            if tag == "br" and not self.skip_depth:
                self.parts.append(" ")
            return
        classes = set((dict(attrs).get("class") or "").split())
        if self.skip_depth:
            self.skip_depth += 1
        elif tag in SKIP_TAGS or classes & SKIP_CLASSES:
            self.skip_depth = 1
        elif "sc" in classes:
            self.small_caps_depth += 1
        if tag == "p" and not self.skip_depth:
            self.parts.append(" ")  # poetry lines are separate <p>s

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        if self.skip_depth:
            self.skip_depth -= 1
        elif self.small_caps_depth and tag == "span":
            self.small_caps_depth -= 1

    def handle_data(self, data):
        if self.skip_depth:
            return
        # The NLT prints "LORD" (God's name) in small caps; render it as all caps.
        self.parts.append(data.upper() if self.small_caps_depth else data)


def parse_passage_html(html: str) -> str:
    parser = _VerseTextParser()
    parser.feed(html)
    text = re.sub(r"\s+", " ", "".join(parser.parts)).strip()
    text = re.sub(r"\s+([,.;:!?’”])", r"\1", text)
    return balance_quotes(text)


def balance_quotes(text: str) -> str:
    """A passage can start or end mid-speech (e.g. John 3:16), leaving a lone “ or ”."""
    opens, closes = text.count("“"), text.count("”")
    if opens > closes:
        text += "”"
    elif closes > opens:
        text = "“" + text
    return text


def fetch_nlt(reference: str, api_key: str) -> str:
    resp = requests.get(
        NLT_API_URL,
        params={"ref": reference, "version": "NLT", "key": api_key},
        timeout=30,
    )
    resp.raise_for_status()
    text = parse_passage_html(resp.text)
    if not text:
        raise RuntimeError(f"NLT API returned no text for {reference!r}")
    return text
