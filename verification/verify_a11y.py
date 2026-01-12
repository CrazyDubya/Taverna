import os
from playwright.sync_api import sync_playwright

def verify_a11y():
    cwd = os.getcwd()
    file_path = f"file://{cwd}/living_rusted_tankard/game/templates/enhanced_game.html"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Emulate a desktop viewport
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()

        print(f"Navigating to {file_path}")
        page.goto(file_path)

        # 1. Verify Roles
        print("Checking for 'main' role...")
        main_loc = page.get_by_role("main")
        if main_loc.count() > 0:
            print("PASS: <main> element found via role='main'.")
        else:
            print("FAIL: <main> element NOT found.")

        print("Checking for 'complementary' role (aside)...")
        aside_loc = page.get_by_role("complementary")
        if aside_loc.count() > 0:
            print("PASS: <aside> element found via role='complementary'.")
        else:
            print("FAIL: <aside> element NOT found.")

        # 2. Verify Skip Link
        print("Checking for Skip Link...")
        # It's hidden initially (sr-only)
        skip_link = page.get_by_role("link", name="Skip to Main Content")

        if skip_link.count() > 0:
            print("PASS: Skip link found in DOM.")
        else:
            print("FAIL: Skip link NOT found in DOM.")

        # 3. Verify Visuals on Focus
        # Force focus to test visibility
        print("Focusing skip link...")
        skip_link.focus()

        # Take screenshot
        screenshot_path = "verification/skip_link_focused.png"
        page.screenshot(path=screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")

        # Check if it is visible (bounding box should be non-zero and within viewport)
        box = skip_link.bounding_box()
        if box:
            print(f"Skip link bounding box: {box}")
            if box['width'] > 1 and box['height'] > 1:
                print("PASS: Skip link has dimensions when focused.")
            else:
                print("FAIL: Skip link has zero dimensions.")
        else:
            print("FAIL: Skip link has no bounding box.")

        browser.close()

if __name__ == "__main__":
    verify_a11y()
