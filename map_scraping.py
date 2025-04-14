from base import WebScrapingBase
from selenium.common.exceptions import TimeoutException, NoSuchAttributeException
import time
import re


class GoogleMapScraping(WebScrapingBase):

    def __init__(self, remote, region, keyword_search):
        super().__init__(remote=remote)
        map_url_for_region = f"https://www.google.com.tw/maps/place/{region}/?hl=en"
        self.driver.get(map_url_for_region)
        self.web_wait()
        self.wait.until(lambda x: "@" in self.driver.current_url)
        cur_url = self.driver.current_url
        value = self.extract_coordinates(cur_url)
        map_url_for_search = f"https://www.google.com.tw/maps/search/{keyword_search}/@{value[0]},{value[1]},15z/?hl=en"
        self.driver.get(map_url_for_search)
        self.wait_for_element("search_list", wait_except="visible")
        self.wait.until(lambda x: "entry" in self.driver.current_url)
        self.click("zoom_out")
        self.click(self.wait_for_element("search_this_area", wait_except="visible"))

    def extract_coordinates(self, url):
        match = re.search(r"@([0-9.]+),([0-9.]+)", url)
        if match:
            latitude = match.group(1)
            longitude = match.group(2)
            return [latitude, longitude]
        else:
            return None, None

    def cleaner(self):
        self.driver.delete_all_cookies()
        self.driver.execute_script("window.localStorage.clear();")
        self.driver.execute_script("window.sessionStorage.clear();")

    def wait_map_loaded(self):
        self.sleep(0.5)
        return self.wait_for_element("detail_load", wait_except="invisible")

    def scraping_web_url(self):
        url_info = self.find_elements("copy_web")
        if url_info:
            return self.get_attritue(url_info[0], "href")
        return None

    def scraping_address(self):
        address_info = self.find_elements("store_address")
        if address_info:
            address = self.get_attritue(address_info[0], "aria-label")
            return address
        return None

    def scraping_phone(self):
        phone_info = self.find_element("store_phone")
        if phone_info:
            phone_to_text = phone_info.text
            phone_text = phone_to_text.split("\n")[1] if "\n" in phone_to_text else phone_to_text
            return phone_text
        return None

    def close_window(self, window_name):
        if window_name == "share_window":
            self.click("close_window")
        elif window_name == "detail_window":
            self.click("detail_close")

    def scraping_share_link(self, retry=True, close_share=False):
        try:
            self.click("share_entry", action_click=True)
            share_link_ele = self.wait_for_element("share_link", wait_except="visible")
            share_link = self.get_attritue(share_link_ele, "value")
        except (TimeoutException, NoSuchAttributeException):
            if retry:
                share_link = self.scraping_share_link(retry=False)
                if close_share:
                    self.close_window("share_window")
                    self.wait_for_element("share_window", wait_except="invisible")
            else:
                share_link = None
        return share_link

    def access_detail(self, store, retry=True):
        try:
            self.click(store, scroll_view=True, action_click=False)
            self.wait_map_loaded()
            self.wait_for_element("detail_layout", wait_except="visible")
            label = self.get_attritue(store, "aria-label")
            if "· Visited link" in label:
                label = label.replace("· Visited link", "").strip()
            result = self.wait.until(lambda d: label == self.find_element("store_name").text)
            if result:
                self.close_window("detail_window")
                self.wait_for_element("detail_layout", wait_except="invisible")
                return True
            return False
        except (TimeoutException, NoSuchAttributeException):
            if retry:
                return self.access_detail(store, retry=False)

    def _is_search_result(self):
        return self.wait_for_element("multi_search_result", wait_except="visible")

    def _bottom_of_list(self):
        return True if self.find_elements("bottom_of_list") else False

    def search_list_scroll_to_bottom(self):
        start_time = time.time()
        bottom = False
        while not bottom:
            self.keybord(key="page_down")
            bottom = self._bottom_of_list()
            self.click(self.find_elements("search_list")[-1])
            if bottom:
                print("Bottom")
            if time.time() - start_time > 60:
                print("TimeOut")
                break

    def scapping_detail_data(self, link=True, close_share=False):
        address = self.scraping_address()
        phone = self.scraping_phone()
        url = self.scraping_web_url()
        share_link = self.scraping_share_link(close_share=close_share) if link else None
        store_name = self.find_element("store_name").text
        score = self.find_element("google_score").text.replace("\n", "-")
        expenses = self.find_element("avg_expenses")
        if expenses and "\n" in expenses.text:
            expenses = expenses.text.split("\n")
            expenses = expenses[0] + f" ({expenses[1]})"
        data = {"Store name": store_name, "URL": url, "Address": address, "Phone": phone, "Share link": share_link, "Score": score, "expenses": expenses}
        print(data)
        return data

    def all_search_result(self, link=True):
        current_url = self.current_url()
        print("Current URL: ", current_url)
        store_info = self.find_elements("search_list")
        for store in store_info:
            try:
                self.access_detail(store)
                self.scapping_detail_data(link=link)
            except (TimeoutException, NoSuchAttributeException) as e:
                print(f"Error : {e}")
                continue

    def get_all_link_from_search_result(self):
        current_url = self.current_url()
        print("Current URL: ", current_url)
        self.click(self.find_elements("search_list", single=True))
        self.search_list_scroll_to_bottom()
        store_info = self.find_elements("search_list")
        url_list = []
        for store in store_info:
            url = self.get_attritue(store, "href")
            url_list.append(url)
        return url_list

    def all_search_result_v2(self, link=True):
        url_list = self.get_all_link_from_search_result()
        for url in url_list:
            self.cleaner()
            self.driver.execute_script("window.open('');")
            window_handles = self.driver.window_handles
            self.driver.switch_to.window(window_handles[-1])
            self.driver.get(url)
            self.web_wait()
            self.wait_for_element("main_store_detail", wait_except="visible")
            self.scapping_detail_data(link=link, close_share=False)
            self.driver.close()
            self.driver.switch_to.window(window_handles[0])
