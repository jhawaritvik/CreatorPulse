
from playwright.sync_api import sync_playwright, expect

def run_verification(playwright):
    browser = playwright.chromium.launch(headless=True)
    context = browser.new_context()
    page = context.new_page()

    try:
        # 1. Navigate to the login page and log in
        page.goto("http://localhost:3000/login")
        page.get_by_label("Email").fill("test@example.com")
        page.get_by_label("Password").fill("password")
        page.get_by_role("button", name="Login").click()

        # 2. Wait for navigation to the dashboard and go to the newsletter page
        expect(page).to_have_url("http://localhost:3000/dashboard")
        page.goto("http://localhost:3000/newsletter")

        # 3. Create a new newsletter
        page.get_by_role("button", name="Create New").click()
        page.get_by_label("Newsletter Title").fill("Test Newsletter")
        page.get_by_label("Newsletter Content").fill("This is a test newsletter.")
        page.get_by_role("button", name="Send Newsletter").click()

        # 4. Select a client and send the newsletter
        page.get_by_label("Select Recipients").check()
        page.get_by_role("button", name="Send Newsletter").click()

        # 5. Take a screenshot of the success message
        expect(page.get_by_text("Newsletter sent successfully")).to_be_visible()
        page.screenshot(path="jules-scratch/verification/verification.png")

    finally:
        browser.close()

with sync_playwright() as playwright:
    run_verification(playwright)
