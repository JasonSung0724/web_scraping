from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import random
import time
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
import pyperclip

chrome_options = Options()
chrome_options.add_argument("--disable-popup-blocking")
chrome_options.add_experimental_option("debuggerAddress", "localhost:9222")
driver = webdriver.Chrome(options=chrome_options)
# /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222
current_url = driver.current_url
print("Current URL: ", current_url)


def copy_info(item):
    ele = driver.find_elements(By.XPATH, f"//*[@aria-label='{item}']")
    data = None
    if len(ele) > 0:
        actions.click(ele[0]).perform()
        data = pyperclip.paste()
    return data


store_info = driver.find_elements(By.XPATH, '//*[@class="hfpxzc"]')
target = []
actions = ActionChains(driver)
for store in store_info:
    url = store.get_attribute("href")
    target.append(url)
for i, url in enumerate(target):
    driver.execute_script(f"window.open('{url}');")
    handles = driver.window_handles
    driver.switch_to.window(handles[-1])
    name = driver.find_element(By.XPATH, '//*[@class="a5H0ec"]/..').text
    print(name)
    address = copy_info("複製地址")
    print(address)
    web_site = copy_info("複製網站")
    print(web_site)
    phone_num = copy_info("複製電話號碼")
    print(phone_num)

    driver.close()
    driver.switch_to.window(handles[0])
    if i == 5:
        break
print(handles)
