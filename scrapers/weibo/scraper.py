import random
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError


class WeiboHomeScraper:
    """
    负责抓取微博主页内容的 Playwright 封装。
    """

    def __init__(self, context: BrowserContext):
        self.context = context
        self.page: Optional[Page] = None

    async def _new_prepared_page(self) -> Page:
        page = await self.context.new_page()
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
        )
        return page

    async def _ensure_page(self) -> Page:
        if self.page is None or self.page.is_closed():
            self.page = await self._new_prepared_page()
        return self.page

    async def _goto_page(self, page: Page, url: str) -> None:
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            return
        except PlaywrightTimeoutError:
            pass
        # In headless mode, the "load" event can hang; fall back to commit.
        await page.goto(url, wait_until="commit", timeout=30000)

    async def close(self):
        try:
            if self.page and not self.page.is_closed():
                await self.page.close()
        except Exception:
            pass

    @staticmethod
    def _normalize_stat(raw: Optional[str]) -> str:
        if not raw:
            return "0"
        txt = str(raw).strip().lower()
        if not txt:
            return "0"
        match = re.search(r"([\d\.]+)\s*([万w]?)(?:\+)?", txt)
        if not match:
            digits = re.sub(r"\D", "", txt)
            return digits or "0"
        value = float(match.group(1))
        unit = match.group(2)
        if unit in ("万", "w"):
            value *= 10000
        return str(int(value)) if value.is_integer() else str(int(round(value)))

    @staticmethod
    def _normalize_post_id(href: Optional[str]) -> Optional[str]:
        if not href:
            return None
        target = href.strip()
        if not target:
            return None
        # 统一成路径形式
        if target.startswith("http"):
            parts = target.split("?")[0].rstrip("/").split("/")
            candidate = parts[-1] if parts else ""
        else:
            candidate = target.split("?")[0].rstrip("/").split("/")[-1]
        if re.fullmatch(r"[A-Za-z0-9]+", candidate or ""):
            return candidate
        return None

    @staticmethod
    def _normalize_url(href: str) -> str:
        if not href:
            return ""
        if href.startswith("http://") or href.startswith("https://"):
            return href
        if href.startswith("//"):
            return "https:" + href
        if href.startswith("/"):
            return f"https://weibo.com{href}"
        return f"https://weibo.com/{href.lstrip('/')}"

    @staticmethod
    def _normalize_post_time(raw: Optional[str]) -> str:
        if not raw:
            return ""
        raw_str = str(raw).strip()
        if not raw_str:
            return ""

        now = datetime.now()

        # 预处理文本：去除冗余信息、统一分隔符
        text = raw_str.replace("\u3000", " ").replace("：", ":").replace("／", "/")
        # 去掉来源等附加信息
        text = re.split(r"\s*(?:来自|from)\s*", text, 1)[0]
        text = text.split("·")[0]
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            return ""

        lower_text = text.lower()
        # AM/PM 标记
        ampm = None
        if any(word in text for word in ("下午", "晚上", "夜间", "傍晚", "午后", "晚间")) or re.search(r"\bpm\b", lower_text):
            ampm = "pm"
        elif any(word in text for word in ("上午", "清晨", "凌晨", "早上")) or re.search(r"\bam\b", lower_text):
            ampm = "am"

        # 去除 AM/PM 用语后用于解析
        text_clean = re.sub(r"(上午|下午|晚上|夜间|凌晨|清晨|早上|午后|晚间|AM|PM|am|pm)", "", text, flags=re.I).strip()

        def apply_ampm(dt: datetime, include_time: bool) -> datetime:
            if not include_time or ampm is None:
                return dt
            hour = dt.hour
            if ampm == "pm" and hour < 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            return dt.replace(hour=hour)

        def format_dt(dt: datetime, include_time: bool) -> str:
            dt = dt.replace(microsecond=0)
            if include_time:
                if dt.second:
                    return dt.strftime("%Y-%m-%d %H:%M:%S")
                return dt.strftime("%Y-%m-%d %H:%M")
            return dt.strftime("%Y-%m-%d")

        # 相对时间（秒/分钟/小时/天/周/月/年）
        rel_map = [
            (r"(\d+)\s*秒前", lambda n: timedelta(seconds=n)),
            (r"(\d+)\s*分钟前", lambda n: timedelta(minutes=n)),
            (r"(\d+)\s*小?时前", lambda n: timedelta(hours=n)),
            (r"(\d+)\s*天前", lambda n: timedelta(days=n)),
            (r"(\d+)\s*周前", lambda n: timedelta(weeks=n)),
            (r"(\d+)\s*月前", lambda n: timedelta(days=30 * n)),
            (r"(\d+)\s*年前", lambda n: timedelta(days=365 * n)),
        ]
        for pat, delta_fn in rel_map:
            mr = re.search(pat, text_clean)
            if mr:
                n = int(mr.group(1))
                dt = now - delta_fn(n)
                dt = dt.replace(microsecond=0)
                return format_dt(dt, include_time=True)

        # 特殊关键字：今天/昨天/前天
        day_keywords = (
            ("今天", 0),
            ("昨日", 1),
            ("昨天", 1),
            ("前天", 2),
        )
        for keyword, days_ago in day_keywords:
            if keyword in text_clean:
                time_match = re.search(rf"{keyword}\s*(\d{{1,2}}):(\d{{1,2}})(?::(\d{{1,2}}))?", text_clean)
                base_dt = (now - timedelta(days=days_ago)).replace(microsecond=0)
                if time_match:
                    hour = int(time_match.group(1))
                    minute = int(time_match.group(2))
                    second = int(time_match.group(3) or 0)
                    dt = base_dt.replace(hour=hour, minute=minute, second=second)
                    dt = apply_ampm(dt, include_time=True)
                    return format_dt(dt, include_time=True)
                dt = base_dt.replace(hour=0, minute=0, second=0)
                return format_dt(dt, include_time=False)

        if "刚刚" in text_clean:
            return format_dt(now, include_time=True)

        # 绝对日期解析
        normalized = text_clean
        normalized = re.sub(r"(星期|周)[一二三四五六日天]", "", normalized)
        normalized = normalized.replace("年", "-").replace("月", "-").replace("日", "")
        normalized = normalized.replace("/", "-").replace(".", "-")
        normalized = re.sub(r"\s+", " ", normalized).strip(" ,-")

        fmt_candidates = [
            ("%Y-%m-%d %H:%M:%S", True),
            ("%Y-%m-%d %H:%M", True),
            ("%Y-%m-%d %H:%M:%S %z", True),
            ("%Y-%m-%d", False),
        ]
        for fmt, include_time in fmt_candidates:
            try:
                dt = datetime.strptime(normalized, fmt)
                dt = apply_ampm(dt, include_time)
                return format_dt(dt, include_time=include_time)
            except Exception:
                continue

        # 处理两位年份，如 "25-12-21 15:46" 表示 2025-12-21
        yymmdd_match = re.match(
            r"(?P<yy>\d{2})-(?P<month>\d{1,2})-(?P<day>\d{1,2})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2})(?::(?P<second>\d{1,2}))?)?$",
            normalized,
        )
        if yymmdd_match:
            yy = int(yymmdd_match.group("yy"))
            year = 2000 + yy if yy < 100 else yy
            month = int(yymmdd_match.group("month"))
            day = int(yymmdd_match.group("day"))
            hour = int(yymmdd_match.group("hour") or 0)
            minute = int(yymmdd_match.group("minute") or 0)
            second = int(yymmdd_match.group("second") or 0)
            try:
                dt = datetime(year, month, day, hour, minute, second)
                dt = apply_ampm(dt, include_time=True)
                return format_dt(dt, include_time=True)
            except Exception:
                pass

        # 处理缺少年份的情况，例如 "11-4 20:16"
        mmdd_match = re.match(
            r"(?P<month>\d{1,2})-(?P<day>\d{1,2})(?:\s+(?P<hour>\d{1,2}):(?P<minute>\d{1,2})(?::(?P<second>\d{1,2}))?)?$",
            normalized,
        )
        if mmdd_match:
            month = int(mmdd_match.group("month"))
            day = int(mmdd_match.group("day"))
            hour = int(mmdd_match.group("hour") or 0)
            minute = int(mmdd_match.group("minute") or 0)
            second = int(mmdd_match.group("second") or 0)
            year = now.year
            try:
                dt = datetime(year, month, day, hour, minute, second)
            except ValueError:
                # 回退一分钟以防止无效日期
                return ""
            if dt > now + timedelta(days=1):
                # 跨年情况：例如当前为 1 月，却出现 11 月，判定为上一年
                try:
                    dt = dt.replace(year=year - 1)
                except ValueError:
                    return ""
            dt = apply_ampm(dt, include_time=bool(mmdd_match.group("hour")))
            return format_dt(dt, include_time=bool(mmdd_match.group("hour")))

        # 无法解析时返回空
        return ""

    @staticmethod
    async def _first_text(page: Page, selectors: List[str]) -> str:
        for sel in selectors:
            try:
                loc = page.locator(sel).first
                if await loc.count() == 0:
                    continue
                try:
                    await loc.wait_for(state="attached", timeout=3000)
                except Exception:
                    pass
                text = await loc.inner_text()
                if text and text.strip():
                    return text.strip()
            except Exception:
                continue
        return ""

    async def scrape_home_posts(
        self,
        user_url: str,
        max_posts: int = 20,
        scrolls: int = 1,
    ) -> List[Dict]:
        """
        爬取微博主页的内容列表。
        """
        page = await self._ensure_page()
        await self._goto_page(page, user_url)

        try:
            await page.wait_for_selector(
                'article, div[class*="vue-recycle-list"], div[class*="Feed"]',
                timeout=20000,
            )
        except Exception:
            await page.wait_for_timeout(2000)

        # 初次加载后等待，确保首屏渲染完整
        await page.wait_for_timeout(1000)
        await self._ensure_logged_in(page)

        seen_ids: set[str] = set()
        collected_by_idx: Dict[int, Dict] = {}
        collected_order: List[Dict] = []

        def _parse_idx(raw_val, num_val) -> Optional[int]:
            if raw_val is not None:
                raw_str = str(raw_val).strip()
                if raw_str:
                    import re as _re
                    m = _re.search(r"-?\d+", raw_str)
                    if m:
                        try:
                            return int(m.group(0))
                        except Exception:
                            pass
            if isinstance(num_val, (int, float)):
                try:
                    import math as _math
                    if not _math.isnan(num_val):
                        return int(num_val)
                except Exception:
                    pass
            return None

        async def collect_current(stage: str) -> bool:
            """采集当前 wrapper 中的所有条目，按 data-index 去重并收集。"""
            start_scroll: Optional[float] = None
            targeted_indices: set[int] = set()

            def _next_missing_idx() -> int:
                idx = 0
                while idx in collected_by_idx:
                    idx += 1
                return idx

            def _stage_target_limit() -> Optional[int]:
                if "首屏" in stage or "滚动前" in stage:
                    return 3
                return None

            target_limit = _stage_target_limit()

            attempt = 0
            max_attempts = 4
            while attempt < max_attempts:
                data = await page.evaluate(
                    """() => {
                        const wrapper = document.querySelector('.vue-recycle-scroller__item-wrapper');
                        if (!wrapper) return [];
                        const items = Array.from(wrapper.querySelectorAll('.wbpro-scroller-item'));
                        return items.map((item, order) => {
                            const dataset = item.dataset || {};
                            const idxAttr = item.getAttribute('data-index') ?? dataset.index ?? '';
                            let idxNum = null;
                            if (idxAttr !== undefined && idxAttr !== null && idxAttr !== '') {
                                const num = Number(idxAttr);
                                if (!Number.isNaN(num)) {
                                    idxNum = num;
                                }
                            }
                            const article = item.querySelector('article');
                            const header = (article && article.querySelector('header')) || item.querySelector('header');
                            const timeLink = header ? header.querySelector('a[class*=\"_time_\"]') : null;
                            const linkSelectors = [
                                'a[class*=\"head-info_time_\"]',
                                'a[href*=\"m.weibo.cn/detail\"]',
                                'a[href*=\"/status/\"]',
                                'a[href*=\"/detail/\"]',
                                'a[href*=\"/profile/\"]',
                            ];
                            let link = timeLink || null;
                            if (!link) {
                                for (const sel of linkSelectors) {
                                    const candidate = item.querySelector(sel);
                                    if (candidate) { link = candidate; break; }
                                }
                            }
                            const normalizeHref = (u) => {
                                if (!u) return '';
                                const val = String(u).trim();
                                if (!val) return '';
                                if (/\\.(?:jpe?g|png|gif|webp|svg)(\\?|$)/i.test(val)) return '';
                                return val;
                            };
                            const headerEl = header && header.hasAttribute('id') ? header : item.querySelector('header[id]');
                            const headerId = headerEl ? (headerEl.getAttribute('id') || '') : '';
                            const headerLink = headerEl ? headerEl.querySelector('a[class*=\"_time_\"], a[class*=\"time_\"]') : null;
                            const headerHref = normalizeHref(headerLink ? (headerLink.getAttribute('href') || '') : '');
                            const href = normalizeHref(link ? (link.getAttribute('href') || '') : '');
                            const rawTime = link ? (link.textContent || '').trim() : '';
                            const rect = item.getBoundingClientRect();
                            const authorEl = item.querySelector('a[class*=\"head-info_nick_\"], a[class*=\"name\"], a[node-type=\"feed_list_originNick\"]');
                            const author = authorEl ? (authorEl.textContent || '').trim() : '';
                            const mid = item.getAttribute('mid') || dataset.mid || '';
                            const feedId = item.getAttribute('data-id') || dataset.id || '';
                            const hasVideo = !!item.querySelector('[class*="card-video"]');
                            return {
                                idxRaw: idxAttr,
                                idxNum,
                                order,
                                headerHref,
                                href,
                                rawTime,
                                headerId,
                                author,
                                top: (rect.top || 0) + (window.scrollY || 0),
                                mid,
                                feedId,
                                hasVideo,
                            };
                        });
                    }"""
                )
                if not isinstance(data, list):
                    return False

                def _sort_key(item):
                    idx_val = _parse_idx(item.get("idxRaw"), item.get("idxNum"))
                    top_val = item.get("top", float("inf"))
                    order_val = item.get("order", 0)
                    if idx_val is None:
                        return (float("inf"), top_val, order_val)
                    return (idx_val, top_val, order_val)

                data_sorted = sorted(data, key=_sort_key)

                before_count = len(collected_by_idx)
                suffix = "" if attempt == 0 else f" (nudge {attempt})"
                print(f"[WeiboHomeScraper] {stage}{suffix} 当前 wrapper 条目：")
                for entry in data_sorted:
                    idx_val = _parse_idx(entry.get("idxRaw"), entry.get("idxNum"))
                    if idx_val is None and entry.get("idxRaw"):
                        print(f"[WeiboHomeScraper] 无法解析 idxRaw={entry.get('idxRaw')} idxNum={entry.get('idxNum')} order={entry.get('order')} top={entry.get('top')}")
                    header_href = entry.get("headerHref") or ""
                    href = header_href or entry.get("href") or ""
                    candidate_mid = entry.get("mid") or entry.get("feedId") or ""
                    header_id = entry.get("headerId") or ""
                    note_id = header_id or self._normalize_post_id(href)
                    if not note_id and candidate_mid:
                        note_id = candidate_mid.strip()
                    if not note_id:
                        raw_href = href or ""
                        if raw_href:
                            import urllib.parse as _urlparse
                            try:
                                parsed = _urlparse.urlparse(raw_href)
                                qs = _urlparse.parse_qs(parsed.query or "")
                                for key in ("mid", "id", "rid", "weibo_id"):
                                    if key in qs and qs[key]:
                                        note_id = qs[key][0]
                                        break
                            except Exception:
                                note_id = None
                    raw_time = entry.get("rawTime") or ""
                    author_name = entry.get("author") or ""
                    top_val = entry.get("top", float("inf"))
                    idx_display = entry.get("idxRaw")
                    if idx_display is None or idx_display == "":
                        idx_display = idx_val if idx_val is not None else "N/A"
                    is_new_idx = idx_val is not None and idx_val not in collected_by_idx
                    is_new_note = note_id and note_id not in seen_ids
                    tag = "     "

                    if is_new_idx:
                        post_time = self._normalize_post_time(raw_time)
                        entry_data = {
                            "idx": idx_val,
                            "idx_raw": idx_display,
                            "note_id": note_id or "",
                            "url": self._normalize_url(href),
                            "raw_href": href,
                            "header_href": header_href,
                            "post_time": post_time,
                            "author_name": author_name,
                            "raw_time": raw_time,
                            "top": top_val,
                            "is_video": bool(entry.get("hasVideo")),
                        }
                        collected_by_idx[idx_val] = entry_data
                        collected_order.append(entry_data)
                        tag = "(new-idx)"
                    elif is_new_note:
                        tag = "(new-note)"

                    if is_new_note:
                        seen_ids.add(note_id)

                    print(
                        f"  idx={idx_display} {tag} note_id={note_id or 'N/A'} header_id={header_id or 'N/A'} time_text={raw_time} author={author_name} href={href} header_href={header_href or 'N/A'} mid={candidate_mid or ''} top={top_val:.1f}"
                    )
                    if is_new_idx and len(collected_by_idx) >= max_posts:
                        return True

                added_new = len(collected_by_idx) > before_count
                if len(collected_by_idx) >= max_posts:
                    return True

                next_missing = _next_missing_idx()
                need_more = target_limit is not None and next_missing <= target_limit
                if need_more:
                    try:
                        targeted_indices.add(next_missing)
                        target_found = await page.evaluate(
                            """(idx) => {
                                const wrapper = document.querySelector('.vue-recycle-scroller__item-wrapper');
                                if (!wrapper) return false;
                                const selectors = [
                                    `.wbpro-scroller-item[data-index='${idx}']`,
                                    `.wbpro-scroller-item[data-virtual-index='${idx}']`,
                                    `.wbpro-scroller-item[data-index="${idx}"]`,
                                    `.wbpro-scroller-item[data-virtual-index="${idx}"]`
                                ];
                                let el = null;
                                for (const sel of selectors) {
                                    el = wrapper.querySelector(sel);
                                    if (el) break;
                                }
                                if (el) {
                                    el.style.outline = '2px solid rgba(255,0,0,0.3)';
                                    if (typeof el.scrollIntoView === 'function') {
                                        el.scrollIntoView({ block: 'center' });
                                        return true;
                                    }
                                }
                                return false;
                            }""",
                            next_missing,
                        )
                        if target_found:
                            await page.wait_for_timeout(600)
                            continue
                    except Exception:
                        pass

                if need_more:
                    # 仍有缺失索引需要加载，尝试轻推
                    pass
                else:
                    if added_new:
                        return False
                    else:
                        break

                if attempt < max_attempts - 1:
                    try:
                        if start_scroll is None:
                            start_scroll = await page.evaluate("() => window.scrollY || 0")
                        await page.evaluate(
                            """(step) => {
                                const current = window.scrollY || 0;
                                const vh = window.innerHeight || 800;
                                const base = Math.max(vh * 0.4, 220);
                                const extra = Math.min(vh * 0.35, 280);
                                const offset = base + extra * step;
                                window.scrollTo(0, current + offset);
                            }""",
                            attempt,
                        )
                        await page.wait_for_timeout(300)
                        if start_scroll is not None:
                            await page.evaluate(
                                """(target) => { window.scrollTo(0, target); }""",
                                start_scroll,
                            )
                        await page.wait_for_timeout(250)
                    except Exception:
                        pass
                    attempt += 1
                    continue
                break
            return len(collected_by_idx) >= max_posts

        await collect_current("首屏")

        for scroll_idx in range(max(0, scrolls)):
            if await collect_current(f"第 {scroll_idx + 1} 次滚动前"):
                break
            await page.evaluate("window.scrollBy(0, document.body.scrollHeight)")
            await page.wait_for_timeout(1000)
            if await collect_current(f"第 {scroll_idx + 1} 次滚动后"):
                break

        if collected_by_idx:
            entries_sorted = sorted(
                collected_by_idx.values(),
                key=lambda item: (
                    item.get("idx") if item.get("idx") is not None else float("inf"),
                    item.get("top", float("inf")),
                ),
            )
        entries_sorted = sorted(
            collected_by_idx.values(),
            key=lambda item: (
                item.get("idx") if item.get("idx") is not None else float("inf"),
                item.get("top", float("inf")),
            ),
        )
        print(f"[WeiboHomeScraper] 共收集 {len(entries_sorted)} 条帖子。")
        return entries_sorted[:max_posts]

    async def scrape_post_details(self, post_ref: Dict) -> Optional[Dict]:
        """
        根据列表项打开详情，抓取内容并整理为统一结构。
        """
        note_id_log = post_ref.get("note_id") or ""
        detail_url = (
            post_ref.get("url")
            or post_ref.get("header_href")
            or post_ref.get("raw_href")
            or ""
        )
        detail_url = self._normalize_url(detail_url)
        def _is_image_link(u: str) -> bool:
            if not u:
                return False
            try:
                core = u.split("#", 1)[0]
            except Exception:
                core = u
            return bool(re.search(r"\.(?:jpe?g|png|gif|webp|svg)(?:$|\\?)", core, re.IGNORECASE))
        def _log_detail(msg: str):
            print(f"[WeiboDetail] note_id={note_id_log or 'N/A'} url={detail_url} {msg}")
        if _is_image_link(detail_url):
            _log_detail("检测到图片链接，丢弃并尝试用 note_id 构造详情链接")
            detail_url = ""
        if not detail_url and note_id_log:
            detail_url = f"https://weibo.com/detail/{note_id_log}"
        if _is_image_link(detail_url):
            _log_detail("原因=链接仍为图片，放弃抓取")
            return None
        if not detail_url:
            _log_detail("原因=url为空")
            return None

        detail_page: Optional[Page] = None
        try:
            detail_page = await self._new_prepared_page()
            await self._goto_page(detail_page, detail_url)

            try:
                await self._ensure_logged_in(detail_page)
            except Exception as e:
                _log_detail(f"登录态失效或检查失败: {e}")
                return None

            try:
                await detail_page.wait_for_selector(
                    "article, div[class*='detail_wbtext_'], div[class*='WB_detail']",
                    timeout=15000,
                )
            except Exception:
                pass

            await detail_page.wait_for_timeout(2000)
            is_video_detail = False
            has_video_box_in_content = False
            try:
                video_locator = detail_page.locator('video, [class*="card-video"], [class*="video-player"], [class*="Video"]')
                if await video_locator.count() > 0:
                    is_video_detail = True
            except Exception:
                is_video_detail = False
            try:
                has_video_box_in_content = await detail_page.evaluate(
                    """() => {
                        const nodes = document.querySelectorAll('[class*="wbpro-feed-content"]');
                        for (const node of nodes) {
                            if (node.querySelector('div[class*="_videoBox_"]')) {
                                return true;
                            }
                        }
                        return false;
                    }"""
                )
                if has_video_box_in_content:
                    is_video_detail = True
            except Exception:
                has_video_box_in_content = False
            try:
                for _ in range(3):
                    await detail_page.evaluate("window.scrollBy(0, Math.max(400, window.innerHeight))")
                    await detail_page.wait_for_timeout(600)
            except Exception:
                pass

            content_text = ""
            try:
                content_text = await detail_page.eval_on_selector(
                    ".wbpro-feed-ogText", "el => (el.innerText || '').trim()"
                )
            except Exception:
                content_text = ""
            if not content_text:
                content_selectors = [
                    "div[class*='detail_wbtext_']",
                    "div[class*='detail_wbtext']",
                    "div._wbtext_1psp9_14",
                    "div[class*='_wbtext_']",
                    "div[class*='wbtext']",
                    "article div[class*='text']",
                    "article [class*='text']",
                    "section[class*='Detail']",
                    "div[class*='Detail_text']",
                    "div[class*='Fullfeed']",
                    "div[class*='WooPanel-main']",
                    "article",
                ]
                content_text = await self._first_text(detail_page, content_selectors)
            if not content_text:
                try:
                    candidates = await detail_page.evaluate(
                        """() => {
                            const selectors = [
                                'article',
                                'section[class*="Detail"]',
                                'div[class*="Detail"]',
                                'div[class*="Fullfeed"]',
                                'div[class*="WooPanel-main"]'
                            ];
                            const results = [];
                            const seen = new Set();
                            const add = (el) => {
                                if (!el || seen.has(el)) return;
                                seen.add(el);
                                const text = (el.innerText || '').trim();
                                if (text) results.push({ text, len: text.length });
                            };
                            for (const sel of selectors) {
                                document.querySelectorAll(sel).forEach(add);
                            }
                            if (!results.length && document.body) {
                                const text = (document.body.innerText || '').trim();
                                if (text) results.push({ text, len: text.length });
                            }
                            results.sort((a, b) => b.len - a.len);
                            return results.slice(0, 1);
                        }"""
                    )
                    if isinstance(candidates, list) and candidates:
                        content_text = candidates[0].get("text") or ""
                    else:
                        content_text = ""
                except Exception:
                    content_text = ""
            content_text = (content_text or "").strip()

            author_selectors = [
                "a[class*='detail_userName_']",
                "a[node-type='feed_list_originNick']",
                "div[class*='WB_info'] a",
            ]
            try:
                author_name = await detail_page.eval_on_selector(
                    "a[class*='_name_'] span", "el => (el.textContent || '').trim()"
                )
            except Exception:
                author_name = ""
            if not author_name:
                try:
                    candidate = await detail_page.evaluate(
                        """() => {
                            const nodes = Array.from(document.querySelectorAll('[usercard]'));
                            for (const node of nodes) {
                                const tag = (node.tagName || '').toLowerCase();
                                if (tag === 'a') {
                                    const span = node.querySelector('span');
                                    const txt = span ? (span.textContent || '') : (node.textContent || '');
                                    const val = txt.trim();
                                    if (val) return val;
                                } else if (tag === 'span') {
                                    const txt = (node.textContent || '').trim();
                                    if (txt) return txt;
                                }
                            }
                            return '';
                        }"""
                    )
                    if isinstance(candidate, str) and candidate.strip():
                        author_name = candidate.strip()
                except Exception:
                    pass
            if not author_name:
                author_name = await self._first_text(detail_page, author_selectors) or post_ref.get("author_name", "")

            time_selectors = [
                "header a[class*='_time_']",
                "time",
                "a[class*='detail_time_']",
                "span[class*='head-info_time_']",
                "div[class*='WB_from'] a",
            ]
            detail_time_raw = await self._first_text(detail_page, time_selectors)
            post_time = self._normalize_post_time(detail_time_raw)
            if not post_time:
                post_time = post_ref.get("post_time") or ""
            if not post_time and post_ref.get("raw_time"):
                post_time = self._normalize_post_time(post_ref.get("raw_time"))

            image_urls: List[str] = []
            is_video_from_picture = False
            try:
                pic_info = await detail_page.evaluate(
                    """() => {
                        const picture = document.querySelector('.picture');
                        const urls = [];
                        let hasVideo = false;
                        if (picture) {
                            if (picture.querySelector('video')) {
                                hasVideo = true;
                                urls.push('视频');
                            } else {
                                picture.querySelectorAll('img').forEach(img => {
                                    const src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-original') || '';
                                    if (src) urls.push(src);
                                });
                            }
                        }
                        return { urls, hasVideo };
                    }"""
                )
            except Exception:
                pic_info = {"urls": [], "hasVideo": False}
            if isinstance(pic_info, dict):
                raw_pic_urls = pic_info.get("urls") or []
                is_video_from_picture = bool(pic_info.get("hasVideo"))
                for u in raw_pic_urls:
                    if not u:
                        continue
                    image_url = u.strip()
                    if image_url:
                        image_urls.append(image_url)

            # 兜底：额外收集媒体区域的图片/视频链接
            try:
                if not image_urls:
                    image_candidates = await detail_page.evaluate(
                        """() => {
                            const selectors = [
                                'article',
                                'section[class*="Detail"]',
                                'div[class*="Detail"]',
                                'div[class*="Fullfeed"]',
                                'div[class*="WooPanel-main"]',
                                '[class*="picture_inlineNum3"]',
                                '[class*="picture-box"]',
                                'div._videoBox_19lrd_132',
                                '[class*="media"]',
                            ];
                            const urls = new Set();
                            const isAvatar = (img) => {
                                const cls = (img.className || '').toLowerCase();
                                if (cls.includes('avatar') || cls.includes('profile') || cls.includes('head')) return true;
                                const w = Number(img.getAttribute('width') || img.width || 0);
                                const h = Number(img.getAttribute('height') || img.height || 0);
                                return (w && w <= 40) || (h && h <= 40);
                            };
                            const addUrl = (u) => {
                                if (!u) return;
                                const val = u.trim();
                                if (val) urls.add(val);
                            };
                            for (const sel of selectors) {
                                const nodes = document.querySelectorAll(sel);
                                nodes.forEach(node => {
                                    node.querySelectorAll('img').forEach(img => {
                                        if (isAvatar(img)) return;
                                        const src = img.getAttribute('src') || img.getAttribute('data-src') || img.getAttribute('data-original') || '';
                                        const srcset = img.getAttribute('srcset') || '';
                                        addUrl(src);
                                        if (srcset) {
                                            srcset.split(',').forEach(part => {
                                                const url = part.trim().split(' ')[0];
                                                addUrl(url);
                                            });
                                        }
                                    });
                                    node.querySelectorAll('video').forEach(v => {
                                        const poster = v.getAttribute('poster') || '';
                                        const src = v.getAttribute('src') || '';
                                        addUrl(poster);
                                        addUrl(src);
                                        const sources = v.querySelectorAll('source');
                                        sources.forEach(s => addUrl(s.getAttribute('src') || ''));
                                    });
                                });
                            }
                            return Array.from(urls);
                        }"""
                    )
                else:
                    image_candidates = []
            except Exception:
                image_candidates = []
            is_retweet = False
            try:
                is_retweet = await detail_page.evaluate(
                    """(rootSelectors) => {
                        const matches = (node) => {
                            if (!node) return false;
                            let classText = '';
                            if (typeof node.className === 'string') {
                                classText = node.className;
                            } else if (node.getAttribute) {
                                classText = node.getAttribute('class') || '';
                            }
                            return typeof classText === 'string' && classText.toLowerCase().includes('retweet');
                        };

                        const scopedSearch = (root) => {
                            if (!root) return false;
                            if (matches(root)) return true;
                            const nodes = root.querySelectorAll('[class]');
                            for (const el of nodes) {
                                if (matches(el)) {
                                    return true;
                                }
                            }
                            return false;
                        };

                        for (const sel of rootSelectors) {
                            const candidate = document.querySelector(sel);
                            if (candidate && scopedSearch(candidate)) {
                                return true;
                            }
                        }

                        return scopedSearch(document.body || document.documentElement);
                    }""",
                    [
                        "article",
                        "div[class*='Detail']",
                        "div[class*='detail']",
                        "div[class*='Fullfeed']",
                        "section[class*='Detail']",
                    ],
                )
            except Exception:
                is_retweet = False

            if image_candidates:
                for raw in image_candidates:
                    raw = raw.strip()
                    if not raw or raw.startswith("data:"):
                        continue
                    if raw.startswith("//"):
                        normalized = "https:" + raw
                    elif raw.startswith("http"):
                        normalized = raw
                    else:
                        normalized = self._normalize_url(raw)
                    if normalized and normalized not in image_urls:
                        image_urls.append(normalized)

            # 规范化已收集的图片/媒体链接
            normalized_media: List[str] = []
            for raw in list(image_urls):
                if not raw:
                    continue
                raw = raw.strip()
                if not raw:
                    continue
                if raw == "视频":
                    normalized_media.append(raw)
                    continue
                if raw.startswith("//"):
                    normalized = "https:" + raw
                elif raw.startswith("http"):
                    normalized = raw
                else:
                    normalized = self._normalize_url(raw)
                if normalized and normalized not in normalized_media:
                    normalized_media.append(normalized)
            image_urls = normalized_media
            if has_video_box_in_content:
                image_urls = ["视频"]
            if is_video_from_picture or any(u == "视频" for u in image_urls):
                is_video_detail = True

            stat_map = {"shares_count": "0", "likes_count": "0", "comments_count": "0"}
            try:
                stats = await detail_page.evaluate(
                    """() => {
                        // 返回 [转发, 评论, 点赞]，点赞严格遵循 woo-like-count 纯数字规则
                        const textContent = (node) => (node && node.textContent ? node.textContent.trim() : '');
                        const isPureNumber = (txt) => /^\\d+$/.test(String(txt || '').trim());
                        const result = ["0", "0", "0"];

                        const footer = document.querySelector('footer');
                        if (footer) {
                            const firstFlex = footer.querySelector('.woo-box-item-flex');
                            if (firstFlex) {
                                const likeDiv = firstFlex.querySelector('.woo-like-count');
                                if (likeDiv) {
                                    const txt = textContent(likeDiv);
                                    result[2] = isPureNumber(txt) ? txt : "0";
                                }
                                const innerDivs = firstFlex.querySelectorAll(':scope > div > div');
                                if (innerDivs.length >= 2) {
                                    const span1 = innerDivs[0].querySelector('[class*="_num_"]') || innerDivs[0];
                                    const span2 = innerDivs[1].querySelector('[class*="_num_"]') || innerDivs[1];
                                    const txt1 = textContent(span1);
                                    const txt2 = textContent(span2);
                                    if (txt1) result[0] = txt1;
                                    if (txt2) result[1] = txt2;
                                }
                            }
                        }

                        // 退化：尝试旧的 toolbar（仅填充转发/评论；点赞保持 woo-like-count 规则）
                        const toolbar = document.querySelector('[class*="toolbar_main"]');
                        if (toolbar) {
                            const items = Array.from(toolbar.querySelectorAll('*')).filter(node => {
                                const cls = node.className || '';
                                return typeof cls === 'string' && cls.includes('toolbar_item');
                            });
                            items.slice(0, 3).forEach((item, idx) => {
                                if (idx === 2) return; // 点赞仅取 woo-like-count
                                const candidates = [
                                    item.querySelector('[class*="toolbar_num"]'),
                                    item.querySelector('[class*="like-count"]'),
                                ];
                                for (const node of candidates) {
                                    const txt = textContent(node);
                                    if (txt) { result[idx] = txt; break; }
                                }
                            });
                        }
                        return result;
                    }"""
                )
                if isinstance(stats, list) and stats:
                    normalized = [self._normalize_stat(val) for val in stats]
                    while len(normalized) < 3:
                        normalized.append("0")
                    stat_map["shares_count"] = normalized[0]
                    stat_map["comments_count"] = normalized[1]
                    stat_map["likes_count"] = normalized[2]
                    if _is_image_link(detail_url):
                        _log_detail("原因=链接为图片，详情结果作废")
                        return None
            except Exception:
                pass

            if not content_text:
                _log_detail("原因=正文为空或未找到内容节点")
                return None

            title = content_text.split("\n", 1)[0][:60]
            if not title:
                title = f"微博-{post_ref.get('note_id')}"

            details = {
                "note_id": post_ref.get("note_id"),
                "post_url": detail_url,
                "title": title,
                "author_name": author_name,
                "content": content_text,
                "images": image_urls,
                "post_time": post_time,
                "tags": "",
                "likes_count": stat_map["likes_count"],
                "collections_count": "0",
                "comments_count": stat_map["comments_count"],
                "shares_count": stat_map["shares_count"],
                "platform": "微博",
                "is_video": is_video_detail or post_ref.get("is_video", False),
                "isRetweet": "是" if is_retweet else "否",
            }
            _log_detail(
                f"抓取完成 post_time={post_time} raw_time={detail_time_raw} "
                f"author={author_name} imgs={len(image_urls)} is_video={details['is_video']} "
                f"shares={details['shares_count']} comments={details['comments_count']} likes={details['likes_count']}"
            )
            return details
        except Exception as e:
            _log_detail(f"异常: {e}")
            return None
        finally:
            if detail_page is not None:
                try:
                    await detail_page.close()
                except Exception:
                    pass

    async def _ensure_logged_in(self, page: Page) -> None:
        if await self._is_logged_out(page):
            raise RuntimeError("微博登录状态已失效，请重新运行 weibo_login_helper.py 更新会话。")

    @staticmethod
    async def _is_logged_out(page: Page) -> bool:
        try:
            url = (page.url or "").lower()
            if "passport.weibo.com" in url or "weibo.com/login" in url:
                return True
        except Exception:
            pass
        try:
            return await page.evaluate(
                """() => {
                    const bodyText = (document.body?.innerText || '').slice(0, 2000);
                    if (bodyText.includes('登录微博') || bodyText.includes('手机号码登录')) return true;
                    const loginForm = document.querySelector('input[name="username"], form[action*="login"], form[action*="passport"]');
                    if (loginForm) return true;
                    const loginBtn = Array.from(document.querySelectorAll('a, button')).find(el => {
                        const txt = (el.textContent || '').trim();
                        return txt.includes('登录') || txt.includes('登 录');
                    });
                    return !!loginBtn;
                }"""
            )
        except Exception:
            return False
