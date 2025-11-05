# --*-- coding: utf-8 --*--
import os

# ===============================================================================
# 飞书应用凭证
# 优先从环境变量读取，方便 GitHub Actions 等 CI/CD 环境部署
# 如果环境变量不存在，则从本文件读取，方便本地调试
# https://open.feishu.cn/app
# ===============================================================================
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a82f83f6eed3501c")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "oyWom5iYRryFnfUbee3SnfSN6hgwtW1e")


# ===============================================================================
# 飞书多维表格配置
# ===============================================================================
# 多维表格的 App Token，在多维表格 URL 中可以找到，例如:
# https://<your-domain>.feishu.cn/base/<THIS_IS_THE_APP_TOKEN>?table=<table_id>&view=<view_id>
FEISHU_BASE_APP_TOKEN = os.environ.get("FEISHU_BASE_APP_TOKEN", "GYnKbo7sIaHm5zseN4gc1NM0nzg") #漫展攻略
# FEISHU_BASE_APP_TOKEN = os.environ.get("FEISHU_BASE_APP_TOKEN", "LDSjbNlMdadMlNsuFq6cli4Anlc") #抓取漫展官方情报


# ===============================================================================
# 小红书配置
# ===============================================================================
# 要爬取的小红书用户主页URL列表，可以配置多个
XHS_TARGET_URLS = [
    ## 攻略
    "https://www.xiaohongshu.com/user/profile/67bd26f8000000000d00a18c",
    "https://www.xiaohongshu.com/user/profile/5c2ef7bf000000000700e62b",
    "https://www.xiaohongshu.com/user/profile/677e61fb000000000801e050",
    "https://www.xiaohongshu.com/user/profile/5e5cc694000000000100bfc4",
    "https://www.xiaohongshu.com/user/profile/678393bc000000000803ce90"

    ## 官方情报
    # "https://www.xiaohongshu.com/user/profile/66270a52000000001700ecbf",
    # "https://www.xiaohongshu.com/user/profile/66b026de000000001d033004",
    # "https://www.xiaohongshu.com/user/profile/64d9e1bb00000000010052c7",
    # "https://www.xiaohongshu.com/user/profile/622b98f1000000001000bb77",
    # "https://www.xiaohongshu.com/user/profile/63ed03690000000026004e31"
    
    # "https://www.xiaohongshu.com/user/profile/66c81184000000001d033a99"
    # "https://www.xiaohongshu.com/user/profile/65dc09e6000000000500dd6a"
]

# 要爬取的微博主页URL列表，可以配置多个
WEIBO_TARGET_URLS = [
    "https://weibo.com/u/7517194482",
    "https://weibo.com/u/3136375497",
    "https://weibo.com/u/5638891142",
    "https://weibo.com/u/7617585695",
    "https://weibo.com/u/2462905490",
    "https://weibo.com/u/6537754228"
]

# Playwright 会话状态文件路径，用于保存登录状态
XHS_AUTH_STATE_PATH = "auth_state.json"

# 是否使用无头模式运行浏览器（默认否）。
# 可通过环境变量 XHS_HEADLESS=1/true/yes 开启无头模式（如在服务器/CI上）。
XHS_HEADLESS = os.environ.get("XHS_HEADLESS", "false").lower() in ("1", "true", "yes")


# ===============================================================================
# 飞书多维表格字段映射
# 请确保这里的键（key）与你在飞书表格中创建的列名（字段名）完全一致
# ===============================================================================
FEISHU_FIELD_MAPPING_XHS = {
    "note_id": "笔记ID",          # 笔记ID (单行文本)
    "content": "描述",        # 笔记内容 (多行文本)
    "images": "图片数组",             # 笔记图片 (附件)
    "post_time": "发布时间",      # 发布时间 (日期)
    "post_url": "笔记链接",       # 笔记链接 (URL)
    "title": "标题",          # 笔记标题 (单行文本)
    "author_name": "作者",    # 作者名称 (单行文本)
    "tags": "标签",               # 标签 (单行文本)
    "likes_count": "点赞数",      # 点赞数 (数字)
    "collections_count": "收藏数",# 收藏数 (数字)
    "comments_count": "评论数",   # 评论数 (数字)
    "shares_count": "转发数",     # 转发数 (数字)
}

FEISHU_FIELD_MAPPING_WB = {
    "note_id": "内容ID",          # 内容ID (单行文本)
    "content": "描述",        # 笔记内容 (多行文本)
    "images": "图片数组",             # 笔记图片 (附件)
    "post_time": "发布时间",      # 发布时间 (日期)
    "post_url": "内容链接",       # 内容链接 (URL)
    "author_name": "作者",    # 作者名称 (单行文本)
    "likes_count": "点赞数",      # 点赞数 (数字)
    "comments_count": "评论数",   # 评论数 (数字)
    "shares_count": "转发数",     # 转发数 (数字)
}

# ===============================================================================
# 多渠道 -> 多飞书表格配置（可扩展）
# key 为自定义的 sink 名称；每条任务可引用其中一个 sink 名称
# 未配置时，默认使用上面的 FEISHU_BASE_APP_TOKEN/FEISHU_BASE_TABLE_ID/FEISHU_FIELD_MAPPING
# ===============================================================================
FEISHU_SINKS = {
    "xhs_default": {
        "app_token": FEISHU_BASE_APP_TOKEN,
        "table_id": "tbloiTbxqmYBdGiz", ##攻略
        # "table_id": "tbl3fl5oaC1PNMeN", ##官方情报
        "field_mapping": FEISHU_FIELD_MAPPING_XHS,
    },
    "weibo_default": {
        "app_token": FEISHU_BASE_APP_TOKEN,
        "table_id": "tblisrHchFiWYU7f", ##官方情报
        "field_mapping": FEISHU_FIELD_MAPPING_WB,
    },
    # 示例：微信渠道可以写入到另一张表（如需）
    # "wechat_default": {
    #     "app_token": "<another_app_token>",
    #     "table_id": "<another_table_id>",
    #     "field_mapping": FEISHU_FIELD_MAPPING,
    # },
}

# ===============================================================================
# 任务声明（后续扩展其它渠道时在此添加）
# type: 任务类型；目前仅支持 "xhs_user_notes"
# sink: 使用的 FEISHU_SINKS 键名，用于写入对应表格
# params: 渠道参数；xhs_user_notes 支持 user_urls、per_account_limit、scrolls
# ===============================================================================
TASKS = [
    {
        "type": "xhs_user_notes",
        "sink": "xhs_default",
        "params": {
            "urls": XHS_TARGET_URLS,
            "per_account_limit": 10,
            "scrolls": 1,
        },
    },
    # {
    #     "type": "weibo_home",
    #     "sink": "weibo_default",
    #     "params": {
    #         "urls": WEIBO_TARGET_URLS,
    #         "per_account_limit": 10,
    #         "scrolls": 1,
    #     },
    # },
]
