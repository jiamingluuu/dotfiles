# BABI 火山账号查询

查询复用 babi-cli 当前登录用户身份。首次使用尚未登录时，按产品 Skill 的认证流程执行
`bytedcli auth login`；不要向用户索取 BABI OpenAPI AK/SK。

## 列出当前用户有权限的有效火山账号

```bash
# 默认只返回账号 ID
bytedcli babi volc-account list --page 1 --page-size 20

# 返回 owner、成本中心、服务树和状态等完整字段
bytedcli babi volc-account list --full --page 1 --page-size 20

# 按一个或多个火山账号 ID 筛选，设置后忽略分页
bytedcli babi volc-account list --full --account-ids demo-volc-account

# 按火山或 BytePlus 类别筛选
bytedcli babi volc-account list --category volc,byteplus
```

`volc-account list` 请求用户态 `POST /v3/cloud_account/volc/list`。登录态由 babi-cli runtime 注入，请求显式携带 `is_auth=true` 与 `status=1` 筛选，只返回当前用户有读取权限且状态有效的账号；不携带 AK/SK。
默认输出账号 ID；`--full` 输出完整记录。`--category` 接受 `volc`、`byteplus`，
CLI 内部分别映射为用户态接口编码 `1`、`2`；`--account-ids` 支持逗号分隔或重复传入。

## 按 ID 查询 owner

```bash
bytedcli babi volc-account get --account-id demo-volc-account
```

`volc-account get` 使用与 BABI 页面一致的账号 ID 搜索条件，请求同一个用户态列表接口，
再按返回记录中的 `volc_account_id` 精确匹配。成功时返回一条规范化记录；没有精确匹配时
返回 not found，不把模糊命中的其他账号作为结果。

## 安全边界

- 该 Skill 只提供查询能力。
- 不调用 BABI OpenAPI AK/SK 签名接口。
- 不调用 identity 或 AK/SK 生成接口。
- 不接收、输出、记录或持久化 BABI OpenAPI 密钥。
