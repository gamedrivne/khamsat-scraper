import asyncio
from playwright.async_api import async_playwright

async def scrape_khamsat_designing():
    url = "https://khamsat.com/designing"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)

        await page.wait_for_selector(".gig-card")

        services = await page.query_selector_all(".gig-card")

        results = []

        for service in services:
            title = await service.query_selector_eval(".gig-card-title", "el => el.innerText.trim()") if await service.query_selector(".gig-card-title") else None
            price = await service.query_selector_eval(".gig-card-price span", "el => el.innerText.trim()") if await service.query_selector(".gig-card-price span") else None
            seller = await service.query_selector_eval(".username", "el => el.innerText.trim()") if await service.query_selector(".username") else None
            rating = await service.query_selector_eval(".gig-rating", "el => el.innerText.trim()") if await service.query_selector(".gig-rating") else None
            link = await service.query_selector_eval("a", "el => el.href") if await service.query_selector("a") else None

            results.append({
                "title": title,
                "price": price,
                "seller": seller,
                "rating": rating,
                "link": link
            })

        await browser.close()
        return results


async def main():
    data = await scrape_khamsat_designing()
    print("---- SCRAPED SERVICES ----")
    for d in data:
        print(d)

if __name__ == "__main__":
    asyncio.run(main())
