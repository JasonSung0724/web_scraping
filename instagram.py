import asyncio
from ins_scraping import InstagramScraping
from playwright.async_api import async_playwright
from playwright_base import PlaywrightBase

async def instagram():

    async with async_playwright() as p:
        ins = InstagramScraping(user_name="goodfriends.dessert", password="Aa03092596")
        page_id = await ins.launch_login(p)
        await ins.keyword_search(keyword="___07___24", page_id=page_id)
        



        

if __name__ == "__main__":
    asyncio.run(instagram())