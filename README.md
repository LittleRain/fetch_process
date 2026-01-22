# Feishu Social Scraper (XHS/Weibo)

This project uses Playwright to scrape Xiaohongshu (XHS) and Weibo user home pages, then writes structured records into Feishu Bitable. It supports multi-task configs and per-platform sinks.

## Features

- XHS user note list + detail scraping with resilient selectors and fallback URLs.
- Weibo home timeline list + detail scraping, including media, stats, and retweet detection.
- Feishu Bitable integration with field mapping, batching, and duplicate check by `note_id`.
- Configurable tasks, per-account limits, scroll depth, and recent-window filtering.
- Manual login helpers that persist Playwright storage state for XHS and Weibo.

## Supported sources

- XHS: `xhs_user_notes` / `xhs_home`
- Weibo: `weibo_home`
- WeChat: `wechat_articles` (skeleton only; list/detail parsing not implemented yet)

## Quick start

1) Install dependencies

```bash
pip install -r requirements.txt
playwright install
```

2) Configure Feishu and targets in `config.py` (or via environment variables)

- `FEISHU_APP_ID`, `FEISHU_APP_SECRET`
- `FEISHU_BASE_APP_TOKEN`
- `FEISHU_SINKS` table IDs + field mappings
- `TASKS` for per-source URLs and limits

3) Login once to save session state

```bash
python login_helper.py
python weibo_login_helper.py
```

This creates `auth_state.json` and `weibo_auth_state.json`.

4) Run

```bash
python main.py
```

## Configuration notes

- `TASKS` entries:
  - `type`: `xhs_user_notes`, `xhs_home`, `weibo_home`, `wechat_articles`
  - `sink`: key in `FEISHU_SINKS`
  - `params`: `urls`, `per_account_limit`, `scrolls`
- Recent window filter: `WITHIN_LAST_DAYS` (applies to XHS and Weibo).
- XHS detail concurrency: `XHS_DETAIL_CONCURRENCY` env var (default 2).
- Headless: `XHS_HEADLESS` (defaults to `True` in `config.py`).
- `TASK_TYPE` in `config.py` switches preset targets/tables if you keep the built-in presets.

## Data fields written

XHS and Weibo detail data is normalized to the following keys (mapped to your Bitable columns via `FEISHU_FIELD_MAPPING_*`):

- `note_id`, `title`, `content`, `author_name`, `post_time`, `post_url`
- `images` (stored as comma-separated URLs)
- `likes_count`, `collections_count`, `comments_count`, `shares_count`

## Behavior

- Dedupes by querying existing `note_id` in Feishu before fetching details.
- Skips XHS videos (Weibo videos are allowed).
- Stops XHS account scraping early if 3 consecutive notes are older than the time window.

## Troubleshooting

- Missing session file: run `python login_helper.py` or `python weibo_login_helper.py`.
- Playwright browser not installed: run `playwright install`.
- No records written: confirm `FEISHU_SINKS` table IDs and column names match your Bitable.

## Disclaimer

Use responsibly and comply with platform terms of service. Add rate limiting if needed.
