import json
from typing import List, Optional
from playwright.sync_api import Page, sync_playwright, Playwright
from contextlib import contextmanager
from datetime import datetime
from core.config import (
    BOT_STORAGE_SESSION_FOLDER,
    SUPABASE_KEY,
    SUPABASE_URL,
)
from ai_messenger import generate_comment_from_user_last_post
from pika_service import get_pika_session
from supabase import Client, create_client

# Note; username == creator and user_username == the user the bot is interacting with
TIMEOUT = 60000


@contextmanager
def run(playwright: Playwright, username: str, user_id: str):
    # start up the browser and load session if available
    chromium = playwright.firefox  # or "firefox" or "webkit".
    browser = chromium.launch(headless=False, slow_mo=3000)
    context = browser.new_context(
        storage_state=f"./{BOT_STORAGE_SESSION_FOLDER}/{username}.json"
    )
    page = context.new_page()
    try:
        yield page
    except Exception as e:
        # Save the status to db
        print(f"Browser Error - {e}")
        client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        client.table("bot_status").insert(
            {
                "creator": username,
                "bot_type": "comment",
                "status": "failed",
                "last_error": str(e),
                "last_run": datetime.now().isoformat(),
                "user": user_id,
            }
        ).execute()
    finally:
        # close browser and context
        page.close()
        context.close()
        browser.close()


def write_comment(page: Page, user_id: str):
    # generate the comment
    message, post_link = generate_comment_from_user_last_post(user_id)
    # visit the post page and leave a comment
    if not message:
        raise ValueError("Error generating comment")
    if not post_link:
        raise ValueError("Error getting post link")
    page.goto(post_link, timeout=TIMEOUT)
    page.get_by_role("textbox", name="Add a comment…").click()
    page.get_by_role("textbox", name="Add a comment…").fill(message)
    page.get_by_role("button", name="Post", exact=True).click()


def send_comment(
    username: str, user_id: str, past_creators: Optional[List[str]]
):
    with sync_playwright() as playwright:
        with run(playwright, username, user_id) as page:
            write_comment(page, user_id=user_id)
            page.wait_for_timeout(60000)

            # Save the status to db
            client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            client.table("bot_status").insert(
                {
                    "creator": username,
                    "bot_type": "comment",
                    "status": "success",
                    "last_error": None,
                    "last_run": datetime.now().isoformat(),
                    "user": user_id,
                }
            ).execute()

            # Update the user also
            if past_creators:
                past_creators.append(username)
            else:
                past_creators = [username]
            client.table("users").update(
                {
                    "last_interaction_date": datetime.now().isoformat(),
                    "past_creators": past_creators,
                }
            ).eq("user_id", user_id).execute()


def main():
    # the action to be performed when the message is received from Rabbitmq
    def callback(ch, method, properties, body: bytes):
        record_str = body.decode()
        record = json.loads(record_str)
        print(record)
        send_comment(
            username=record.get("assigned"),
            user_id=record.get("user_id"),
            past_creators=record.get("past_creators"),
        )

    # initialize pika session, queue and wait for message
    with get_pika_session() as connection:
        channel = connection.channel()
        channel.queue_declare(queue="bot")
        channel.basic_consume(
            "bot", on_message_callback=callback, auto_ack=True
        )

        channel.basic_qos(prefetch_count=1)
        channel.start_consuming()


if __name__ == "__main__":
    print("Waiting for the a record to be dispatch")
    main()
