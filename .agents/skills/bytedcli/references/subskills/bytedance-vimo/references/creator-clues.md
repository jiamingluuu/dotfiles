# 海外 Vimo 创作线索

## 目录

- [功能边界](#功能边界)
- [鉴权与网络](#鉴权与网络)
- [标准执行流程](#标准执行流程)
- [查询线索类型](#查询线索类型)
- [查询创作线索](#查询创作线索)
- [常用示例](#常用示例)
- [JSON 输出](#json-输出)
- [错误处理](#错误处理)

## 功能边界

使用以下两个只读命令访问 CapCut 海外 Vimo 中的“创作线索”：

```bash
bytedcli --site i18n vimo creator clue-type list
bytedcli --site i18n vimo creator clue list [options]
```

两者固定支持 CapCut 海外业务 `capcut`。`clue-type list` 动态读取当前主、子
类型目录；`clue list` 查询线索并支持组合筛选。这两个 leaf 不写入；受控 AI 线索创建与下发
见 [`creator-task-mutations.md`](creator-task-mutations.md)。线索类型修改和旧线索删除不支持。

## 鉴权与网络

| 环境                    | 凭证与配置                                                            | 目标 origin                   | 行为                                     |
| ----------------------- | --------------------------------------------------------------------- | ----------------------------- | ---------------------------------------- |
| 托管生产网沙箱          | 注入完整 `BYTEDCLI_VIMO_COOKIE`，设置 `BYTEDCLI_NETWORK_PROFILE=prod` | `vimo-oversea.byteintl.net`   | 缺 Cookie 时 fail-closed；不回退 SSO/CAS |
| 本地/办公网 Cookie 模式 | 注入完整 `BYTEDCLI_VIMO_COOKIE`                                       | `vimo-oversea.tiktok-row.net` | Cookie 优先于缓存 Session                |
| 本地/办公网 SSO 模式    | 先执行 TikTok SSO 登录                                                | `vimo-oversea.tiktok-row.net` | 通过 TLB CAS 获取 Vimo Session           |

生产网命令示例：

```bash
BYTEDCLI_NETWORK_PROFILE=prod \
  bytedcli --site i18n --json vimo creator clue-type list
```

本地安全读取 Cookie：

```bash
printf 'Vimo Cookie: '
IFS= read -rs BYTEDCLI_VIMO_COOKIE
printf '\n'
export BYTEDCLI_VIMO_COOKIE
bytedcli --site i18n --json vimo creator clue-type list
unset BYTEDCLI_VIMO_COOKIE
```

遵守以下约束：

- 传入完整 Cookie 请求头的值，不带 `Cookie:` 前缀。
- Cookie 值不得超过 64 KiB，不能包含换行、其他控制字符或非法 Cookie 名。
- 不打印、不写文件、不提交 Cookie；Cookie 只绑定当前进程并且不写入 Vimo Session 缓存。
- 不使用 `BYTEDCLI_USER_CLOUD_JWT`；它不是 Vimo Web 凭证。
- Creator 命令统一显式传 `--site i18n`；`--site i18n-tt` 只用于办公网 TikTok SSO 登录。
- 生产网不要传 `x-use-ppe`、`x-tt-env` 或 `x-schedule-vdc`。CLI 会在生产网 origin
  忽略这些全局头。
- 浏览器刷新登录态后，旧进程不会自动获得浏览器的新 Cookie。启动新命令进程时必须由
  托管环境重新注入，或在本地重新设置最新 Cookie。
- TLB 返回的同源 `Set-Cookie` 只会更新当前 CLI 进程的内存 CookieJar。它不会回写浏览器、
  `BYTEDCLI_VIMO_COOKIE`、父 Shell 或持久缓存；下一条独立命令仍需要最新 Cookie 快照。
- 办公网没有 Cookie 时才使用：

  ```bash
  bytedcli --site i18n-tt auth login --session --auto --yes
  ```

## 标准执行流程

1. 确认版本和命令面：

   ```bash
   bytedcli --version
   bytedcli --site i18n vimo creator clue-type list --help
   bytedcli --site i18n vimo creator clue list --help
   ```

2. 根据运行环境选择 Cookie 或办公网 SSO。已有 `BYTEDCLI_VIMO_COOKIE` 时不要再登录。
3. 先查询动态类型目录，获取主类型、子类型 ID。
4. 使用 `--json` 执行线索查询；`--json` 必须放在 `vimo` 前面。
5. 检查顶层 `status`。成功时读取 `data.clues`。
6. 当 `data.has_more=true` 时，把 `data.next_cursor` 传给下一次 `--cursor`。

## 查询线索类型

```bash
bytedcli --site i18n --json vimo creator clue-type list
```

命令参数：

| 参数 | 默认值 | 说明 |
| ---- | ------ | ---- |

成功输出中的 `data.types` 结构：

```json
[
  {
    "main_type": "1",
    "name": "sample_main_type",
    "sub_types": [
      {
        "sub_type": "1",
        "name": "sample_sub_type"
      }
    ]
  }
]
```

类型来自实时 `GetClueSysConfig`。不要在 Agent 提示词或自动化中硬编码固定的类型总数、名称
或 ID；先执行该命令，再把所需 ID 传给 `clue list`。

## 查询创作线索

```bash
bytedcli --site i18n --json vimo creator clue list [options]
```

| 参数                         | 默认值 | 筛选语义                                                            |
| ---------------------------- | ------ | ------------------------------------------------------------------- |
| `--main-type <types>`        | `1`    | 主类型 ID；逗号或中文逗号分隔，支持多值并自动去重                   |
| `--sub-type <types>`         | 无     | 子类型 ID；逗号或中文逗号分隔，支持多值并自动去重；应来自所选主类型 |
| `--biz-ids <ids>`            | 无     | “国家”选择器返回的地区业务 ID；正整数多值，不是顶层 `the top-level CapCut bid`       |
| `--title <text>`             | 无     | 把文本传给 Vimo `title` 筛选；匹配规则由 Vimo 服务决定              |
| `--clue-id <id>`             | 无     | 线索 ID；始终按字符串处理                                           |
| `--task-id <id>`             | 无     | 已关联的 Creator 任务 ID；始终按字符串处理                          |
| `--production-task-id <id>`  | 无     | 已关联的 AIGC 投产任务 ID；始终按字符串处理                         |
| `--task-generated <boolean>` | 无     | `true`=已生成 Creator 任务，`false`=未生成                          |
| `--aigc-produced <boolean>`  | 无     | `true`=已生成 AIGC 投产任务，`false`=未生成                         |
| `--cursor <cursor>`          | `0`    | 不透明分页游标，使用上次返回的 `next_cursor`                        |
| `--page-size <n>`            | `30`   | 单页数量，范围 `1..100`                                             |

参数约束：

- `--task-generated`、`--aigc-produced` 只接受严格的 `true` 或 `false`。
- `--biz-ids` 不能传 `KR` 等国家码，也不能传顶层 CapCut bid。当前 CLI 没有地区目录查询命令；
  数字地区业务 ID 需要从 Vimo 页面的国家选择器或对应浏览器请求中取得。
- `--main-type`、`--sub-type`、`--biz-ids` 一旦显式传入就不能为空；空字符串或只有逗号会
  返回 `VIMO_INPUT_ERROR`，防止意外扩大查询范围。
- CLI 选择器中的 64 位 ID 和游标按字符串处理；JSONbig 会保全后端原始记录中的大整数
  精度。不要在调用方把它们转成 JavaScript `number`。
- 标题包含空格或 shell 特殊字符时使用引号，例如 `--title 'Wardrobe Dress Up'`。
- 所有筛选可以组合；未传入的可选筛选不会出现在请求体中。

CLI 到 Vimo BFF 的关键映射：

| CLI                           | BFF 字段                            |
| ----------------------------- | ----------------------------------- |
| `--main-type`                 | `mainTypes[]`                       |
| `--sub-type`                  | `subTypes[]`                        |
| `--biz-ids`                   | `bizIds[]`                          |
| `--title`                     | `title`                             |
| `--clue-id`                   | `clueId`                            |
| `--task-id`                   | `taskId`                            |
| `--production-task-id`        | `relate_serv_objs[]`                |
| `--task-generated true/false` | `status: 1/0`                       |
| `--aigc-produced true/false`  | `has_related_serv["2"]: true/false` |

## 常用示例

按标题查询：

```bash
bytedcli --site i18n --json vimo creator clue list \
  --title 'Wardrobe Dress Up' \
  --page-size 10
```

同时查询多个主、子类型：

```bash
bytedcli --site i18n --json vimo creator clue list \
  --main-type <main-type-id-1>,<main-type-id-2> \
  --sub-type <sub-type-id-1>,<sub-type-id-2> \
  --page-size 20
```

按国家/地区筛选：

```bash
bytedcli --site i18n --json vimo creator clue list \
  --biz-ids <region-biz-id> \
  --page-size 20
```

按任务生成状态筛选：

```bash
bytedcli --site i18n --json vimo creator clue list --task-generated true
bytedcli --site i18n --json vimo creator clue list --task-generated false
bytedcli --site i18n --json vimo creator clue list --aigc-produced true
bytedcli --site i18n --json vimo creator clue list --aigc-produced false
```

按关联任务 ID 筛选：

```bash
bytedcli --site i18n --json vimo creator clue list --clue-id <clue-id>
bytedcli --site i18n --json vimo creator clue list --task-id <creator-task-id>
bytedcli --site i18n --json vimo creator clue list --production-task-id <production-task-id>
```

组合筛选：

```bash
bytedcli --site i18n --json vimo creator clue list \
  --main-type <main-type-id-1>,<main-type-id-2> \
  --sub-type <sub-type-id-1>,<sub-type-id-2> \
  --title 'Wardrobe Dress Up' \
  --biz-ids <region-biz-id> \
  --task-generated true \
  --aigc-produced false \
  --page-size 10
```

继续下一页：

```bash
bytedcli --site i18n --json vimo creator clue list \
  --main-type <main-type-id-1>,<main-type-id-2> \
  --cursor '<next_cursor>' \
  --page-size 30
```

必须原样传递返回的 `next_cursor`，不要自增、拼接或转换为数字；持续查询直到
`has_more=false`。

## JSON 输出

线索列表成功输出：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "cursor": "0",
    "page_size": 10,
    "clues": [],
    "next_cursor": "0",
    "has_more": false
  },
  "error": null,
  "context": {}
}
```

判断规则：

- 先判断顶层 `status`，不要只根据进程是否输出文本判断成功。
- `clues=[]` 且 `status=success` 表示查询成功但没有匹配项，不是鉴权失败。
- 不要假设 `clues` 中每个业务记录只有固定字段；原始线索记录会随 Vimo 契约扩展。
- 使用 `cursor -> next_cursor` 和 `has_more` 分页，不要自行计算页码。
- 不带 `--json` 时，文本表格只展示 `ID`、`Title`、`Main Type`、`Sub Type`、`Region`、
  `Status` 和 `Created`。需要关系、统计等完整原始字段时使用 `--json`。

## 错误处理

| 错误                                | 含义                           | 处理                                           |
| ----------------------------------- | ------------------------------ | ---------------------------------------------- |
| `CLI_PARSE_ERROR`                   | 当前版本不认识命令或参数       | 升级 bytedcli，重新查看 `--help`               |
| `VIMO_INPUT_ERROR`                  | 业务、分页或筛选值非法         | 根据 `error.hint` 修正；不要把空值当成“全部”   |
| `VIMO_AUTH_REQUIRED` / HTTP 401     | 缺少或过期的 Vimo 登录态       | 刷新浏览器 Vimo，并向新进程注入最新完整 Cookie |
| `VIMO_PERMISSION_DENIED` / HTTP 403 | 当前用户缺少对应业务权限       | 申请 CapCut Creator Vimo 权限；不要反复登录    |
| `VIMO_API_ERROR`                    | Vimo 返回业务错误              | 检查筛选组合和 `error.message`                 |
| `VIMO_REQUEST_FAILED`               | Vimo 返回非成功 HTTP 状态      | 检查参数、网络和目标 origin                    |
| `VIMO_PARSE_ERROR`                  | 响应不是预期 JSON 或契约不匹配 | 重试；持续出现时检查 Vimo 服务或 CLI 版本      |
| `HTTP_ERROR`                        | DNS、代理或 origin 不可达      | 核对 `BYTEDCLI_NETWORK_PROFILE` 和当前网络环境 |

不要在错误报告、日志、截图或 AI 输出中包含 Cookie、`X-Bytedance-User`、SSO Cookie 或 JWT
原值。
