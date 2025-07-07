from typing import Tuple, Optional
import httpx
from model import Comment
from core import config
from google import genai
from google.genai import types

client = genai.Client(api_key=config.GEMINI_API_KEY)


def image_to_bytes(image_url: str) -> bytes | None:
    """
    Convert image into bytes
    """
    response = httpx.get(image_url)
    if response.status_code == 200:
        image_data = response.content
        return image_data
    else:
        return None


def get_last_post(user_id: str) -> tuple[bytes, str] | tuple[None, None]:
    """
    Get the instagram latest post of a user

    :param user_id: user_id of the creator
    """
    url = f"https://{config.RAPID_API_INSTAGRAM_HOST}/v1/posts"
    querystring = {"username_or_id_or_url": user_id}
    headers = {
        "x-rapidapi-key": config.RAPID_API_KEY,
        "x-rapidapi-host": config.RAPID_API_INSTAGRAM_HOST,
    }

    # create an async client to send a requests to the rapid api
    with httpx.Client() as session:
        response = session.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        json_data = response.json()
        post_data = json_data.get("data", {})
        posts = post_data.get("items", [])
        for post in posts:
            if post.get("is_pinned") or post.get("is_video"):
                continue
            post_id = post.get("code")
            # published_at = post.get("taken_at_date", None)
            post_url = f"https://www.instagram.com/p/{post_id}/"
            image_versions = post.get("image_versions", {})
            if not image_versions:
                continue
            image_items = image_versions.get("items", [])
            if not image_items:
                continue
            image_url = None
            for image_item in image_items:
                image_url = image_item.get("url")
            if not image_url:
                continue
            image_bytes = image_to_bytes(image_url)
            if not image_bytes:
                continue
            return image_bytes, post_url
    return None, None


def generate_comment_from_user_last_post(
    user_id: str,
) -> Tuple[Optional[str], Optional[str]]:
    image_bytes, post_link = get_last_post(user_id)
    if not image_bytes:
        return None, None
    image = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            "Return a messaage that I can send as a comment, I want something cute and flirty",
            image,
        ],
        config={
            "response_mime_type": "application/json",
            "response_schema": Comment,
        },
    )

    parsed = response.parsed
    if not parsed:
        return None, None
    return parsed.message, post_link
