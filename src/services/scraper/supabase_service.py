from supabase import create_client
from core.config import SUPABASE_KEY, SUPABASE_URL


def get_supabase_sync():
    # Initialize the Supabase Sync client
    return create_client(supabase_url=SUPABASE_URL, supabase_key=SUPABASE_KEY)


def send_data_to_supabase(user_info: dict):
    # Send to supabase
    supabase = get_supabase_sync()
    supabase.table("users").upsert(
        {
            "user_id": user_info["user_id"],
            "username": user_info["username"],
            "full_name": user_info["full_name"],
            "profile_link": user_info["profile_link"],
        }
    ).execute()


def get_token_if_exist(username: str) -> str | None:
    supabase = get_supabase_sync()
    token = None
    table_response = (
        supabase.table("scraping_tracker")
        .select("token")
        .eq("username", username)
        .execute()
    )
    table_data = table_response.data
    if table_data:
        token = table_data[0].get("token")
    return token


def save_username_token(username: str, token: str | None = None):
    supabase = get_supabase_sync()
    if not token:
        supabase.table("scraping_tracker").insert(
            {"username": username, "token": token}
        ).execute()
    else:
        supabase.table("scraping_tracker").update({"token": token}).eq(
            "username", username
        ).execute()
