from playwright.sync_api import sync_playwright


def run():
    with sync_playwright() as p:
        # 設置 headless=False 以顯示瀏覽器窗口
        browser = p.chromium.launch(headless=False)

        num_contexts = 10
        contexts = []
        pages = []

        for i in range(num_contexts):
            context = browser.new_context()
            page = context.new_page()
            page.goto("https://example.com")
            contexts.append(context)
            pages.append(page)

        for page in pages:
            print(page.title())

        for context in contexts:
            context.close()

        browser.close()


run()
