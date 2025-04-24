from playwright_base import PlaywrightBase
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import time
import re
import json


class GoogleMapScraping(PlaywrightBase):

    def __init__(self, language, region, keyword_to_search, need_share_link=True):
        self.region = region
        self.keyword_to_search = keyword_to_search
        super().__init__(targets=["GoogleMap"], timeout=1000 * 60 * 2)
        self.language = language.lower()
        self.need_share_link = need_share_link
        self.data_list = []

    async def execute(self, playwright, scraping_method="v1"):
        await self.launch_browser(playwright)
        semaphore = asyncio.Semaphore(5)

        async def run_task(region, keyword):
            async with semaphore:
                context = await self.new_context()
                try:
                    if scraping_method == "v1":
                        await self.main_scripts(context, link=self.need_share_link, keyword=keyword, region=region)
                finally:
                    await context.close()

        tasks = [run_task(region, keyword) for region in self.region for keyword in self.keyword_to_search]
        await asyncio.gather(*tasks)

    async def keyword_search(self, context, region, keyword):
        page_id = await self.new_page(context)
        map_url_for_region = f"https://www.google.com.tw/maps/place/{region}/?hl={self.language}"
        await self.direct_url(url=map_url_for_region, page_id=page_id)
        await self.get_page(page_id).wait_for_function("() => document.location.href.includes('@')")
        value, size = await self.extract_coordinates(page_id)
        map_url_for_search = f"https://www.google.com.tw/maps/search/{keyword}/@{value[0]},{value[1]},{size}z/?hl={self.language}"
        await self.direct_url(url=map_url_for_search, page_id=page_id)
        await self.find_element("search_list", page_id=page_id)
        await self.get_page(page_id).wait_for_function("() => document.location.href.includes('entry')")
        if int(size) > 15:
            await self.click(element="zoom_in", page_id=page_id)
        else:
            await self.click(element="zoom_out", page_id=page_id)
        await self.click(await self.wait_for_element("search_this_area", page_id=page_id))
        return page_id

    async def extract_coordinates(self, page_id):
        await self.get_page(page_id).wait_for_function("() => document.location.href.includes('@')")
        cur_url = await self.current_url(page_id=page_id)
        match = re.search(r"@([0-9.]+),([0-9.]+),([0-9.]+)z", cur_url)
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            size = match.group(3)
            return [latitude, longitude], size
        else:
            return None, None

    def extract_place_id(self, url):
        try:
            start = url.index("!1s") + 3
            end = url.index("!", start)
            place_id = url[start:end]
            return place_id
        except ValueError:
            return None

    async def scraping_web_url(self, page_id):
        url_info = await self.find_element("web_site", page_id=page_id)
        if url_info:
            return await self.get_attribute(url_info, "href")
        return None

    async def scraping_address(self, page_id):
        address_info = await self.find_element("store_address", page_id=page_id)
        if address_info:
            address = await self.get_attribute(address_info, "aria-label")
            return address
        return None

    async def scraping_phone(self, page_id):
        phone_info = await self.find_element("store_phone", page_id=page_id)
        if phone_info:
            phone_to_text = await phone_info.inner_text()
            phone_text = phone_to_text.split("\n")[1] if "\n" in phone_to_text else phone_to_text
            return phone_text
        return None

    async def close_window(self, window_name, page_id):
        if window_name == "share_window":
            await self.click("close_window", page_id)
        elif window_name == "detail_window":
            await self.click("detail_close", page_id)

    async def scraping_share_link(self, page_id, retry=True, close_share=False):
        try:
            await self.click("action_share_entry", page_id=page_id)
            share_link_ele = await self.wait_for_element("share_link", page_id=page_id, wait_except="visible")
            share_link = await self.get_attribute(share_link_ele, "value")
        except PlaywrightTimeoutError:
            if retry:
                share_link = await self.scraping_share_link(retry=False, page_id=page_id)
                if close_share:
                    await self.close_window("share_window", page_id=page_id)
            else:
                share_link = None
        return share_link

    async def _bottom_of_list(self, page_id):
        bottom_tips_element = await self.find_element("bottom_of_list", page_id)
        bottom_tips = await bottom_tips_element.inner_text() if bottom_tips_element else ""
        return True if "You've reached the end of the list." in bottom_tips else False

    async def search_list_scroll_to_bottom(self, page_id):
        start_time = time.time()
        bottom = False
        while not bottom:
            await self.sleep(0.5)
            await self.get_page(page_id).keyboard.press("PageDown")
            await self.click((await self.find_elements("search_list", page_id))[-1])
            bottom = await self._bottom_of_list(page_id)
            if bottom:
                print("Bottom")
            if time.time() - start_time > 60:
                print("TimeOut")
                break

    async def scapping_detail_data(self, page_id, link=True, close_share=False):
        coordinates = await self.extract_coordinates(page_id)
        address = await self.scraping_address(page_id)
        phone = await self.scraping_phone(page_id)
        web_site_url = await self.scraping_web_url(page_id)
        share_link = await self.scraping_share_link(close_share=close_share, page_id=page_id) if link else None
        store_name_element = await self.find_element("store_name", page_id)
        store_name = await store_name_element.inner_text() if store_name_element else None
        google_score_element = await self.find_element("google_score", page_id)
        score = (await google_score_element.inner_text()).replace("\n", "-") if google_score_element else None
        expenses_element = await self.find_element("avg_expenses", page_id)
        expenses_text = await expenses_element.inner_text() if expenses_element else None
        if expenses_text and "\n" in expenses_text:
            expenses_parts = expenses_text.split("\n")
            expenses = expenses_parts[0] + f" ({expenses_parts[1]})"
        else:
            expenses = expenses_text

        data = {
            "Store name": store_name,
            "URL": web_site_url,
            "Coordinates": coordinates,
            "Address": address,
            "Phone": phone,
            "Share link": share_link,
            "Score": score,
            "Expenses": expenses,
        }

        print(data)
        return data

    async def get_all_element_for_search_result(self, page_id):
        await self.search_list_scroll_to_bottom(page_id)
        search_result_element = await self.find_elements("search_list", page_id)
        return search_result_element

    async def get_all_link_from_search_result(self, page_id):
        current_url = await self.current_url(page_id)
        print("Current URL: ", current_url)
        await self.click("search_list", page_id)
        await self.search_list_scroll_to_bottom(page_id)
        store_info = await self.find_elements("search_list", page_id)
        url_list = []
        for store in store_info:
            url = await self.get_attribute(store, "href")
            url_list.append(url)
        return url_list

    async def main_scripts(self, context, region, keyword, link=True, max_concurrent_tasks=10):
        page_id = await self.keyword_search(context=context, region=region, keyword=keyword)
        url_list = await self.get_all_link_from_search_result(page_id)
        await self.clear_context_cookie(context)
        semaphore = asyncio.Semaphore(max_concurrent_tasks)
        tasks = []

        async def sem_task(url):
            async with semaphore:
                pid = await self.new_page(context)
                await self.process_page(pid, url, link)

        for url in url_list:
            task = asyncio.create_task(sem_task(url))
            tasks.append(task)

        await asyncio.gather(*tasks)
        await self.save_to_json()
        await context.close()

    async def process_page(self, pid, url, link):
        try:
            place_id = self.extract_place_id(url)
            await self.direct_url(url=url, page_id=pid)
            await self.find_element("main_store_detail", page_id=pid)
            data = await self.scapping_detail_data(pid, link=link)
            self.data_list.append(data)
        except Exception as e:
            print(f"Error processing page {url}: {e}")
        finally:
            await self.close_page(pid)

    async def save_to_json(self):
        try:
            with open("output.json", "w", encoding="utf-8") as f:
                json.dump(self.data_list, f, ensure_ascii=False, indent=4)
            print("Data saved to output.json")
        except Exception as e:
            print(f"Error saving data to JSON: {e}")
