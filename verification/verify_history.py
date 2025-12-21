from playwright.sync_api import Page, expect, sync_playwright

def verify_command_history(page: Page):
    """
    Verifies that the command history items are rendered as buttons and are accessible.
    """
    # 1. Arrange: Go to the game page.
    # Note: The server must be running.
    page.goto("http://localhost:8000/")

    # Wait for the game to load (look for the input field)
    command_input = page.get_by_placeholder("What would you like to do?")
    expect(command_input).to_be_visible(timeout=10000)

    # 2. Act: Submit a command to populate history.
    command_input.fill("look around")

    # Submit using the button to ensure it works
    submit_btn = page.get_by_label("Send command")
    submit_btn.click()

    # Wait for the response (narrative content updates)
    # We can just wait a bit or look for the command echo in the narrative
    expect(page.locator("#narrative-content")).to_contain_text("> look around")

    # 3. Act: Open the history panel.
    history_toggle = page.get_by_text("Command History")
    history_toggle.click()

    # 4. Assert: Check if the history item is a button.
    # The history list should now be visible
    history_panel = page.locator("#command-history-panel")
    expect(history_panel).to_be_visible()

    # Find the button with the command text
    history_item = history_panel.get_by_role("button", name="look around")

    # Check if it exists and is visible
    expect(history_item).to_be_visible()

    # Verify aria-label
    expect(history_item).to_have_attribute("aria-label", "Reuse command: look around")

    # 5. Act: Click the history item to reuse it.
    history_item.click()

    # 6. Assert: Check if the input is populated and panel is hidden.
    expect(command_input).to_have_value("look around")
    expect(history_panel).to_be_hidden()

    # Check focus - this is hard to verify with Playwright's expect(page).to_have_focus() sometimes in headless,
    # but we can try checking if the active element is the input.
    # evaluate_handle returns a JSHandle, we can check its id.
    is_focused = page.evaluate("document.activeElement === document.getElementById('command-input')")
    assert is_focused, "Focus should be returned to command input"

    # 7. Screenshot
    # Let's open the history again to take a screenshot of the accessible buttons
    history_toggle.click()
    page.screenshot(path="/home/jules/verification/history_verification.png")

if __name__ == "__main__":
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            verify_command_history(page)
            print("Verification successful!")
        except Exception as e:
            print(f"Verification failed: {e}")
            page.screenshot(path="/home/jules/verification/failure.png")
            raise
        finally:
            browser.close()
