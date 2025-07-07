from supabase import Client, create_client
from core.config import SUPABASE_KEY, SUPABASE_URL
from datetime import timedelta, datetime
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--limit", type=int, required=True)
args = parser.parse_args()

NEXT_30_DAYS = datetime.now() + timedelta(30)
START_DATE = datetime.now()


def share_creator(creator: str, limit: int):
    """
    Share the creator among users

    """
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = (
        supabase.table("users")
        .select("*")
        .is_("assigned", "null")
        .or_(
            f"last_interaction_date.is.null,last_interaction_date.gt.{NEXT_30_DAYS}"
        )
        .execute()
    )

    global START_DATE

    start_time = START_DATE + timedelta(hours=2)

    # go through the users and assign to valid users
    added = 0
    for record in response.data:
        if added == limit:
            print("Limit reached")
            break
        past_creators = record.get("past_creators")
        if (past_creators) and (creator in past_creators):
            print("Creator has already interacted with user skipping")
            continue
        start_time += timedelta(minutes=10)
        supabase.table("users").update(
            {"assigned": creator, "scheduled_at": start_time.isoformat()}
        ).eq("id", record.get("id")).execute()
        added += 1


def main():
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    response = supabase.table("creators").select("*").execute()
    for creator in response.data:
        creator_username = creator["creator"]
        print(f"creator - {creator_username}")
        share_creator(creator_username, args.limit)


if __name__ == "__main__":
    print(args.limit + 10)
    main()
