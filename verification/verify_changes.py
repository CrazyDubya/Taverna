from playwright.sync_api import sync_playwright

def verify_changes():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # We need to serve the file directly or mock the server if we can't run it
        # Since I can't guarantee the server run, I'll load the HTML file directly.
        # But wait, it's a template, so it might need rendering.
        # However, checking the file `enhanced_game.html`, it looks mostly static except for some potential Jinja2 blocks (but I didn't see any obvious ones in the read_file output).
        # Ah, I see `{% ... %}` is NOT in the read_file output I got earlier. Let me check again.
        # The file content I read earlier seemed to be pure HTML with some script tags.
        # Let's double check if there are jinja tags.

        # Load the file
        import os
        cwd = os.getcwd()
        filepath = f"file://{cwd}/living_rusted_tankard/game/templates/enhanced_game.html"

        page.goto(filepath)

        # 1. Verify "Skip to Main Content" link
        skip_link = page.get_by_role("link", name="Skip to main content")

        # It should be present
        if skip_link.count() > 0:
            print("SUCCESS: Skip link found")
        else:
            print("FAILURE: Skip link not found")

        # It should be visually hidden initially (sr-only class)
        # We can check if it has the class
        if "sr-only" in skip_link.get_attribute("class"):
             print("SUCCESS: Skip link has sr-only class")
        else:
             print("FAILURE: Skip link missing sr-only class")

        # Focus it to see if it becomes visible (this is hard to check with properties, but we can take a screenshot)
        skip_link.focus()
        page.screenshot(path="verification/skip_link_focused.png")
        print("Screenshot taken of focused skip link")

        # 2. Verify Submit Button Spinner
        # We need to trigger the showLoading function
        # We can execute JS
        page.evaluate("window.gameInterface.showLoading(true)")

        submit_btn = page.locator("#submit-btn")

        # Check if spinner SVG is present
        if submit_btn.locator("svg.animate-spin").count() > 0:
            print("SUCCESS: Spinner found in submit button")
        else:
             print("FAILURE: Spinner not found in submit button")

        page.screenshot(path="verification/spinner_shown.png")
        print("Screenshot taken of spinner")

        # Restore
        page.evaluate("window.gameInterface.showLoading(false)")
        # Check if text is back
        if "Send" in submit_btn.text_content() or "→" in submit_btn.text_content():
             print("SUCCESS: Submit button text restored")
        else:
             print("FAILURE: Submit button text not restored")

        browser.close()

if __name__ == "__main__":
    verify_changes()
