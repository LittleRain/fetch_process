
import asyncio
import random
import re
from playwright.async_api import (
    Page,
    BrowserContext,
    Frame,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
from urllib.parse import urlparse, urlunparse, urljoin
from typing import List, Dict, Optional, Union

class XhsScraper:
    def __init__(self, context: BrowserContext):
        self.context = context
        self.page: Optional[Page] = None

    async def init_page(self):
        """初始化一个新的页面并进行基本设置"""
        self.page = await self.context.new_page()
        # 降低被检测的风险
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
        """)

    async def _goto_with_retry(self, url: str, *, wait_until: str = "domcontentloaded", retries: int = 3):
        """对 goto 进行重试封装，处理小红书页面偶发的导航抢占。"""
        if not self.page:
            await self.init_page()

        last_error: Optional[Exception] = None
        for attempt in range(1, max(1, retries) + 1):
            try:
                await self.page.goto(url, wait_until=wait_until)
                return
            except (PlaywrightTimeoutError, PlaywrightError) as exc:
                msg = str(exc) if exc else ""
                interrupt = "is interrupted by another navigation" in msg
                timed_out = isinstance(exc, PlaywrightTimeoutError)
                if attempt < retries and (interrupt or timed_out):
                    print(f"导航到 {url} 未完成，原因: {msg or exc.__class__.__name__}。第 {attempt} 次重试...")
                    try:
                        await self.page.wait_for_load_state("load")
                    except Exception:
                        pass
                    await self.page.wait_for_timeout(800)
                    last_error = exc
                    continue
                last_error = exc
                break

        if last_error:
            raise last_error

    async def close(self):
        """关闭页面"""
        if self.page and not self.page.is_closed():
            await self.page.close()

    async def check_login_status(self) -> bool:
        """
        通过访问个人主页并检查特定元素来验证登录状态。
        """
        if not self.page:
            await self.init_page()
        
        print("正在检查登录状态...")
        # 访问一个需要登录才能正常显示的页面
        await self._goto_with_retry("https://www.xiaohongshu.com/explore")
        await self.page.wait_for_timeout(random.randint(2000, 4000))

        # 寻找登录后才会出现的元素，例如首页的 '关注' '发现' tab
        # 使用更可靠的选择器，寻找“创作服务”链接，这是登录后才有的标志
        follow_tab_selector = 'a[href*="creator.xiaohongshu.com"]'
        try:
            await self.page.wait_for_selector(follow_tab_selector, timeout=10000)
            print("登录状态正常。")
            return True
        except Exception:
            print("登录状态失效或未登录。")
            return False

    async def scrape_user_notes(self, user_url: str, max_notes: int = 10) -> List[Dict]:
        """
        从指定用户主页爬取最新的笔记列表。
        :param user_url: 用户主页 URL
        :param max_notes: 本次最多爬取的笔记数量
        :return: 包含笔记基本信息的字典列表
        """
        if not self.page:
            await self.init_page()

        print(f"正在访问用户主页: {user_url}")
        await self._goto_with_retry(user_url)

        # 等待笔记的父容器加载完成（用户主页用 #userPostedFeeds 更稳）
        feeds_container_selector = "div#userPostedFeeds.feeds-container" if "/user/profile/" in user_url else "div.feeds-container"
        try:
            print(f"正在等待核心容器 '{feeds_container_selector}' 加载...")
            await self.page.wait_for_selector(feeds_container_selector, timeout=20000)
            print("核心容器加载成功。")
        except Exception:
            print("在20秒内未找到核心容器，页面可能为空或结构已更改。")
            # 保存一张截图以便调试
            await self.page.screenshot(path="debug_screenshot.png")
            print("已保存截图 `debug_screenshot.png` 以供分析。")
            return []

        # 模拟向下滚动以加载更多笔记（按需仅滚动 1 次）
        for i in range(1): # 滚动1次
            print(f"正在进行第 {i+1} 次向下滚动...")
            await self.page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await self.page.wait_for_timeout(random.randint(2500, 4000))

        # 确保至少有一个卡片出现
        try:
            await self.page.wait_for_selector(
                f"{feeds_container_selector} section.note-item a, {feeds_container_selector} a[href*='/explore/']",
                timeout=20000
            )
        except Exception:
            pass

        # 回到页面顶部，确保从最上方开始抓取
        try:
            await self.page.evaluate("window.scrollTo(0, 0)")
            await self.page.wait_for_timeout(300)
        except Exception:
            pass

        # 现在在已加载的容器内查找可点击的卡片封面（优先 'cover mask ld' 元素）
        notes_locator = None
        try:
            # 基础 anchors：主页中指向笔记详情的链接（同时覆盖 note-item 下的 cover 链接）
            anchors_all = self.page.locator(
                f"{feeds_container_selector} section.note-item a.cover, {feeds_container_selector} a[href*='/explore/']"
            )
            count_all = await anchors_all.count()
            print(f"候选锚点（含 '/explore/'）数量: {count_all}")

            # 优先匹配带 cover/mask/ld 的卡片链接
            preferred = self.page.locator(f"{feeds_container_selector} a.cover.mask.ld")
            if await preferred.count() == 0:
                preferred = self.page.locator(f"{feeds_container_selector} a.cover.mask")
            if await preferred.count() == 0:
                preferred = self.page.locator(f"{feeds_container_selector} a.cover.ld")
            if await preferred.count() == 0:
                preferred = self.page.locator(f"{feeds_container_selector} a.cover")
            # 如果依旧没有，尝试：a 内部包含 .cover.mask.ld 的情况
            if await preferred.count() == 0:
                preferred = anchors_all.filter(has=self.page.locator('.cover.mask.ld'))
            if await preferred.count() == 0:
                preferred = anchors_all.filter(has=self.page.locator('.cover'))

            preferred_count = await preferred.count()
            if preferred_count > 0:
                notes_locator = preferred
                print(f"使用 'cover' 优先选择，命中 {preferred_count} 个卡片链接。")
            else:
                notes_locator = anchors_all
                print("未命中 'cover' 相关选择器，回退到所有 '/explore/' 链接。")
        except Exception as e:
            print(f"定位主页卡片链接时异常: {e}")
            notes_locator = self.page.locator(f"{feeds_container_selector} a[href*='/explore/']")
        

        def _parse_note_id(href: str) -> Optional[str]:
            try:
                if not href:
                    return None
                # 标准化路径部分
                path = href
                if href.startswith("http"):
                    try:
                        from urllib.parse import urlparse
                        path = urlparse(href).path
                    except Exception:
                        path = href
                # 常见匹配模式
                patterns = [
                    r"/explore/([A-Za-z0-9]+)",
                    r"/user/profile/[^/]+/([A-Za-z0-9]+)",
                    r"/profile/[^/]+/([A-Za-z0-9]+)",
                    r"/note/([A-Za-z0-9]+)",
                ]
                for pat in patterns:
                    m = re.search(pat, path)
                    if m:
                        part = m.group(1)
                        if 8 <= len(part) <= 64:
                            return part
                # 兜底：取路径最后一段作为候选
                segs = [s for s in path.split('/') if s]
                if segs:
                    cand = segs[-1]
                    if re.fullmatch(r"[A-Za-z0-9]{8,64}", cand):
                        return cand
            except Exception:
                pass
            return None

        count_found = await notes_locator.count()
        max_count = min(count_found, max_notes)
        print(f"准备从 {max_count}/{count_found} 个卡片中提取 href。")
        if max_count == 0:
            # 无卡片可用，保存调试信息
            try:
                html_content = await self.page.content()
                with open("debug_homepage.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                await self.page.screenshot(path="debug_screenshot_no_notes.png", full_page=True)
                print("已保存 debug_homepage.html 与 debug_screenshot_no_notes.png 以供分析。")
            except Exception as e:
                print(f"保存首页调试信息失败: {e}")
        # 严格按页面“从上到下（再从左到右）”顺序选取前 max_count 条
        scraped_notes = []
        handles = []
        try:
            handles = await notes_locator.element_handles()
        except Exception as e:
            print(f"获取卡片元素句柄时异常: {e}")

        positioned = []
        skipped_handles = 0
        for idx, h in enumerate(handles):
            top, left = 1e9, 1e9
            try:
                pos = await h.evaluate(
                    "el => {\n"
                    "  const card = el.closest('section.note-item, li.note-item, .note-item, .note-card') || el;\n"
                    "  const r = card.getBoundingClientRect();\n"
                    "  return { t: (r.top || 0) + window.scrollY, l: (r.left || 0) + window.scrollX };\n"
                    "}"
                )
                if pos:
                    top = float(pos.get('t', 1e9))
                    left = float(pos.get('l', 1e9))
            except Exception:
                pass

            note_url = None
            try:
                note_url = await h.get_attribute('href')
            except Exception:
                note_url = None
            if not note_url:
                try:
                    note_url = await h.evaluate("el => el.closest('a') && el.closest('a').getAttribute('href')")
                except Exception:
                    note_url = None
            if not note_url:
                skipped_handles += 1
                continue

            note_id = _parse_note_id(note_url)
            if not note_id:
                continue

            full_url = note_url if not note_url.startswith('/') else f"https://www.xiaohongshu.com{note_url}"
            positioned.append((top, left, idx, note_id, full_url, note_url))

        if skipped_handles:
            print(f"有 {skipped_handles} 个卡片未能提取有效链接，已跳过。")

        if positioned:
            positioned.sort(key=lambda x: (x[0], x[1]))
            seen_ids = set()
            # DEBUG: 打印排序后的前若干条用于定位顺序问题
            try:
                preview = positioned[:max_count]
                print("已按页面位置排序（前序预览）：")
                for i, (t, l, oidx, nid, full_url, raw_href) in enumerate(preview, start=1):
                    print(f"  #{i} y={int(t)} x={int(l)} id={nid} href={raw_href}")
            except Exception:
                pass
            for _, __, orig_idx, note_id, full_url, raw_href in positioned:
                if note_id in seen_ids:
                    continue
                seen_ids.add(note_id)
                scraped_notes.append({
                    "note_id": note_id,
                    "url": full_url,
                    "index": orig_idx,
                    "raw_href": raw_href,
                })
                if len(scraped_notes) >= max_count:
                    break

        if not scraped_notes and max_count > 0:
            print("未能按位置排序卡片，回退到 DOM 顺序。")
            seen_ids = set()
            for idx in range(max_count):
                note_handle = notes_locator.nth(idx)
                note_url = None
                try:
                    note_url = await note_handle.get_attribute('href')
                except Exception:
                    note_url = None
                if not note_url:
                    try:
                        note_url = await note_handle.evaluate("el => el.closest('a') && el.closest('a').getAttribute('href')")
                    except Exception:
                        note_url = None
                if not note_url:
                    continue
                note_id = _parse_note_id(note_url)
                if not note_id or note_id in seen_ids:
                    continue
                seen_ids.add(note_id)
                full_url = note_url if not note_url.startswith('/') else f"https://www.xiaohongshu.com{note_url}"
                scraped_notes.append({
                    "note_id": note_id,
                    "url": full_url,
                    "index": idx,
                    "raw_href": note_url,
                })
                if len(scraped_notes) >= max_count:
                    break

        print(f"最终收集到 {len(scraped_notes)} 条笔记。")
        return scraped_notes
        

    async def scrape_note_details(self, note_info: Dict) -> Dict:
        """
        进入笔记详情页，爬取详细信息。
        :param note_info: 包含笔记 ID 和 URL 的字典
        :return: 包含笔记所有详细信息的字典
        """
        if not self.page:
            await self.init_page()

        print(f"正在爬取笔记详情: {note_info['url']}")

        # 优先尝试在当前用户主页通过“点击”进入详情（可能是同页导航或新标签页，或浮层 iframe）
        pg: Union[Page, Frame] = self.page  # 默认在当前页
        clicked_navigation = False
        popup_page: Optional[Page] = None
        extra_note_page: Optional[Page] = None
        restore_url: Optional[str] = None

        def _build_direct_note_url() -> Optional[str]:
            """
            返回用于新页直开的“正确链接”：直接使用 raw_href（包含 token 的真实路由），
            如：/user/profile/<uid>/<note_id>?xsec_token=...。必要时补全域名。
            """
            try:
                raw = note_info.get("raw_href") or note_info.get("url")
                if not raw:
                    return None
                if raw.startswith("http"):
                    return raw
                if raw.startswith("/"):
                    return f"https://www.xiaohongshu.com{raw}"
                # 其它相对形式兜底
                return f"https://www.xiaohongshu.com/{raw}"
            except Exception:
                return None

        def _build_explore_url_with_query() -> Optional[str]:
            """从 raw_href 提取 query 并生成 /explore/<note_id>?<query> 链接（若可用）。"""
            try:
                raw = note_info.get("raw_href") or note_info.get("url")
                nid = note_info.get("note_id")
                if not raw or not nid:
                    return None
                p = urlparse(raw if raw.startswith("http") else f"https://www.xiaohongshu.com{raw}")
                qs = ("?" + p.query) if p.query else ""
                return f"https://www.xiaohongshu.com/explore/{nid}{qs}"
            except Exception:
                return None
        
        async def _find_overlay_frame() -> Optional[Frame]:
            """在当前页面中扫描可能的浮层 frame（根据 URL 关键字判断）。"""
            try:
                for _ in range(30):
                    for fr in self.page.frames:
                        try:
                            fu = getattr(fr, 'url', '') or ''
                            if ('/explore/' in fu) or re.search(r"/user/profile/.+?/([A-Za-z0-9]{8,64})", fu or ''):
                                return fr
                        except Exception:
                            continue
                    await self.page.wait_for_timeout(250)
            except Exception:
                pass
            return None
        try:
            if self.page:
                feeds_container_selector = "div.feeds-container"

                # 1) 优先：按 raw_href 精确点击（更符合当前页面行为，常打开浮层）
                if "raw_href" in note_info and note_info["raw_href"]:
                    raw = note_info["raw_href"]
                    raw_sel = f"{feeds_container_selector} a[href='{raw}']"
                    if await self.page.locator(raw_sel).count() == 0 and raw.startswith("http"):
                        try:
                            from urllib.parse import urlparse
                            p = urlparse(raw)
                            raw_sel = f"{feeds_container_selector} a[href='{p.path}']"
                        except Exception:
                            pass
                    if await self.page.locator(raw_sel).count() > 0:
                        locator2 = self.page.locator(raw_sel).first
                        try:
                            await locator2.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        try:
                            async with self.context.expect_page(timeout=3000) as pi2:
                                await locator2.click(force=True)
                            popup_page = await pi2.value
                            pg = popup_page
                            clicked_navigation = True
                            print("raw_href 点击后捕获到新标签页。")
                        except Exception:
                            try:
                                async with self.page.expect_navigation(timeout=3000):
                                    await locator2.click(force=True)
                                pg = self.page
                                clicked_navigation = True
                                print("raw_href 点击后发生同页导航。")
                            except Exception:
                                try:
                                    await locator2.click(force=True)
                                except Exception:
                                    pass
                                overlay_selector = "div.container[data-v-fc1041fa]"
                                iframe_selector = f"{overlay_selector} iframe"
                                try:
                                    await self.page.wait_for_selector(overlay_selector, timeout=7000)
                                    
                                    try:
                                        _ = await self.page.locator(overlay_selector).first.get_attribute("class")
                                    except Exception:
                                        pass
                                    iframe_el = await self.page.wait_for_selector(iframe_selector, timeout=7000)
                                    # 同时打印 attribute 与 property 的 src，便于调试
                                    iframe_attr_src = None
                                    iframe_prop_src = None
                                    try:
                                        iframe_attr_src = await iframe_el.get_attribute("src")
                                        iframe_prop_src = await iframe_el.evaluate("el => el.src || ''")
                                    except Exception:
                                        pass
                                    # 优先按 iframe 的 prop/src 同页跳转抓取，避免空 frame
                                    try:
                                        target_url = None
                                        if iframe_prop_src and not iframe_prop_src.startswith('about:'):
                                            target_url = iframe_prop_src
                                        elif iframe_attr_src and not iframe_attr_src.startswith('about:'):
                                            target_url = iframe_attr_src
                                        else:
                                            target_url = _build_explore_url_with_query() or _build_direct_note_url() or note_info['url']
                                        if target_url:
                                            try:
                                                restore_url = self.page.url
                                            except Exception:
                                                restore_url = None
                                            
                                            await self._goto_with_retry(target_url)
                                            try:
                                                await self.page.wait_for_load_state("networkidle")
                                            except Exception:
                                                pass
                                            pg = self.page
                                            clicked_navigation = True
                                            # 跳过后续 overlay_frame 处理
                                            raise Exception("skip_overlay_processing")
                                    except Exception:
                                        pass
                                    # 优先使用浮层 content_frame 抓取，避免跳转导致上下文丢失
                                    if clicked_navigation:
                                        raise Exception("skip_overlay_processing")
                                    overlay_frame = None
                                    try:
                                        for _ in range(40):  # 最长 ~10s 等待浮层加载
                                            overlay_frame = await iframe_el.content_frame()
                                            if overlay_frame:
                                                break
                                            await self.page.wait_for_timeout(250)
                                    except Exception:
                                        if clicked_navigation:
                                            raise Exception("skip_overlay_processing")
                                        overlay_frame = None
                                    if not overlay_frame:
                                        try:
                                            overlay_frame = await _find_overlay_frame()
                                        except Exception:
                                            if clicked_navigation:
                                                raise Exception("skip_overlay_processing")
                                            overlay_frame = None
                                    if overlay_frame:
                                        try:
                                            _ = overlay_frame.url
                                        except Exception:
                                            pass
                                        used_frame = overlay_frame
                                        try:
                                            await overlay_frame.wait_for_selector("article, .slider-container, #detail-desc, .note-desc, .note-content, .desc", timeout=8000)
                                        except Exception:
                                            # 若顶层 frame 未出现内容，尝试其子 frame
                                            try:
                                                for nf in overlay_frame.child_frames:
                                                    try:
                                                        await nf.wait_for_selector("article, .slider-container, #detail-desc, .note-desc, .note-content, .desc", timeout=2000)
                                                        used_frame = nf
                                                        break
                                                    except Exception:
                                                        continue
                                            except Exception:
                                                pass
                                        pg = used_frame
                                        clicked_navigation = True
                                        
                                    else:
                                        # 兜底：同页跳转到详情链接再抓取（最后手段）
                                        direct_url = _build_explore_url_with_query() or _build_direct_note_url() or note_info['url']
                                        
                                        await self._goto_with_retry(direct_url)
                                        try:
                                            await self.page.wait_for_load_state("networkidle")
                                        except Exception:
                                            pass
                                        pg = self.page
                                        clicked_navigation = True
                                except Exception:
                                    pass

                # 2) 其次：按 note_id 片段匹配
                if not clicked_navigation and "note_id" in note_info:
                    note_anchor_sel = f"{feeds_container_selector} a[href*='{note_info['note_id']}']"
                    print(f"尝试通过选择器点击进入详情(按 note_id 片段): {note_anchor_sel}")
                    if await self.page.locator(note_anchor_sel).count() > 0:
                        locator = self.page.locator(note_anchor_sel).first
                        try:
                            await locator.scroll_into_view_if_needed()
                        except Exception:
                            pass
                        try:
                            async with self.context.expect_page(timeout=3000) as pi:
                                await locator.click(force=True)
                            popup_page = await pi.value
                            pg = popup_page
                            clicked_navigation = True
                        except Exception:
                            try:
                                async with self.page.expect_navigation(timeout=3000):
                                    await locator.click(force=True)
                                pg = self.page
                                clicked_navigation = True
                            except Exception:
                                try:
                                    await locator.click(force=True)
                                except Exception:
                                    pass
                                overlay_selector = "div.container[data-v-fc1041fa]"
                                iframe_selector = f"{overlay_selector} iframe"
                                try:
                                    await self.page.wait_for_selector(overlay_selector, timeout=7000)
                                    iframe_el = await self.page.wait_for_selector(iframe_selector, timeout=7000)
                                    try:
                                        iframe_attr_src = await iframe_el.get_attribute("src")
                                        iframe_prop_src = await iframe_el.evaluate("el => el.src || ''")
                                    except Exception:
                                        pass
                                    # 优先使用 iframe 的 prop src/attr src 进行同页跳转抓取
                                    try:
                                        same_page_target = (
                                            (iframe_prop_src if iframe_prop_src and not iframe_prop_src.startswith('about:') else None) or
                                            (iframe_attr_src if iframe_attr_src and not iframe_attr_src.startswith('about:') else None) or
                                            _build_explore_url_with_query() or
                                            _build_direct_note_url() or
                                            note_info['url']
                                        )
                                        try:
                                            restore_url = self.page.url
                                        except Exception:
                                            restore_url = None
                                        
                                        await self._goto_with_retry(same_page_target)
                                        try:
                                            await self.page.wait_for_load_state("networkidle")
                                        except Exception:
                                            pass
                                        pg = self.page
                                        clicked_navigation = True
                                        # 直接跳过后续 overlay_frame 处理
                                        raise Exception("skip_overlay_processing")
                                    except Exception:
                                        # 失败再尝试使用 content_frame
                                        overlay_frame = None
                                        try:
                                            for _ in range(40):
                                                overlay_frame = await iframe_el.content_frame()
                                                if overlay_frame:
                                                    break
                                                await self.page.wait_for_timeout(250)
                                        except Exception:
                                            overlay_frame = None
                                        if not overlay_frame:
                                            try:
                                                overlay_frame = await _find_overlay_frame()
                                            except Exception:
                                                overlay_frame = None
                                        if overlay_frame:
                                            used_frame = overlay_frame
                                            try:
                                                await overlay_frame.wait_for_selector("article, .slider-container, #detail-desc, .note-desc, .note-content, .desc", timeout=8000)
                                            except Exception:
                                                pass
                                            pg = used_frame
                                            clicked_navigation = True
                                        else:
                                                # 最后再同页跳转
                                                direct_url = _build_explore_url_with_query() or _build_direct_note_url() or note_info['url']
                                                
                                                try:
                                                    restore_url = self.page.url
                                                except Exception:
                                                    restore_url = None
                                                await self._goto_with_retry(direct_url)
                                                try:
                                                    await self.page.wait_for_load_state("networkidle")
                                                except Exception:
                                                    pass
                                                pg = self.page
                                                clicked_navigation = True
                                except Exception:
                                    pass

                # 3) 再次：按 index 兜底点击
                if not clicked_navigation and "index" in note_info:
                    print("按 raw_href/note_id 都失败，尝试按索引点击...")
                    try:
                        anchors = self.page.locator(
                            f"{feeds_container_selector} a.cover.mask.ld, "
                            f"{feeds_container_selector} a.cover.mask, "
                            f"{feeds_container_selector} a.cover.ld, "
                            f"{feeds_container_selector} a.cover"
                        )
                        if await anchors.count() > note_info["index"]:
                            idx_locator = anchors.nth(note_info["index"])
                            try:
                                await idx_locator.scroll_into_view_if_needed()
                            except Exception:
                                pass
                            try:
                                async with self.context.expect_page(timeout=3000) as pi2:
                                    await idx_locator.click(force=True)
                                popup_page = await pi2.value
                                pg = popup_page
                                clicked_navigation = True
                            except Exception:
                                try:
                                    async with self.page.expect_navigation(timeout=3000):
                                        await idx_locator.click(force=True)
                                    pg = self.page
                                    clicked_navigation = True
                                except Exception:
                                    try:
                                        await idx_locator.click(force=True)
                                    except Exception:
                                        pass
                                    overlay_selector = "div.container[data-v-fc1041fa]"
                                    iframe_selector = f"{overlay_selector} iframe"
                                    try:
                                        await self.page.wait_for_selector(overlay_selector, timeout=7000)
                                        iframe_el = await self.page.wait_for_selector(iframe_selector, timeout=7000)
                                        try:
                                            iframe_attr_src = await iframe_el.get_attribute("src")
                                            iframe_prop_src = await iframe_el.evaluate("el => el.src || ''")
                                        except Exception:
                                            pass
                                        # 优先使用 iframe 的 prop src/attr src 进行同页跳转抓取
                                        same_page_target = (
                                            _build_explore_url_with_query() or
                                            (iframe_prop_src if iframe_prop_src and not iframe_prop_src.startswith('about:') else None) or
                                            (iframe_attr_src if iframe_attr_src and not iframe_attr_src.startswith('about:') else None) or
                                            _build_direct_note_url() or
                                            note_info['url']
                                        )
                                        try:
                                            try:
                                                restore_url = self.page.url
                                            except Exception:
                                                restore_url = None
                                            
                                            await self._goto_with_retry(same_page_target)
                                            try:
                                                await self.page.wait_for_load_state("networkidle")
                                            except Exception:
                                                pass
                                            pg = self.page
                                            clicked_navigation = True
                                        except Exception:
                                            # 失败再尝试使用 content_frame
                                            overlay_frame = None
                                            try:
                                                for _ in range(40):
                                                    overlay_frame = await iframe_el.content_frame()
                                                    if overlay_frame:
                                                        break
                                                    await self.page.wait_for_timeout(250)
                                            except Exception:
                                                overlay_frame = None
                                            if not overlay_frame:
                                                try:
                                                    overlay_frame = await _find_overlay_frame()
                                                except Exception:
                                                    overlay_frame = None
                                            if overlay_frame:
                                                try:
                                                    _ = overlay_frame.url
                                                except Exception:
                                                    pass
                                                used_frame = overlay_frame
                                                try:
                                                    await overlay_frame.wait_for_selector("article, .slider-container, #detail-desc, .note-desc, .note-content, .desc", timeout=8000)
                                                except Exception:
                                                    try:
                                                        for nf in overlay_frame.child_frames:
                                                            try:
                                                                await nf.wait_for_selector("article, .slider-container, #detail-desc, .note-desc, .note-content, .desc", timeout=2000)
                                                                used_frame = nf
                                                                break
                                                            except Exception:
                                                                continue
                                                    except Exception:
                                                        pass
                                                pg = used_frame
                                                clicked_navigation = True
                                                
                                            else:
                                                # 最后再同页跳转
                                                direct_url = _build_explore_url_with_query() or _build_direct_note_url() or note_info['url']
                                                
                                                try:
                                                    restore_url = self.page.url
                                                except Exception:
                                                    restore_url = None
                                                await self._goto_with_retry(direct_url)
                                                try:
                                                    await self.page.wait_for_load_state("networkidle")
                                                except Exception:
                                                    pass
                                                pg = self.page
                                                clicked_navigation = True
                                    except Exception:
                                        print("索引点击也失败。")
                    except Exception as ie:
                        print(f"索引点击过程异常: {ie}")

            if not clicked_navigation:
                # 兜底：直接跳转到详情URL
                print("点击未触发导航，使用 goto 兜底跳转详情页...")
                await self._goto_with_retry(note_info['url'])
                pg = self.page

            # 等待渲染完成：Page 等待 networkidle；Frame 则直接等待一段时间
            try:
                # 等待详情核心元素出现
                try:
                    await pg.wait_for_selector("article, .slider-container, img.note-slider-img, #detail-desc, .note-desc, .note-content, .desc", timeout=12000)
                except Exception:
                    pass
                if isinstance(pg, Page):
                    try:
                        await pg.wait_for_load_state("networkidle")
                    except Exception:
                        pass
                await pg.wait_for_timeout(random.randint(2000, 3500))
                # 轻微滚动以触发图片懒加载
                try:
                    for _ in range(4):
                        await pg.evaluate("window.scrollBy(0, Math.max(300, window.innerHeight))")
                        await pg.wait_for_timeout(700)
                except Exception:
                    pass
            except Exception:
                pass

        except Exception:
            # 导航/等待阶段的兜底，不阻塞后续解析流程
            pass

        # 选择器候选（页面经常改版，保留多套兜底）
        title_candidates = [
            "#detail-title",
            "h1.title",
            ".note-title",
            "article h1",
        ]
        author_candidates = [
            ".author-info .name",
            ".author .name",
            "a[href*='/user/profile'] .name",
        ]
        tags_candidates = [
            ".tag-list .tag",
            ".note-tags .tag",
        ]
        content_candidates = [
            "#detail-desc",
            ".desc",
            ".note-desc",
            ".note-content",
            "article .desc",
            "article .content",
            "article",
            "xpath=//div[contains(@class,'desc') or contains(@class,'content') or contains(@class,'text')]",
        ]
        image_candidates = [
            "div.swiper-slide img.preview-image",
            "img.preview-image",
            "article img",
            "img[src*='xiaohongshu.com']",
            "img[src*='xhsimg']",
            "img[src*='sns-img']",
        ]
        time_candidates = [
            "time[datetime]",
            "#detail-time",
            "time",
            "[class*='time']",
        ]
        # 互动数据选择器
        likes_selector = ".like-wrapper .count"
        collections_selector = ".collect-wrapper .count"
        comments_selector = ".comment-wrapper .count"
        shares_selector = ".share-wrapper .count"

        async def first_text(selectors, page: Union[Page, Frame]) -> str:
            for sel in selectors:
                try:
                    loc = page.locator(sel).first
                    if await loc.count() > 0:
                        # 等待元素出现但不强制可见
                        try:
                            await page.wait_for_selector(sel, timeout=3000)
                        except Exception:
                            pass
                        try:
                            text = await loc.inner_text()
                            if text and text.strip():
                                return text.strip()
                        except Exception:
                            continue
                except Exception:
                    continue
            return ""

        async def first_attr_from_all(selectors, attr: str, page: Union[Page, Frame]) -> List[str]:
            seen = []
            for sel in selectors:
                try:
                    nodes = await page.query_selector_all(sel)
                    for node in nodes:
                        try:
                            val = await node.get_attribute(attr)
                            if val and val not in seen:
                                seen.append(val)
                        except Exception:
                            continue
                except Exception:
                    continue
            return seen

        async def extract_post_date(page: Union[Page, Frame]) -> str:
            """尽可能提取 YYYY-MM-DD 格式的发布日期文本（支持相对时间）。
            优先使用 .note-content .date 的文本，形如：
            - 09-01 江苏 -> 今年-09-01
            - 4天前 上海 -> 以当前时间回推 4 天
            其次再回退到 time[datetime]、meta、正文文本与脚本。
            """
            import re as _re
            from datetime import datetime, timedelta

            def _fmt(y: int, m: int, d: int) -> str:
                return f"{y:04d}-{m:02d}-{d:02d}"

            now = datetime.now()

            # 0) 优先从 .note-content .date 读取
            try:
                date_text = await first_text([".note-content .date"], page)
                if date_text:
                    t = date_text.strip()
                    # 先尝试完整日期（含年）
                    m = _re.search(r"(20\d{2})[-/\.](\d{1,2})[-/\.]([0-3]?\d)", t)
                    if m:
                        return _fmt(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    # 再尝试 MM-DD（忽略后续的城市）
                    m2 = _re.search(r"(\d{1,2})[-/\.](\d{1,2})", t)
                    if m2:
                        return _fmt(now.year, int(m2.group(1)), int(m2.group(2)))
                    # 相对时间（X分钟前/小时前/天前/周前/月前/年前，或 昨天/前天/今天）
                    rel_pats = [
                        (r"(\d+)\s*分钟前", 'minutes'),
                        (r"(\d+)\s*小?时前", 'hours'),
                        (r"(\d+)\s*天前", 'days'),
                        (r"(\d+)\s*周前", 'weeks'),
                        (r"(\d+)\s*月前", 'months'),
                        (r"(\d+)\s*年前", 'years'),
                    ]
                    for pat, unit in rel_pats:
                        mr = _re.search(pat, t)
                        if mr:
                            n = int(mr.group(1))
                            if unit == 'minutes':
                                dt = now - timedelta(minutes=n)
                            elif unit == 'hours':
                                dt = now - timedelta(hours=n)
                            elif unit == 'days':
                                dt = now - timedelta(days=n)
                            elif unit == 'weeks':
                                dt = now - timedelta(weeks=n)
                            elif unit == 'months':
                                dt = now - timedelta(days=30 * n)
                            else:
                                dt = now - timedelta(days=365 * n)
                            return _fmt(dt.year, dt.month, dt.day)
                    if '昨天' in t:
                        dt = now - timedelta(days=1)
                        return _fmt(dt.year, dt.month, dt.day)
                    if '前天' in t:
                        dt = now - timedelta(days=2)
                        return _fmt(dt.year, dt.month, dt.day)
                    if '今天' in t:
                        return _fmt(now.year, now.month, now.day)
            except Exception:
                pass

            # 1) time[datetime] 或 meta
            try:
                dt_attr = await page.evaluate(
                    "() => {\n"
                    "  const t = document.querySelector('time[datetime]');\n"
                    "  if (t) return t.getAttribute('datetime') || '';\n"
                    "  const m1 = document.querySelector('meta[property=\"article:published_time\"]');\n"
                    "  if (m1) return m1.getAttribute('content') || '';\n"
                    "  const m2 = document.querySelector('meta[name=\"publish_date\"], meta[name=\"pubdate\"]');\n"
                    "  if (m2) return m2.getAttribute('content') || '';\n"
                    "  return '';\n"
                    "}"
                )
                if dt_attr:
                    m = _re.search(r"(\d{4})[-/\.](\d{1,2})[-/\.]([0-3]?\d)", dt_attr)
                    if m:
                        return _fmt(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            except Exception:
                pass

            # 2) 正文文本/相对时间
            try:
                body_text = await page.evaluate("document.body.innerText")
                m = _re.search(r"(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.]((?:0?[1-9])|[12]\d|3[01])", body_text)
                if m:
                    return _fmt(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                m2 = _re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日", body_text)
                if m2:
                    return _fmt(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
                rel_patterns = [
                    (r"(\d+)\s*分钟前", 'minutes'),
                    (r"(\d+)\s*小?时前", 'hours'),
                    (r"(\d+)\s*天前", 'days'),
                    (r"(\d+)\s*周前", 'weeks'),
                    (r"(\d+)\s*月前", 'months'),
                    (r"(\d+)\s*年前", 'years'),
                ]
                for pat, unit in rel_patterns:
                    mr = _re.search(pat, body_text)
                    if mr:
                        n = int(mr.group(1))
                        if unit == 'minutes':
                            dt = now - timedelta(minutes=n)
                        elif unit == 'hours':
                            dt = now - timedelta(hours=n)
                        elif unit == 'days':
                            dt = now - timedelta(days=n)
                        elif unit == 'weeks':
                            dt = now - timedelta(weeks=n)
                        elif unit == 'months':
                            dt = now - timedelta(days=30 * n)
                        else:
                            dt = now - timedelta(days=365 * n)
                        return _fmt(dt.year, dt.month, dt.day)
                if '昨天' in body_text:
                    dt = now - timedelta(days=1)
                    return _fmt(dt.year, dt.month, dt.day)
                if '前天' in body_text:
                    dt = now - timedelta(days=2)
                    return _fmt(dt.year, dt.month, dt.day)
                if '今天' in body_text:
                    return _fmt(now.year, now.month, now.day)
            except Exception:
                pass

            # 3) 退化：候选选择器文本
            try:
                t_text = await first_text(time_candidates, page)
                if t_text:
                    m = _re.search(r"(20\d{2})[-/\.](0?[1-9]|1[0-2])[-/\.]((?:0?[1-9])|[12]\d|3[01])", t_text)
                    if m:
                        return _fmt(int(m.group(1)), int(m.group(2)), int(m.group(3)))
                    m2 = _re.search(r"(20\d{2})年\s*(\d{1,2})月\s*(\d{1,2})日", t_text)
                    if m2:
                        return _fmt(int(m2.group(1)), int(m2.group(2)), int(m2.group(3)))
            except Exception:
                pass

            # 4) HTML 中的 JSON/脚本查找
            try:
                html = await page.content()
                m = _re.search(r'"(?:publish(?:Time|_time|Date|_date)|time)"\s*:\s*"(20\d{2}[-/\.]\d{1,2}[-/\.]\d{1,2})', html)
                if m:
                    y, mo, d = [int(x) for x in _re.split(r"[-/.]", m.group(1))]
                    return _fmt(y, mo, d)
                m2 = _re.search(r'"(?:publish(?:Time|_time)|time)"\s*:\s*(\d{10,13})', html)
                if m2:
                    ts = int(m2.group(1))
                    if ts > 10**12:
                        ts = ts // 1000
                    dt = datetime.fromtimestamp(ts)
                    return _fmt(dt.year, dt.month, dt.day)
            except Exception:
                pass
            return ""


        async def extract_image_urls(page: Union[Page, Frame]) -> List[str]:
            """提取笔记详情页的大图 URL，优先解析 `.swiper-wrapper img` 节点。"""

            def _normalize_url(raw: str, base_url: str) -> str:
                if not raw:
                    return ""
                candidate = raw.strip()
                if not candidate or candidate.startswith("data:"):
                    return ""
                if candidate.startswith("//"):
                    scheme = "https:" if base_url.startswith("https") else "http:"
                    return scheme + candidate
                if candidate.startswith("http://") or candidate.startswith("https://"):
                    return candidate
                if base_url:
                    return urljoin(base_url, candidate)
                return candidate

            base_url = ""
            try:
                base_url = page.url
            except Exception:
                base_url = ""
            if not base_url:
                fallback_base = note_info.get("raw_href") or note_info.get("url") or ""
                if fallback_base.startswith("//"):
                    base_url = "https:" + fallback_base
                elif fallback_base.startswith("/"):
                    base_url = f"https://www.xiaohongshu.com{fallback_base}"
                else:
                    base_url = fallback_base

            urls: List[str] = []
            try:
                swiper_items = await page.evaluate(
                    "() => {\n"
                    "  const pickFromSrcset = (s) => {\n"
                    "    if (!s) return '';\n"
                    "    const parts = s.split(',').map(p => p.trim()).filter(Boolean);\n"
                    "    if (!parts.length) return '';\n"
                    "    const last = parts[parts.length - 1];\n"
                    "    return (last.split(' ')[0] || '').trim();\n"
                    "  };\n"
                    "  const slides = Array.from(document.querySelectorAll('.swiper-wrapper .swiper-slide'));\n"
                    "  const mainSlides = slides.filter(slide => !slide.classList.contains('swiper-slide-duplicate'));\n"
                    "  const targetSlides = mainSlides.length ? mainSlides : slides;\n"
                    "  const res = [];\n"
                    "  const seen = new Set();\n"
                    "  const pushCandidate = (order, img) => {\n"
                    "    if (!img) return;\n"
                    "    const src = img.getAttribute('src') || '';\n"
                    "    const dataSrc = img.getAttribute('data-src') || img.dataset.src || '';\n"
                    "    const srcset = pickFromSrcset(img.getAttribute('srcset') || '');\n"
                    "    const candidates = [src, dataSrc, srcset].filter(Boolean);\n"
                    "    if (!candidates.length) return;\n"
                    "    res.push({ order, candidates });\n"
                    "  };\n"
                    "  if (targetSlides.length) {\n"
                    "    targetSlides.forEach((slide, order) => {\n"
                    "      const idxAttr = slide.getAttribute('data-swiper-slide-index');\n"
                    "      const hasIdx = idxAttr !== null && idxAttr !== '';\n"
                    "      const realIndex = hasIdx ? Number(idxAttr) : order;\n"
                    "      if (Number.isNaN(realIndex)) return;\n"
                    "      if (hasIdx && seen.has(realIndex)) return;\n"
                    "      if (hasIdx) seen.add(realIndex);\n"
                    "      const img = slide.querySelector('img');\n"
                    "      pushCandidate(realIndex, img);\n"
                    "    });\n"
                    "  }\n"
                    "  if (!res.length) {\n"
                    "    const imgs = Array.from(document.querySelectorAll('.swiper-wrapper img'));\n"
                    "    imgs.forEach((img, order) => pushCandidate(order, img));\n"
                    "  }\n"
                    "  return res;\n"
                    "}"
                )
                if swiper_items:
                    swiper_items = sorted(swiper_items, key=lambda item: item.get('order', 0))
                    for item in swiper_items:
                        for candidate in item.get('candidates') or []:
                            normalized = _normalize_url(candidate, base_url)
                            if normalized and normalized not in urls:
                                urls.append(normalized)
                                break
            except Exception:
                urls = []

            if not urls:
                try:
                    fallback_items = await page.evaluate(
                        "() => {\n"
                        "  const pickFromSrcset = (s) => {\n"
                        "    if (!s) return '';\n"
                        "    const parts = s.split(',').map(p => p.trim()).filter(Boolean);\n"
                        "    if (!parts.length) return '';\n"
                        "    const last = parts[parts.length - 1];\n"
                        "    return (last.split(' ')[0] || '').trim();\n"
                        "  };\n"
                        "  const parseNumeric = (val) => {\n"
                        "    if (val === undefined || val === null) return null;\n"
                        "    const num = Number(val);\n"
                        "    return Number.isFinite(num) ? num : null;\n"
                        "  };\n"
                        "  const res = [];\n"
                        "  const pushCandidate = (img, domOrder) => {\n"
                        "    if (!img) return;\n"
                        "    const dataset = img.dataset || {};\n"
                        "    const orderSources = [\n"
                        "      dataset.index, dataset.imageIndex, dataset.idx, dataset.order, dataset.no, dataset.seq,\n"
                        "      img.getAttribute('data-index'),\n"
                        "      img.getAttribute('data-image-index'),\n"
                        "      img.getAttribute('data-idx'),\n"
                        "      img.getAttribute('data-order'),\n"
                        "    ];\n"
                        "    let order = null;\n"
                        "    for (const src of orderSources) {\n"
                        "      const num = parseNumeric(src);\n"
                        "      if (num !== null) { order = num; break; }\n"
                        "    }\n"
                        "    const src = img.getAttribute('src') || '';\n"
                        "    const dataSrc = img.getAttribute('data-src') || dataset.src || '';\n"
                        "    const srcset = pickFromSrcset(img.getAttribute('srcset') || '');\n"
                        "    const candidates = [src, dataSrc, srcset].filter(Boolean);\n"
                        "    if (!candidates.length) return;\n"
                        "    res.push({ order, domOrder, candidates });\n"
                        "  };\n"
                        "  const imgs = Array.from(document.querySelectorAll('article img, .note-content img'));\n"
                        "  imgs.forEach((img, idx) => pushCandidate(img, idx));\n"
                        "  return res;\n"
                        "}"
                    )
                    if fallback_items:
                        def _fallback_sort_key(item):
                            order = item.get('order')
                            dom_order = item.get('domOrder', 0)
                            return (order if order is not None else float('inf'), dom_order)

                        fallback_items = sorted(fallback_items, key=_fallback_sort_key)
                        seen_normalized = set()
                        for item in fallback_items:
                            for candidate in item.get('candidates') or []:
                                normalized = _normalize_url(candidate, base_url)
                                if normalized and normalized not in seen_normalized:
                                    seen_normalized.add(normalized)
                                    urls.append(normalized)
                                    break
                except Exception:
                    pass

            return urls


        async def extract_interactions(page: Union[Page, Frame]) -> Dict[str, str]:
            """提取互动数据：严格根据 .interact-container 中的分隔节点取数。
            - 点赞：.like-wrapper .count
            - 收藏：.collect-wrapper .count
            - 评论：.chat-wrapper .count
            - 转发：.share-wrapper .count（若有）
            """
            import re as _re
            def _norm_num(s: str) -> str:
                if not s:
                    return ''
                t = s.strip().lower()
                m = _re.search(r"([\d\.]+)\s*([wk]?)", t)
                if not m:
                    return ''
                num = float(m.group(1))
                unit = m.group(2)
                if unit == 'w':
                    return str(int(num * 10000))
                if unit == 'k':
                    return str(int(num * 1000))
                return str(int(num)) if num.is_integer() else str(num)

            result = {'likes': '', 'collections': '', 'comments': '', 'shares': ''}
            try:
                has_container = await page.locator('.interact-container').first.count() > 0
                if has_container:
                    data = await page.evaluate(
                        "() => {\n"
                        "  const root = document.querySelector('.interact-container');\n"
                        "  const pick = (sel) => { const el = root && root.querySelector(sel); return el ? (el.textContent||'').trim() : ''; };\n"
                        "  return {\n"
                        "    likes: pick('.like-wrapper .count') || pick('[class*=like] .count') || pick('[class*=like]'),\n"
                        "    collections: pick('.collect-wrapper .count') || pick('[class*=collect] .count') || pick('[class*=favorite] .count') || pick('[class*=bookmark] .count'),\n"
                        "    comments: pick('.chat-wrapper .count') || pick('[class*=comment] .count') || pick('[class*=chat] .count') || pick('[class*=reply] .count'),\n"
                        "    shares: pick('.share-wrapper .count') || pick('[class*=share] .count') || pick('[class*=repost] .count') || pick('[class*=forward] .count'),\n"
                        "  };\n"
                        "}"
                    )
                    result['likes'] = _norm_num((data or {}).get('likes'))
                    result['collections'] = _norm_num((data or {}).get('collections'))
                    result['comments'] = _norm_num((data or {}).get('comments'))
                    result['shares'] = _norm_num((data or {}).get('shares'))

                # 兜底：通用选择器（页面改版时）
                if not any(result.values()):
                    candidates = {
                        'likes': ['.like-wrapper .count', '[class*=like] .count', '[class*=like]'],
                        'collections': ['.collect-wrapper .count', '[class*=collect] .count', '[class*=favorite] .count', '[class*="fav"] .count', '[class*=bookmark] .count'],
                        'comments': ['.chat-wrapper .count', '.comment-wrapper .count', '[class*=comment] .count'],
                        'shares': ['.share-wrapper .count', '[class*=share] .count', '[class*=repost] .count', '[class*=forward] .count'],
                    }
                    for key, sels in candidates.items():
                        for sel in sels:
                            try:
                                txt = await first_text([sel], page)
                                n = _norm_num(txt)
                                if n:
                                    result[key] = n
                                    break
                            except Exception:
                                continue
            except Exception:
                pass

            return result

        try:
            # --- 抓取内容文本（多候选） ---
            content = await first_text(content_candidates, pg)

            # --- 抓取发布时间（转换为 YYYY-MM-DD） ---
            post_time = await extract_post_date(pg)
            

            # --- 打印图片结构供确认，并抓取图片URL（过滤头像/图标） ---
            
            unique_image_urls = await extract_image_urls(pg)

            # 若首次解析获取不到正文或图片，启用“直开详情页”兜底。
            # 直接以 raw_href 或 explore/<id>?query 生成绝对 URL，在新标签页中打开并重新解析。
            need_fallback = (not content or not content.strip() or not unique_image_urls)
            if need_fallback:
                try:
                    fb_url = _build_direct_note_url() or _build_explore_url_with_query() or note_info.get('url')
                    if fb_url and fb_url.startswith('/'):
                        fb_url = f"https://www.xiaohongshu.com{fb_url}"
                except Exception:
                    fb_url = note_info.get('url')
                    if fb_url and fb_url.startswith('/'):
                        fb_url = f"https://www.xiaohongshu.com{fb_url}"

                if fb_url:
                    try:
                        extra_note_page = await self.context.new_page()
                        await extra_note_page.goto(fb_url, wait_until="domcontentloaded")
                        try:
                            await extra_note_page.wait_for_load_state("networkidle")
                        except Exception:
                            pass
                        try:
                            for _ in range(4):
                                await extra_note_page.evaluate("window.scrollBy(0, Math.max(300, window.innerHeight))")
                                await extra_note_page.wait_for_timeout(700)
                        except Exception:
                            pass

                        # 切换解析上下文为新开的详情页
                        pg = extra_note_page
                        clicked_navigation = True

                        # 重新解析
                        content2 = await first_text(content_candidates, pg)
                        imgs2 = await extract_image_urls(pg)
                        # 时间也可能在直开页更完整
                        post_time2 = await extract_post_date(pg)
                        if content2 and content2.strip():
                            content = content2
                        if imgs2:
                            unique_image_urls = imgs2
                        if post_time2:
                            post_time = post_time2
                    except Exception:
                        # 兜底失败则继续使用原解析结果
                        pass

            # --- 其他字段 ---
            note_details = {}

            # 标题
            try:
                note_details["title"] = await first_text(title_candidates, pg)
                if not note_details["title"] and isinstance(pg, Page):
                    # 回退到页面标题
                    try:
                        note_details["title"] = await pg.title()
                    except Exception:
                        pass
            except Exception:
                note_details["title"] = ""

            # 作者
            try:
                note_details["author_name"] = await first_text(author_candidates, pg)
                if not note_details["author_name"]:
                    # 回退：尝试从链接文本提取
                    try:
                        loc = pg.locator("a[href*='/user/profile']").first
                        if await loc.count() > 0:
                            note_details["author_name"] = (await loc.inner_text()).strip()
                    except Exception:
                        pass
            except Exception:
                note_details["author_name"] = ""

            # 标签
            try:
                tags_texts = []
                for sel in tags_candidates:
                    try:
                        els = await pg.query_selector_all(sel)
                        for el in els:
                            try:
                                t = (await el.inner_text()).strip()
                                if t:
                                    tags_texts.append(t)
                            except Exception:
                                continue
                    except Exception:
                        continue
                note_details["tags"] = " ".join(tags_texts)
            except Exception:
                note_details["tags"] = ""

            # 互动数据
            inter = await extract_interactions(pg)
            def _nz(v: str) -> str:
                return v if (v and v.strip()) else "0"
            note_details["likes_count"] = _nz(inter.get('likes'))
            note_details["collections_count"] = _nz(inter.get('collections'))
            note_details["comments_count"] = _nz(inter.get('comments'))
            note_details["shares_count"] = _nz(inter.get('shares'))

            # --- 组合所有字段 ---
            # 使用真实打开页的 URL；若为浮层 Frame 或 about:blank，则回退到 raw_href/full_url
            current_url = None
            try:
                if isinstance(pg, Page):
                    current_url = pg.url
            except Exception:
                current_url = None
            if (not current_url) or current_url.startswith("about:") or current_url.startswith("data:"):
                current_url = note_info.get("raw_href") or note_info.get("url") or note_info['url']
                if current_url.startswith("/"):
                    current_url = f"https://www.xiaohongshu.com{current_url}"
            note_details.update({
                "note_id": note_info['note_id'],
                "post_url": current_url,
                "content": (content or "").strip(),
                "images": unique_image_urls,
                "post_time": post_time,
            })

            # 清理：
            # - 弹窗打开：关闭弹窗
            # - 浮层 iframe：关闭浮层（按 Esc 或点击关闭按钮）
            # - 同页导航或兜底 goto：返回列表页（优先使用 restore_url，避免误回首页）
            try:
                if clicked_navigation:
                    if popup_page is not None and not popup_page.is_closed():
                        await popup_page.close()
                    if extra_note_page is not None and not extra_note_page.is_closed():
                        await extra_note_page.close()
                    elif isinstance(pg, Frame):
                        # 浮层关闭
                        try:
                            await self.page.keyboard.press("Escape")
                            await self.page.wait_for_timeout(500)
                        except Exception:
                            pass
                        try:
                            close_btn = self.page.locator("div.container[data-v-fc1041fa] .close-icon").first
                            if await close_btn.count() > 0:
                                await close_btn.click()
                        except Exception:
                            pass
                    elif pg is self.page:
                        try:
                            if restore_url:
                                await self._goto_with_retry(restore_url)
                                try:
                                    await self.page.wait_for_load_state("networkidle")
                                except Exception:
                                    pass
                            else:
                                await self.page.go_back()
                        except Exception:
                            pass
                else:
                    if pg is self.page:
                        try:
                            if restore_url:
                                await self._goto_with_retry(restore_url)
                                try:
                                    await self.page.wait_for_load_state("networkidle")
                                except Exception:
                                    pass
                            else:
                                await self.page.go_back()
                        except Exception:
                            pass
            except Exception:
                pass

            print(f"笔记 {note_info['note_id']} 详情爬取成功，URL: {current_url}")
            return note_details

        except Exception as e:
            print(f"爬取笔记 {note_info['note_id']} 详情失败: {e}")
            # --- DEBUG: 保存详情页HTML & 截图以供分析 ---
            try:
                html_content = await pg.content()
                with open("debug_note_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                await pg.screenshot(path="debug_note_screenshot.png", full_page=True)
                print("!!! DEBUG文件 `debug_note_page.html` 与 `debug_note_screenshot.png` 已保存，请查看。")
            except Exception as save_e:
                print(f"保存debug文件时发生错误: {save_e}")
            # --- DEBUG END ---
            return None
