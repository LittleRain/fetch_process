# --*-- coding: utf-8 --*--
import os

TASK_TYPE = 2 #1:IP资讯; 2:官方情报; 3:漫展攻略
match TASK_TYPE:
    case 1: 
        curFeishuAppToken = "K9orbPg4harHLwsywv5cMvUMn2e"
        curXhsTableId = "tblCpHS6AQv7RL8y"
        curWbTableId = "tblIfMp2AhsXTZlM"
        curXhsTargets = [
            "https://www.xiaohongshu.com/user/profile/654e6fa50000000002037e2b",
            "https://www.xiaohongshu.com/user/profile/60724f13000000000101f9ab",
            "https://www.xiaohongshu.com/user/profile/5d08fee2000000001200d6e5",
            "https://www.xiaohongshu.com/user/profile/6652c3ff00000000070046f1",
            "https://www.xiaohongshu.com/user/profile/641c321a0000000014010069"
        ]
        curWbTargets = [
            "https://weibo.com/u/1886672467",
            "https://weibo.com/u/1195908387",
            "https://weibo.com/u/2686948620"
        ]
    case 2: 
        curFeishuAppToken = "LDSjbNlMdadMlNsuFq6cli4Anlc"
        curXhsTableId = "tbl3fl5oaC1PNMeN"
        curWbTableId = "tblisrHchFiWYU7f"
        curXhsTargets = [
            # "https://www.xiaohongshu.com/user/profile/66270a52000000001700ecbf",
            # "https://www.xiaohongshu.com/user/profile/66b026de000000001d033004",
            # "https://www.xiaohongshu.com/user/profile/64d9e1bb00000000010052c7",
            # "https://www.xiaohongshu.com/user/profile/622b98f1000000001000bb77",
            # "https://www.xiaohongshu.com/user/profile/63ed03690000000026004e31",
            # "https://www.xiaohongshu.com/user/profile/61e15c43000000001000a13b",
            # "https://www.xiaohongshu.com/user/profile/5c412ace000000000702449a",
            # "https://www.xiaohongshu.com/user/profile/657a77fe000000001c01ad19",
            # "https://www.xiaohongshu.com/user/profile/630b1226000000001501c72e",
            # "https://www.xiaohongshu.com/user/profile/65030082000000000200e3c6",
            # "https://www.xiaohongshu.com/user/profile/625920720000000010006da0",
            # "https://www.xiaohongshu.com/user/profile/66cfc859000000000d02709d",
            # "https://www.xiaohongshu.com/user/profile/6323ed23000000002303fff0",
            # "https://www.xiaohongshu.com/user/profile/607510c80000000001000cc6",
            # "https://www.xiaohongshu.com/user/profile/6004567d00000000010079e4",
            # "https://www.xiaohongshu.com/user/profile/6896469a0000000028036b9e",
            # "https://www.xiaohongshu.com/user/profile/67dae5b4000000000d00a436",
            # "https://www.xiaohongshu.com/user/profile/61ed208f00000000100047b3",
            # "https://www.xiaohongshu.com/user/profile/649bc55f000000001f007928",
            # "https://www.xiaohongshu.com/user/profile/625b9e6a00000000100068a0",
            # "https://www.xiaohongshu.com/user/profile/58e9fd766a6a6925090cd8c7",
            # "https://www.xiaohongshu.com/user/profile/6257ed340000000021028330",
            # "https://www.xiaohongshu.com/user/profile/62f6211f000000001e01faa7",
            # "https://www.xiaohongshu.com/user/profile/63f365180000000014011eb7",
            # "https://www.xiaohongshu.com/user/profile/613f08ee00000000020266c5",
            # "https://www.xiaohongshu.com/user/profile/620dcfbe00000000100096fb",
            # "https://www.xiaohongshu.com/user/profile/5e7253e5000000000100139f",
            # "https://www.xiaohongshu.com/user/profile/682d888a000000000d00b0a8",
            # "https://www.xiaohongshu.com/user/profile/65ab964a000000000d03c4c0",
            # "https://www.xiaohongshu.com/user/profile/64bb81aa000000001403e07b",
            # "https://www.xiaohongshu.com/user/profile/60eff850000000000100188b",
            # "https://www.xiaohongshu.com/user/profile/6516b7e1000000000200e24d",
            # "https://www.xiaohongshu.com/user/profile/58e9fd766a6a6925090cd8c7",
            # "https://www.xiaohongshu.com/user/profile/620dcfbe00000000100096fb",
            # "https://www.xiaohongshu.com/user/profile/6649cfd1000000000303048f",
            # "https://www.xiaohongshu.com/user/profile/66175e9a0000000007007eea",
            # "https://www.xiaohongshu.com/user/profile/6031d1950000000001009e65",
            # "https://www.xiaohongshu.com/user/profile/67f7537b000000000e01f95d",
            # "https://www.xiaohongshu.com/user/profile/6693aadb000000000f0350f7",
            # "https://www.xiaohongshu.com/user/profile/6031d1950000000001009e65",
            # "https://www.xiaohongshu.com/user/profile/6613a6b5000000000b0303a3",
            # "https://www.xiaohongshu.com/user/profile/66a5ba4e000000001d03024b",
            # "https://www.xiaohongshu.com/user/profile/600cdd33000000000101e272",
            # "https://www.xiaohongshu.com/user/profile/652f958c000000000200f263",
            # "https://www.xiaohongshu.com/user/profile/67b49ba8000000000a03c347",
            # "https://www.xiaohongshu.com/user/profile/5e7253e5000000000100139f",
            # "https://www.xiaohongshu.com/user/profile/68886c95000000001e03aba0",
            # "https://www.xiaohongshu.com/user/profile/65e6139a00000000050081fc",
            # "https://www.xiaohongshu.com/user/profile/5f427fab000000000100af58",
            # "https://www.xiaohongshu.com/user/profile/600e98f7000000000101c47f"
            "https://www.xiaohongshu.com/user/profile/5ec6434700000000010030fe?xsec_token=ABg_oFJSUsyg_nEdTLuXR0-k8aDQW9JiDlcPJ2fb1zfNQ=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/618d4e9b0000000021027817?xsec_token=ABsC1UboLoSlr5a6GJUCxorIWgMNTKM8GIQaXdUHlIdbs=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5f496779000000000101eeec?xsec_token=AB_GA8sHzH55EbK3XraLfKu2RaNTDhm1UkDXrV95AMb-o=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5dfa6deb000000000100aeb7?xsec_token=AB4ZUs2HzvCOR31L8sZWIQC6q3kg_I3y4mFwBiO0Ho2C8%3D&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/64ec82a20000000001013032?xsec_token=AB4DMTV7NXAsyh6vmZcqTjm1Jrkx71oipyWeyHkaD6Z-0=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/60365ef90000000001008917?xsec_token=ABmAhnemdqOtmjixjrV7zGMZv_l6PgvFQJint8k2zCKlo=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/6123af4f00000000010080c2?xsec_token=ABjowKDtO2FxLlGedN1UZWL3MV-sbQ9GAiPaA2xpP0ilw=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/62062f6f0000000010009a28?xsec_token=ABx5apZ0-olW1NxXCSBx1MCFzftGwUOoAVAfqmaN8rcho=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/646f43f8000000002b00baa3?xsec_token=ABSNBRaq0OJULK37uDKKYC-D8fiQ8ZMBUGcqBkloRg0o4=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/68415151000000001e03865f?xsec_token=AB7kRJDirDLredDgaAX28AlyQrOzW70P4B2ppjoMbyqcM=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/6761c938000000001801626e?xsec_token=AB4lLL4EvQfuI_t16okYJ3Uj2L08TwrlDFmaIHXUmgagE=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5d7bca46000000000101a84d?xsec_token=ABNRadH5I6kGCEKEKioQm-kjylwL1yREtk7bMhGOxGt0k%3D&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/6257ed340000000021028330?xsec_token=AB-d2VCUFwpBKzoIXcp-lxDX3YtpeHhp9NQhGNDaX9mII=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5c8343960000000012000bf5?xsec_token=AB9VKPbd8DJ-ZJhhwNbt8K6fAsyC7MW6GPyhyBhnbQxQI=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/648838610000000011000f6e?xsec_token=AB2XIypmVP3sLIH7KJstkfQceij6L4O7FJdqM_ZnS_61o%3D&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/65f4052b000000000500dbab?xsec_token=ABs16EyLZEgMz2T9XxD8QrAxNeYo02GPjefzxtzlKeoq8=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/66bb88d1000000001d032a8d?xsec_token=ABw65yOeuMz8M9GQjFyanH0ur4gNklVplpIZzScfuwvDA=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5c9f1e0b0000000010012f72?xsec_token=ABnwn9SxmZqUS5dCeT5wLq5ddwByZSktLe2C0ZGGueJKo=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/656d220f0000000019012f12?xsec_token=AB6homJNjkWDb5o2oMHB10THWBUSruMxe-0svS68x9PoE=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/62cfefe5000000000303c004?xsec_token=ABuIZx6W77KUNI1yseKWJB5iU36RRUnZYBCOX9RCPnaR8=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/687a677c000000001e03f8f7?xsec_token=ABq4ifmbUJIBlWZ9QzeOhO0Oz68ypU4x9-FqxRpvXs5sY=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/66637ec4000000000700618c?xsec_token=ABRw3K3-wylchSRjK6L2_f84mEYnqDQVP1rDRcjG03zVQ=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/5ea159eb000000000100a2f6?xsec_token=AB4DXoTsZQZxC_pT4ZaAyIe355OV7RQc5iN8scUGzE5Yg=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/67fc5bcf000000001b00b25b?xsec_token=ABf_gBOyN3k4fdreM8tGp3CqiCGedVkaQiqscXBCnzRr4=&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/63f365180000000014011eb7?xsec_token=ABbeuL4aL7QqKjlh5uMqtELQb8MdhYIYr307eJDn-BAeE%3D&xsec_source=pc_search",
            "https://www.xiaohongshu.com/user/profile/6788e3b1000000000803f229?xsec_token=AB0IrTwPqqha94FWm93ixLXB2jKL2BoOnxnUJTjj8rNeg=&xsec_source=pc_search"
        ]
        curWbTargets = [
            # "https://weibo.com/3136375497",
            # "https://weibo.com/u/5638891142",
            # "https://weibo.com/u/7617585695",
            # "https://weibo.com/u/2462905490",
            # "https://weibo.com/u/6537754228",
            # "https://weibo.com/5889398001",
            # "https://weibo.com/2073298963",
            # "https://weibo.com/2786659525",
            # "https://weibo.com/2531071125",
            # "https://weibo.com/7317743892",
            # "https://weibo.com/u/3832084542",
            # "https://weibo.com/5873857966",
            # "https://weibo.com/u/7617585695",
            # "https://weibo.com/u/5361306361",
            # "https://weibo.com/2073298963",
            # "https://weibo.com/u/7960412164",
            # "https://weibo.com/u/6411589951",
            # "https://weibo.com/7886945717",
            # "https://weibo.com/u/7617585695",
            # "https://weibo.com/3832084542",
            # "https://weibo.com/u/6188204640",
            # "https://weibo.com/u/1745046144",
            # "https://weibo.com/u/3949708968",
            # "https://weibo.com/u/3832084542",
            # "https://weibo.com/u/2073298963",
            # "https://weibo.com/u/7866313834",
            # "https://weibo.com/5889398001",
            # "https://weibo.com/u/3218573045"
            "https://weibo.com/u/2132531824",
            "https://weibo.com/u/5638891142",
            "https://weibo.com/2073298963",
            "https://weibo.com/2073298963",
    ]
    case 3: 
        curFeishuAppToken = "GYnKbo7sIaHm5zseN4gc1NM0nzg"
        curXhsTableId = "tbloiTbxqmYBdGiz"
        curWbTableId = ""
        curWbTargets = [
            "https://www.xiaohongshu.com/user/profile/67bd26f8000000000d00a18c",
            "https://www.xiaohongshu.com/user/profile/5c2ef7bf000000000700e62b",
            "https://www.xiaohongshu.com/user/profile/677e61fb000000000801e050",
            "https://www.xiaohongshu.com/user/profile/5e5cc694000000000100bfc4",
            "https://www.xiaohongshu.com/user/profile/678393bc000000000803ce90"
        ]
        WEIBO_TARGET_URLS = []



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
FEISHU_BASE_APP_TOKEN = os.environ.get("FEISHU_BASE_APP_TOKEN", curFeishuAppToken)


# ===============================================================================
# 小红书配置
# ===============================================================================
# 要爬取的小红书用户主页URL列表，可以配置多个
XHS_TARGET_URLS = curXhsTargets

# 要爬取的微博主页URL列表，可以配置多个
WEIBO_TARGET_URLS = curWbTargets

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
    "note_id": "内容ID",          # 笔记ID (单行文本)
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
        "table_id": curXhsTableId,
        "field_mapping": FEISHU_FIELD_MAPPING_XHS,
    },
    "weibo_default": {
        "app_token": FEISHU_BASE_APP_TOKEN,
        "table_id": curWbTableId,
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
    {
        "type": "weibo_home",
        "sink": "weibo_default",
        "params": {
            "urls": WEIBO_TARGET_URLS,
            "per_account_limit": 10,
            "scrolls": 3,
        },
    },
]
