from datetime import datetime
from supabase_service import (
    get_token_if_exist,
    save_username_token,
    send_data_to_supabase,
    get_supabase_sync,
)
from concurrent.futures import ThreadPoolExecutor
from get_gender import start_gender_service
from core import config
import requests
from user_info import get_user_infos
from the_retry import retry
from exceptions_client import exceptions
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--users", type=str)
parser.add_argument("--limit", type=int)
args = parser.parse_args()


@retry(attempts=5, expected_exception=exceptions)
def get_posts(username, token, min_comments=10):
    # get the post ids and use token in available
    try:
        # Initialise the parameters needed to send the requests
        id_list = []
        url = f"https://{config.RAPID_API_INSTAGRAM_HOST}/v1/posts"
        querystring = {"username_or_id_or_url": username}
        if token:
            querystring["pagination_token"] = token
        headers = {
            "x-rapidapi-key": config.RAPID_API_KEY,
            "x-rapidapi-host": config.RAPID_API_INSTAGRAM_HOST,
        }

        # Analyse and parse the response
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        json_data = response.json()
        data = json_data.get("data", {})
        new_token = json_data.get("pagination_token", None)
        user = data.get("user", {}) if data else {}
        is_private = user.get("is_private", False) if user else False
        if is_private:
            return None
        posts = data.get("items", []) if data else []
        for p in posts:
            comment_count = p.get("comment_count", 0) if p else 0
            post_id = p.get("id", None) if p else None
            if comment_count > min_comments and post_id:
                id_list.append(post_id)

        return id_list, new_token
    except Exception as e:
        print(f"Error while getting posts: {e}")
        return None, None


@retry(attempts=5, expected_exception=exceptions)
def get_followers(username: str, token):
    # get the followers username and use token if available
    try:
        # Initialise the parameters needed to send the requests
        id_list = []
        url = f"https://{config.RAPID_API_INSTAGRAM_HOST}/v1/followers"
        querystring = {"username_or_id_or_url": username}

        if token:
            querystring["pagination_token"] = token
        headers = {
            "x-rapidapi-key": config.RAPID_API_KEY,
            "x-rapidapi-host": config.RAPID_API_INSTAGRAM_HOST,
        }

        # Analyse and parse the response
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()
        json_data = response.json()
        data = json_data.get("data", {})
        new_token = json_data.get("pagination_token", None)
        followers = data.get("items", []) if data else []
        for follower in followers:
            if not follower.get("is_private"):
                id_list.append(follower["username"])

        return id_list, new_token
    except Exception as e:
        print(f"Error while getting posts: {e}")
        return None, None


def analyse_username(username: str) -> int:
    # start the user analysis (step 2)
    gender_output = 0
    try:
        print("Starting ------------------------------------ Analysis")
        info = get_user_infos(username)
        if info:
            user_info = info["user_infos"]
            gender_output = start_gender_service(
                user_info,
                info["image_bytes"],
            )
            if gender_output == 1:
                # Save to supabase
                send_data_to_supabase(user_info)
        print(f"Gender - {gender_output}")
        print("Ending ------------------------------------ Analysis")
        return gender_output
    except Exception as e:
        print(f"Error analysing username - {e}")
        return 0


def anaylse_usernames(usernames: list[str]):
    results = []
    with ThreadPoolExecutor(max_workers=10) as worker:
        results = worker.map(analyse_username, usernames)

    return sum(results)


def main(input_list: list[str], total_results: int):
    client = get_supabase_sync()

    # Initialise the variable to use
    already_got = 0
    if input_list.count == 0:
        return None

    # starting
    job_infos = (
        client.table("scraping_status").insert({"status": "running"}).execute()
    )
    job_info = job_infos.data[0]

    # starting the iteration of the input usernames
    try:
        for index, username in enumerate(input_list):
            if already_got >= total_results:
                break
            print(
                f"*** Processing Username n* {index} : {username} | total_results_to_get: {total_results} | already_got: {already_got}"
            )
            try:
                next_for_follower = True
                while next_for_follower:
                    # Check if any token is registered for the username
                    token_next_for_follower = get_token_if_exist(username)
                    if not token_next_for_follower:
                        save_username_token(username)
                    print(
                        f"-- Before processing : username --> {username} ; token --> {token_next_for_follower}"
                    )
                    follower_list, token_next_for_follower = get_followers(
                        username, token_next_for_follower
                    )
                    if not follower_list:
                        break
                    added = anaylse_usernames(follower_list)
                    # Update the token for the username
                    save_username_token(
                        username=username, token=token_next_for_follower
                    )
                    print(f"Total added: {added}")
                    already_got += added
                    print(
                        f"** Ok - Username added | Total: {already_got}/{total_results}"
                    )
                    if already_got >= total_results:
                        next_for_follower = False
                        break

            except Exception as e:
                print(f"Error processing username {username}: {e}")
        client.table("scraping_status").update(
            {
                "id": job_info.get("id"),
                "status": "success",
                "end_time": datetime.now().isoformat(),
                "items_scraped": already_got,
            }
        ).eq("id", job_info.get("id")).execute()

    except Exception as e:
        client.table("scraping_status").update(
            {
                "id": job_info.get("id"),
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now().isoformat(),
            }
        ).eq("id", job_info.get("id")).execute()

    print("DONE!")


if __name__ == "__main__":
    users = args.users.split(";")
    print(users, args.limit)
    main(users, args.limit)
