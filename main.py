from map_scraping import GoogleMapScraping
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as browser:
        scraper = GoogleMapScraping(region=["台北信義區"], keyword_to_search=["酒吧"], language="en")
        await scraper.execute(playwright=browser)


if __name__ == "__main__":
    asyncio.run(main())
