"""Publish an image post via the Instagram API with Instagram Login (graph.instagram.com)."""

import time

import requests

GRAPH = "https://graph.instagram.com/v23.0"


def _check(resp: requests.Response) -> dict:
    data = resp.json()
    if resp.status_code >= 400 or "error" in data:
        raise RuntimeError(f"Instagram API error: {data.get('error', data)}")
    return data


def publish_image(user_id: str, token: str, image_url: str, caption: str) -> str:
    """Create a media container from a public JPEG URL, wait for it, then publish. Returns the media id."""
    container = _check(requests.post(
        f"{GRAPH}/{user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=60,
    ))["id"]

    for _ in range(30):
        status = _check(requests.get(
            f"{GRAPH}/{container}",
            params={"fields": "status_code,status", "access_token": token},
            timeout=30,
        ))
        if status.get("status_code") == "FINISHED":
            break
        if status.get("status_code") in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"Instagram could not process the image: {status}")
        time.sleep(5)
    else:
        raise RuntimeError("Timed out waiting for Instagram to process the image")

    return _check(requests.post(
        f"{GRAPH}/{user_id}/media_publish",
        data={"creation_id": container, "access_token": token},
        timeout=60,
    ))["id"]


def refresh_token(token: str) -> str:
    """Long-lived tokens last 60 days; refreshing returns a new one good for another 60."""
    return _check(requests.get(
        "https://graph.instagram.com/refresh_access_token",
        params={"grant_type": "ig_refresh_token", "access_token": token},
        timeout=30,
    ))["access_token"]
