from base import WebScrapingBase
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
import asyncio
import time
import re


class GoogleMapScraping(WebScrapingBase):

    def __init__(self, remote, region, keyword_search):
        self.remote = remote
        self.region = region
        self.keyword_search = keyword_search
        self.base = super().__init__(remote=self.remote)

    async def setup(self):
        await self.base_setup()
        map_url_for_region = f"https://www.google.com.tw/maps/place/{self.region}/?hl=en"
        await self.page.goto(map_url_for_region)
        await self.page.wait_for_function("() => document.location.href.includes('@')")
        cur_url = self.page.url
        # value = self.extract_coordinates(cur_url)
        # map_url_for_search = f"https://www.google.com.tw/maps/search/{self.keyword_search}/@{value[0]},{value[1]},15z/?hl=en"
        # await self.page.goto(map_url_for_search)
        # await self.wait_for_element("search_list", wait_except="visible")
        # await self.page.wait_for_function("() => document.location.href.includes('entry')")
        # await self.click("zoom_out")
        # await self.click(await self.wait_for_element("search_this_area", wait_except="visible"))

    def extract_coordinates(self, url):
        match = re.search(r"@([0-9.]+),([0-9.]+)", url)
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            return [latitude, longitude]
        else:
            return None, None

    async def cleaner(self):
        await self.page.context.clear_cookies()
        await self.page.evaluate("window.localStorage.clear();")
        await self.page.evaluate("window.sessionStorage.clear();")

    async def wait_map_loaded(self):
        await asyncio.sleep(0.5)
        return await self.wait_for_element("detail_load", wait_except="invisible")

    async def scraping_web_url(self):
        url_info = await self.find_elements("copy_web")
        if url_info:
            return await self.get_attribute(url_info[0], "href")
        return None

    async def scraping_address(self):
        address_info = await self.find_element("store_address")
        if address_info:
            address = await self.get_attribute(address_info, "aria-label")
            return address
        return None

    async def scraping_phone(self):
        phone_info = await self.find_element("store_phone")
        if phone_info:
            phone_to_text = await phone_info.inner_text()
            phone_text = phone_to_text.split("\n")[1] if "\n" in phone_to_text else phone_to_text
            return phone_text
        return None

    async def close_window(self, window_name):
        if window_name == "share_window":
            await self.click("close_window")
        elif window_name == "detail_window":
            await self.click("detail_close")

    async def scraping_share_link(self, retry=True, close_share=False):
        try:
            await self.click("share_entry")
            share_link_ele = await self.wait_for_element("share_link", wait_except="visible")
            share_link = await self.get_attribute(share_link_ele, "value")
        except PlaywrightTimeoutError:
            if retry:
                share_link = await self.scraping_share_link(retry=False)
                if close_share:
                    await self.close_window("share_window")
                    await self.wait_for_element("share_window", wait_except="invisible")
            else:
                share_link = None
        return share_link

    async def access_detail(self, store, retry=True):
        try:
            await self.click(store)
            await self.wait_map_loaded()
            await self.wait_for_element("detail_layout", wait_except="visible")
            label = await self.get_attribute(store, "aria-label")
            if "· Visited link" in label:
                label = label.replace("· Visited link", "").strip()
            result = await self.page.wait_for_function(f"() => document.querySelector('store_name').innerText === '{label}'")
            if result:
                await self.close_window("detail_window")
                await self.wait_for_element("detail_layout", wait_except="invisible")
                return True
            return False
        except PlaywrightTimeoutError:
            if retry:
                return await self.access_detail(store, retry=False)

    async def _is_search_result(self):
        return await self.wait_for_element("multi_search_result", wait_except="visible")

    async def _bottom_of_list(self):
        return True if await self.find_elements("bottom_of_list") else False

    async def search_list_scroll_to_bottom(self):
        start_time = time.time()
        bottom = False
        while not bottom:
            await asyncio.sleep(0.5)
            await self.page.keyboard.press("PageDown")
            bottom = await self._bottom_of_list()
            await self.click((await self.find_elements("search_list"))[-1])
            if bottom:
                print("Bottom")
            if time.time() - start_time > 60:
                print("TimeOut")
                break

    async def scapping_detail_data(self, link=True, close_share=False):
        time.sleep(5)
        address = await self.scraping_address()
        phone = await self.scraping_phone()
        url = await self.scraping_web_url()
        share_link = await self.scraping_share_link(close_share=close_share) if link else None
        store_name = await (await self.find_element("store_name")).inner_text()
        score = await (await self.find_element("google_score")).inner_text().replace("\n", "-")
        expenses = await self.find_element("avg_expenses")
        if expenses and "\n" in (await expenses.inner_text()):
            expenses = await expenses.inner_text().split("\n")
            expenses = expenses[0] + f" ({expenses[1]})"
        data = {"Store name": store_name, "URL": url, "Address": address, "Phone": phone, "Share link": share_link, "Score": score, "expenses": expenses}
        print(data)
        return data

    async def all_search_result(self, link=True):
        current_url = await self.current_url()
        print("Current URL: ", current_url)
        store_info = await self.find_elements("search_list")
        for store in store_info:
            try:
                await self.access_detail(store)
                await self.scapping_detail_data(link=link)
            except PlaywrightTimeoutError as e:
                print(f"Error : {e}")
                continue

    async def get_all_link_from_search_result(self):
        current_url = await self.current_url()
        print("Current URL: ", current_url)
        await self.click("search_list")
        await self.search_list_scroll_to_bottom()
        store_info = await self.find_elements("search_list")
        url_list = []
        for store in store_info:
            url = await self.get_attribute(store, "href")
            url_list.append(url)
        return url_list

    async def all_search_result_v2(self, link=True):
        # url_list = await self.get_all_link_from_search_result()
        url_list = [
            "https://www.google.com.tw/maps/place/Delectable+Hot+Pot+Lab/data=!4m7!3m6!1s0x3442a9432d6aea2b:0xbe19f9bab838e633!8m2!3d25.0425391!4d121.5046305!16s%2Fg%2F11h4nb92xx!19sChIJK-pqLUOpQjQRM-Y4uLr5Gb4?authuser=0&hl=en&rclk=1",
            "https://www.google.com.tw/maps/place/Xin+Xin+Hot+Pot+-+Ximen+Branch/data=!4m7!3m6!1s0x3442a9cb2d8d6363:0x4ea54c0d44dcbf62!8m2!3d25.0435258!4d121.5031485!16s%2Fg%2F11rg3q6gjd!19sChIJY2ONLcupQjQRYr_cRA1MpU4?authuser=0&hl=en&rclk=1",
        ]
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            tasks = []
            for url in url_list:
                context = await browser.new_context()
                page = await context.new_page()

                # 將每個上下文的操作作為一個獨立的任務
                task = asyncio.create_task(self.process_page(context, page, url, link))
                tasks.append(task)

            # 等待所有任務完成
            await asyncio.gather(*tasks)

    async def process_page(self, context, page, url, link):
        try:
            await page.goto(url)
            await page.wait_for_function("() => document.readyState === 'complete'")
            await page.wait_for_selector("main_store_detail", state="visible")

            # 確保 scapping_detail_data 是異步的
            await self.scapping_detail_data(page, link=link)
        except Exception as e:
            print(f"Error processing page {url}: {e}")
        finally:
            await page.close()
            await context.close()
