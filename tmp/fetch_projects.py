import requests
from datetime import datetime
from math import ceil
from openpyxl import Workbook

API_URL = "https://show-mng.bilibili.co/api/ticket/mis/project/search"

# Headers mirror the provided curl request. Cookie values are hardcoded as given.
HEADERS = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6",
    "cache-control": "no-cache",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://show-mng.bilibili.co/",
    "sec-ch-ua": '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"macOS"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/143.0.0.0 Safari/537.36"
    ),
    "cookie": (
        "buvid3=BF4AA9E2-9FDE-705C-604D-4465A1E5859039047infoc; "
        "b_nut=1765442938; "
        "buvid4=8824C5E2-D62E-9E34-9D3A-1B4889A2600G39047-025121116-kVpKSGPR9WB+TkKA9xJ3PQ==; "
        "_AJSESSIONID=4d14541648ea31c9a3bbf4ca2ac9ccae; "
        "username=luke"
    ),
}

BASE_PARAMS = {
    "name": "",
    "id": "",
    "pub_min": "",
    "pub_max": "",
    "sale_min": "",
    "sale_max": "",
    "start_min": "2025-01-01 00:00:00",
    "start_max": "2025-12-31 00:00:00",
    "city": "",
    "sale_flag": "",
    "type": "",
    "project_type": "",
    "merchant_name": "",
    "is_exclusive": "",
    "page": 1,
    "size": 100,
    "status": 1,
    "channel": 1,
    "channel_user_id": "",
}


def format_ts(ts_value):
    """Convert a 10-digit timestamp to 'YYYY-MM-DD HH:MM:SS'."""
    if not ts_value:
        return ""
    try:
        return datetime.fromtimestamp(int(ts_value)).strftime("%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return ""


def fetch_page(session, page_num):
    params = dict(BASE_PARAMS)
    params["page"] = page_num
    response = session.get(API_URL, params=params, headers=HEADERS, timeout=15)
    response.raise_for_status()
    payload = response.json()
    return payload.get("data") or {}


def collect_items():
    session = requests.Session()
    session.headers.update(HEADERS)

    results = []
    current_page = 1
    total_pages = 1

    while current_page <= total_pages:
        data = fetch_page(session, current_page)
        page_info = data.get("page") or {}

        total_items = page_info.get("total") or 0
        page_size = page_info.get("size") or BASE_PARAMS["size"]
        if page_size:
            total_pages = max(total_pages, ceil(total_items / page_size))
        else:
            total_pages = max(total_pages, 1)

        current = page_info.get("num") or current_page

        items = data.get("item", [])
        for item in items:
            results.append(
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "total_count": item.get("total_count"),
                    "start_time": format_ts(item.get("start_time")),
                    "end_time": format_ts(item.get("end_time")),
                }
            )

        print(
            f"Page {current}/{total_pages} (size={page_size}, total_items={total_items}): "
            f"fetched {len(items)} items, total collected {len(results)}"
        )

        if current >= total_pages:
            break
        current_page = current + 1

    return results


def save_to_excel(rows, filepath):
    wb = Workbook()
    ws = wb.active
    ws.title = "projects"
    ws.append(["id", "name", "total_count", "start_time", "end_time"])
    for row in rows:
        ws.append(
            [
                row.get("id", ""),
                row.get("name", ""),
                row.get("total_count", ""),
                row.get("start_time", ""),
                row.get("end_time", ""),
            ]
        )
    wb.save(filepath)


def main():
    items = collect_items()
    output_path = "tmp/bilibili_projects.xlsx"
    save_to_excel(items, output_path)
    print(f"Saved {len(items)} rows to {output_path}")


if __name__ == "__main__":
    main()
