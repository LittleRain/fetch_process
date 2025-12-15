import asyncio
import os

from playwright.async_api import async_playwright

import config


async def main():
    """
    启动一个浏览器，手动完成微博登录后，保存会话状态到 config.WEIBO_AUTH_STATE_PATH。
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(
            no_viewport=True,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            extra_http_headers={
                "Accept-Language": "zh-CN,zh;q=0.9",
            },
        )
        page = await context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )

        print("正在打开微博登录页面...")
        await page.goto("https://weibo.com/login.php")

        line_1 = "=" * 80
        line_2 = "请在弹出的浏览器窗口中，手动完成微博登录（推荐扫码），直到能正常刷到首页。"
        line_3 = "完成后，回到终端并按 Enter 继续，程序会保存当前登录态。"
        print(f"\n{line_1}\n{line_2}\n{line_3}\n{line_1}\n")

        input()
        print("检测到按键，开始保存会话状态...")

        await context.storage_state(path=config.WEIBO_AUTH_STATE_PATH)
        print(f"会话状态已保存到: {os.path.abspath(config.WEIBO_AUTH_STATE_PATH)}")

        await browser.close()
        print("浏览器已关闭。")


if __name__ == "__main__":
    asyncio.run(main())
