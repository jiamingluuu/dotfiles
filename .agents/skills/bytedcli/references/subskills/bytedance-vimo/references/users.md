# 海外 Vimo 用户查询

本参考适用于所有 `bytedcli --site i18n vimo user` 请求。该命令映射 CapCut 海外 Vimo
“基础信息 > 用户查询”页面，只提供查询能力。

## 功能边界

```bash
bytedcli --site i18n --json vimo user list [options]
```

命令支持四种查询模式，且每次必须、也只能选择一种：

1. 按一个或多个 CapCut UID 查询；
2. 按一个或多个 CapCut 号查询；
3. 按营销视频签约状态查询；
4. 按营销图片签约状态查询，可在“已签约”时限定签约日期。

该 `list` leaf 不会列出无筛选的全量用户，也不执行写入。用户查询/基础用户视图与创作者是同级但不同的
业务域；不要用 `--site i18n vimo creator` 的权限、标签、UID 关联或处罚命令修改用户查询/基础用户视图。只有请求明确指向
创作者/作者时，才切换到 [`creator-mutations.md`](creator-mutations.md)。用户创建、删除和 raw patch
仍不支持。页面表格里的国家、创作者类型、标签、创作者来源和推荐渠道是返回字段，不是当前查询接口的筛选条件。

## 鉴权与网络

海外 `/user/**` BFF 优先使用 `i18n-tt` 个人 ByteCloud JWT。JWT 获取失败或服务端返回 HTTP 401
时，读请求才回退到 Vimo Cookie。不要输出 JWT 或 Cookie 原值。

验证已部署 JWT 鉴权的 PPE 环境时，同时传入 PPE 路由头：

```bash
bytedcli --site i18n \
  --http-header "x-use-ppe: 1" \
  --http-header "x-tt-env: sample-ppe-env" \
  --json vimo user list --uids "<capcut-uid>"
```

未部署 JWT 鉴权的环境会返回 401，并按读请求策略回退 Cookie。需要 Cookie 时，可通过
`BYTEDCLI_VIMO_COOKIE` 注入完整浏览器 Cookie，或先建立 TikTok SSO session：

```bash
bytedcli --site i18n-tt auth login --session --auto --yes
bytedcli --site i18n --json vimo user list --uids "<capcut-uid>"
```

生产网入口由 `BYTEDCLI_NETWORK_PROFILE=prod` 选择；全局 PPE 路由头不会覆盖生产网受保护的
`x-use-ppe`、`x-tt-env` 和 `x-schedule-vdc`。

## 参数

| 参数                               | 输入                                      | 语义                                                    |
| ---------------------------------- | ----------------------------------------- | ------------------------------------------------------- |
| `--biz <nameOrBid>`                | `capcut`                                  | 可选顶层业务；默认 `capcut`，请求使用 bid `106`         |
| `--uids <ids>`                     | 逗号、中文逗号、空格或换行分隔            | CapCut UID 精确查询；每个值为 1..19 位数字，最多 100 个 |
| `--ccids <ids>`                    | 逗号、中文逗号、空格或换行分隔            | CapCut 号精确查询，最多 100 个                          |
| `--video-contract-status <status>` | 见下方状态表                              | 按营销视频签约状态查询                                  |
| `--image-contract-status <status>` | 见下方状态表                              | 按营销图片签约状态查询                                  |
| `--start <time>`                   | `YYYY-MM-DD`、ISO/RFC 3339、Unix 秒或毫秒 | 图片签约时间起点；必须与 `--end` 同时使用               |
| `--end <time>`                     | 同上                                      | 图片签约时间终点；必须与 `--start` 同时使用             |
| `--page <n>`                       | `1..1000000`                              | 一基页码；默认 `1`                                      |
| `--page-size <n>`                  | `1..100`                                  | 单页数量；默认 `20`                                     |

四个主查询参数互斥。不要同时传 `--uids` 与 `--ccids`，也不要把标识查询与签约状态查询
混在同一条命令中。上游 BFF 对冲突条件存在静默优先级，bytedcli 会在请求发出前拒绝这种输入，
防止用户误以为所有条件均已生效。

`--biz` 不参与四种查询模式的互斥校验。省略时默认 `capcut`；新调用使用 `capcut`。历史写法
`--biz 106` 为已有脚本继续保留，两者都会解析成数字 bid `106` 后调用 Vimo。

UID 和 CapCut 号列表不允许重复。UID 始终作为字符串处理，不能先转成 JavaScript `number`。

## 签约状态

| CLI 语义值         | 上游值 | 页面含义                 |
| ------------------ | -----: | ------------------------ |
| `unsigned`         |    `0` | 未签约                   |
| `contract-created` |    `1` | 已创建合同，但未完成签约 |
| `signed`           |    `2` | 已签约                   |

上游 IDL 还有一个页面未开放的状态值；CLI 不暴露它。不要直接传数字状态。

`--start` 和 `--end` 只允许与 `--image-contract-status signed` 一起使用，并且必须成对传入。
日期形式按 UTC 自然日展开：起点为 `00:00:00.000Z`，终点为 `23:59:59.999Z`。

## 示例

按 UID 查询：

