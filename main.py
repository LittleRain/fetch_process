import asyncio
import os
import random
import re
from datetime import datetime, timedelta
from playwright.async_api import async_playwright, APIRequestContext

import config
from xhs_scraper import XhsScraper
from feishu_client import FeishuClient
from scrapers.wechat.scraper import WeChatArticleScraper
from scrapers.weibo.scraper import WeiboHomeScraper


def _is_within_last_days(post_time: str, window_days: int) -> bool:
    """判断给定的发布日期是否在最近 window_days 天内。"""
    if not post_time:
        return False
    text = str(post_time).strip()
    if not text:
        return False

    now = datetime.now()
    lower_text = text.lower()

    # 情况1：相对时间（分钟/小时内）视为近30天
    if any(keyword in text for keyword in ("刚刚", "秒前", "分钟前", "小时内", "小时前")):
        return True

    # 情况2：昨天/今天/前天 -> 视为近30天
    if any(keyword in text for keyword in ("昨天", "今日", "今天", "前天")):
        return True

    # 情况3：匹配 mm-dd 或 mm-dd HH:mm
    mmdd_match = re.match(
        r"^\s*(\d{1,2})[-/.月](\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?\s*$",
        text,
    )
    if mmdd_match:
        month = int(mmdd_match.group(1))
        day = int(mmdd_match.group(2))
        hour = int(mmdd_match.group(3) or 0)
        minute = int(mmdd_match.group(4) or 0)
        second = int(mmdd_match.group(5) or 0)
        year = now.year
        try:
            dt = datetime(year, month, day, hour, minute, second)
        except ValueError:
            return False
        # 处理跨年：如果日期在未来太多，视作上一年
        if dt > now + timedelta(days=1):
            try:
                dt = dt.replace(year=year - 1)
            except ValueError:
                return False
        if dt > now:
            return True
        return dt >= now - timedelta(days=window_days)

    # 情况4：匹配 yyyy-mm-dd 或 yyyy-mm-dd HH:mm
    ymd_match = re.match(
        r"^\s*(\d{4})[-/.年](\d{1,2})[-/.月](\d{1,2})(?:\s+(\d{1,2}):(\d{1,2})(?::(\d{1,2}))?)?\s*$",
        text,
    )
    if ymd_match:
        year = int(ymd_match.group(1))
        month = int(ymd_match.group(2))
        day = int(ymd_match.group(3))
        hour = int(ymd_match.group(4) or 0)
        minute = int(ymd_match.group(5) or 0)
        second = int(ymd_match.group(6) or 0)
        try:
            dt = datetime(year, month, day, hour, minute, second)
        except ValueError:
            return False
        if dt > now:
            return True
        return dt >= now - timedelta(days=window_days)

    # 情况5：尝试标准格式解析
    parse_formats = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]
    for fmt in parse_formats:
        try:
            parsed = datetime.strptime(text, fmt)
            if parsed > now:
                return True
            return parsed >= now - timedelta(days=window_days)
        except ValueError:
            continue

    return False


def _is_within_last_month(post_time: str) -> bool:
    """保留兼容函数，判断是否在最近30天内。"""
    return _is_within_last_days(post_time, 14)

