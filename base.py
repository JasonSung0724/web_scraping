from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import json
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import ElementNotInteractableException
import pyperclip


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

    def __init__(self):
        self.timeout = 5
        chrome_options = Options()
        chrome_options.add_argument("--disable-popup-blocking")
        chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
        self.driver = webdriver.Chrome(options=chrome_options)
        self.action = ActionChains(self.driver)
        self.wait = WebDriverWait(self.driver, self.timeout, poll_frequency=0.5)
        self.element_list = self.get_elements_list()

    def __call__(self):
        return self.driver

    def _isWebElement(self, element):
        return isinstance(element, EC.WebElement)

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
        else:
            print(f"Element not found : {ele_key}")

    def web_wait(self):
        return self.wait.until(lambda d: d.execute_script("return document.readyState === 'complete' && document.body.innerHTML.trim().length > 0;"))

    def current_url(self):
        wait = "Done" if self.web_wait() else "Failed"
        url = self.driver.current_url
        print(f"\n{wait}\n{url}")
        return url

    def click(self, element):
        ele = self.find_element(element)
        try:
            ele.click()
        except (ElementClickInterceptedException, ElementNotInteractableException):
            self.action.move_to_element(ele).click().perform()
        except Exception as e:
            print(f"Click Error : {e}")

    def get_attritue(self, element, attr):
        ele = self.find_element(element)
        return ele.get_attribute(attr)

    def copy_button(self, element):
        ele = self.find_elements(element)
        data = None
        if len(ele) > 0:
            self.action.move_to_element(ele[0]).click().perform()
            data = pyperclip.paste()
        return data
