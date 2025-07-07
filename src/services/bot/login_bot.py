from playwright.sync_api import sync_playwright, Playwright
from core.config import BOT_STORAGE_SESSION_FOLDER


def run(playwright: Playwright, email: str, password: str, username: str):
    # start up the browser
    chromium = playwright.firefox  # or "firefox" or "webkit".
    browser = chromium.launch(headless=False, slow_mo=3000)
    context = browser.new_context()
    page = context.new_page()

    page.goto("https://www.instagram.com/accounts/login")

    # pause the page to interact with
    page.pause()

    # save storage
    context.storage_state(
        path=f"./{BOT_STORAGE_SESSION_FOLDER}/{username}.json"
    )
    # close browser and context
    page.close()
    context.close()
    browser.close()


def main(email: str, password: str, username: str):
    with sync_playwright() as playwright:
        run(playwright, email, password, username)


if __name__ == "__main__":
    email = "khaliqsalawoudeen@gmail.com"
    password = "Khaleeq-instagram12345$"
    username = "khaliq"
    main(email, password, username)
