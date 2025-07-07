import json
import pika
from supabase import Client, create_client
from core.config import SUPABASE_KEY, SUPABASE_URL
from pika_service import get_pika_session
from datetime import timedelta, datetime
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--creator", type=str)
args = parser.parse_args()

NEXT_30_DAYS = datetime.now() + timedelta(30)


def dispatch_creator(creator: str):
    """
    Dispatch creator to cron

    """
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase.table("users")
        .select("*")
        .eq("assigned", creator)
        .or_(
            f"last_interaction_date.is.null,last_interaction_date.gt.{NEXT_30_DAYS}"
        )
        .execute()
    )
    if not response.data:
        print("No more records")

    for record in response.data:
        past_creators = record.get("past_creators")
        if (past_creators) and (creator in past_creators):
            continue
        if not record.get("last_post_link"):
            continue
        print(record)
        with get_pika_session() as connection:
            channel = connection.channel()
            channel.queue_declare(queue="bot")
            channel.basic_publish(
                exchange="",
                routing_key="bot",
                body=json.dumps(record),
                properties=pika.BasicProperties(
                    content_type="application/json"
                ),
            )
        break


if __name__ == "__main__":
    print(f"Dispatching creator {args.creator}")
    dispatch_creator(args.creator)
