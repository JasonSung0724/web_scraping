from map_scraping import GoogleMapScraping
import asyncio


async def main():
    scraper = GoogleMapScraping(remote=False, region="Taipei", keyword_search="Hotpot")
    await scraper.setup()
    await scraper.all_search_result_v2(link=False)
    await scraper.close()


if __name__ == "__main__":
    asyncio.run(main())
