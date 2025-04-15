from playwright_base import PlaywrightBase
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import time
import re


class GoogleMapScraping(PlaywrightBase):

    def __init__(self, language, region, keyword_to_search):
        self.region = region
        self.keyword_to_search = keyword_to_search
        super().__init__(targets=["GoogleMap"], timeout=10000)
        self.language = language.lower()

    async def setup(self, playwright):
        await self.launch_browser(playwright)
        for area in self.region:
            context = await self.new_context()
            await self.main_scripts(context, link=True)

    async def keyword_search(self, conteext, region, keyword_to_search):
        page_id, page = self.new_page(conteext)
        map_url_for_region = f"https://www.google.com.tw/maps/place/{region}/?hl={self.language}"
        await self.direct_url(url=map_url_for_region, page_id=page_id)
        await self.get_page(page_id).wait_for_function("() => document.location.href.includes('@')")
        cur_url = await self.current_url(page_id=page_id)
        value, size = self.extract_coordinates(cur_url)
        map_url_for_search = f"https://www.google.com.tw/maps/search/{keyword_to_search}/@{value[0]},{value[1]},{size}z/?hl={self.language}"
        await self.direct_url(url=map_url_for_search, page_id=page_id)
        await self.find_element("search_list", page_id=page_id)
        await self.get_page(page_id).wait_for_function("() => document.location.href.includes('entry')")
        if int(size) > 15:
            await self.click(element="zoom_in", page_id=page_id)
        else:
            await self.click(element="zoom_out", page_id=page_id)
        await self.click(await self.wait_for_element("search_this_area", page_id=page_id))

    def extract_coordinates(self, url):
        match = re.search(r"@([0-9.]+),([0-9.]+),([0-9.]+)z", url)
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

    async def cleaner(self):
        await self.page.context.clear_cookies()
        await self.page.evaluate("window.localStorage.clear();")
        await self.page.evaluate("window.sessionStorage.clear();")

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

    async def _bottom_of_list(self):
        bottom_tips_element = await self.find_element("bottom_of_list", self.init_page_id)
        bottom_tips = await bottom_tips_element.inner_text() if bottom_tips_element else ""
        return True if "You've reached the end of the list." in bottom_tips else False

    async def search_list_scroll_to_bottom(self):
        start_time = time.time()
        bottom = False
        while not bottom:
            await self.sleep(0.5)
            await self.get_page(self.init_page_id).keyboard.press("PageDown")
            await self.click((await self.find_elements("search_list", self.init_page_id))[-1])
            bottom = await self._bottom_of_list()
            if bottom:
                print("Bottom")
            if time.time() - start_time > 60:
                print("TimeOut")
                break

    async def scapping_detail_data(self, page_id, link=True, close_share=False):
        address = await self.scraping_address(page_id)
        phone = await self.scraping_phone(page_id)
        url = await self.scraping_web_url(page_id)
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

        data = {"Store name": store_name, "URL": url, "Address": address, "Phone": phone, "Share link": share_link, "Score": score, "Expenses": expenses}

        print(data)
        return data

    async def get_all_link_from_search_result(self):
        current_url = await self.current_url(self.init_page_id)
        print("Current URL: ", current_url)
        await self.click("search_list", self.init_page_id)
        await self.search_list_scroll_to_bottom()
        store_info = await self.find_elements("search_list", self.init_page_id)
        url_list = []
        for store in store_info:
            url = await self.get_attribute(store, "href")
            url_list.append(url)
        return url_list

    async def main_scripts(self, conteext, link=True, max_concurrent_tasks=10):
        self.keyword_search(conteext)
        url_list = await self.get_all_link_from_search_result()
        semaphore = asyncio.Semaphore(max_concurrent_tasks)
        tasks = []

        async def sem_task(url):
            async with semaphore:
                pid, page = await self.new_page(conteext)
                await self.process_page(pid, url, link)

        for url in url_list:
            task = asyncio.create_task(sem_task(url))
            tasks.append(task)

        await asyncio.gather(*tasks)

    async def process_page(self, pid, url, link):
        try:
            place_id = self.extract_place_id(url)
            print(place_id)
            await self.direct_url(url=url, page_id=pid)
            await self.find_element("main_store_detail", page_id=pid)
            data = await self.scapping_detail_data(pid, link=link)
        except Exception as e:
            print(f"Error processing page {url}: {e}")
        finally:
            await self.close_page(pid)
