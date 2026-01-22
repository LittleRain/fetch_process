# --*-- coding: utf-8 --*--
import os

TASK_TYPE = 2  # 1:IP资讯; 2:漫展官方情报; 3:漫展攻略 4:模型上新情报
# 统一配置内容有效期（天），由业务场景控制
WITHIN_LAST_DAYS = 10
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
        WITHIN_LAST_DAYS = 10
    case 2:  ##官方情报
        curFeishuAppToken = "LDSjbNlMdadMlNsuFq6cli4Anlc"
        curXhsTableId = "tbl3fl5oaC1PNMeN"
        curWbTableId = "tblisrHchFiWYU7f"
        curXhsTargets = [
            "https://www.xiaohongshu.com/user/profile/68d749730000000021022212",
            "https://www.xiaohongshu.com/user/profile/5b5bfd5011be1063b4027d9e",
            "https://www.xiaohongshu.com/user/profile/6252726c0000000021029634",
            "https://www.xiaohongshu.com/user/profile/61b08ef20000000021020c2b",
            "https://www.xiaohongshu.com/user/profile/67f8c723000000000e01e2ee",
            "https://www.xiaohongshu.com/user/profile/63fcdbb60000000029014275",
            "https://www.xiaohongshu.com/user/profile/64ec82a20000000001013032",
            "https://www.xiaohongshu.com/user/profile/5ba9dd7953c4f60001664591",
            "https://www.xiaohongshu.com/user/profile/692549e70000000037007974",
            "https://www.xiaohongshu.com/user/profile/66542ba00000000003030c3f",
            "https://www.xiaohongshu.com/user/profile/657a77fe000000001c01ad19",
            "https://www.xiaohongshu.com/user/profile/62fd24bb000000000f00685f",
            "https://www.xiaohongshu.com/user/profile/5c29ffeb000000000701325f",
            "https://www.xiaohongshu.com/user/profile/630b1226000000001501c72e",
            "https://www.xiaohongshu.com/user/profile/6322e0520000000023026032",
            "https://www.xiaohongshu.com/user/profile/5b97bda78cd78c0001a535e0",
            "https://www.xiaohongshu.com/user/profile/593a3c475e87e72cec242de8",
            "https://www.xiaohongshu.com/user/profile/637f37db000000001f015266",
            "https://www.xiaohongshu.com/user/profile/5a0ad24b4eacab287e8a916f",
            "https://www.xiaohongshu.com/user/profile/62bc9590000000001b02a3b2",
            "https://www.xiaohongshu.com/user/profile/692d6eaf00000000370049c4",
            "https://www.xiaohongshu.com/user/profile/687aecd1000000001d015f37",
            "https://www.xiaohongshu.com/user/profile/66df1a1d000000001d032d8f",
            "https://www.xiaohongshu.com/user/profile/629aebeb000000001b0246e3",
            "https://www.xiaohongshu.com/user/profile/67e02fee0000000007003831",
            "https://www.xiaohongshu.com/user/profile/6760f43e0000000014031aee",
            "https://www.xiaohongshu.com/user/profile/6819c9980000000018021356",
            "https://www.xiaohongshu.com/user/profile/6792fd33000000000e02f6bd",
            "https://www.xiaohongshu.com/user/profile/5f39108f0000000001006ed5",
            "https://www.xiaohongshu.com/user/profile/649bc55f000000001f007928",
            "https://www.xiaohongshu.com/user/profile/5caec8f10000000017008bd4",
            "https://www.xiaohongshu.com/user/profile/62c3ac61000000001b0255c4",
            "https://www.xiaohongshu.com/user/profile/60365ef90000000001008917",
            "https://www.xiaohongshu.com/user/profile/666ff951000000000d024f03",
            "https://www.xiaohongshu.com/user/profile/682d888a000000000d00b0a8",
            "https://www.xiaohongshu.com/user/profile/67174ea2000000000d0264c5",
            "https://www.xiaohongshu.com/user/profile/5c734dd7000000001102286e",
            "https://www.xiaohongshu.com/user/profile/59d766296eea88058aaeaa61",
            "https://www.xiaohongshu.com/user/profile/63f365180000000014011eb7",
            "https://www.xiaohongshu.com/user/profile/6488861200000000250352d0",
            "https://www.xiaohongshu.com/user/profile/676ef3a60000000018014f14",
            "https://www.xiaohongshu.com/user/profile/6004567d00000000010079e4",
            "https://www.xiaohongshu.com/user/profile/6257ed340000000021028330",
            "https://www.xiaohongshu.com/user/profile/5cfdfd57000000000603704e",
            "https://www.xiaohongshu.com/user/profile/5c4e8a1d0000000011036be5",
            "https://www.xiaohongshu.com/user/profile/63881633000000001f01b349",
            "https://www.xiaohongshu.com/user/profile/680fac41000000000a03ef21",
            "https://www.xiaohongshu.com/user/profile/64a3cc69000000000a021774",
            "https://www.xiaohongshu.com/user/profile/61a1a88e000000001000910f",
            "https://www.xiaohongshu.com/user/profile/68886c95000000001e03aba0",
            "https://www.xiaohongshu.com/user/profile/651a0d9f00000000020135d5",
            "https://www.xiaohongshu.com/user/profile/686cb26400000000070304f7",
            "https://www.xiaohongshu.com/user/profile/61ada9c20000000010004a96",
            "https://www.xiaohongshu.com/user/profile/6929095e000000003700be07",
            "https://www.xiaohongshu.com/user/profile/630c6245000000000f005e48",
            "https://www.xiaohongshu.com/user/profile/6275b5850000000015014f75",
            "https://www.xiaohongshu.com/user/profile/65030082000000000200e3c6",
            "https://www.xiaohongshu.com/user/profile/646f43f8000000002b00baa3",
            "https://www.xiaohongshu.com/user/profile/63ed03690000000026004e31",
            "https://www.xiaohongshu.com/user/profile/6123c269000000000100579f",
            "https://www.xiaohongshu.com/user/profile/6075660a000000000101db5f",
            "https://www.xiaohongshu.com/user/profile/65e85872000000000d026582",
            "https://www.xiaohongshu.com/user/profile/5fa276ff00000000010080ef",
            "https://www.xiaohongshu.com/user/profile/66b026de000000001d033004",
            "https://www.xiaohongshu.com/user/profile/685289c3000000001e003037",
            "https://www.xiaohongshu.com/user/profile/622b98f1000000001000bb77",
            "https://www.xiaohongshu.com/user/profile/64ec82a20000000001013032"
        ]
        curWbTargets = [
           "https://weibo.com/u/6411589951",
            "https://weibo.com/u/7617585695"
        ]
        WITHIN_LAST_DAYS = 5
    case 3:  ##漫展攻略
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
        WITHIN_LAST_DAYS = 10
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
        WITHIN_LAST_DAYS = 10