async def main():
    """主函数，编排整个爬取和写入流程"""
    print("====== 开始执行抓取任务 ======")

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

        tasks = getattr(config, 'TASKS', [])
        if not tasks:
            # 兼容旧配置：按单一小红书任务执行
            tasks = [{
                "type": "xhs_user_notes",
                "sink": "xhs_default",
                "params": {
                    "urls": config.XHS_TARGET_URLS,
                    "per_account_limit": 10,
                    "scrolls": 1,
                }
            }]

        xhs_task_types = {'xhs_user_notes', 'xhs_home'}
        supported_types = {
            'xhs_user_notes',
            'xhs_home',
            'wechat_articles',
            'weibo_home',
        }
        has_xhs_tasks = any(task.get('type') in xhs_task_types for task in tasks)

        if has_xhs_tasks and not os.path.exists(config.XHS_AUTH_STATE_PATH):
            print(f"错误：未找到会话文件 {config.XHS_AUTH_STATE_PATH}。")
            print("请先运行 python login_helper.py 进行手动登录以生成会话文件。")
            await request_context.dispose()
            return

        # 启动浏览器：本地默认有头，服务器/CI可通过 XHS_HEADLESS 切换
        browser = await p.chromium.launch(
            headless=config.XHS_HEADLESS,
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"]
        )
        context_kwargs = {
            "no_viewport": True,
            "user_agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
        }
        if has_xhs_tasks:
            context_kwargs["storage_state"] = config.XHS_AUTH_STATE_PATH
        context = await browser.new_context(**context_kwargs)
        
        scraper = XhsScraper(context)
        wechat_scraper = WeChatArticleScraper(context)
        weibo_scraper = WeiboHomeScraper(context)

        try:
            summary_counts = {}
            xhs_login_checked = False
            for task in tasks:
                t_type = task.get('type')
                if t_type not in supported_types:
                    print(f"跳过不支持的任务类型: {t_type}")
                    continue
                if t_type in xhs_task_types and not xhs_login_checked:
                    try:
                        if not await scraper.check_login_status():
                            print("错误：小红书登录状态已失效。")
                            print("请重新运行 python login_helper.py 更新会话文件。")
                            return
                        xhs_login_checked = True
                    except Exception as e:
                        print(f"检查小红书登录状态时出错: {e}")
                        return

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
                urls = params.get('urls') or params.get('user_urls') or []
                per_account_limit = int(params.get('per_account_limit') or 10)
                scrolls = int(params.get('scrolls') or 1)

                if t_type in ('xhs_user_notes', 'xhs_home'):
                    note_id_key = 'note_id'
                elif t_type == 'wechat_articles':
                    note_id_key = 'article_id'
                else:
                    note_id_key = 'note_id'

                for user_url in urls:
                    print(f"\n--- 开始处理用户: {user_url} ---")
                    try:
                        if t_type in ('xhs_user_notes', 'xhs_home'):
                            candidate_limit = max(per_account_limit, min(40, per_account_limit * 2))
                            notes = await scraper.scrape_user_notes(
                                user_url,
                                max_notes=candidate_limit,
                                scrolls=scrolls,
                            )
                        elif t_type == 'wechat_articles':
                            # wechat_articles：这里 user_url 代表公众号ID或主页URL
                            notes = await wechat_scraper.scrape_account_articles(user_url, max_articles=max(40, per_account_limit * 4))
                        else:
                            notes = await weibo_scraper.scrape_home_posts(
                                user_url,
                                max_posts=max(40, per_account_limit * 4),
                                scrolls=scrolls,
                            )
                        if not notes:
                            print("未在该用户主页发现任何可用条目，或爬取失败。")
                            summary_counts[user_url] = 0
                            continue
                    except Exception as e:
                        print(f"爬取用户 {user_url} 列表时出错: {e}")
                        summary_counts[user_url] = 0
                        continue

                    # 批量查询已存在的 note_id，避免逐条请求
                    try:
                        note_ids_for_check = []
                        for note_info in notes:
                            raw_id = note_info.get(note_id_key) or note_info.get('note_id')
                            if raw_id is None:
                                continue
                            raw_id_str = str(raw_id).strip()
                            if raw_id_str:
                                note_ids_for_check.append(raw_id_str)
                        existing_note_ids = await feishu_for_task.check_notes_exist_batch(note_ids_for_check)
                        print(f"[批量去重] sink={sink_key} -> 待查 {len(note_ids_for_check)} 条, 已存在 {len(existing_note_ids)} 条")
                    except Exception as e:
                        print(f"[批量去重失败] sink={sink_key} 错误: {e}")
                        existing_note_ids = set()
                    existing_note_ids_normalized = {str(s).strip().lower() for s in existing_note_ids if isinstance(s, str)}

                    existed_count = 0
                    filtered_notes = []
                    for note_info in notes:
                        note_id_val = note_info.get(note_id_key) or note_info.get('note_id')
                        note_id_val_str = str(note_id_val).strip() if note_id_val is not None else ""
                        if not note_id_val_str:
                            print(f"[跳过] 未获取到 note_id 字段，原始={note_id_val}")
                            continue
                        note_id_val_lower = note_id_val_str.lower()
                        if note_id_val_str in existing_note_ids or note_id_val_lower in existing_note_ids_normalized:
                            existed_count += 1
                            print(f"[已存在-批] 跳过 id={note_id_val_str}")
                            continue
                        if note_info.get('is_video') and t_type not in ('weibo_home',):
                            print(f"[跳过] 视频内容 id={note_id_val_str}")
                            continue
                        filtered_notes.append(note_info)

                    if not filtered_notes:
                        summary_counts[user_url] = 0
                        print(f"[批量去重] sink={sink_key} -> 无需处理新内容，结束账号 {user_url}")
                        continue

                    total_candidates = len(notes) if notes else 0
                    successful_note_ids: list[str] = []
                    consecutive_expired = 0  # 仅用于小红书任务，追踪连续过期数量
                    is_xhs_task = t_type in ('xhs_user_notes', 'xhs_home')

                    async def attempt_write(note_info_inner, note_details_inner, note_id_val_str_inner):
                        nonlocal consecutive_expired
                        if not note_details_inner:
                            print(f"[未写入] id={note_id_val_str_inner} 原因=详情抓取失败")
                            return False, False
                        ctt = note_details_inner.get("content")
                        if not ctt or not str(ctt).strip():
                            print(f"[未写入] id={note_id_val_str_inner} 原因=正文为空")
                            return False, False
                        imgs = note_details_inner.get("images") or []
                        valid_imgs = []
                        if isinstance(imgs, list):
                            valid_imgs = [u for u in imgs if isinstance(u, str) and u.strip() and not u.startswith("data:")]
                        elif isinstance(imgs, str) and imgs.strip():
                            valid_imgs = [imgs]
                        is_video_note = note_details_inner.get("is_video") or note_info_inner.get('is_video')
                        if not valid_imgs and not is_video_note:
                            print(f"[未写入] id={note_id_val_str_inner} 原因=无有效图片")
                            return False, False

                        if is_xhs_task:
                            post_time_str = note_details_inner.get("post_time")
                            is_expired = not _is_within_last_days(post_time_str, 14)
                            if is_expired:
                                print(f"[过期] 跳过 id={note_id_val_str_inner} post_time={post_time_str}")
                        elif t_type == 'weibo_home':
                            post_time_str = note_details_inner.get("post_time")
                            is_expired = not _is_within_last_days(post_time_str, 14)
                            if is_expired:
                                print(f"[过期] 跳过 id={note_id_val_str_inner} post_time={post_time_str}")
                        else:
                            is_expired = False

                        if is_expired:
                            if is_xhs_task:
                                consecutive_expired += 1
                                if consecutive_expired >= 3:
                                    print(f"[终止账号] {user_url} 连续3条内容均已过期，结束该账号抓取。")
                                    return False, True
                            return False, False
                        else:
                            if is_xhs_task and consecutive_expired:
                                consecutive_expired = 0

                        await feishu_for_task.add_note(note_details_inner)
                        print(f"[写入成功] sink={sink_key} id={note_id_val_str_inner}")
                        existing_note_ids.add(note_id_val_str_inner)
                        existing_note_ids_normalized.add(note_id_val_str_inner.lower())
                        successful_note_ids.append(note_id_val_str_inner)
                        await asyncio.sleep(random.randint(5, 10))
                        return True, False

                    if is_xhs_task:
                        detail_concurrency = int(os.environ.get("XHS_DETAIL_CONCURRENCY", "2") or "2")
                        if detail_concurrency < 1:
                            detail_concurrency = 1
                        detail_concurrency = min(detail_concurrency, per_account_limit)
                        pending_tasks = []
                        note_index = 0
                        stop_due_to_expired = False

                        async def run_detail_fetch(note_payload):
                            detail_page = None
                            try:
                                detail_page = await scraper.create_prepared_page()
                                return await scraper.scrape_note_details(note_payload, page=detail_page)
                            finally:
                                if detail_page:
                                    try:
                                        await detail_page.close()
                                    except Exception:
                                        pass

                        while (note_index < len(filtered_notes) or pending_tasks) and len(successful_note_ids) < per_account_limit:
                            while (
                                note_index < len(filtered_notes)
                                and len(pending_tasks) < detail_concurrency
                                and len(successful_note_ids) + len(pending_tasks) < per_account_limit
                            ):
                                note_info = filtered_notes[note_index]
                                note_index += 1
                                note_id_val = note_info.get(note_id_key) or note_info.get('note_id')
                                note_id_val_str = str(note_id_val).strip() if note_id_val is not None else ""
                                if not note_id_val_str:
                                    continue
                                print(f"[需要抓详情] id={note_id_val_str}")
                                pending_tasks.append(
                                    (note_info, note_id_val_str, asyncio.create_task(run_detail_fetch(note_info)))
                                )

                            if not pending_tasks:
                                break

                            note_info_cur, note_id_str_cur, task = pending_tasks.pop(0)
                            note_details = None
                            try:
                                note_details = await task
                            except Exception as e:
                                print(f"[未写入] id={note_id_str_cur} 原因=详情抓取异常 {e}")
                            _, should_stop = await attempt_write(note_info_cur, note_details, note_id_str_cur)
                            if should_stop:
                                stop_due_to_expired = True
                                break

                        # 结束循环后取消剩余任务，避免页面泄漏
                        for _, __, task in pending_tasks:
                            task.cancel()
                            try:
                                await task
                            except Exception:
                                pass
                        if stop_due_to_expired:
                            # 清理后直接结束本账号
                            pass
                    else:
                        for note_info in filtered_notes:
                            if len(successful_note_ids) >= per_account_limit:
                                break
                            try:
                                note_id_val = note_info.get(note_id_key) or note_info.get('note_id')
                                note_id_val_str = str(note_id_val).strip() if note_id_val is not None else ""
                                if not note_id_val_str:
                                    continue
                                print(f"[需要抓详情] id={note_id_val_str}")

                                if t_type == 'weibo_home':
                                    summary_post_time = note_info.get('post_time')
                                    if summary_post_time and not _is_within_last_days(summary_post_time, 14):
                                        print(f"[过期] 跳过 id={note_id_val_str} post_time={summary_post_time}")
                                        continue

                                if t_type == 'wechat_articles':
                                    note_details = await wechat_scraper.scrape_article_details(note_info)
                                else:
                                    note_details = await weibo_scraper.scrape_post_details(note_info)
                                _, should_stop = await attempt_write(note_info, note_details, note_id_val_str)
                                if should_stop:
                                    break
                            except Exception as e:
                                print(f"[未写入] id={note_info.get('note_id')} 原因=异常 {e}")

                    sent_count = len(successful_note_ids)
                    print(f"--- 用户 {user_url} 处理完毕，本次已发送 {sent_count}/{per_account_limit} 条 ---")
                    print(f"=== 小结: 候选 {total_candidates} 条 | 已存在 {existed_count} 条 | 新写入 {sent_count} 条 ===")
                    summary_counts[user_url] = sent_count

        finally:
            # 确保所有资源被关闭
            await scraper.close()
            await wechat_scraper.close()
            await weibo_scraper.close()
            await browser.close()
            await request_context.dispose()
    
    # 汇总输出各账号发送条数
    try:
        if 'summary_counts' in locals() and summary_counts:
            print("\n====== 发送汇总 ======")
            total_sent = 0
            for u, c in summary_counts.items():
                print(f"账号: {u} -> 发送 {c} 条")
                total_sent += c
            print(f"总计发送 {total_sent} 条")
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
