# 海外 Vimo 线索下发计划

## 目录

- [功能边界](#功能边界)
- [鉴权与网络](#鉴权与网络)
- [标准执行流程](#标准执行流程)
- [筛选参数](#筛选参数)
- [下发应用](#下发应用)
- [常用示例](#常用示例)
- [请求字段映射](#请求字段映射)
- [JSON 输出与分页](#json-输出与分页)
- [错误与安全](#错误与安全)

## 功能边界

使用以下只读命令查询 CapCut 海外 Vimo 的“线索下发计划”：

```bash
bytedcli --site i18n vimo creator clue-plan list [options]
```

该命令固定支持 CapCut 海外业务 `capcut`，可以按计划名称、订阅 ID、包含的
线索 ID、线索国家、下发应用、线索主/子类型和启用状态组合筛选。该 `list` leaf 不会写入；
计划生命周期与线索下发的正式命令见
[`creator-task-mutations.md`](creator-task-mutations.md)。

Vimo 页面上的“订阅”与 CLI 中的“线索下发计划”指同一类记录，因此 `--name` 匹配计划/订阅
名称，`--subscription-ids` 匹配计划的订阅 ID。

## 鉴权与网络

线索下发计划沿用 Creator 线索的海外 Vimo 鉴权，不使用
`BYTEDCLI_USER_CLOUD_JWT`：

| 环境                    | 必需配置                                                     | 目标环境                | 关键行为                                  |
| ----------------------- | ------------------------------------------------------------ | ----------------------- | ----------------------------------------- |
| 托管生产网沙箱          | 完整 `BYTEDCLI_VIMO_COOKIE`；`BYTEDCLI_NETWORK_PROFILE=prod` | 海外 Vimo 生产网 origin | 缺 Cookie 时 fail-closed；忽略 PPE 请求头 |
| 本地/办公网 Cookie 模式 | 完整 `BYTEDCLI_VIMO_COOKIE`                                  | 海外 Vimo 办公网 origin | Cookie 优先于缓存 Session                 |
| 本地/办公网 SSO 模式    | TikTok SSO Session；不设置 `BYTEDCLI_VIMO_COOKIE`            | 海外 Vimo 办公网 origin | 通过 TLB CAS 获取 Vimo Session            |

本地安全读取一次 Cookie 并查询：

```bash
printf 'Vimo Cookie: '
IFS= read -rs BYTEDCLI_VIMO_COOKIE
printf '\n'
export BYTEDCLI_VIMO_COOKIE
bytedcli --site i18n --json vimo creator clue-plan list --page-size 1
unset BYTEDCLI_VIMO_COOKIE
```

生产网查询：

```bash
BYTEDCLI_NETWORK_PROFILE=prod \
  bytedcli --site i18n --json vimo creator clue-plan list --page-size 1
```

办公网无 Cookie 时才登录 TikTok SSO：

```bash
bytedcli --site i18n-tt auth login --session --auto --yes
```

传入完整 Cookie 请求头的值，但不要包含 `Cookie:` 前缀。浏览器登录态变化后，已有 CLI
进程不会自动获得新 Cookie；每个新命令进程都必须由托管环境或本地环境注入当前快照。
同源 `Set-Cookie` 仅更新当前进程的内存 CookieJar，不会回写浏览器、父 Shell、环境变量或
持久 Session 缓存。

生产网 origin 会忽略全局 `x-use-ppe`、`x-tt-env` 和 `x-schedule-vdc`，不要依赖这些头进行
路由。

## 标准执行流程

1. 确认版本和命令参数：

   ```bash
   bytedcli --version
   bytedcli --site i18n vimo creator clue-plan list --help
   ```

2. 根据运行环境选择 Cookie 或办公网 TikTok SSO/CAS。生产网必须使用 Cookie。
3. 需要按线索类型筛选时，先执行 `bytedcli --site i18n --json vimo creator clue-type list`，从实时目录
   取得主、子类型 ID。
4. 把用户明确要求的筛选项组合到 `clue-plan list`。全局 `--json` 必须放在 `vimo` 前面。
5. 检查顶层 `status`。成功时读取 `data.plans`，不要把原始嵌套记录强制压平成固定结构。
6. 当 `data.has_more=true` 时，把 `data.next_cursor` 原样传入下一次 `--cursor`；否则停止。

## 筛选参数

```bash
bytedcli --site i18n --json vimo creator clue-plan list [options]
```

| 参数                       | 默认值 | 筛选语义                                                          |
| -------------------------- | ------ | ----------------------------------------------------------------- |
| `--name <text>`            | 无     | 计划/订阅名称模糊匹配；前后空白会被去除                           |
| `--subscription-ids <ids>` | 无     | 订阅 ID；逗号或中文逗号分隔的正整数多值                           |
| `--clue-ids <ids>`         | 无     | 计划中包含的线索 ID；逗号或中文逗号分隔的正整数多值               |
| `--biz-ids <ids>`          | 无     | “线索国家”选择器返回的地区业务 ID；正整数多值，不是顶层 `the top-level CapCut bid` |
| `--dispatch-app-ids <ids>` | 无     | “下发应用”ID；逗号或中文逗号分隔，只接受 `1`、`2`、`100`          |
| `--main-type <types>`      | 无     | 线索主类型 ID；逗号或中文逗号分隔的非负整数多值                   |
| `--sub-type <types>`       | 无     | 线索子类型 ID；逗号或中文逗号分隔的非负整数多值，应属于所选主类型 |
| `--active <boolean>`       | 无     | `true`=仅查询启用计划；`false`=仅查询停用计划                     |
| `--cursor <cursor>`        | `0`    | 非负十进制分页游标；使用上次返回的 `next_cursor`                  |
| `--page-size <n>`          | `20`   | 单次返回数量，范围 `1..100`                                       |

参数约束：

- 多值参数会自动去除空白、去重，并同时接受英文逗号和中文逗号。
- `--subscription-ids`、`--clue-ids` 和 `--biz-ids` 必须是大于 `0` 的十进制字符串；CLI 按
  字符串保留 64 位 ID 精度。
- `--main-type`、`--sub-type`、`--subscription-ids`、`--clue-ids`、`--biz-ids` 和
  `--dispatch-app-ids` 一旦显式传入就不能为空；空字符串或只有逗号会返回
  `VIMO_INPUT_ERROR`，防止意外扩大查询范围。
- `--active` 只接受严格的 `true` 或 `false`。
- `--cursor` 必须是 JavaScript 安全整数范围内的非负十进制数。分页时使用服务端返回值，
  不要自行递增、拼接或转换成其他格式。
- 当前 CLI 没有地区目录查询命令；`--biz-ids` 需要从 Vimo 页面的“线索国家”选择器或对应
  浏览器请求中取得，不能传 `KR` 等国家码。
- 主、子类型目录会变化。不要在 Agent 提示词或自动化中硬编码固定类型总数、名称或 ID。

## 下发应用

`--dispatch-app-ids` 使用以下固定映射：

| ID    | 含义                 | 使用限制                         |
| ----- | -------------------- | -------------------------------- |
| `1`   | Task / 任务          | 正常业务下发应用                 |
| `2`   | AIGC Template / 模板 | 正常业务下发应用                 |
| `100` | Lark Notice          | 仅测试用途，不要当作生产业务应用 |

可以一次传多个值，例如 `--dispatch-app-ids 1,2`。其他数字会返回 `VIMO_INPUT_ERROR`，CLI
不会把未知应用 ID 透传给服务端。

## 常用示例

```bash
# 先获取实时主、子类型目录
bytedcli --site i18n --json vimo creator clue-type list

# 查询第一页
bytedcli --site i18n --json vimo creator clue-plan list --page-size 20

# 按计划/订阅名称模糊筛选
bytedcli --site i18n --json vimo creator clue-plan list \
  --name 'sample-weekly-plan' \
  --page-size 10

# 按订阅 ID 或计划内线索 ID 筛选
bytedcli --site i18n --json vimo creator clue-plan list \
  --subscription-ids <subscription-id-1>,<subscription-id-2> \
  --clue-ids <clue-id-1>,<clue-id-2>

# 组合国家、下发应用和动态类型筛选
bytedcli --site i18n --json vimo creator clue-plan list \
  --biz-ids <country-biz-id-1>,<country-biz-id-2> \
  --dispatch-app-ids 1,2 \
  --main-type <main-type-id-1>,<main-type-id-2> \
  --sub-type <sub-type-id-1>,<sub-type-id-2>

# 分别查询启用或停用计划
bytedcli --site i18n --json vimo creator clue-plan list --active true
bytedcli --site i18n --json vimo creator clue-plan list --active false

# 继续下一页：next_cursor 必须来自上一页
bytedcli --site i18n --json vimo creator clue-plan list \
  --cursor '<next_cursor>' \
  --page-size 20
```

所有筛选都可以组合；未传入的可选筛选不会进入请求体。

## 请求字段映射

CLI 会固定发送空 `scene` 和 CapCut `the top-level CapCut bid`。筛选放在 BFF 的 `options` 对象中：

| CLI 参数             | BFF 字段                     |
| -------------------- | ---------------------------- |
| `--name`             | `options.name`               |
| `--subscription-ids` | `options.ids[]`              |
| `--clue-ids`         | `options.clue_ids[]`         |
| `--biz-ids`          | `options.biz_ids[]`          |
| `--dispatch-app-ids` | `options.dispatch_app_ids[]` |
| `--main-type`        | `options.main_type[]`        |
| `--sub-type`         | `options.sub_type[]`         |
| `--active`           | `options.is_active`          |
| `--cursor`           | `cursor`                     |
| `--page-size`        | `count`                      |

只有至少一个筛选时才发送 `options`；没有筛选时不会发送空对象。

## JSON 输出与分页

成功输出示例：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "cursor": "0",
    "page_size": 20,
    "plans": [
      {
        "id": "<subscription-id>",
        "name": "sample-weekly-plan",
        "sub_clue": {
          "biz_id": ["<country-biz-id>"],
          "main_type": "<main-type-id>",
          "sub_type": ["<sub-type-id>"]
        },
        "dispatch": {
          "app_id": 1,
          "amount": "20"
        },
        "is_active": true,
        "last_status": "sample-status"
      }
    ],
    "current_count": 1,
    "total": 42,
    "next_cursor": "20",
    "has_more": true
  },
  "error": null,
  "context": {}
}
```

字段语义：

- `plans`：BFF 返回的原始嵌套计划记录。不同下发应用可能增加不同字段；自动化应读取所需
  字段并容忍额外字段。
- `current_count`：本页 `plans.length`。
- `total`：BFF 返回的匹配计划总数。
- `cursor`：当前请求游标；`next_cursor`：服务端返回的下一页游标。
- `has_more`：是否还有下一页。仅在其为 `true` 时继续请求。

文本模式为了可读性只展示计划 ID、名称、下发应用、国家、主/子类型、下发量、启用状态和
最后状态，并可能截断长值。需要完整嵌套数据或稳定机器处理时使用 `--json`。

## 错误与安全

| 错误码                   | 典型原因                                                  | 处理方式                                       |
| ------------------------ | --------------------------------------------------------- | ---------------------------------------------- |
| `VIMO_INPUT_ERROR`       | 空/非法 ID 列表、未知下发应用、非法游标或页大小           | 按参数表修正；先查询动态类型目录               |
| `VIMO_AUTH_REQUIRED`     | 未注入 Cookie、Cookie 已失效，或办公网 SSO/CAS 登录态失效 | 获取当前 Cookie；办公网也可重新登录 TikTok SSO |
| `VIMO_PERMISSION_DENIED` | 当前用户没有 CapCut 海外 Vimo 线索计划读取权限            | 申请对应业务权限后重试                         |
| `VIMO_API_ERROR`         | Vimo 返回其他业务错误                                     | 检查筛选值与业务权限后重试                     |
| `VIMO_PARSE_ERROR`       | 响应结构或 `total` 不符合预期                             | 重试；持续出现时保留脱敏日志反馈服务端         |

安全要求：

- Cookie 值不得超过 64 KiB，不能包含换行、其他控制字符或非法 Cookie 名。
- 不打印、不记录、不写文件、不提交 Cookie、JWT 或完整 HTTP 鉴权头。
- Cookie 模式下，凭证仅绑定当前 CLI 进程；不要通过参数、命令输出或临时文件转交。
- 生产网不携带 PPE 路由头；不要尝试用 PPE 参数绕过生产网 fail-closed。
- 该 leaf 是只读列表查询。写请求只使用
  [`creator-task-mutations.md`](creator-task-mutations.md) 明确列出的语义命令。
