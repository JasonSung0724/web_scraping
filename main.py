from map_scraping import GoogleMapScraping
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as browser:
        scraper = GoogleMapScraping(region=["台北信義區", "新北汐止區", "新北板橋區", "日本沖繩"], keyword_to_search=["酒吧", "火鍋"], language="en")
        await scraper.execute(playwright=browser)


if __name__ == "__main__":
    asyncio.run(main())
