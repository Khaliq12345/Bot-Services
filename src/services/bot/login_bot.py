from playwright.sync_api import sync_playwright, Playwright
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--username", type=str, required=True)
parser.add_argument("--folder", type=str, required=True)
args = parser.parse_args()


def run(playwright: Playwright, username: str, folder: str):
    # start up the browser
    chromium = playwright.firefox  # or "firefox" or "webkit".
    browser = chromium.launch(headless=False, slow_mo=3000)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.instagram.com/accounts/login")

    # pause the page to interact with
    page.pause()

    # save storage
    context.storage_state(path=f"{folder}/{username}.json")
    # close browser and context
    page.close()
    context.close()
    browser.close()


def main():
    with sync_playwright() as playwright:
        run(playwright, args.username, args.folder)


if __name__ == "__main__":
    main()
