import asyncio
import os
import random
from playwright.async_api import async_playwright, APIRequestContext

import config
from xhs_scraper import XhsScraper
from feishu_client import FeishuClient
from scrapers.wechat.scraper import WeChatArticleScraper

async def main():
    """主函数，编排整个爬取和写入流程"""
    print("====== 开始执行小红书笔记抓取任务 ======")

    # 1. 检查登录会话文件是否存在
    if not os.path.exists(config.XHS_AUTH_STATE_PATH):
        print(f"错误：未找到会话文件 {config.XHS_AUTH_STATE_PATH}。")
        print("请先运行 python login_helper.py 进行手动登录以生成会话文件。")
        return

    async with async_playwright() as p:
        # 创建一个统一的异步网络请求上下文
        request_context = await p.request.new_context()
        
        # 初始化飞书客户端，并传入网络上下文
        try:
            feishu_client = FeishuClient(request_context)
        except Exception as e:
            print(f"初始化飞书客户端失败: {e}")
            await request_context.dispose()
            return

        # 启动浏览器：本地默认有头，服务器/CI可通过 XHS_HEADLESS 切换
        browser = await p.chromium.launch(
            headless=config.XHS_HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        # 加载保存的会话状态，并模拟桌面端环境
        context = await browser.new_context(
            storage_state=config.XHS_AUTH_STATE_PATH,
            no_viewport=True,
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        )
        
        scraper = XhsScraper(context)
        wechat_scraper = WeChatArticleScraper(context)

        try:
            # 2. 检查登录状态是否有效
            if not await scraper.check_login_status():
                print("错误：小红书登录状态已失效。")
                print("请重新运行 python login_helper.py 更新会话文件。")
                return

            # 3. 读取任务并执行（支持不同渠道写入不同表格）
            summary_counts = {}
            tasks = getattr(config, 'TASKS', [])
            if not tasks:
                # 兼容旧配置：按单一小红书任务执行
                tasks = [{
                    "type": "xhs_user_notes",
                    "sink": "xhs_default",
                    "params": {
                        "user_urls": config.XHS_TARGET_URLS,
                        "per_account_limit": 10,
                        "scrolls": 1,
                    }
                }]

            for task in tasks:
                t_type = task.get('type')
                if t_type not in ('xhs_user_notes', 'wechat_articles'):
                    print(f"跳过不支持的任务类型: {t_type}")
                    continue

                sink_key = task.get('sink') or 'xhs_default'
                sink_conf = config.FEISHU_SINKS.get(sink_key, {})
                # 为该任务单独构造飞书客户端（指向不同表格）
                try:
                    feishu_for_task = FeishuClient(
                        request_context,
                        app_token=sink_conf.get('app_token'),
                        table_id=sink_conf.get('table_id'),
                        field_mapping=sink_conf.get('field_mapping'),
                    )
                except Exception as e:
                    print(f"初始化飞书客户端失败: {e}")
                    continue

                params = task.get('params', {})
                user_urls = params.get('user_urls') or []
                per_account_limit = int(params.get('per_account_limit') or 10)

                for user_url in user_urls:
                    print(f"\n--- 开始处理用户: {user_url} ---")
                    try:
                        if t_type == 'xhs_user_notes':
                            notes = await scraper.scrape_user_notes(user_url, max_notes=max(40, per_account_limit * 4))
                        else:
                            # wechat_articles：这里 user_url 代表公众号ID或主页URL
                            notes = await wechat_scraper.scrape_account_articles(user_url, max_articles=max(40, per_account_limit * 4))
                        if not notes:
                            print("未在该用户主页发现任何可用条目，或爬取失败。")
                            summary_counts[user_url] = 0
                            continue
                    except Exception as e:
                        print(f"爬取用户 {user_url} 列表时出错: {e}")
                        summary_counts[user_url] = 0
                        continue

                    sent_count = 0
                    existed_count = 0
                    total_candidates = len(notes) if notes else 0
                    for note_info in notes:
                        if sent_count >= per_account_limit:
                            break
                        try:
                            # 增量检查：判断笔记是否已存在
                            note_id_key = 'note_id' if t_type == 'xhs_user_notes' else 'article_id'
                            note_id_val = note_info.get(note_id_key) or note_info.get('note_id')
                            print(f"[去重检查] sink={sink_key} id={note_id_val} -> 查询飞书是否已存在...")
                            exists = await feishu_for_task.check_note_exists(note_id_val)
                            if exists:
                                print(f"[已存在] 跳过 id={note_id_val}")
                                existed_count += 1
                                continue
                            else:
                                print(f"[需要抓详情] id={note_id_val}")

                            # 爬取笔记详情
                            if t_type == 'xhs_user_notes':
                                note_details = await scraper.scrape_note_details(note_info)
                            else:
                                note_details = await wechat_scraper.scrape_article_details(note_info)
                            if not note_details:
                                continue

                            # 如果内容为空，跳过写入
                            ctt = note_details.get("content")
                            if not ctt or not str(ctt).strip():
                                continue
                            # 如果图片数组为空，跳过写入
                            imgs = note_details.get("images") or []
                            valid_imgs = []
                            if isinstance(imgs, list):
                                valid_imgs = [u for u in imgs if isinstance(u, str) and u.strip() and not u.startswith("data:")]
                            elif isinstance(imgs, str) and imgs.strip():
                                valid_imgs = [imgs]
                            if not valid_imgs:
                                continue

                            await feishu_for_task.add_note(note_details)
                            sent_count += 1
                            await asyncio.sleep(random.randint(5, 10))
                        except Exception as e:
                            print(f"处理笔记 {note_info.get('note_id')} 时发生严重错误: {e}")

                    print(f"--- 用户 {user_url} 处理完毕，本次已发送 {sent_count}/{per_account_limit} 条 ---")
                    print(f"=== 小结: 候选 {total_candidates} 条 | 已存在 {existed_count} 条 | 新写入 {sent_count} 条 ===")
                    summary_counts[user_url] = sent_count

        finally:
            # 确保所有资源被关闭
            await scraper.close()
            await browser.close()
            await request_context.dispose()
    
    # 汇总输出各账号发送条数
    try:
        if 'summary_counts' in locals() and summary_counts:
            print("\n====== 发送汇总 ======")
            for u, c in summary_counts.items():
                print(f"账号: {u} -> 发送 {c} 条")
    except Exception:
        pass
    print("\n====== 所有任务执行完毕 ======")

if __name__ == "__main__":
    # 检查配置是否已填写
    if config.FEISHU_APP_ID == "在此处填入你的飞书App ID" or \
       config.FEISHU_BASE_APP_TOKEN == "在此处填入你的多维表格App Token":
        print("错误：请先在 config.py 文件中填写您的飞书应用和多维表格配置信息！")
    else:
        asyncio.run(main())
