import asyncio
import httpx
from playwright.async_api import async_playwright, expect

async def run_e2e_test():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        
        # Two independent incognito contexts
        context_a = await browser.new_context()
        context_b = await browser.new_context()
        
        page_a = await context_a.new_page()
        page_b = await context_b.new_page()
        
        import time
        timestamp = int(time.time())
        user_a_email = f"normal_{timestamp}@test.com"
        user_b_email = f"medic_{timestamp}@test.com"
        campus_id_a = f"N{timestamp}"
        campus_id_b = f"M{timestamp}"

        print("=> Step 1: Sign up Normal User (Session A)")
        await page_a.goto("http://localhost:5173/signup")
        await page_a.locator('input[type="text"]').nth(0).fill("Normal User")
        await page_a.locator('input[type="text"]').nth(1).fill(campus_id_a)
        await page_a.fill('input[type="email"]', user_a_email)
        await page_a.fill('input[type="password"]', "password123")
        await page_a.select_option('select', 'NONE')
        await page_a.click('button:has-text("Create Account")')
        await expect(page_a.locator('text=Hello, Normal User')).to_be_visible(timeout=10000)
        
        print("=> Step 2: Sign up Medical User (Session B)")
        await page_b.goto("http://localhost:5173/signup")
        await page_b.locator('input[type="text"]').nth(0).fill("Medical User")
        await page_b.locator('input[type="text"]').nth(1).fill(campus_id_b)
        await page_b.fill('input[type="email"]', user_b_email)
        await page_b.fill('input[type="password"]', "password123")
        await page_b.select_option('select', 'MEDICAL')
        await page_b.click('button:has-text("Create Account")')
        await expect(page_b.locator('text=Hello, Medical User')).to_be_visible(timeout=10000)

        print("=> Step 3: Report Incident (Session A)")
        await page_a.click('text=Report an Emergency')
        await page_a.fill('textarea', "A student has collapsed near the library.")
        await page_a.fill('input[placeholder="e.g. Main Building, North Gate"]', "Main Library")
        await page_a.click('button:has-text("Submit Emergency")')
        
        print("=> Step 4: Verify AI Analyzing (Session A)")
        await expect(page_a.locator('text=Analyzing Report')).to_be_visible()
        # Wait for transition to response page
        await expect(page_a.locator('text=Help is on the way.').or_(page_a.locator('text=Updating Plan...')).or_(page_a.locator('text=Incident Resolved'))).to_be_visible(timeout=30000)
        
        # Get incident ID from URL
        url_a = page_a.url
        incident_id = url_a.split('/')[-1]
        print(f"Incident ID created: {incident_id}")
        
        print("=> Step 5: Medical Responder sees incident (Session B)")
        # In a real app, they'd get a notification or see it on dash. Let's just navigate to response page.
        await page_b.goto(f"http://localhost:5173/response/{incident_id}")
        await expect(page_b.locator('text=Help is on the way.')).to_be_visible()
        
        # In the demo app, the "Accept" and "Start" buttons are not directly visible on the ResponseInProgress page, 
        # wait, the ResponseInProgress page only has "Update Incident" and "Live Map". 
        # The user said: "Use: POST /api/incidents/{incident_id}/accept from Session B"
        # I will execute the API request for the responder directly since the frontend might not have the Responder Action buttons fully wired on this screen (the objective asked to 'Call: POST /api/incidents... from Session B').
        # I will extract the token from Session B's local storage.
        
        print("=> Step 6: Responder Accepts (API)")
        token_b = await page_b.evaluate("localStorage.getItem('token')")
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://localhost:8000/api/incidents/{incident_id}/accept", headers={"Authorization": f"Bearer {token_b}"})
            assert resp.status_code == 200
            
        print("=> Step 7: Verify UI Updates in Session A (Responder Accepted)")
        # Check timeline for the acceptance
        await expect(page_a.locator('text=Responder has accepted the assignment')).to_be_visible(timeout=10000)
        
        print("=> Step 8: Responder Starts (API)")
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://localhost:8000/api/incidents/{incident_id}/start", headers={"Authorization": f"Bearer {token_b}"})
            assert resp.status_code == 200
            
        print("=> Step 9: Verify UI Updates in Session A (Responder Dispatched)")
        await expect(page_a.locator('text=Responder is on the way')).to_be_visible(timeout=10000)
        
        print("=> Step 10: Simulate Disruption (Replanning) (API)")
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"http://localhost:8000/api/incidents/{incident_id}/simulate-disruption",
                headers={"Authorization": f"Bearer {token_b}"},
                json={"type": "ROUTE_BLOCKED", "description": "Main gate is blocked"}
            )
            assert resp.status_code == 200
            
        print("=> Step 11: Verify Replanning UI Updates in Session A")
        await expect(page_a.locator('text=AI is replanning the response')).to_be_visible(timeout=10000)
        await expect(page_a.locator('text=Updating Plan...')).to_be_visible(timeout=10000)
        # Should eventually show plan updated or changes
        
        print("=> Step 12: Responder Resolves Incident (API)")
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"http://localhost:8000/api/incidents/{incident_id}/resolve", headers={"Authorization": f"Bearer {token_b}"})
            assert resp.status_code == 200
            
        print("=> Step 13: Verify Resolution UI Updates in Session A and B")
        await expect(page_a.locator('text=Incident Resolved')).to_be_visible(timeout=10000)
        await expect(page_b.locator('text=Incident Resolved')).to_be_visible(timeout=10000)
        await expect(page_a.locator('text=The situation has been handled.')).to_be_visible(timeout=10000)
        
        print("================================")
        print("SUCCESS! Real-time WS synchronization perfectly verified across two separate sessions!")
        print("================================")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_e2e_test())
