# 描述
用指定接口爬取数据

# 需求

- 目标接口:curl 'https://show-mng.bilibili.co/api/ticket/mis/project/search?name=&id=&pub_min=&pub_max=&sale_min=&sale_max=&start_min=2025-01-01%2000%3A00%3A00&start_max=2025-12-31%2000%3A00%3A00&city=&sale_flag=&type=&project_type=&merchant_name=&is_exclusive=&page=1&size=20&status=1&channel=1&channel_user_id=' \
  -H 'accept: */*' \
  -H 'accept-language: en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7,zh-TW;q=0.6' \
  -H 'cache-control: no-cache' \
  -b 'buvid3=BF4AA9E2-9FDE-705C-604D-4465A1E5859039047infoc; b_nut=1765442938; buvid4=8824C5E2-D62E-9E34-9D3A-1B4889A2600G39047-025121116-kVpKSGPR9WB%2BTkKA9xJ3PQ%3D%3D; _AJSESSIONID=4d14541648ea31c9a3bbf4ca2ac9ccae; username=luke' \
  -H 'pragma: no-cache' \
  -H 'priority: u=1, i' \
  -H 'referer: https://show-mng.bilibili.co/' \
  -H 'sec-ch-ua: "Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"' \
  -H 'sec-ch-ua-mobile: ?0' \
  -H 'sec-ch-ua-platform: "macOS"' \
  -H 'sec-fetch-dest: empty' \
  -H 'sec-fetch-mode: cors' \
  -H 'sec-fetch-site: same-origin' \
  -H 'user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
- 用这个接口不断增加分页，直到拉取所有数据
    - 当前分页：返回的数据的data.page.num
    - 总页数：返回的数据的data.page.total
- 把接口返回的data.item[i]字段id/name/total_count/start_time/end_time存下来，最后统一生成在一个新的Excel里
    - 其中，start_time/end_time是10位的timestamp，需要改成YYYY-MM-dd HH:MM:SS的格式