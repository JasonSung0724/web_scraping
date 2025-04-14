from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
import time
from selenium.webdriver.common.keys import Keys
from urllib.parse import urlparse, parse_qs


class WebScrapingBase:

    # For mac os
    # open chrome with remote debugging port
    # open terminal and run the following command:
    # /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222

    # For windows
    # open chrome with remote debugging port
    # open cmd and run the following command:
    # 'cd C:\Program Files\Google\Chrome\Application'
    # 'chrome.exe --remote-debugging-port=9222 --user-data-dir="C:\selenium\NewProfile"'

    def __init__(self, remote=True):
        self.timeout = 5
        self.element_list = self.get_elements_list()
        if remote:
            chrome_options = Options()
            chrome_options.add_argument("--disable-popup-blocking")
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
            self.driver = webdriver.Chrome(options=chrome_options)
        else:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service)
        self.action = ActionChains(self.driver)
        self.wait = WebDriverWait(self.driver, self.timeout, poll_frequency=0.5)

    def __call__(self):
        return self.driver

    def _isWebElement(self, element):
        return isinstance(element, EC.WebElement)

    def sleep(self, sec):
        time.sleep(sec)

    def wait_for_element(self, element, wait_except="default"):
        if self._isWebElement(element):
            return element
        ele_locator = self.get_locator(element)
        method, value = self.find_method(ele_locator)
        if wait_except == "default":
            return self.wait.until(EC.presence_of_element_located((method, value)))
        elif wait_except == "visible":
            return self.wait.until(EC.visibility_of_element_located((method, value)))
        elif wait_except == "clickable":
            return self.wait.until(EC.element_to_be_clickable((method, value)))
        elif wait_except == "invisible":
            return self.wait.until(EC.invisibility_of_element_located((method, value)))

    def find_method(self, element_dict):
        method = element_dict.get("method", "xpath")
        value = element_dict.get("value", None)
        if method == "id":
            return By.ID, value
        elif method == "xpath":
            return By.XPATH, value
        elif method == "css":
            return By.CSS_SELECTOR, value
        elif method == "name":
            return By.NAME, value
        elif method == "class":
            return By.CLASS_NAME, value

    def get_elements_list(self):
        with open("locator.json", "r", encoding="utf-8") as f:
            ele_list = json.load(f)
        return ele_list

    def get_locator(self, ele_key):
        try:
            return self.element_list[ele_key]
        except KeyError as e:
            print(f"Element key not set yet: {e} ")

    def find_element(self, ele_key):
        return self.find_elements(ele_key, single=True)

    def find_elements(self, ele_key, single=False):
        if self._isWebElement(ele_key):
            return ele_key
        ele_locator = self.get_locator(ele_key)
        method, value = self.find_method(ele_locator)
        element = self.driver.find_elements(method, value)
        if len(element) > 0:
            if single:
                return element[0]
            return element
        return None

    def web_wait(self):
        return self.wait.until(lambda d: d.execute_script("return document.readyState === 'complete' && document.body.innerHTML.trim().length > 0;"))

    def current_url(self):
        wait = "Done" if self.web_wait() else "Failed"
        url = self.driver.current_url
        print(f"\n{wait}\n{url}")
        return url

    def click(self, element, action_click=False, scroll_view=False):
        ele = self.find_element(element)
        try:
            self.wait_for_element(ele, wait_except="clickable")
            if scroll_view:
                self.driver.execute_script("arguments[0].scrollIntoView();", ele)
            if action_click:
                return self.action.move_to_element(ele).click().perform()
            ele.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.action.move_to_element(ele).click().perform()
        except Exception as e:
            print(f"Click Error : {e}")

    def get_attritue(self, element, attr):
        ele = self.find_element(element)
        return ele.get_attribute(attr)

    def keybord(self, key):
        if "page_down" == key:
            self.action.send_keys(Keys.PAGE_DOWN).perform()
        elif "enter" == key:
            self.action.send_keys(Keys.ENTER).perform()

    def input_text(self, element, text):
        ele = self.find_element(element)
        ele.clear()
        ele.send_keys(text)
