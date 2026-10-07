# 海外 Vimo 模板列表与导航 Tab

本参考适用于 `bytedcli --site i18n vimo template list`、`bytedcli --site i18n vimo template tab list` 与兼容的
请求。它们映射 CapCut 海外 Vimo“模板管理”下的模板列表与导航 Tab；本参考中的 leaf
只提供读取能力。受控模板写命令见
[`template-mutations.md`](template-mutations.md)。

## 命令边界与分流

```bash
bytedcli --site i18n --json vimo template list [--biz capcut] [--region-biz-id <id>] [filters]
bytedcli --site i18n --json vimo template tab list --region-biz-id <id> [--nav-type <id>] [--env draft|online]
```

- `--site i18n vimo template list` 查询视频模板资源；实际 BFF 是
  `POST /template/api/videoTemplate/list/resource/getResource`。
- `--site i18n vimo template tab list` 查询当前“导航Tab”配置；实际 BFF 是
  `POST /template/api/nav/getTabList`。
- `--site i18n vimo creator task-template list` 查询任务管理中的“任务模板”，不是素材模板。
- `--site i18n vimo incentive template list` 查询用户激励中的“推荐模板”，也不是素材模板。

这些查询 leaf 不写入。只能使用 [`template-mutations.md`](template-mutations.md) 明确列出的
元数据、生命周期和标签语义写命令；付费模板添加、Tab 编辑、自动规则及未映射按钮仍
不支持。

## 鉴权与网络

模板列表和导航 Tab 复用 CapCut 海外 Vimo 浏览器 Cookie/SSO 能力，不使用
`BYTEDCLI_USER_CLOUD_JWT`。

托管生产网沙箱应向每个命令进程注入完整、当前的浏览器 Cookie，并选择生产网域名：

```bash
BYTEDCLI_NETWORK_PROFILE=prod \
  bytedcli --site i18n --json vimo template list --page-size 1
```

本地可安全读取一次 Cookie；只传 Cookie 值，不要包含 `Cookie:` 前缀：

```bash
printf 'Vimo Cookie: '
IFS= read -rs BYTEDCLI_VIMO_COOKIE
printf '\n'
BYTEDCLI_VIMO_COOKIE="$BYTEDCLI_VIMO_COOKIE" \
  bytedcli --site i18n --json vimo template tab list --region-biz-id '<region-biz-id>'
BYTEDCLI_VIMO_COOKIE="$BYTEDCLI_VIMO_COOKIE" \
  bytedcli --site i18n --json vimo template list --page-size 1
unset BYTEDCLI_VIMO_COOKIE
```

办公网没有 Cookie 时才使用 TikTok SSO/CAS：

```bash
bytedcli --site i18n-tt auth login --session --auto --yes
bytedcli --site i18n --json vimo template list --page-size 1
```

Cookie 只存在于当前命令进程。服务端返回的同源 `Set-Cookie` 只更新该进程的内存
CookieJar，不会回写浏览器、父 Shell、环境变量或持久 Session。生产网请求会忽略全局
`x-use-ppe`、`x-tt-env` 和 `x-schedule-vdc` 头。

## 模板列表业务参数与分页

| 参数                   | 输入                    | 语义                                                            |
| ---------------------- | ----------------------- | --------------------------------------------------------------- |
| `--biz <nameOrBid>`    | `capcut`                | 可选顶层业务；默认 `capcut`，请求使用 bid `106`                 |
| `--region-biz-id <id>` | 可选正安全整数          | 地区模板业务 ID；默认使用内置 CapCut 地区值，高级用户可显式覆盖 |
| `--query-mode <mode>`  | `warehouse` 或 `server` | 默认 `warehouse`；两种模式差异见下文                            |
| `--page <n>`           | `1..1000000`            | 一基页码；默认 `1`                                              |
| `--page-size <n>`      | `1..1000`               | 单页数量；默认 `20`                                             |

命令查询页面的模板面板。`--biz` 可省略；新调用使用 `capcut`。历史写法 `--biz 106` 为已有脚本
继续保留，两者都会转换为数字顶层 bid `106`。
`--region-biz-id` 未提供时安全默认到内置地区模板业务 ID；它与顶层 CapCut bid 是两个不同概念。仅当用户或 Vimo 页面
明确给出其他地区 `bizId` 时才显式覆盖；不要把 AppID（例如 `3006`）当作地区业务 ID。

## 页面主筛选

| CLI 参数               | 页面含义     | BFF 字段与约束                                                              |
| ---------------------- | ------------ | --------------------------------------------------------------------------- |
| `--template-ids <ids>` | 模板 ID      | `resourceIds: string[]`；逗号、空格或换行分隔，最多 5000 个正 i64，禁止重复 |
| `--uids <ids>`         | CapCut UID   | `uids: string[]`；1..19 位数字，最多 100 个                                 |
| `--hashtag-ids <ids>`  | hashtag ID   | `hashtagIds: string[]`；最多 100 个正 i64                                   |
| `--keywords <values>`  | 素材关键词   | `shortTitles: string[]`；逗号或换行分隔，可组合多个关键词                   |
| `--ratios <values>`    | 尺寸比例     | `scale: number[]`；使用下方语义值                                           |
| `--statuses <values>`  | 素材状态     | `statusList: number[]`；使用下方语义值                                      |
| `--tags <paths>`       | V4 标签      | `template_global_tags: string[]`；传叶节点完整路径，例如 `root/leaf`        |
| `--start <time>`       | 创建时间起点 | 与 `--end` 成对；转换成 epoch 毫秒字符串                                    |
| `--end <time>`         | 创建时间终点 | 与 `--start` 成对；转换成 epoch 毫秒字符串                                  |

