
from playwright.sync_api import Page, expect, sync_playwright
import time
import sys

def test_skip_link(page: Page):
    print("Starting test...")
    try:
        # 1. Arrange: Go to the app
        print("Navigating to localhost:8000...")
        page.goto("http://localhost:8000")

        # Wait for the page to load
        print("Waiting for #command-input...")
        page.wait_for_selector("#command-input")

        # 2. Act: Focus the skip link
        print("Finding skip link...")
        skip_link = page.get_by_text("Skip to main content")

        print("Focusing skip link...")
        skip_link.focus()

        # 3. Assert
        print("Asserting visibility...")
        expect(skip_link).to_be_visible()

        print("Checking landmarks...")
        main = page.locator("main#main-content")
        expect(main).to_be_visible()

        aside = page.locator("aside")
        expect(aside).to_be_visible()

        # 4. Screenshot
        print("Taking screenshot...")
        page.screenshot(path="/home/jules/verification/skip-link-focused.png")
        print("Screenshot saved.")

    except Exception as e:
        print(f"Error: {e}")
        raise e

if __name__ == "__main__":
    print("Main block running...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            test_skip_link(page)
        finally:
            browser.close()
    print("Done.")
