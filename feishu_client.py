import time
import json as _json
import config
from typing import Dict, List, Any, Optional
from urllib.parse import quote
from playwright.async_api import APIRequestContext

class FeishuClient:
    BASE_URL = "https://open.feishu.cn/open-apis"

    def __init__(self, request_context: APIRequestContext, *,
                 app_token: Optional[str] = None,
                 table_id: Optional[str] = None,
                 field_mapping: Optional[Dict[str, Any]] = None):
        self.app_id = config.FEISHU_APP_ID
        self.app_secret = config.FEISHU_APP_SECRET
        # 允许按任务覆盖 app_token、table_id、字段映射
        self.base_app_token = app_token or config.FEISHU_BASE_APP_TOKEN
        self.table_id = table_id or config.FEISHU_BASE_TABLE_ID
        if field_mapping is None:
            self.field_mapping = getattr(config, "FEISHU_FIELD_MAPPING", {})
        elif isinstance(field_mapping, str):
            self.field_mapping = getattr(config, field_mapping, {}) or {}
        else:
            self.field_mapping = field_mapping
        self._tenant_access_token = ""
        self._token_expiry_time = 0
        self.request_context = request_context
        self._field_types_cache: Dict[str, Any] = {}

    async def _get_field_types(self) -> Dict[str, Any]:
        """获取并缓存表字段的类型映射: {显示名称: 类型}
        说明：类型返回原始值（可能是字符串或数字枚举），上层自行做兼容处理。
        """
        if self._field_types_cache:
            return self._field_types_cache
        headers = await self._get_auth_headers()
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.base_app_token}/tables/{self.table_id}/fields?page_size=100"
        page_token = None
        types: Dict[str, Any] = {}
        while True:
            u = url if not page_token else (url + f"&page_token={page_token}")
            resp = await self.request_context.get(u, headers=headers)
            try:
                data = await resp.json()
            except Exception:
                data = {}
            if not resp.ok or data.get('code') != 0:
                # 静默失败：使用默认策略
                break
            items = (data.get('data') or {}).get('items') or (data.get('data') or {}).get('records') or []
            for it in items:
                name = it.get('field_name') or it.get('name') or it.get('title') or it.get('alias')
                ftype = it.get('type')
                if name:
                    types[str(name)] = ftype
            has_more = (data.get('data') or {}).get('has_more')
            if has_more:
                page_token = (data.get('data') or {}).get('page_token')
                if not page_token:
                    break
            else:
                break
        if types:
            self._field_types_cache = types
        return types

    @staticmethod
    def _normalize_field_type(raw: Any) -> str:
        """将飞书返回的字段类型归一化为: text|number|url|attachment|date|unknown"""
        if raw is None:
            return 'unknown'
        if isinstance(raw, str):
            t = raw.strip().lower()
            if 'number' in t:
                return 'number'
            if 'text' in t or 'string' in t or 'rich_text' in t:
                return 'text'
            if 'url' in t or 'link' in t:
                return 'url'
            if 'attachment' in t or 'file' in t:
                return 'attachment'
            if 'date' in t or 'time' in t:
                return 'date'
            return 'unknown'
        if isinstance(raw, int):
            # 兼容数字枚举（经验映射）
            mapping = {
                1: 'text',    # 可能为文本
                2: 'number',  # 可能为数字
                3: 'single_select',
                4: 'multi_select',
                5: 'date',
                7: 'url',
                11: 'attachment',
            }
            return mapping.get(raw, 'unknown')
        return 'unknown'

    @staticmethod
    def _to_number(value: Any) -> int:
        try:
            if isinstance(value, (int, float)):
                return int(value)
            if isinstance(value, str):
                v = value.strip().lower()
                if v.endswith('w'):
                    return int(float(v[:-1]) * 10000)
                if v.endswith('k'):
                    return int(float(v[:-1]) * 1000)
                return int(float(v))
        except Exception:
            pass
        return 0

    async def _get_tenant_access_token(self) -> str:
        """获取或刷新 tenant_access_token"""
        if self._tenant_access_token and time.time() < self._token_expiry_time:
            return self._tenant_access_token

        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        payload = {"app_id": self.app_id, "app_secret": self.app_secret}
        response = await self.request_context.post(url, data=payload)
        data = await response.json()

        if data.get("code") == 0:
            self._tenant_access_token = data["tenant_access_token"]
            self._token_expiry_time = time.time() + data["expire"] - 60
            return self._tenant_access_token
        else:
            raise Exception(f"获取 tenant_access_token 失败: {data.get('msg')}")

    async def _get_auth_headers(self) -> Dict[str, str]:
        """获取包含认证信息的请求头"""
        token = await self._get_tenant_access_token()
        return {"Authorization": f"Bearer {token}"}

    async def _download_image(self, url: str) -> bytes:
        """下载图片并返回二进制内容"""
        response = await self.request_context.get(url)
        if not response.ok:
            raise Exception(f"下载图片失败: {url}")
        return await response.body()

    async def _upload_image(self, image_bytes: bytes) -> str:
        """上传图片到飞书云空间，返回 file_token"""
        url = f"{self.BASE_URL}/drive/v1/medias/upload_all"
        headers = await self._get_auth_headers()
        
        response = await self.request_context.post(
            url,
            headers=headers,
            multipart={
                "file": {"name": "image.jpg", "mimeType": "image/jpeg", "buffer": image_bytes},
                "parent_type": "bitable_image",
                "parent_node": self.base_app_token,
                "size": str(len(image_bytes)),
            }
        )
        data = await response.json()
        if data.get("code") == 0:
            return data["data"]["file_token"]
        else:
            raise Exception(f"上传图片失败: {data.get('msg')}")

    async def check_note_exists(self, note_id: str) -> bool:
        """检查指定 note_id 的笔记是否已存在于多维表格中"""
        filter_param = f'''CurrentValue.[{self.field_mapping["note_id"]}]="{note_id}"'''
        encoded_filter = quote(filter_param)
        url = f"{self.BASE_URL}/bitable/v1/apps/{self.base_app_token}/tables/{self.table_id}/records?filter={encoded_filter}&page_size=1"

        print(f"[FeishuClient] 查询去重: app_token={self.base_app_token} table_id={self.table_id} note_id={note_id}")
        
        headers = await self._get_auth_headers()
        response = await self.request_context.get(url, headers=headers)
        data = await response.json()

        if not response.ok:
            raise Exception(f"查询飞书记录失败: {data.get('msg')}")

        if data.get("code") == 0:
            return data.get("data", {}).get("total", 0) > 0
        else:
            raise Exception(f"查询飞书记录失败: {data.get('msg')}")

    async def add_note(self, note_data: Dict[str, Any]):
        """向多维表格中添加一条新的笔记记录"""
        # 移除飞书相关日志输出

        # 根据实际表字段类型进行写入，若获取失败则按文本/URL的默认策略
        field_types = await self._get_field_types()
        fields = {}
        for key, field_name in self.field_mapping.items():
            ftype_norm = self._normalize_field_type(field_types.get(field_name)) if field_types else 'unknown'
            if key == "images":
                # 不上传图片，直接写入图片URL数组为逗号分隔的字符串，或空字符串（文本字段）
                try:
                    imgs = note_data.get("images") or []
                    if isinstance(imgs, list):
                        fields[field_name] = ", ".join(imgs)
                    elif isinstance(imgs, str):
                        fields[field_name] = imgs
                    else:
                        fields[field_name] = ""
                except Exception:
                    fields[field_name] = ""
            elif key == "post_url":
                # 按 URL 超链接对象写入（link+text）。你的表此列为超链接类型。
                try:
                    link = (note_data.get("post_url") or "").strip()
                    text = (note_data.get("title") or link)
                    fields[field_name] = {"link": link, "text": text}
                except Exception:
                    fields[field_name] = {"link": note_data.get("post_url", "")}
            elif key in note_data and note_data[key] is not None:
                # 数值字段按数字写入；否则按文本写入
                try:
                    value = note_data[key]
                    if ftype_norm == 'number':
                        fields[field_name] = self._to_number(value)
                    else:
                        fields[field_name] = str(value)
                except Exception:
                    fields[field_name] = ""

        url = f"{self.BASE_URL}/bitable/v1/apps/{self.base_app_token}/tables/{self.table_id}/records"
        headers = await self._get_auth_headers()
        # 明确指定 JSON 提交，避免被当作表单编码
        headers = {**headers, "Content-Type": "application/json; charset=utf-8"}
        payload = {"fields": fields}
        # 移除飞书请求详情打印

        # 移除飞书请求/响应打印函数
        def _print_req(*args, **kwargs):
            return
        def _print_resp(*args, **kwargs):
            return

        attempt = 1
        while True:
            payload_str = _json.dumps(payload, ensure_ascii=False)
            _print_req(url, headers, payload, attempt)
            response = await self.request_context.post(url, headers=headers, data=payload_str)
            resp_text = ""
            try:
                resp_text = await response.text()
            except Exception:
                resp_text = ""
            _print_resp(response, resp_text)
            try:
                data = _json.loads(resp_text) if resp_text else {}
            except Exception:
                data = {}

            if response.ok and isinstance(data, dict) and data.get('code') == 0:
                break

            # 若为数字字段格式错误，自动将报错字段转换为数字后重试（最多2次）
            msg = (data.get('msg') if isinstance(data, dict) else "") or ""
            err = (data.get('error') if isinstance(data, dict) else {}) or {}
            err_msg = err.get('message', '') if isinstance(err, dict) else ''
            code = data.get('code') if isinstance(data, dict) else None
            import re as _re
            m = _re.search(r"fields\.(.*?)'", err_msg or msg)
            if attempt <= 2 and m:
                bad_field_display_name = m.group(1)
                # 找到映射 key
                bad_key = None
                for k, v in self.field_mapping.items():
                    if v == bad_field_display_name:
                        bad_key = k
                        break
                # URL 字段对象化重试
                if code == 1254068 or 'URLFieldConvFail' in (msg or ''):
                    try:
                        link = (note_data.get('post_url') or '').strip()
                        text_val = (note_data.get('title') or link)
                        payload['fields'][bad_field_display_name] = {"link": link, "text": text_val}
                        attempt += 1
                        continue
                    except Exception:
                        pass
                if bad_key and bad_key in note_data:
                    # 转数字后重试
                    try:
                        num_val = self._to_number(note_data[bad_key])
                        payload['fields'][bad_field_display_name] = num_val
                        attempt += 1
                        continue
                    except Exception:
                        pass

            # 其它错误，抛出
            error_message = (data.get('msg') if isinstance(data, dict) else None) or '未知错误'
            raise Exception(f"添加飞书记录失败: {error_message}")

        # 解析响应 JSON
        resp_text = ""
        try:
            resp_text = await response.text()
        except Exception:
            resp_text = ""
        try:
            data = _json.loads(resp_text) if resp_text else {}
        except Exception:
            data = {}

        if (not response.ok) or data.get('code') != 0:
            error_message = (data.get('msg') if isinstance(data, dict) else None) or '未知错误'
            raise Exception(f"添加飞书记录失败: {error_message}")
        # 成功不打印日志
