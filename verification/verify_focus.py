from playwright.sync_api import sync_playwright, expect
import time

def verify_quick_action_focus():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Navigate to the game
        page.goto("http://localhost:8000")

        # Wait for the game to load (look for specific element)
        page.wait_for_selector("#command-input", state="visible")

        # Click a quick action button (e.g., "Look Around")
        look_btn = page.locator("button[data-command='look']")
        look_btn.click()

        # Wait for a moment for the interaction to process
        time.sleep(1)

        # Verify that the command input has focus
        input_field = page.locator("#command-input")
        expect(input_field).to_be_focused()

        # Take a screenshot
        page.screenshot(path="verification/focus_check.png")
        print("Focus check verification completed successfully.")

        browser.close()

if __name__ == "__main__":
    verify_quick_action_focus()