# ===============================================================================
# 飞书应用凭证
# 优先从环境变量读取，方便 GitHub Actions 等 CI/CD 环境部署
# 如果环境变量不存在，则从本文件读取，方便本地调试
# https://open.feishu.cn/app
# ===============================================================================
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "cli_a82f83f6eed3501c")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "oyWom5iYRryFnfUbee3SnfSN6hgwtW1e")

# 飞书接口请求重试/超时（毫秒），可按需覆盖环境变量
FEISHU_REQUEST_TIMEOUT_MS = int(os.environ.get("FEISHU_REQUEST_TIMEOUT_MS", "60000") or "60000")
FEISHU_REQUEST_MAX_RETRIES = int(os.environ.get("FEISHU_REQUEST_MAX_RETRIES", "3") or "3")
FEISHU_REQUEST_RETRY_BACKOFF_SECONDS = int(os.environ.get("FEISHU_REQUEST_RETRY_BACKOFF_SECONDS", "2") or "2")


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
            "scrolls": 3,
        },
    },
    # {
    #     "type": "weibo_home",
    #     "sink": "weibo_default",
    #     "params": {
    #         "urls": WEIBO_TARGET_URLS,
    #         "per_account_limit": 30,
    #         "scrolls": 8,
    #     },
    # },
]
