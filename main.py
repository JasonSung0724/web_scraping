from map_scraping import GoogleMapScraping
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        scraper = GoogleMapScraping(region="Taipei", keyword_search="停車場", language="en")
        await scraper.setup(p)
        await scraper.scripts(link=True)


if __name__ == "__main__":
    asyncio.run(main())