所有 ID 在进入 API 前都经过显式校验。模板 ID、UID、hashtag ID 以及响应中的
TemplateID/UID/CreateTime/UsageAmount 等潜在 64 位字段保持字符串，不能先转 JavaScript
`number`。

## 语义枚举

### 素材状态

| CLI 值       | 上游值 | 页面含义 |
| ------------ | -----: | -------- |
| `online`     |      1 | 上线     |
| `offline`    |      2 | 下架     |
| `deleted`    |      3 | 删除     |
| `banned`     |      4 | 封禁     |
| `pre-review` |      5 | 审核前   |

CLI 只暴露当前页面主筛选实际开放的五个状态，不接受裸数字。

### 尺寸比例

| CLI 值     | 上游值 |
| ---------- | -----: |
| `1:1`      |      1 |
| `9:16`     |      2 |
| `16:9`     |      3 |
| `4:3`      |      4 |
| `2:3`      |      5 |
| `940:788`  |      6 |
| `1640:924` |      7 |
| `4:1`      |      8 |
| `other`    |   9999 |

Vimo 选择 `other` 时会忽略其他比例。为避免产生错误的 AND/OR 预期，CLI 禁止把 `other`
与命名比例组合在同一条命令中。

## 更多筛选器

| CLI 参数                       | 值                       | 上游语义                         |
| ------------------------------ | ------------------------ | -------------------------------- |
| `--grades <values>`            | `unrated,high,basic,low` | 评级 0/1/2/3                     |
| `--exclude-test-templates`     | 无值开关                 | 排除测试模板                     |
| `--exclude-test-accounts`      | 无值开关                 | 排除测试账号下的模板             |
| `--mute <boolean>`             | `true`/`false`           | 静音发布/非静音发布              |
| `--resource-scene <scene>`     | `standard`/`shooting`    | 普通剪同款 0 / 拍同款 4          |
| `--template-function <value>`  | 动态字符串               | 模板功能；值来自页面动态配置     |
| `--ccweb-only`                 | 无值开关                 | 只看 CapCut Web 可用模板         |
| `--shared <boolean>`           | `true`/`false`           | 是否用户分享发布                 |
| `--share-result <result>`      | `pass`/`fail`            | 分享模型结果 1/2                 |
| `--originality-types <values>` | 见下方                   | 原创类型数组                     |
| `--publish-biz-ids <ids>`      | 正整数列表               | 模板发布国家业务 ID              |
| `--visibility <value>`         | `profile`/`feed`         | 个人主页可见 100 / feed 流可见 0 |

原创类型值：

- `original`：原创；
- `same-author-processed`：同一创作者轻微加工；
- `different-author-processed`：不同创作者轻微加工；
- `multiple-submissions`：一稿多投；
- `copied`：搬运。

不要为没有公开 flag 的页面字段自行拼装请求。部分 BFF schema 字段当前数仓并未消费，部分
筛选目录来自动态 TCC；Skill 只承诺 `--help` 中已经实现并验证的参数。

## warehouse 与 server

`warehouse` 是默认模式，支持组合所有已实现筛选，并返回数仓总数：

```bash
bytedcli --site i18n --json vimo template list \
  --keywords 'sample-keyword' \
  --statuses online \
  --ratios 9:16 \
  --page 1 \
  --page-size 20
```

按 CapCut UID 精确查询模板时也使用默认的 `warehouse` 模式：

```bash
bytedcli --site i18n --json vimo template list \
  --uids '<capcut-uid-1>,<capcut-uid-2>' \
  --page-size 20
```

`server` 只根据模板 ID 直接获取下游详情，并由 Vimo 在输入 ID 列表上分页：

```bash
bytedcli --site i18n --json vimo template list \
  --query-mode server \
  --template-ids '<template-id-1>,<template-id-2>' \
  --page-size 20
```

`server` 必须提供 `--template-ids`。Vimo 会静默忽略其他数仓筛选，因此 bytedcli 会在请求
前拒绝任何“server + 其他业务筛选”组合。若需要组合筛选，改用 `warehouse`。

日期形式按 UTC 自然日展开：起点为 `00:00:00.000Z`，终点为 `23:59:59.999Z`。也接受
ISO/RFC 3339、Unix 秒或毫秒。不要把带尖括号的占位符不加引号直接粘贴到 Shell；`<` 和
`>` 会被当作重定向。

## 导航 Tab

公开的当前配置入口是导航 Tab：

