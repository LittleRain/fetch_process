import asyncio
from playwright.async_api import async_playwright
import config
import os

async def main():
    """
    启动一个浏览器，用户手动登录后，保存会话状态。
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--start-maximized"])
        context = await browser.new_context(no_viewport=True)
        page = await context.new_page()

        print("正在打开小红书登录页面...")
        await page.goto("https://www.xiaohongshu.com/explore")

        # 使用最简单的字符串拼接，避免任何转义问题
        line_1 = "================================================================================"
        line_2 = "请在弹出的浏览器窗口中，手动完成所有登录步骤。"
        line_3 = "包括：1. 扫码 -> 2. 输入可能出现的验证码 -> 3. 直到您看到小红书的主页。"
        line_4 = ""
        line_5 = "完成后，回到这个终端，然后按 Enter 键继续..."
        line_6 = "================================================================================"
        print(f"\n{line_1}\n{line_2}\n{line_3}\n{line_4}\n{line_5}\n{line_6}\n")

        # 程序会在这里暂停，直到您在终端按回车键
        input()

        print("\n检测到您已按键，继续执行...")

        print("正在保存会话状态...")
        await context.storage_state(path=config.XHS_AUTH_STATE_PATH)
        
        print(f"会话状态已成功保存到: {os.path.abspath(config.XHS_AUTH_STATE_PATH)}")
        
        await browser.close()
        print("浏览器已关闭。")

if __name__ == "__main__":
    if config.FEISHU_APP_ID == "在此处填入你的飞书App ID":
        print("错误：请先在 config.py 中完成您的飞书应用配置！")
    else:
        asyncio.run(main())