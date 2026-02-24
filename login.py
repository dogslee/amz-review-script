import asyncio
from playwright.async_api import async_playwright

async def save_login_state():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # 必须有界面，手动登录
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
        )

        page = await context.new_page()
        await page.goto("https://www.amazon.com/gp/sign-in.html", wait_until="domcontentloaded")

        print("请在浏览器中手动完成登录，登录成功后按 Enter 继续...")
        input()

        # 保存登录状态（cookies + localStorage）
        await context.storage_state(path="amazon_state.json")
        print("✅ 登录状态已保存至 amazon_state.json")

        await browser.close()

asyncio.run(save_login_state())