```bash
bytedcli --site i18n --json vimo template tab list \
  --region-biz-id '<region-biz-id>' \
  --nav-type 2000 \
  --env draft
```

| 参数                   | 约束                           | 含义                                                            |
| ---------------------- | ------------------------------ | --------------------------------------------------------------- |
| `--region-biz-id <id>` | 必填正整数                     | 地区模板业务 ID                                                 |
| `--nav-type <id>`      | 正整数，默认 `2000`            | 导航面板；`2000` 是移动端模板首页，其他值来自 Vimo 当前面板配置 |
| `--env <env>`          | `draft`/`online`，默认 `draft` | 草稿配置或当前生效配置                                          |

`navType` 是动态面板 ID，不能把模板列表筛选值直接传入。接口按导航配置顺序
返回完整 Tab 数组，不分页。`tab_id`、数据库 `id`、`source_tab_id` 保持字符串；状态
`visible/hidden` 对应上游 1/2，排序 `default/recommend/insert` 对应上游 0/1/2。

Tab 的 `label_ids`、`hashtag_ids` 等字段是分发匹配规则。它们不代表 Tab ID。查询某个
Tab 下的 Feed 模板是另一个接口，本命令只列导航 Tab 配置。

## JSON 输出

模板列表成功结构：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "region_biz_id": "<region-biz-id>",
    "query_mode": "warehouse",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "templates": [
      {
        "TemplateID": "<64-bit-template-id>",
        "UID": "<64-bit-author-uid>",
        "ShortTitle": "Sample template",
        "Status": 1,
        "CreateTime": "<unix-seconds>"
      }
    ]
  },
  "error": null,
  "context": {}
}
```

`templates` 保留 Vimo 返回的完整 `PackedTemplate` 记录及未知新字段，常见内容包括
`User`、`Grade`、`ManualReview`、`TextTopicCfg`、`TemplateFunction`、
`templateTags`、`disposalInfo`、版权和发布状态。文本模式只展示摘要；自动化处理应使用
全局 `--json`。

导航 Tab 成功结构包含：

```json
{
  "data": {
    "region_biz_id": 123,
    "nav_type": 2000,
    "env": "draft",
    "tabs": [
      {
        "id": "<64-bit-row-id>",
        "tab_id": "<64-bit-tab-id>",
        "name": "Trending",
        "status": 1,
        "status_text": "visible",
        "sort_type": 1,
        "sort_type_text": "recommend",
        "raw": {}
      }
    ]
  }
}
```

`raw` 保留 BFF 的完整 Tab 记录及未知新字段；自动化应使用全局 `--json`。

## 请求字段与分页

列表请求固定包含当前页面所需上下文：

```json
{
  "scene": "template_manage_region_<region-biz-id>",
  "bid": "<capcut-bid>",
  "bizId": "<region-biz-id>",
  "pageIndex": 1,
  "pageSize": 20,
  "queryMode": "warehouse",
  "selectMethod": "all",
  "tagTreeBiz": 1,
  "agentVersion": "1.0"
}
```

CLI 只在用户提供筛选时添加对应字段。`pageIndex` 从 1 开始；`total` 是符合条件的总模板
数。继续下一页的条件为 `data.page * data.page_size < data.total`。

上面的默认地区业务 ID 来自模板列表配置；显式覆盖后，`scene` 与 `bizId` 会同步使用覆盖值。
Vimo 前置权限中间件还依赖通用 `scene`/`bid` 请求上下文，因此 CLI 会同时发送这些字段。

导航 Tab 请求只发送 `bizId`、`navType` 和 `env`；BFF 返回有序数组，没有 `page` 或
`total`。不要根据数组位置合成长期稳定 ID。

## 错误与安全

| 错误码                   | 含义                                       | 处理                                    |
| ------------------------ | ------------------------------------------ | --------------------------------------- |
| `VIMO_INPUT_ERROR`       | 区域、ID、枚举、时间、分页或模式组合不合法 | 按 `error.hint` 修正参数，不会发请求    |
| `VIMO_AUTH_REQUIRED`     | Cookie 缺失、过期或被拒绝                  | 注入当前浏览器 Cookie，或刷新办公网 SSO |
| `VIMO_PERMISSION_DENIED` | 身份有效但缺少模板列表或导航面板读权限     | 申请相应区域/面板读权限                 |
| `VIMO_API_ERROR`         | Vimo 返回其他业务错误                      | 检查脱敏错误信息和筛选条件              |
| `VIMO_PARSE_ERROR`       | 响应列表、总数或 Tab 不符合契约            | 重试一次后报告脱敏元数据                |

- 始终先检查顶层 `status`，再读取 `data.templates` 或 `data.tabs`。
- 不要打印 Cookie、`X-Bytedance-User`、JWT 或环境变量原值。
- 不要持久化浏览器 Cookie，也不要把它传给非海外 Vimo 域名。
- 不要携带 PPE 头访问生产网域名。
- 不要根据页面按钮猜测并调用模板写接口。
- 显式无效或会被上游忽略的筛选必须 fail-closed，不能降级成更宽的查询。
