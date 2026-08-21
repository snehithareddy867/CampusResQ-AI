import asyncio
from playwright.async_api import async_playwright
import time

async def run_tests():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        
        context_a = await browser.new_context()
        page_a = await context_a.new_page()
        
        context_b = await browser.new_context()
        page_b = await context_b.new_page()
        
        # 1. Register User A
        print("Registering User A (Normal)...")
        await page_a.goto("http://localhost:5173/signup")
        await page_a.fill("input[type='text']", "User A")
        await page_a.locator("input[type='text']").nth(1).fill(f"CAMPUS_A_{int(time.time())}")
        await page_a.fill("input[type='email']", f"user_a_{int(time.time())}@example.com")
        await page_a.fill("input[type='password']", "password")
        await page_a.select_option("select", "NONE")
        await page_a.click("button[type='submit']")
        await page_a.wait_for_url("**/dashboard", timeout=10000)
        print("User A registered and on dashboard.")
        
        # 2. Register User B
        print("Registering User B (Medical)...")
        await page_b.goto("http://localhost:5173/signup")
        await page_b.fill("input[type='text']", "User B")
        await page_b.locator("input[type='text']").nth(1).fill(f"CAMPUS_B_{int(time.time())}")
        await page_b.fill("input[type='email']", f"user_b_{int(time.time())}@example.com")
        await page_b.fill("input[type='password']", "password")
        await page_b.select_option("select", "MEDICAL")
        await page_b.click("button[type='submit']")
        await page_b.wait_for_url("**/dashboard", timeout=10000)
        print("User B registered and on dashboard.")
        
        # 3. Report Emergency from User A
        print("User A reporting an emergency...")
        await page_a.goto("http://localhost:5173/report")
        await page_a.fill("textarea", "A student has collapsed near the library.")
        await page_a.get_by_text("Yes").click()
        await page_a.click("button:has-text('Submit Emergency')")
        
        # wait for AI Analyzing
        await page_a.wait_for_url("**/analyzing/**", timeout=10000)
        print("User A submitted emergency, AI is analyzing...")
        
        # wait for Response In Progress page
        await page_a.wait_for_url("**/response/**", timeout=30000)
        print("User A reached response page.")
        
        # get Incident ID from URL
        url_a = page_a.url
        incident_id = url_a.split('/')[-1]
        print(f"Incident ID: {incident_id}")
        
        # 4. User B (Medical) checks Dashboard
        print("Refreshing User B Dashboard...")
        await page_b.goto("http://localhost:5173/dashboard")
        await page_b.wait_for_selector(f"text={incident_id.split('-')[0]}", timeout=10000)
        print("User B sees the incident on their dashboard.")
        
        # 5. User B accepts the incident
        print("User B navigating to response page...")
        await page_b.goto(f"http://localhost:5173/response/{incident_id}")
        print("User B clicking Accept Incident...")
        await page_b.wait_for_selector("button:has-text('Accept Incident')", timeout=10000)
        await page_b.click("button:has-text('Accept Incident')")
        
        # wait for UI to update to Start Response
        print("Waiting for Start Response button...")
        await page_b.wait_for_selector("button:has-text('Start Response')", timeout=10000)
        print("User B clicking Start Response...")
        await page_b.click("button:has-text('Start Response')")
        
        # 6. Check User A's timeline
        print("Checking User A's timeline for updates...")
        # Since it's a websocket, it should update automatically
        # Look for text "RESPONDER DISPATCHED" or similar in timeline
        await page_a.wait_for_selector("text=RESPONDER_DISPATCHED", timeout=10000)
        print("User A saw RESPONDER_DISPATCHED.")
        
        # 7. Simulate Disruption
        print("Simulating Disruption via API...")
        import urllib.request
        import json
        req = urllib.request.Request(f"http://localhost:8000/api/incidents/{incident_id}/simulate-disruption", method="POST")
        req.add_header('Content-Type', 'application/json')
        body = json.dumps({"type": "ROUTE_BLOCKED", "description": "Main gate is blocked"}).encode('utf-8')
        urllib.request.urlopen(req, data=body)
        print("Disruption simulated.")
        
        # 8. Wait for Replanning on User A
        print("Waiting for REPLANNING_COMPLETED on User A...")
        await page_a.wait_for_selector("text=REPLANNING_COMPLETED", timeout=20000)
        print("User A saw REPLANNING_COMPLETED.")
        
        # 9. User B Resolves Incident
        print("User B clicking Resolve Incident...")
        await page_b.wait_for_selector("button:has-text('Resolve Incident')", timeout=10000)
        await page_b.click("button:has-text('Resolve Incident')")
        
        # 10. Check User A sees Incident Resolved
        print("Checking User A sees Incident Resolved...")
        await page_a.wait_for_selector("h1:has-text('Incident Resolved')", timeout=10000)
        print("All tests passed successfully!")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_tests())
