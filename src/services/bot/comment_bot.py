import os
import json
from typing import List, Optional
from playwright.sync_api import Page, sync_playwright, Playwright
from contextlib import contextmanager
from datetime import datetime
from core.config import (
    SUPABASE_KEY,
    SUPABASE_URL,
)
from ai_messenger import generate_comment_from_user_last_post
from pika_service import get_pika_session
from supabase import Client, create_client
from argparse import ArgumentParser
from datetime import datetime

parser = ArgumentParser()
parser.add_argument("--headless", action="store_true")
args = parser.parse_args()

# Note; username == creator and user_username == the user the bot is interacting with
TIMEOUT = 60000


@contextmanager
def run(
    playwright: Playwright, username: str, user_id: str, bot_status_id: int
):
    # start up the browser and load session if available
    chromium = playwright.firefox  # or "firefox" or "webkit".
    browser = chromium.launch(slow_mo=3000, headless=args.headless)
    unique_id = int(datetime.now().timestamp())

    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    with open(f"{unique_id}.json", "wb+") as f:
        response = client.storage.from_("sessions").download(f"{username}.json")
        f.write(response)

    context = browser.new_context(storage_state=f"./{unique_id}.json")
    os.remove(f"{unique_id}.json")

    # Save storage state into the file.
    context.storage_state(path=f"{unique_id}_new.json")

    page = context.new_page()
    try:
        yield page
    except Exception as e:
        # Save the status to db
        print(f"Browser Error - {e}")
        client.table("bot_status").update(
            {
                "status": "failed",
                "last_error": str(e),
                "last_run": datetime.now().isoformat(),
            }
        ).eq("id", bot_status_id).execute()
        client.table("users").update(
            {
                "last_interaction_date": datetime.now().isoformat(),
            }
        ).eq("user_id", user_id).execute()
    finally:
        # close browser and context
        page.close()
        context.close()
        browser.close()

        # save to supabase
        with open(f"./{unique_id}_new.json", "rb") as f:
            (
                client.storage.from_("sessions").upload(
                    file=f,
                    path=f"{username}.json",
                    file_options={"cache-control": "3600", "upsert": "true"},
                )
            )

        # remove file from storage
        os.remove(f"{unique_id}_new.json")


def write_comment(page: Page, user_id: str) -> Optional[str]:
    # generate the comment
    message, post_link = generate_comment_from_user_last_post(user_id)
    print(f"Comment generated -> {message}")
    # visit the post page and leave a comment
    if not message:
        return None
    if not post_link:
        raise ValueError("Error getting post link")
    page.goto(post_link, timeout=TIMEOUT)
    print("Post Page Loaded")
    page.get_by_role("textbox", name="Add a comment…").click()
    page.get_by_role("textbox", name="Add a comment…").fill(message)
    page.get_by_role("button", name="Post", exact=True).click()
    print("Done commenting")
    return post_link


def send_comment(
    username: str, user_id: str, past_creators: Optional[List[str]]
):
    client: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

    # show that bot is running
    response = (
        client.table("bot_status")
        .insert(
            {
                "creator": username,
                "bot_type": "comment",
                "status": "running",
                "user": user_id,
            }
        )
        .execute()
    )
    bot_status = response.data[0]
    with sync_playwright() as playwright:
        with run(playwright, username, user_id, bot_status["id"]) as page:
            post_link = write_comment(page, user_id=user_id)
            page.wait_for_timeout(60000)

            # Save the status to db
            client.table("bot_status").update(
                {
                    "status": "success",
                    "last_error": None,
                    "last_run": datetime.now().isoformat(),
                    "post_link": post_link,
                }
            ).eq("id", bot_status["id"]).execute()

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
            print("SUCCESS")


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
    print(args.headless, "headless")
    main()
