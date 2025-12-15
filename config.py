# --*-- coding: utf-8 --*--
import os

TASK_TYPE = 1 #1:IP资讯; 2:漫展官方情报; 3:漫展攻略 4:模型上新情报
match TASK_TYPE:
    case 1:  ##IP资讯
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
    case 2: ##官方情报
        curFeishuAppToken = "LDSjbNlMdadMlNsuFq6cli4Anlc"
        curXhsTableId = "tbl3fl5oaC1PNMeN"
        curWbTableId = "tblisrHchFiWYU7f"
        curXhsTargets = [
            "https://www.xiaohongshu.com/user/profile/5f39108f0000000001006ed5",
            "https://www.xiaohongshu.com/user/profile/692549e70000000037007974",
            "https://www.xiaohongshu.com/user/profile/5c29ffeb000000000701325f",
            "https://www.xiaohongshu.com/user/profile/5bef681d7f485d000185930a",
            "https://www.xiaohongshu.com/user/profile/682d888a000000000d00b0a8",
            "https://www.xiaohongshu.com/user/profile/610e6b100000000001005f43",
            "https://www.xiaohongshu.com/user/profile/64c9380a000000000b00916f",
            "https://www.xiaohongshu.com/user/profile/6475eeb9000000002a034448",
            "https://www.xiaohongshu.com/user/profile/68247dd5000000000d008a1d",
            "https://www.xiaohongshu.com/user/profile/5f819473000000000101eab0",
            "https://www.xiaohongshu.com/user/profile/5c734dd7000000001102286e",
            "https://www.xiaohongshu.com/user/profile/660b66ee000000000b00f85f",
            "https://www.xiaohongshu.com/user/profile/692549e70000000037007974",
            "https://www.xiaohongshu.com/user/profile/5c29ffeb000000000701325f",
            "https://www.xiaohongshu.com/user/profile/67c7c2c8000000000e01f67f",
            "https://www.xiaohongshu.com/user/profile/66542ba00000000003030c3f",
            "https://www.xiaohongshu.com/user/profile/6004567d00000000010079e4",
            "https://www.xiaohongshu.com/user/profile/665bfa8c0000000003030b42",
            "https://www.xiaohongshu.com/user/profile/62cfefe5000000000303c004",
            "https://www.xiaohongshu.com/user/profile/68bdb586000000001900cdc3",
            "https://www.xiaohongshu.com/user/profile/665812ac000000000d0270d3",
            "https://www.xiaohongshu.com/user/profile/680cd9b5000000000e011920",
            "https://www.xiaohongshu.com/user/profile/686cb26400000000070304f7",
            "https://www.xiaohongshu.com/user/profile/659be6110000000022007918",
            "https://www.xiaohongshu.com/user/profile/621c6970000000001000d87e",
            "https://www.xiaohongshu.com/user/profile/666ff951000000000d024f03",
            "https://www.xiaohongshu.com/user/profile/6285b65f0000000021026650",
            "https://www.xiaohongshu.com/user/profile/6821ca49000000000a03f5dc",
            "https://www.xiaohongshu.com/user/profile/5c47208d00000000100367d4",
            "https://www.xiaohongshu.com/user/profile/6821ca49000000000a03f5dc",
            "https://www.xiaohongshu.com/user/profile/5c47208d00000000100367d4",
            "https://www.xiaohongshu.com/user/profile/6744456b00000000010031a3",
            "https://www.xiaohongshu.com/user/profile/61e15c43000000001000a13b",
            "https://www.xiaohongshu.com/user/profile/625acec500000000210201fa",
            "https://www.xiaohongshu.com/user/profile/63f365180000000014011eb7",
            "https://www.xiaohongshu.com/user/profile/692549e70000000037007974",
            "https://www.xiaohongshu.com/user/profile/5c4e8a1d0000000011036be5",
            "https://www.xiaohongshu.com/user/profile/593a3c475e87e72cec242de8",
            "https://www.xiaohongshu.com/user/profile/6323ed23000000002303fff0",
            "https://www.xiaohongshu.com/user/profile/5cf827600000000018039ce1",
            "https://www.xiaohongshu.com/user/profile/5bc4245adb088100011aa4f9",
            "https://www.xiaohongshu.com/user/profile/64ec82a20000000001013032",
            "https://www.xiaohongshu.com/user/profile/6123af4f00000000010080c2",
            "https://www.xiaohongshu.com/user/profile/68415151000000001e03865f",
            "https://www.xiaohongshu.com/user/profile/6257ed340000000021028330",
            "https://www.xiaohongshu.com/user/profile/648838610000000011000f6e",
            "https://www.xiaohongshu.com/user/profile/65f4052b000000000500dbab",
            "https://www.xiaohongshu.com/user/profile/66bb88d1000000001d032a8d",
            "https://www.xiaohongshu.com/user/profile/6788e3b1000000000803f229",
            "https://www.xiaohongshu.com/user/profile/67f7537b000000000e01f95d",
            "https://www.xiaohongshu.com/user/profile/6693aadb000000000f0350f7",
            "https://www.xiaohongshu.com/user/profile/6896469a0000000028036b9e",
            "https://www.xiaohongshu.com/user/profile/649bc55f000000001f007928",
            "https://www.xiaohongshu.com/user/profile/625920720000000010006da0",
            "https://www.xiaohongshu.com/user/profile/65030082000000000200e3c6",
            "https://www.xiaohongshu.com/user/profile/657a77fe000000001c01ad19",
            "https://www.xiaohongshu.com/user/profile/5c412ace000000000702449a",
            "https://www.xiaohongshu.com/user/profile/622b98f1000000001000bb77"
        ]
        curWbTargets = [
            "https://weibo.com/3949708968",
            "https://weibo.com/5873857966",
            "https://weibo.com/u/7617585695",
            "https://weibo.com/u/2132531824",
            "https://weibo.com/u/6188204640",
            "https://weibo.com/u/7866313834",
            "https://weibo.com/u/7960412164",
            "https://weibo.com/2073298963",
            "https://weibo.com/u/5361306361",
            "https://weibo.com/7317743892",
            "https://weibo.com/2531071125",
            "https://weibo.com/2786659525",
            "https://weibo.com/u/6537754228",
            "https://weibo.com/u/2462905490"
    ]
    case 3: ##漫展攻略
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
    case 4:  ##模型上新情报
        curFeishuAppToken = "Gc9CblE4maBzzPsx4DCcyNKbnaf"
        curXhsTableId = "tblvfsjzRE0rPSp9"
        curWbTableId = "tblYeUADNDj94KWk"
        curXhsTargets = [
            
        ]
        curWbTargets = [
            "https://weibo.com/u/7411704896",
            "https://weibo.com/u/6876869557",
            "https://weibo.com/u/6019162065",
            "https://weibo.com/u/7790031436",
            "https://weibo.com/u/3903547693",
            "https://weibo.com/u/7570941228",
            "https://weibo.com/u/7483371607",
            "https://weibo.com/u/3937986035",
            "https://weibo.com/u/7306606797",
            "https://weibo.com/u/6287858398",
            "https://weibo.com/u/7898868903",
            "https://weibo.com/u/6218707574",
            "https://weibo.com/u/7269915751",
            "https://weibo.com/u/5976787598",
            "https://weibo.com/7875770784",
            "https://weibo.com/u/7741654964",
            "https://weibo.com/u/7586264459",
            "https://weibo.com/7707583095",
            "https://weibo.com/u/2707183173",
            "https://weibo.com/7997821939",
            "https://weibo.com/6089959951",
            "https://weibo.com/7961348211",
            "https://weibo.com/7595731999",
            "https://weibo.com/u/1794868400",
            "https://weibo.com/u/7283011762",
            "https://weibo.com/u/7716811519",
            "https://weibo.com/u/2805898290",
            "https://weibo.com/u/7181070055",
            "https://weibo.com/u/6694667657",
            "https://weibo.com/7383325027",
            "https://weibo.com/7671798601"
        ]



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
# 微博登录态文件，运行 weibo_login_helper.py 生成
WEIBO_AUTH_STATE_PATH = "weibo_auth_state.json"

# 是否使用无头模式运行浏览器（默认否）。
# 可通过环境变量 XHS_HEADLESS=1/true/yes 开启无头模式（如在服务器/CI上）。
# XHS_HEADLESS = os.environ.get("XHS_HEADLESS", "false").lower() in ("1", "true", "yes")
XHS_HEADLESS = True


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
