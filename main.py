from map_scraping import GoogleMapScraping
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as p:
        scraper = GoogleMapScraping(region="Taipei", keyword_search="Hotpot")
        await scraper.setup(p)
        await scraper.all_search_result_v2(link=True)


if __name__ == "__main__":
    asyncio.run(main())
