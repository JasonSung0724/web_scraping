import asyncio
from playwright.async_api import async_playwright
import json


async def main():
    async with async_playwright() as playwright:
        b = playwright.chromium.launch(headless=False)


asyncio.run(main())
