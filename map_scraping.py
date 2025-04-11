from selenium.webdriver.common.by import By
from base import WebScrapingBase
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait


def scraping_web_url():
    url_info = driver.find_elements("copy_web")
    if url_info:
        return driver.get_attritue(url_info[0], "href")
    return None


def scraping_address():
    address_info = driver.find_elements("store_address")
    if address_info:
        address = driver.get_attritue(address_info[0], "aria-label")
        return address
    return None


def scraping_phone():
    phone_info = driver.find_elements("store_phone")
    if phone_info:
        phone = phone_info[0].text
        return phone
    return None


if __name__ == "__main__":
    driver = WebScrapingBase()
    current_url = driver.current_url()
    print("Current URL: ", current_url)
    store_info = driver.find_elements("search_list")
    for store in store_info:
        driver.click(store)
        driver.web_wait()
        label = driver.get_attritue(store, "aria-label")
        driver.wait.until(lambda d: label == driver.find_element("store_name").text)
        address = scraping_address()
        phone = scraping_phone()
        url = scraping_web_url()
        print(f"\nStore name : {label}")
        print(f"URL : {url}")
        print(f"Address : {address}")
        print(f"Phone : {phone}")