```bash
CAPCUT_UIDS='<capcut-uid-1>,<capcut-uid-2>'
bytedcli --site i18n --json vimo user list --uids "$CAPCUT_UIDS"
```

按 CapCut 号查询：

```bash
CAPCUT_IDS='<capcut-id-1>,<capcut-id-2>'
bytedcli --site i18n --json vimo user list --ccids "$CAPCUT_IDS"
```

查询已签约营销视频用户查询/基础用户视图：

```bash
bytedcli --site i18n --json vimo user list \
  --video-contract-status signed \
  --page 1 \
  --page-size 20
```

查询指定 UTC 日期范围内完成营销图片签约的用户查询/基础用户视图：

```bash
bytedcli --site i18n --json vimo user list \
  --image-contract-status signed \
  --start 2026-08-01 \
  --end 2026-08-07 \
  --page-size 20
```

查询尚未签约营销图片的用户查询/基础用户视图：

```bash
bytedcli --site i18n --json vimo user list --image-contract-status unsigned
```

不要把带尖括号的占位符原样、且不加引号地粘贴到 Shell；`<` 和 `>` 会被 Shell 当作重定向。

## JSON 输出

成功响应的稳定外层结构如下：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "query_mode": "video-contract-status",
    "page": 1,
    "page_size": 20,
    "pagination_source": "vimo",
    "total": 1,
    "users": [
      {
        "UID": "<capcut-uid>",
        "Name": "Sample User",
        "UniqueIDInfo": { "UniqueID": "sample-capcut-id" },
        "followerCount": "<count>",
        "businessSignCode": 2,
        "businessPicSignCode": 0
      }
    ]
  },
  "error": null,
  "context": {}
}
```

`users` 保留 Vimo 返回的完整原始用户记录和未知新字段。常见字段包括：

- `UID`、`Name`、`AvatarURL`、`Description`、`CreateTime`；
- `UniqueIDInfo.UniqueID`（CapCut 号）；
- `followerCount`、`followingCount`；
- `CapcutCreatorInfo`、`creatorSource`、`recommendChannel`；
- `businessSignCode`、`businessPicSignCode` 及对应签约信息；
- 权限、处罚、推荐和创作者类型等嵌套信息。

不要假设所有可选字段都存在，也不要把 UID、创建时间、关联 UID、粉丝数等潜在 64 位值转换为
JavaScript `number`。文本模式只展示常用摘要；完整处理应使用全局 `--json`。

## 分页差异

- 签约状态模式由 Vimo 服务端分页，`pagination_source` 为 `vimo`。
- UID/CapCut 号模式的 BFF 会一次返回全部已匹配输入；bytedcli 再按 `--page` 和
  `--page-size` 本地切片，`pagination_source` 为 `bytedcli`。
- 两种模式均使用 `data.total` 判断总命中数。继续下一页的条件为
  `data.page * data.page_size < data.total`。

分页方式不同不会改变筛选语义；脚本应读取 `pagination_source`，不要假设上游总会分页。

## 错误与安全

| 错误码                   | 含义                                    | 处理                                       |
| ------------------------ | --------------------------------------- | ------------------------------------------ |
| `VIMO_INPUT_ERROR`       | 查询模式冲突、标识/状态/时间/分页不合法 | 按 `error.hint` 修正参数                   |
| `VIMO_AUTH_REQUIRED`     | JWT 与 Cookie 均不可用或被拒绝          | 检查个人 JWT；必要时注入 Cookie 或刷新 SSO |
| `VIMO_PERMISSION_DENIED` | 身份有效但缺少用户查询权限              | 申请 Vimo 用户查询/基础用户视图权限        |
| `VIMO_API_ERROR`         | Vimo 返回其他业务错误                   | 检查脱敏错误信息和筛选条件                 |
| `VIMO_PARSE_ERROR`       | 响应列表或总数不符合契约                | 重试一次后报告脱敏元数据                   |

- 始终先检查顶层 `status`，再读取 `data.users`。
- 不要打印 Cookie、`X-Bytedance-User`、JWT 或环境变量原值。
- 不要持久化浏览器 Cookie，也不要把它传给非海外 Vimo 域名。
- 不要根据页面按钮猜测并调用用户写接口。
- 显式无效或冲突的筛选必须 fail-closed，不能降级为全量查询。

## 请求字段映射

CLI 调用只读 BFF `POST /user/api/User/getUser`。请求体映射如下：

| CLI                       | BFF 字段                              |
| ------------------------- | ------------------------------------- |
| `--uids`                  | `uids: string[]`                      |
| `--ccids`                 | `ccids: string[]`                     |
| `--video-contract-status` | `videoTemplateContractState: 0\|1\|2` |
| `--image-contract-status` | `imageTemplateContractState: 0\|1\|2` |
| `--start`                 | `imageSignStartTimeStamp`（毫秒）     |
| `--end`                   | `imageSignEndTimeStamp`（毫秒）       |
| `--page`                  | `page`                                |
| `--page-size`             | `pageSize`                            |

`scene` 和 `bid` 不属于该 BFF 的 JSON body。业务上下文由已解析的 CapCut business 和页面
Referer 提供，调用方不要自行添加未声明字段。
