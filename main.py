from map_scraping import GoogleMapScraping
import asyncio
from playwright.async_api import async_playwright


async def main():
    async with async_playwright() as browser:
        scraper = GoogleMapScraping(
            region=["台北信義區", "台北中山區", "新北三重區", "新北汐止區"], keyword_to_search=["酒吧", "火鍋", "飲料", "便利商店"], language="en"
        )
        await scraper.execute(browser)


if __name__ == "__main__":
    asyncio.run(main())
