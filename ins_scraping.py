from playwright_base import PlaywrightBase
import asyncio
import cv2
import numpy as np

class InstagramScraping(PlaywrightBase):

    def __init__(self, user_name, password):
        super().__init__(targets=["Instagram"], timeout=1000 * 60 * 2)
        self.user_name = user_name
        self.password = password
        self.language = "/?hl=en"
        self.homepage_url = "https://www.instagram.com"
        self.login_state = {}

    def get_url(self, route=None):
        return self.homepage_url + (route or "") + self.language

    async def launch_login(self, playwright):
        await self.launch_browser(playwright)
        context = await self.new_context()
        page_id = await self.new_page(context)
        await self.direct_url(url=self.get_url(), page_id=page_id)
        account = await self.find_element(ele_name="account_input", page_id=page_id)
        password = await self.find_element(ele_name="password_input", page_id=page_id)
        await self.input_text(account, self.user_name, page_id=page_id)
        await self.input_text(password, self.password, page_id=page_id)
        await self.click("submit", page_id=page_id)
        await self.wait_for_network(page_id=page_id)
        await self.direct_url(url=self.get_url(route="/"+self.user_name), page_id=page_id)
        await self.check_login_state(page_id=page_id)
        return page_id
    
    async def check_login_state(self, page_id):
        side_menu = await self.wait_for_element("side_menu", page_id=page_id)
        self.login_state[page_id] = True if side_menu else False

    async def keyword_search(self, keyword, page_id):
        await self.click("sider_search_icon", page_id=page_id)
        await self.input_text(element=await self.wait_for_element("search_input", page_id=page_id), text=keyword)
        await self.wait_for_network(page_id=page_id)
        await self.find_elements("search_result")
        


    

    