from typing import List, Optional, Tuple
from google.genai import types
from google import genai
from pydantic import BaseModel
from core import config
import requests
from dateparser import parse
from the_retry import retry
from exceptions_client import exceptions

client = genai.Client(api_key=config.GEMINI_API_KEY)


# model
class IsMale(BaseModel):
    is_male: bool


# Define system prompt
system_prompt = """
You are an analytical assistant tasked with determining if an image depicts a male person based on visual cues and provided textual information (name, bio).
Use the bio to identify explicit gender indicators (e.g., pronouns like 'he/him', 'she/her', or direct statements like 'I am a man').
If the bio is ambiguous, make a best-effort judgment based on the image, but prioritize textual evidence.
If the bio contains 'promo,' 'crypto,' 'bot,' 'giveaway,' 'follow for,' or any spam account words, return False.
Exclude usernames with lots of numbers, spam phrases, or foreign text; return False if something like that shows up.
Return only 'True' if the person is male, or 'False' if not, with no additional text.
"""


# Define user prompt
def user_prompt(full_name: str, bio: str, country: str):
    return f"""
        Analyze the provided image to determine if it depicts a male person. 
        Use the following name, and bio to inform your decision, prioritizing explicit gender indicators in the bio:
        Name: {full_name}
        Bio: {bio}
        Return 'True' if the person is male and country is valid, 'False' if not.
    """


@retry(attempts=2, backoff=5)
def generate_gender(img_bytes: bytes, full_name: str, bio: str, country: str):
    print("Using LLM to generate gender")
    # Prepare content
    content = [
        types.Part.from_bytes(
            data=img_bytes,
            mime_type="image/jpeg",
        ),
        user_prompt(full_name, bio, country),
    ]

    # generate the gender
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=content,
        config={
            "response_mime_type": "application/json",
            "response_schema": IsMale,
            "system_instruction": system_prompt,
        },
    )
    if response.parsed:
        return response.parsed.is_male  # type: ignore


@retry(attempts=5, backoff=5, expected_exception=exceptions)
def get_username_last_post_date(
    username: str,
) -> Tuple[Optional[str], Optional[str]]:
    print("Getting the date of user last post date")
    # initialise the parameter and variables needed for the requests
    url = f"https://{config.RAPID_API_INSTAGRAM_HOST}/v1/posts"

    querystring = {"username_or_id_or_url": username}

    headers = {
        "x-rapidapi-key": config.RAPID_API_KEY,
        "x-rapidapi-host": config.RAPID_API_INSTAGRAM_HOST,
    }

    # send the requests and parse the response
    response = requests.get(url, headers=headers, params=querystring)
    response.raise_for_status()
    json_data = response.json()
    post_data = json_data.get("data", {})
    post_link = None
    last_post_date = None
    if post_data:
        posts: List[dict] | None = post_data.get("items") if post_data else []
        if not posts:
            return last_post_date, post_link
        for post in posts:
            if post.get("is_pinned"):
                continue
            try:
                last_post_date = (
                    post["caption"]["created_at_utc"] if posts else None
                )
                post_code = post.get("code")
                post_link = (
                    f"https://www.instagram.com/{username}/p/{post_code}"
                )
            except Exception:
                last_post_date = None
                post_link = None
            parsed_date = parse(str(last_post_date)) if last_post_date else None
            last_post_date = parsed_date.isoformat() if parsed_date else None
            return last_post_date, post_link
    return None, None


def start_gender_service(user_info: dict, img_bytes: bytes) -> int:
    print("Starting Gender service")
    # get the gender
    gender = generate_gender(
        img_bytes,
        user_info["full_name"],
        user_info["bio"],
        user_info["country"],
    )
    # validate gender and get last post date
    print(f"Gender - {gender}")
    if gender:
        return 1
    return 0
