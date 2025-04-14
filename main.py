from map_scraping import GoogleMapScraping


if __name__ == "__main__":
    scraper = GoogleMapScraping(remote=False, region="Taipei", keyword_search="Hotpot")
    scraper.all_search_result_v2()
