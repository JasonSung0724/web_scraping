from playwright.async_api import async_playwright, ElementHandle
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import json
import time
import asyncio


class PlaywrightBase:
    def __init__(self, targets: list, timeout=5000):
        self.timeout = timeout
        self.browser = None
        self.contexts = []
        self.pages = {}
        self.locator_dict = self.fetch_locator(targets)

    def fetch_locator(self, targets):
        self.locator_dict = {}
        for item in targets:
            with open(f"{item}_locator.json", "r", encoding="utf-8") as f:
                locator = json.load(f)
            self.locator_dict.update(locator)
        return self.locator_dict

    def get_page(self, page_id):
        return self.pages[str(page_id)]

    async def launch_browser(self, playwright):
        if not self.browser:
            self.browser = await playwright.chromium.launch(headless=False)
        return self.browser

    async def new_context(self, session=None):
        context = await self.browser.new_context(storage_state=session)
        self.contexts.append(context)
        return context

    async def new_page(self, context):
        page = await context.new_page()
        page_id = id(page)
        self.pages.update({str(page_id): page})
        return page_id
    
    async def reload(self, page_id):
        await self.get_page(page_id).reload()
        await self.wait_for_network(page_id=page_id)

    async def clear_context_cookie(self, context):
        await context.clear_cookies()

    def remove_page_by_id(self, page_id):
        del self.pages[str(page_id)]

    async def close_page(self, page_id):
        await self.get_page(page_id=page_id).close()
        self.remove_page_by_id(page_id)

    async def close_browser(self):
        await self.browser.close()

    async def sleep(self, sec):
        return await asyncio.sleep(sec)

    def get_locator(self, ele_key):
        try:
            return self.locator_dict[ele_key]["value"]
        except KeyError as e:
            print(f"Element key not set yet: {e}")

    def _is_ElementHandle(self, obj):
        return isinstance(obj, ElementHandle)

    async def find_element(self, ele_name, page_id=None):
        if not self._is_ElementHandle(ele_name):
            value = self.get_locator(ele_name)
            return await self.get_page(page_id=page_id).query_selector(value)
        return ele_name

    async def find_elements(self, ele_name, page_id):
        value = self.get_locator(ele_name)
        return await self.get_page(page_id=page_id).query_selector_all(value)

    async def wait_for_element(self, element, page_id, timeout=None, wait_except="visible"):
        try:
            timeout = timeout if timeout else self.timeout
            value = self.get_locator(element)
            element = await self.get_page(page_id).wait_for_selector(value, state=wait_except, timeout=timeout)
            return element
        except PlaywrightTimeoutError:
            print(f"Wait for element timeout : {element}")
            return None

    async def wait_for_element_state(self, element, page_id, wait_except="default"):
        if not self._is_ElementHandle(element):
            element = await self.find_element(element, page_id=page_id)
        if wait_except == "visible":
            return await element.wait_for_element_state("visible")
        elif wait_except == "hidden":
            return await element.wait_for_element_state("hidden")
        elif wait_except == "stable":
            return await element.wait_for_element_state("stable")
        elif wait_except == "enabled":
            return await element.wait_for_element_state("enabled")
        elif wait_except == "disab  led":
            return await element.wait_for_element_state("disabled")

    async def input_text(self, element, text, page_id=None):
        if not self._is_ElementHandle(element):
            element = await self.find_element(element, page_id=page_id)
        await element.fill(text)

    async def get_attribute(self, element, attr, page_id=None):
        if not self._is_ElementHandle(element):
            element = await self.find_element(element, page_id=page_id)
        return await element.get_attribute(attr)

    async def click(self, element, page_id=None):
        if not self._is_ElementHandle(element):
            element = await self.find_element(element, page_id)
        try:
            if element is not None:
                await element.click(force=True)
                return element
        except Exception as e:
            print(f"Click Error: {e}")
            return None

    async def current_url(self, page_id):
        url = self.get_page(page_id=page_id).url
        return url

    async def direct_url(self, url, page_id):
        await self.get_page(page_id=page_id).goto(url)
        await self.get_page(page_id=page_id).wait_for_load_state("domcontentloaded")

    async def wait_for_network(self, page_id):
        await self.get_page(page_id=page_id).wait_for_load_state('networkidle')
