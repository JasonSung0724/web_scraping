from playwright.async_api import async_playwright, ElementHandle
import json


class WebScrapingBase:
    def __init__(self, remote=True):
        self.timeout = 5000

        if remote:
            # Playwright 不支持 Selenium 的 remote debugging 方式
            # 需要手動設置或使用 Playwright 的其他配置
            pass

    async def base_setup(self):
        self.element_list = self.get_elements_list()
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()

    def __call__(self):
        return self.page

    async def sleep(self, sec):
        await self.page.wait_for_timeout(sec * 1000)

    async def wait_for_element(self, element, wait_except="default"):
        try:
            value = self.get_locator(element)
            if wait_except == "default":
                return await self.page.wait_for_selector(value, state="attached", timeout=self.timeout)
            elif wait_except == "visible":
                return await self.page.wait_for_selector(value, state="visible", timeout=self.timeout)
            elif wait_except == "clickable":
                return await self.page.wait_for_selector(value, state="visible", timeout=self.timeout)
            elif wait_except == "invisible":
                return await self.page.wait_for_selector(value, state="hidden", timeout=self.timeout)
        except TypeError:
            print(value)

    def get_elements_list(self):
        with open("locator.json", "r", encoding="utf-8") as f:
            ele_list = json.load(f)
        return ele_list

    def get_locator(self, ele_key):
        try:
            return self.element_list[ele_key]["value"]
        except KeyError as e:
            print(f"Element key not set yet: {e}")

    async def find_element(self, ele_key):
        if not self._is_ElementHandle(ele_key):
            value = self.get_locator(ele_key)
            return await self.page.query_selector(value)
        return ele_key

    async def find_elements(self, ele_key):
        value = self.get_locator(ele_key)
        return await self.page.query_selector_all(value)

    async def current_url(self):
        await self.page.wait_for_load_state("domcontentloaded")
        url = self.page.url
        print(f"\n{url}")
        return url

    async def click(self, element):
        if not self._is_ElementHandle(element):
            element = await self.find_element(element)
        try:
            if await element.is_visible():
                await element.click(force=True)
        except Exception as e:
            print(f"Click Error: {e}")

    async def get_attribute(self, element, attr):
        ele = await self.find_element(element)
        return await ele.get_attribute(attr)

    async def input_text(self, element, text):
        ele = await self.find_element(element)
        await ele.fill(text)

    async def close(self):
        await self.context.close()
        await self.browser.close()

    def _is_ElementHandle(self, obj):
        return isinstance(obj, ElementHandle)
