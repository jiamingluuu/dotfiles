---
name: bytedance-tiktok-gecko
description: "Use bytedcli tiktok-gecko commands to query TikTok Gecko resources and perform product-level writes including channel create/update/update-size/delete, SCM config, package and release operations, and permission apply/grant. Trigger this skill to search Gecko resources by keyword (cross-resource global search), look up Gecko apps, host apps, deployments (including by access key) or channels (resource discovery, e.g. finding a deployment meta id), list channel groups under a deployment or the channels in a group, get a package's detail, inspect Gecko resources, manage channel metadata or package size limits, create a ticket to take a channel offline, manage packages and releases, manage channel permissions or check your own roles on a channel, inspect a channel's SCM repo configs, approve/reject Gecko tickets as an approver, list a ticket's candidate approvers, cancel/retry/execute Gecko tickets or watch them to a terminal state, or diagnose why a package did not reach a device (为什么资源没下发/扫码诊断)."
---

# bytedcli TikTok Gecko

## 如何调用 bytedcli

本 skill 支持 TikTok ROW (prod) 与 TikTok BOE i18n 两个站点，二选一即可：

```bash
# Prod (TikTok ROW)：默认推导 TikTok SSO
bytedcli --site i18n-tt --auth-site tiktok <command> [options]

# BOE i18n 分区：默认推导 bytedance SSO
bytedcli --site boe <command> [options]
```

- 支持 `--site`：`i18n-tt`（prod，host `tiktok-gecko-global.tiktok-row.net`）、`boe`（BOE i18n 分区，host `tiktok-gecko-global-boei18n.bytedance.net`）。
- 不传 `--site` 时默认按 `i18n-tt`（prod）执行——全局配置里非 gecko 站点（如默认的 `cn`、为其它 domain 设置的 `eu-ttp`）会被忽略。显式传入其它站点（`--site cn` / `--site eu-ttp` 等）仍会被入口拒绝，错误码 `TIKTOK_GECKO_SITE_AUTH_MISMATCH`。
- `--auth-site` 通常无需显式传入：`i18n-tt` 默认推导 `tiktok`，`boe` 默认推导 `bytedance`。**不要**在 `i18n-tt` 上显式传 `--auth-site bytedance`，也**不要**在 `boe` 上显式传 `--auth-site tiktok`，会被入口校验拒绝。
- 推荐先全局安装：`NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest`，后续直接调用 `bytedcli ...`。仅在无法全局安装时退回到 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest` 作为 fallback。

### 站点对照表（site → host / SSO / JWT issuer）

| `--site`  | Backend host                                        | SSO         | JWT issuer                    | 隐式 vregion                                    |
| --------- | --------------------------------------------------- | ----------- | ----------------------------- | ----------------------------------------------- |
| `i18n-tt` | `https://tiktok-gecko-global.tiktok-row.net`        | `tiktok`    | `cloud.tiktok-row.net`        | （无须）                                        |
| `boe`     | `https://tiktok-gecko-global-boei18n.bytedance.net` | `bytedance` | `cloud-boei18n.bytedance.net` | `boei18n`（CLI 自动注入，无需手动 `--vregion`） |

后文示例统一以 `--site i18n-tt --auth-site tiktok` 写出；要打到 BOE，改用 `--site boe`（auth-site 通常省略），并将 `channel update-size/delete` 的 `--x-target-regions` 设为 `boe-i18n`。CLI 内部会按 `--site` 自动切换 base URL、JWT host 与 permission URL，并拒绝这两个命令中 site 与目标 region 不匹配的调用。

## When to use

- 按名称或条件分页查询 Gecko App / Channel / Ticket / Host App（个人待处理工单用 `ticket list --reviewer <me> --status pending-audit`，关注的 channel 用 `channel list --is-follow`）
- 根据 ID 拉取单个 Gecko 资源详情（App、Channel、Ticket、Host App、Deployment）
- 查看 Deployment 下关联的 Channel 列表
- 需要基于 CLI 快速确认 Gecko 资源 ID、地域、状态或关联关系
- **产品级写操作**：创建 Channel（`channel create`）、更新 Channel（`channel update`）、创建/更新 Channel SCM 仓库配置（`channel scm-config create/update`）、创建资源包（`package create`）、启用/禁用资源包（`package enable/disable`）、基于已有 package / SCM source 发起 Release（`release create`）、回滚线上包（`package online rollback`）、申请/授予 channel 权限角色（`permission apply|grant`）
- **Channel 大小与下线**：`channel update-size` 创建修改资源包大小上限的工单（`--pkg-max-size`，必须为 `1..1048575999` bytes，即严格小于后端 1000 MiB 边界；当前不支持清除 channel 级覆盖值）；`channel delete` 创建不可逆的 Channel 下线工单。两个命令都只创建工单，不会立即应用变更；必须先 `--dry-run`，经用户确认后再提交并执行工单。删除工单提交时还必须传 `--acknowledge-same-name-scope`，明确确认同名 Channel 范围。

```bash
bytedcli --site i18n-tt tiktok-gecko channel update-size \
  --deployment-meta-id <deployment_meta_id> --channel-meta-id <channel_meta_id> \
  --pkg-max-size 10485760 --x-target-regions row --dry-run

bytedcli --site i18n-tt tiktok-gecko channel delete \
  --deployment-meta-id <deployment_meta_id> --channel-meta-id <channel_meta_id> \
  --reason 'demo channel is no longer used' --x-target-regions row --dry-run

# 用户确认同名 Channel 影响范围后提交删除工单
bytedcli --site i18n-tt tiktok-gecko channel delete \
  --deployment-meta-id <deployment_meta_id> --channel-meta-id <channel_meta_id> \
  --reason 'demo channel is no longer used' --x-target-regions row \
  --acknowledge-same-name-scope --yes
```

提交成功拿到 `<ticket_id>` 后，继续执行并等待工单终态：

```bash
bytedcli --site i18n-tt tiktok-gecko ticket execute \
  --ticket-id <ticket_id> --deployment-type <online|in-house> --dry-run
# --deployment-type 按 dry-run 展示的工单目标确认；用户确认后，把 --dry-run 换成 --yes
bytedcli --site i18n-tt tiktok-gecko ticket get \
  --ticket-id <ticket_id> --watch --watch-interval 5 --watch-timeout 600
```

- **高级排障 / 内部编排动作**：`ticket cancel/retry/execute` 仅用于已有工单的生命周期操作，不作为普通用户主入口推荐，也不应作为 bytedcli skill 使用场景 UV 天花板统计项。
- **资源下发诊断**：`diagnose create/list/get/finish/stop` 针对一个 region 内的 package 开诊断任务，设备扫码加入后回报控制面 / server / client 检查结果，定位「为什么资源没下发到这台设备」（灰度未命中 / Libra 配置 / 禁止下发 / 版本不匹配等）。纯观测、low risk。

## 前置条件

- 建议先确认目标站点登录态可用：

```bash
# Prod
bytedcli --site i18n-tt --auth-site tiktok auth status
# BOE i18n
bytedcli --site boe auth status
```

- 若未登录或 token 失效，先执行对应站点的 auth login：

```bash
# Prod 登录态走 TikTok SSO
bytedcli --site i18n-tt --auth-site tiktok auth login
# BOE 登录态走 bytedance SSO
bytedcli --site boe auth login
```

> Prod 与 BOE 使用不同 SSO，登录态彼此独立；切站点前确认对应站点的 token 仍有效。

## Quick start — 只读查询

> 后文示例统一写 prod (`--site i18n-tt --auth-site tiktok`)。要改打 BOE，直接把这两 flag 替换成 `--site boe`，命令其余部分不变。例如：
>
> ```bash
> bytedcli --site boe tiktok-gecko channel get --channel-meta-id <id>
> bytedcli --site boe tiktok-gecko ticket get --ticket-id <id>
> ```

```bash
# 列表查询
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko app list --page 1 --page-size 20
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel list --region row --name demo-channel
# 注意：channel list 后端按聚合前单位分页，返回条数可能多于 --page-size（线上观察 page-size 3 返回 6 条）；
# 翻页以 pagination.total/page 为准，不要用 len(items) 推断页数。
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket list --creator demo.user --status pending-audit
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko host-app list --keyword demo-app

# 详情查询（按 ID）。app/channel/ticket/host-app 的 get 也接受位置参数形式（如 `app get <app_id>`），与对应 --xxx-id flag 等价、二选一
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko app get --app-id <app_id>
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel get --channel-meta-id <channel_meta_id>
# 只知道 channel 名称时可以直接 --name：唯一命中直接出 overview；一名多 deployment（各有一个 meta id）时报错并列出 deployment → meta id 候选，按候选换 --channel-meta-id 重跑
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel get --name demo-channel
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket get --ticket-id <ticket_id>
# 需要下钻查询 region 工单详情
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket get --ticket-id <ticket_id> --include-region-ticket-detail=true
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko host-app get --host-app-id <host_app_id>
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko deployment get --deployment-meta-id <deployment_id>

# 等待工单跑到终态（内置 polling，--watch 模式；agent 不要再自己写 sleep loop）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket get --ticket-id <ticket_id> --watch --watch-interval 5 --watch-timeout 600

# 查询部署下的 Channel
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko deployment channel list --deployment-meta-id <deployment_id> --type all

# 查询某个 Channel 下的资源包（推荐）；id 选择器至少提供一个：--channel-meta-id-list / --meta-package-id-list / --region-package-id-list（--creator-list 仅作附加过滤，不能单独使用）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel package list --channel-meta-id-list <channel_meta_id_a>,<channel_meta_id_b> --creator-list demo.user

# 已知 package id 反查（无需 channel id）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel package list --meta-package-id-list <meta_package_id>

# 查询单个资源包详情（按 region package id）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel package get --package-id <region_package_id>

# 获取与 UI 二维码一致的离线包 URL scheme（只读，不触发客户端下载）
# 必须指定单个 region 和 region package ID；普通输出为原始链接，--json 返回 region/package_id/scheme。
# 只接受离线包 ID，不接受 online package ID；后端未返回 qrCodeScheme 时明确报错。
# scheme 是设备下载安装链接，扫码成功后会禁掉轮询更新；拆包调试请优先使用主包链接。
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package scheme --package-id <region_package_id> --region row

# 查询线上包列表（GET /gecko/api/channel/package-online/list）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package online list --channel-region-id <channel_region_id> --target-os android --page 1 --page-size 20

# 按 deployment AK 查 region 级 channel（返回 channel REGION id，非 meta id）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko deployment region-channel list --access-key <deployment_access_key>

# 查询 channel 可用的 SCM 发布源仓库与 release 模板（只读）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release scm-repo list --channel-name demo-channel
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release template list --channel-name demo-channel

# 查询 channel 上所有有权限的账号（按 region；自查角色用 permission list）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko permission account list --channel-meta-id <channel_meta_id>

# 资源包高级过滤（与控制台 package-meta/list 参数对齐）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel package list \
  --channel-meta-id-list <channel_meta_id_a>,<channel_meta_id_b> \
  --region-list row,eu-ttp,us-ttp \
  --target-os-list ios,android \
  --meta-package-id-list <meta_package_id> \
  --region-package-id-list <region_package_id> \
  --package-type-list offline,online \
  --env-lane-list ppe \
  --creator-list demo.user \
  --page 1 --page-size 20
```

> **跨 region 查询的部分失败语义**：Gecko 大多数接口按 region 分片返回。某些 region 查询失败（后端返回失败 envelope）时，命令不会静默丢结果——JSON 输出会带 `region_errors` 数组（`{region, code, message}`；overview 类命令还带 `source` 标注失败的子查询），文本模式打印 Warning 行；**全部** region 都失败时直接报 `TIKTOK_GECKO_REGION_QUERY_FAILED` 错误。看到 `region_errors` 时结果是不完整的，按 hint 换 `--x-target-regions` 重查或稍后重试。
>
> **`--x-target-regions` 缺省行为**：region 分片的只读命令（`channel scm-config list`、`channel-group list`、`channel-group channel list`、`channel package get`、`permission list`、`permission account list`）缺省时自动按当前 site 的全部 region 查询（i18n-tt → `row,eu-ttp,us-ttp`；boe → `boe-i18n`），后端会与资源实际所在 region 求交集。不要靠省略该参数来"只查当前 region"——后端把缺失的 header 当作空 region 列表，而不是当前 region。`channel package get` 的详情接口每次只接受 1 个 region（多 region 会被拒为 `[30000] only for 1 region request`），CLI 会按 region 逐个请求再合并，无需手动拆分。

## Quick start — 写操作（含风险等级）

> **写操作不做客户端权限预检**：所有写命令直接发请求，由后端 `permission_service.checkCurrentUserPermission`（`@CheckPermission` AOP）裁决；权限被拒时 CLI 错误渲染层（`src/services/tiktok_gecko/error_render.ts`）会基于可选的 `--channel-meta-id` 自动附上申请会员链接（host 也按 site 自动切换：prod 用 `tiktok-gecko-global.tiktok-row.net`、BOE 用 `tiktok-gecko-global-boei18n.bytedance.net`；缺 `--channel-meta-id` 时降级到 `/gecko/site/v2` 首页）。详情见下方 "Permission denial 错误渲染（server-side single source of truth）" 小节。
>
> **写命令同样支持 `--site boe`**：把示例里的 `--site i18n-tt --auth-site tiktok` 替换成 `--site boe`，request body / risk gating / dry-run 流程完全一致；CLI 自动改写 base URL 与 permission URL。BOE 上的 channel meta ID 与 prod 是不同的命名空间，**别复用 prod 的 channel meta ID**——先在 BOE 上用 `--site boe tiktok-gecko channel list` 拿到对应 ID 再继续。

### 0. 资源发现（所有写操作的第一步）

每个写命令都需要 `deployment_meta_id`（统一 flag：`--deployment-meta-id`）和目标 region。**不要猜测或复用其他 channel 的值**——先按已知信息定位：

```bash
# 首选：全局关键词搜索（控制台顶部搜索框同款），一次拿到 type + meta id + 各 region id + 归属树
# 注意：后端只返回 top 匹配、无分页；没搜到就换更精确的 keyword 或用 --type 收敛
bytedcli --site i18n-tt tiktok-gecko search --keyword demo-channel
# 只看某类资源：--type app|channel|deployment|host-app（可逗号分隔；结果 type 字段里的后端拼写 host_app 也接受）
bytedcli --site i18n-tt tiktok-gecko search --keyword demo --type channel,deployment

# 路径一：已知宿主 App（如某端内业务）→ 找 Gecko app → 找 deployment（拿 meta_id + region）
bytedcli --site i18n-tt tiktok-gecko host-app list --keyword demo-app
bytedcli --site i18n-tt tiktok-gecko app get --app-id <app_id>
bytedcli --site i18n-tt tiktok-gecko deployment get --deployment-meta-id <deployment_id>

# 路径二：已知 channel 名 → 反查 channel 与归属
bytedcli --site i18n-tt tiktok-gecko channel list --name demo-channel

# 路径三：看某 deployment 下有哪些 channel
bytedcli --site i18n-tt tiktok-gecko deployment channel list --deployment-meta-id <deployment_id>

# 只有 deployment 的 access key（release/package 流程常见）→ 反查 deployment meta 详情
bytedcli --site i18n-tt tiktok-gecko deployment get --access-key <deployment_access_key>
```

所有路径的终点一致：确认 `deployment_meta_id` 与目标 region，再进入下面的写操作。`search` 结果里每条都带 `type` 字段，按 type 接续对应 `get` 命令即可（channel → `channel get --channel-meta-id <meta_id>`，deployment → `deployment get --deployment-meta-id <meta_id>`，app → `app get --app-id <meta_id>`）。

### ID 类型速查表（必读——不同 id 不可互换）

Gecko 的资源同时存在 **meta 层**（跨 region 的全局身份）与 **region 层**（单 region 内的实例）两套 id，flag 名相近但**不可互换**：

| ID 类型                               | 从哪里产出                                                                                                            | 被哪些 flag 消费                                                                                                                                    |
| ------------------------------------- | --------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| channel **meta** id                   | `search`（type=channel 的 `id`）、`channel list`                                                                      | `channel get/update/update-size/delete --channel-meta-id`、`scm-config list/create/update --channel-meta-id`、`permission` 系列 `--channel-meta-id` |
| channel **region** id                 | `channel get` 的 `regionDetails.items[].regionId`、`search` 的 `regions[].regionId`、`deployment region-channel list` | `package online list --channel-region-id`；region id 不接受 `--channel-meta-id`                                                                     |
| deployment **meta** id                | `search`（type=deployment）、`app get`、`deployment get --access-key`                                                 | `deployment get/channel list --deployment-meta-id`、写命令 `--deployment-meta-id`、`channel-group list --deployment-meta-id`                        |
| deployment **access key（AK）**       | release/package 流程、`deployment get` 详情里的 `accessKey`                                                           | `deployment get --access-key`、`release create --target-deployment-ak`                                                                              |
| channel group **名称**                | 控制台注册；`channel-group list` 的 `name`                                                                            | `channel create --channel-group`（传**名称** CSV）                                                                                                  |
| channel group **id**（region-scoped） | `channel-group list` 的 `id`                                                                                          | `channel-group channel list --channel-group-id`（传数字 **id**）                                                                                    |
| meta **package** id                   | `channel package list` 的 Meta Package ID                                                                             | `--meta-package-id-list`；**不能**喂给 `channel package get --package-id`                                                                           |
| region **package** id                 | `channel package list` 的 Region Package IDs（`region:id`）、`package online list` 的 Package ID                      | `channel package get --package-id`、`package enable/disable` 的 REGION:ID 段、`package online rollback --package-id`                                |
| ticket id（meta） / region ticket id  | 写命令返回的 `ticketId` / `ticket get` 的 region 明细                                                                 | `ticket get/approve/reject/cancel/retry/execute --ticket-id`；region 级用 `--region-ticket <region>:<id>`（仅 cancel/retry/execute 支持）           |

### 错误归因与旧参数迁移

- CLI 会把 Gecko 后端 envelope、HTTP 403、工单 watch 终态以及已知旧 option 归一为稳定的 `TIKTOK_GECKO_*` 错误码，现有 bytedcli 调用埋点会随失败事件上报该 `error_code`。错误正文仍保留后端消息，便于按错误码聚合后继续下钻原因。
- 已知旧 option 不会作为 alias 继续请求后端，而是在参数解析阶段返回 `TIKTOK_GECKO_LEGACY_OPTION` 和替换提示。除 ID 层级迁移（`--channel-id` → `--channel-meta-id` / `--channel-region-id`、`--deployment-id` / `--target-deployment-meta-id` → `--deployment-meta-id`、`--region-package-id` → `--package-id`）外，也覆盖 `--package-type` → `--channel-package-type` / `--resource-package-type`、`--size-bytes` → `--pkg-max-size`；具体目标由当前命令决定。
- `TIKTOK_GECKO_PACKAGE_NOT_FOUND` 的 hint 会说明 `--package-id` 需要 region package ID，并指向能产出该 ID 的列表命令。它不会把 meta package ID 自动转换为 region package ID。
- 这些提示只解释既有命令所需的 ID 层级，不新增 ID 转换接口、不做资源存在性或权限预检，也不增加任何 HTTP 请求。遇到 ID 不确定时，按上面的 ID 类型速查表先执行对应只读命令。

### 工单类型速查（是否需审批 / 如何执行）

| 工单来源                           | 是否需审批                                            | 执行方式                                             |
| ---------------------------------- | ----------------------------------------------------- | ---------------------------------------------------- |
| `channel create`                   | 需审批（`ticket approver list` → `ticket approve`）   | 审批通过后 `ticket execute`（或控制台）              |
| `channel update` / `update-size`   | 需审批                                                | 同上                                                 |
| `channel delete`                   | **不需要审批**                                        | `ticket execute` 直接驱动                            |
| `channel scm-config create/update` | 需审批                                                | 审批通过后 `ticket execute` 直接驱动，无需控制台确认 |
| `release create`                   | in-house：low risk 直接提交执行；online：HIGH，走工单 | in-house 无需 execute；online 按工单流程审批后执行   |
| `permission apply/grant`           | 本身就是审批工单（approver 为 channel 管理者）        | 审批通过即生效，无需 execute                         |

`ticket execute --deployment-type` 的取值以 `ticket execute --dry-run` 展示的工单目标为准：目标含 online deployment → `online`（HIGH，需 `--yes`）；仅 in-house → `in-house`。deployment-agnostic 工单（channel create/update/scm-config）按其目标 deployment 的类型判断，拿不准就先 `--dry-run` 看预览。

### 1. Channel Create（HIGH RISK，必须先 `--dry-run` 再 `--yes`）

创建一个新的 Gecko channel（`POST /gecko/api/channel/create`）。该命令会创建一个后续工单（返回 `ticketId`）；channel 是后续 release 发布的承载资源，属于 deployment-agnostic 写操作（没有 `deploymentType` 可供判级），risk gating 始终判定为 **HIGH**，必须走 `--dry-run` → 用户确认 → `--yes` 二段式。

```bash
# Step 1: 预览请求体，向用户展示（HIGH RISK — 不要自动确认）
# channel-type / channel-package-type 用语义值；deploymentId / creator 由后端从 targetDeploymentMetaIdList / JWT 推导
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel create \
  --deployment-meta-id <meta_id> \
  --name demo-channel \
  --channel-type offline+online \
  --channel-package-type compressed-file \
  --service-tree-id <service_tree_id> \
  --business-scope base --tech-type lynx \
  --x-target-regions row,eu-ttp \
  --dry-run

# Step 2: 用户明确同意后，把同一条命令的 --dry-run 换成 --yes 重新执行
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel create \
  --deployment-meta-id <meta_id> \
  --name demo-channel --channel-type offline+online --channel-package-type compressed-file \
  --service-tree-id <service_tree_id> --business-scope base --tech-type lynx \
  --x-target-regions row,eu-ttp --yes

# 带可选字段（角色、config）的完整示例（同样先 --dry-run 再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel create \
  --deployment-meta-id <meta_id> \
  --name demo-channel --channel-type offline+online --channel-package-type compressed-file \
  --service-tree-id <service_tree_id> --x-target-regions row,eu-ttp \
  --business-type platform-manual --masters demo.master --developers demo.dev1,demo.dev2 --approvers demo.approver \
  --channel-group on_demand --normal-prefix-rule '${deploymentId}/teko/resource' --pkg-max-size 10485760 \
  --business-scope experiment --business-scope-detail 'sample experiment assets' \
  --tech-type model --discard-time '2026-12-31 08:00' --dry-run
```

- **必填项**：`--deployment-meta-id`（可重复或逗号分隔，至少一个）、`--name`、`--channel-type`、`--channel-package-type`、`--service-tree-id`、`--business-scope`、`--tech-type`。`--x-target-regions` 可选：缺省时 CLI 自动按目标 deployment 实际覆盖的 region 推导（见下方坑 3）。
- **`--channel-type`**：`offline | offline+online`（控制台禁用单独的 `online`；CLI 同样拒绝）。原始数字编码仍兼容（如 `--channel-type 1`）。
- **`--channel-package-type`**：`compressed-file | uncompressed-file | settings-data`（控制台创建不提供 `settings-file`；CLI 同样拒绝）。与 `package enable/disable` 的 `--resource-package-type`（`offline_package|online_package`）不是同一套词表。
- **创建来源**：`--business-type none | platform-manual | open-api | ad-landing | ad-creation | spark-platform`；通常从 CLI 手工创建时使用 `platform-manual`。原始数字编码仍兼容。
- **后端推导字段**：不要传请求体里的 `base.deploymentId` / `base.creator`；global-server 从 `targetDeploymentMetaIdList` 和 JWT 登录态生成最终 Sot。
- **角色/开关类可选项**：`--masters` / `--developers` / `--approvers`（csv SSO 用户名；裸名会自动补成 `user_account:<name>`）、`--package-need-approve` / `--disable-self-approve`。
- **config 段**：`--channel-group`（csv；仅在需要把 channel 加入指定分组时传）、`--normal-prefix-rule`（多 app 用 `${deploymentId}` 模板，见坑 2）、`--pkg-max-size`（单位 byte，范围 `1..1048575999`）。
- **business 段**：`--business-scope base | permanent | activity | experiment`（必填）。除 `base` 外必须同时传 `--business-scope-detail`。
- **技术栈**：`--tech-type`（必填）`lynx | react-native | h5 | react-unity | image | video | audio | animation | model | static-other | other`。`other` / `static-other` 分别必须搭配 `--tech-type-detail` / `--tech-type-static-detail`。
- **下线时间**：`--discard-time` 接受 Unix 秒、`YYYY-MM-DD HH:mm`（按 CLI 所在机器本地时区）或带时区的 RFC3339；CLI 在请求前统一转换为 Unix 秒字符串，非法日期和毫秒时间戳会直接报 `TIKTOK_GECKO_INPUT_ERROR`。
- dry-run 的 `semantic_summary` 和文本摘要会同时展示语义名称与后端编码，并把包大小展示为 MiB + byte，便于用户确认后再提交。
- ⚠️ `--deployment-meta-id` 是 deployment id 列表（见坑 1），`--normal-prefix-rule` 多 app 用 `${deploymentId}` 模板（见坑 2）。**别逐字照抄参照 channel 的配置**。
- 非 TTY 环境下缺 `--yes` 会以结构化错误码 `TIKTOK_GECKO_HIGH_RISK_NEED_YES` 拒绝执行；TTY 下会弹 `Proceed with HIGH RISK channel create? [y/N]` 交互 prompt。
- 创建成功后返回 `ticketId`，但**工单不会自动执行**（停在待审批/待执行态）。审批环节可全程在 CLI 完成：用 `ticket approver list --ticket-id <ticket_id>` 查候选审批人；审批人用 `ticket approve --ticket-id <ticket_id>`（ALWAYS HIGH RISK，先 `--dry-run` 再 `--yes`）通过后，再用 `tiktok-gecko ticket execute --ticket-id <ticket_id>` 继续执行；CLI 会兼容控制台同款 meta ticket execute 流程处理 `PASS(3)` 状态。也可以把工单链接返回给用户，让用户在控制台打开并确认执行：
  - 链接格式：`https://tiktok-gecko-global.tiktok-row.net/gecko/site/ticket/<ticketId>`（BOE 站点把 host 换成 `tiktok-gecko-global-boei18n.bytedance.net`）。
  - 例如返回的 `ticketId` 为 `<ticket_id>` 时，可执行 `tiktok-gecko ticket execute --ticket-id <ticket_id>`，或给用户 `https://tiktok-gecko-global.tiktok-row.net/gecko/site/ticket/<ticket_id>` 手动执行。执行完成后再用 `channel list --name <name>` 确认 region/deployment 是否齐全。

#### Channel Create 实战要点 / 常见坑（MUST READ）

以下都是实际创建 channel 时高频踩的坑，按报错顺序排列。参照已有 channel 复制配置时尤其注意坑 2（前缀模板不要逐字照抄）。

1. **`--deployment-meta-id` = 目标 app 的 deployment id 列表，不是 channel meta id。**
   - 想让 channel 同时覆盖多个 app（如 TIKTOK + Musically），就把这些 app 各自的 in_house/online deployment id 全列进去（例如 TIKTOK=`1,2`、Musically=`3,4` → `--deployment-meta-id 1,2,3,4`；也可重复传该 option）。
   - 不确定有哪些 deployment id 时：`channel get --channel-meta-id <参照channel>` 看 `relatedDeploymentIds`，或 `deployment get --deployment-meta-id <id>` 看 `relatedDeployments`（同一 app 的 in_house↔online 互为 related）。
2. **`--normal-prefix-rule` 多 app 必须用模板 `${deploymentId}/teko/resource`，不要硬编码数字前缀。**
   - 字面量前缀（如 `7/teko/resource`）跨多个 app 会报 `[30000] Can't set the same prefix rule under multiple apps!`；即使单 app，硬编码的数字若不属于目标 deployment 还会报 `Your default prefix rule use illegal deploymentId!`。
   - 正确写法是字面 `${deploymentId}` 模板（shell 里务必用**单引号**包住，避免被展开成空串），后端会按每个 deployment 自动替换成各自的 id。参照 channel 里看到的 `7/teko/resource` 是历史遗留/控制台特殊产物，**不要照抄**。
   - 不需要自定义前缀时，直接省略 `--normal-prefix-rule`，让后端自动分配。

3. **`--x-target-regions` 决定 channel/工单在「哪些 region」创建；缺省时 CLI 通过一次只读的 deployment 查询自动推导出目标 deployment 实际覆盖的 region 集合（最不容易踩错配坑）。显式传值时，每个 region 都必须在目标 deployment 的覆盖范围内，否则后端预检报 `Target operation region can not be null!`。若传了 `--channel-group`，该 group 必须在所有目标 region 都已注册，否则报 `"<group>" isn't exist in all region!`。不需要加入指定分组时可以省略 `--channel-group`。**
   - **合法 region 取值只有 `row` / `eu-ttp` / `us-ttp` / `boe-i18n`（`boe-i18n` 用于 `--site boe`），没有裸的 `ttp` / `eu` / `us`**：US TTP 用 `us-ttp`，EU TTP 用 `eu-ttp`，全球用 `row`。CLI 会在发请求前对 `--x-target-regions`（以及 `--target-region` / `--online-region` / `--region` / `--region-ticket` 等所有写操作的 region 入参）做客户端校验，传错会直接报 `TIKTOK_GECKO_INPUT_ERROR` 并给出「did you mean ...」提示，不会再打到后端拿 `Region "ttp" is illegal!`。
   - 什么时候显式传：想把创建范围收敛到 deployment 覆盖范围的子集时（例如 group 只在部分 region 注册）。仅当传了 `--channel-group` 时，还需要确保该 group 已在每个目标 region 注册；否则整单会被拒绝（`isn't exist in all region!`）。
   - 典型坑：`us-ttp`（USDS 合规隔离区，独立 CDN/cloud）常常没有注册对应 channel group，于是带 `us-ttp` 的整单被拒。
   - 传了 `--channel-group` 时，用 `--x-target-regions` 把创建范围收敛到 group 真实存在的 region（例如先 `--x-target-regions row,eu-ttp` 建好，控制台补齐其他 region 的 group 注册后再单独扩区）。
   - **CLI 在真实提交（`--yes`）前会自动跑两项后端预检**（dry-run 不提交；缺省 `--x-target-regions` 时 dry-run 也会跑一次只读的 deployment region 推导查询）：① channel 名称敏感词校验，命中报 `TIKTOK_GECKO_CHANNEL_NAME_INVALID`；② 若传了 `--channel-group`，校验 group 在所有目标 deployment 的交集里，缺失报 `TIKTOK_GECKO_CHANNEL_GROUP_NOT_AVAILABLE`，并在 hint 里列出当前可用的 group 列表。预检接口本身不可达时自动跳过，仍以后端 create 的裁决为准。
   - 排查 group 注册情况用只读命令：`channel-group list --deployment-meta-id <deployment_meta_id>` 看某 deployment 下各 region 注册了哪些 group；`channel-group channel list --channel-group-id <group_id>` 看某 group 下挂了哪些 channel。

### 2. Channel Update（HIGH RISK，必须先 `--dry-run` 再 `--yes`）

更新一个已存在的 Gecko channel（`POST /gecko/api/channel/update`）。channel 创建时信息很可能没有一次填全/填对，本命令用于修正：以 `--channel-meta-id` 定位 channel（与 `channel get` / `channel delete` / `channel update-size` 同名），只传需要修改的字段（后端按 patch 语义处理），同样创建后续工单（返回 `ticketId`）。与 create 一样属于 deployment-agnostic 写操作，risk gating 始终 **HIGH**，必须 `--dry-run` → 用户确认 → `--yes`。

```bash
# Step 1: 预览更新 payload，向用户展示（HIGH RISK — 不要自动确认）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel update \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> \
  --service-tree-id <new_service_tree_id> \
  --x-target-regions row \
  --dry-run

# Step 2: 用户明确同意后，把同一条命令的 --dry-run 换成 --yes 重新执行
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel update \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> --service-tree-id <new_service_tree_id> \
  --x-target-regions row --yes

# 修改多个属性（业务类型 / 审批开关 / business 段）的示例（先 --dry-run 再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel update \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> \
  --business-type platform-manual --package-need-approve --disable-self-approve \
  --business-scope experiment --business-scope-detail 'sample experiment assets' \
  --tech-type model --discard-time '2026-12-31 08:00' --x-target-regions row --dry-run
```

- **必填项**：`--deployment-meta-id`（可重复或逗号分隔，至少一个）、`--channel-meta-id`。`--x-target-regions` 可选：缺省时与 create 相同，自动按目标 deployment 覆盖的 region 推导。其余字段都是可选的，只传需要修改的即可。
- **可改属性**：`--business-type`、`--package-need-approve` / `--disable-self-approve`（布尔开关，置位后设为 1）、`--service-tree-id`。
- **business 段**：与 create 使用相同的语义值和条件参数。非 `base` 的 `--business-scope` 必须搭配 `--business-scope-detail`；`other` / `static-other` 技术类型分别必须搭配 `--tech-type-detail` / `--tech-type-static-detail`。
- **下线时间**：`--discard-time` 与 create 一样接受 Unix 秒、CLI 本地时间或带时区 RFC3339，并在请求前归一为 Unix 秒字符串。
- 与 create 不同，update 不能改 `name` / `channelType` / `packageType` / `creator` / 角色成员；这些在创建时确定，成员变更走控制台的成员管理入口。
- 非 TTY 环境下缺 `--yes` 会以 `TIKTOK_GECKO_HIGH_RISK_NEED_YES` 拒绝执行；TTY 下会弹 `Proceed with HIGH RISK channel update? [y/N]` 交互 prompt。
- 更新成功只表示工单创建成功，并不表示变更已经应用。审批通过后用 `tiktok-gecko ticket execute --ticket-id <id>` 执行，再用 `tiktok-gecko ticket get --ticket-id <id> --watch` 等待终态。

### 2.4 Channel Package Size / Delete（HIGH RISK，只创建工单）

- `channel update-size`：创建包大小上限变更工单；`--pkg-max-size` 使用 byte，只接受 `1..1048575999`。region-server 的部分读取路径把大于等于 1000 MiB 的配置回退为平台默认值，因此 CLI 使用严格小于 1000 MiB 的一致边界。当前接口不能可靠表达“清除 channel 级覆盖值”，因此 CLI 拒绝 `0`。
- `channel delete`：创建 Channel 删除工单；`--reason` 必填。删除不可逆，命令本身不会立即删除 Channel。后端会先用 `--channel-meta-id` 解析 channel 名称，再作用于所选 deployments / regions 下全部同名 Channel，并非只处理传入的 meta id；必须根据 dry-run 中的目标参数确认影响范围。
- 两个命令都要求 `--deployment-meta-id`、`--channel-meta-id`、`--x-target-regions`，始终为 HIGH RISK；必须先 `--dry-run`，得到用户明确确认后再用 `--yes` 提交。`channel delete` 提交时还必须传 `--acknowledge-same-name-scope`；缺少该确认参数时，即使传入 `--yes` 也不会创建工单。
- 提交后返回的 `ticketId` 只是工单 ID。`update-size` 需要先等待审批通过；`delete` 工单不需要审批。根据工单目标确认 `--deployment-type`，执行 `ticket execute --ticket-id <id> --deployment-type <online|in-house>`，再执行 `ticket get --ticket-id <id> --watch`。不要把“工单创建成功”描述为“大小已更新”或“Channel 已删除”。

### 2.5 Channel SCM Repo Config（HIGH RISK，必须先 `--dry-run` 再 `--yes`）

修改 channel 的 SCM 仓库分发配置（repo 驱动的 offline/online 资源分发）。**典型时序**：先 `channel create`（或 `channel update`）创建/修正 channel 并执行其工单完成后，再用本命令为 channel 配置 SCM 仓库。三个子命令：

- `channel scm-config list`（`GET /gecko/api/scm-repo-config/list-by-channel-meta-id`）：只读查看 channel 当前挂载的 SCM 配置（按 region 展示）。**改配置前先跑它确认现状**，不要盲改。list/create/update 都使用 `--channel-meta-id`。`--x-target-regions` 缺省时 CLI 自动按当前 site 的全部 region 查询（i18n-tt → `row,eu-ttp,us-ttp`；boe → `boe-i18n`）；后端把缺失的 region header 当作空列表（不是"当前 region"），会直接报 `Channel not found`，所以不要试图靠省略该参数来"查默认 region"。
- `channel scm-config create`（`POST /gecko/api/scm-repo-config/create`）：为 channel 新建 SCM 仓库配置。
- `channel scm-config update`（`POST /gecko/api/scm-repo-config/update`）：以 `--channel-meta-id` + `--scm-repo` 定位已有 SCM 仓库配置并 patch。

create/update 都是 deployment-agnostic 写操作、都会创建后续工单（返回 `ticketId`），risk gating 始终 **HIGH**，必须 `--dry-run` → 用户确认 → `--yes`。

```bash
# Step 0: 只读查看当前 SCM 配置（改之前先看现状）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel scm-config list \
  --channel-meta-id <channel_meta_id>

# Create — Step 1: 预览（HIGH RISK — 不要自动确认）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel scm-config create \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> \
  --scm-repo org/repo \
  --online-config '[{"configType":"all","resourcePath":"./dist"}]' \
  --dry-run

# Create — Step 2: 用户同意后把 --dry-run 换成 --yes 重新执行
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel scm-config create \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> --scm-repo org/repo \
  --online-config '[{"configType":"all","resourcePath":"./dist"}]' --yes

# Update — 以 channel meta id + scm repo 定位，patch offline/online 列表（先 --dry-run 再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko channel scm-config update \
  --deployment-meta-id <meta_id> \
  --channel-meta-id <channel_meta_id> --scm-repo org/repo \
  --offline-config '[{"configType":"iOS","resourcePath":"./ios"}]' --dry-run
```

- **Create 必填**：`--deployment-meta-id`（可重复/逗号分隔，至少一个）、`--channel-meta-id`、`--scm-repo`，且 `--offline-config` / `--online-config` 至少提供一个。
- **Update 必填**：`--deployment-meta-id`、`--channel-meta-id`、`--scm-repo`，同样至少提供一个 config 列表。后端会按 `channelMetaId + scmRepo` 查找目标配置 id。
- ⚠️ **`--deployment-meta-id` 必须把目标的所有 deployment id 列全（和 channel create 坑 1 同根因）。** SCM 配置按 `targetDeploymentMetaIdList` 逐个 deployment 写入，只传一个（例如只传 TIKTOK online 的 meta id）就**只会改到那一个 deployment**，TIKTOK 内测、MUSICALLY 在线、MUSICALLY 内测都不会被更新（偶发"只改了 TIKTOK 在线"就是这么来的）。想同时覆盖 TIKTOK + Musically 的 in_house/online 四个环境，就把四个 deployment id 全列进去（`--deployment-meta-id <tiktok_inhouse> <tiktok_online> <musically_inhouse> <musically_online>`）。不确定有哪些 id：`channel get --channel-meta-id <channel_meta_id>` 看 `relatedDeploymentIds`，或 `deployment get --deployment-meta-id <id>` 看 `relatedDeployments`。
- **配置列表入参**：`--offline-config` / `--online-config` 接收 JSON 数组（每个元素是一条配置明细，至少含 `configType` 与 `resourcePath`）；也可用 `--offline-config-file` / `--online-config-file` 从文件读取同样的 JSON。不要直接粘贴控制台完整对象；CLI 会拒绝不支持的字段，避免 dry-run 展示与实际提交不一致。
- **配置明细字段**：`configType`（如 `all`/`CDN`/`iOS`/`Android`/`Web`/`Mac`/`Windows`）、`resourcePath`（如 `./dist`）必填；可选 `targetAppVersion`、`issueType`、`issueValue`、`enableCDNDeploy`、`envLane`（数组）。
- 非 TTY 环境下缺 `--yes` 会以 `TIKTOK_GECKO_HIGH_RISK_NEED_YES` 拒绝执行；TTY 下会弹 `Proceed with HIGH RISK channel scm-config create/update? [y/N]` 交互 prompt。
- 成功后返回 `ticketId`。与 channel create/update 不同，**SCM 配置工单支持用 CLI 的 `ticket execute` 直接驱动执行，无需人工打开控制台确认**：审批通过后工单停在待执行态，用 `tiktok-gecko ticket execute --ticket-id <id>` 触发执行（仍走 risk gating，按目标 deployment 传 `--deployment-type`，省略则 fail-safe 视为 HIGH），再用 `tiktok-gecko ticket get --ticket-id <id> --watch` 等待终态。

#### JSON 多行换行（必读）

config 列表是 JSON，建议写成单行内联字符串（如上例）。若必须在 shell 里跨多行，用 `$'...'` 写换行，不要用普通双引号里写 `\n`（bash/zsh 双引号不解释 `\n`，CLI 会拿到字面量两个字符）。更稳妥的做法是把 JSON 存成文件后用 `--online-config-file <path>` / `--offline-config-file <path>` 读取。

### 3. Advanced: Package Create / Enable / Disable（底层直连 API，按 deployment type 判级）

> **Advanced**：这组命令直连后端 package 原始接口，面向内测、排障或特殊场景。常规生产发布优先使用 `release create`（第 4/5 节）或业务发布流水线，不要把 `package create` 当作发布主路径。

`package create` 覆盖 `PACKAGE_CREATE`，支持 offline / online 两个后端 create endpoint。因为离线包和线上包创建表单字段较多且结构不同，CLI 当前以 `--body-json` / `--body-file` 透传后端请求体；body 至少需要包含 `channelName`、`targetOs`、`targetAppVersion`，以及 `targetDeploymentAkList` 或 `targetDeploymentMetaIdList`。offline create 还需要 `candidatePackageId`；不要传顶层 `url`，后端不会消费。

```bash
# Offline package create（用户测试 / in-house 场景）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package create \
  --type offline \
  --body-json '{"channelName":"demo-channel","targetDeploymentAkList":["<ak>"],"candidatePackageId":"<candidate_package_id>","targetOs":2,"targetAppVersion":"1.2.3","issueType":1,"issueValue":{"pct":100}}' \
  --x-target-regions row \
  --deployment-type in-house \
  --dry-run

# Online package create（prod/online 必须先 dry-run，确认后再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package create \
  --type online \
  --body-file /path/to/create-online-package.json \
  --x-target-regions row \
  --deployment-type online \
  --dry-run
```

`package enable` / `package disable` 覆盖 `PACKAGE_ENABLE` / `PACKAGE_DISABLE`，底层接口是 `POST /gecko/api/channel/package-meta/switch-package-status`。单个目标可用 `--region + --package-region-id + --resource-package-type`，多个目标用重复 `--package REGION:PACKAGE_REGION_ID:RESOURCE_PACKAGE_TYPE`。

```bash
# Enable offline package
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package enable \
  --package row:<package_region_id>:offline_package \
  --x-target-regions row \
  --deployment-type in-house \
  --dry-run

# Disable online package（prod/online 必须先 dry-run，确认后再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package disable \
  --region row \
  --package-region-id <package_region_id> \
  --resource-package-type online_package \
  --x-target-regions row \
  --deployment-type online \
  --dry-run
```

- `--type`（`package create`）：`offline` → `/gecko/api/channel/package/create`；`online` → `/gecko/api/channel/package-online/create`。
- `--resource-package-type` / `--package` 第三段：`offline_package` 或 `online_package`（不要与 channel create 的 `--channel-package-type` 混淆）。
- `--deployment-type` 只用于 CLI 端 risk gating：`in-house` 判 low；`online` 或省略都判 HIGH。
- prod package 通常仍应走业务特定流水线；这个能力主要用于用户测试、排障、或明确需要直接调用 Gecko package API 的场景。

### 4. In-house Release（low risk，agent 可直接执行）

`release create` 的对象是已有 Gecko resource package / SCM source 的发布动作，不等同于从零创建资源包。若还没有资源包，先走 `package create` 或业务流水线；prod package 发布通常应走业务特定流水线，不应默认用本 skill 替代。

定位靠 `--channel-name` + `--target-deployment-ak`（+ region / apply-type 等）。可选的 `--channel-meta-id` **不参与发布定位**，仅在权限被拒时用来拼 apply-membership 链接。

```bash
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  --channel-name demo-channel \
  --apply-type offline \
  --description 'fix demo bug' \
  --target-region row \
  --target-deployment-ak <ak> \
  --from-branch master --scm-repo my/repo \
  --target-os android --target-app-version 1.2.3 \
  --deployment-type in-house
```

- `--deployment-type in-house` 让 risk gating 判定为 low，可直接执行。
- 不传 `--deployment-type` 会被 fail-safe 判为 HIGH，需要 `--dry-run` + `--yes` 二段式。

**批量聚合（一张工单发多个 channel / 多个 deployment）**：`--channel-name` / `--target-region` / `--target-deployment-ak` 三个 flag 均可重复或逗号分隔（`--target-deployment-ak <ak_a>,<ak_b>` 与重复两次等价），按出现顺序 zip 成多个 target；只出现一次的 flag 自动广播到所有 target。同一 channel 的多端 deployment（例如 M/T 双 app）就是「channel + region 各一次、AK 重复多次」。**不要**为每个 channel/deployment 逐个开工单——同一 SCM 产物的目标应合并为一张工单。批量对下一节的 Online Release 同样适用（风险等级规则不变）。

**每个 target 各自的 resource path（分片产物）**：`--resource-path` 与 `--online-resource-path` 也可重复，按位置与 `--channel-name` 配对；只给一个值时广播到所有 target。路径**不做逗号切分**（路径本身可能含逗号），要给多个就重复这个 flag。分片模型（一个产物切成多片、每片一个 channel 一个路径）因此可以一张工单发完，不需要一片一单，也不需要裸调 API。

```bash
# 一张工单发 2 个 channel（同 SCM 产物、同发布配置；region 广播为 row）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  --channel-name demo-a --channel-name demo-b \
  --target-region row \
  --target-deployment-ak <ak_a> --target-deployment-ak <ak_b> \
  --apply-type offline --description 'batch release' \
  --from-branch master --scm-repo my/repo \
  --target-os android --target-app-version 1.2.3 \
  --deployment-type in-house

# 一张工单发同一 channel 的两个 deployment（如 M/T 双 app）：只重复 AK
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  --channel-name demo-channel \
  --target-region row \
  --target-deployment-ak <ak_app_m> --target-deployment-ak <ak_app_t> \
  --apply-type offline --description 'M/T batch' \
  --from-branch master --scm-repo my/repo \
  --target-os android --target-app-version 1.2.3 \
  --deployment-type in-house

# 分片产物：一张工单，每个分片 channel 配自己的 resource path（按位置配对）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  --channel-name demo-shard-1 --channel-name demo-shard-2 --channel-name demo-shard-3 \
  --resource-path ./demo_model-1 --resource-path ./demo_model-2 --resource-path ./demo_model-3 \
  --target-region row --target-deployment-ak <ak> \
  --apply-type offline --description 'shard release' \
  --from-branch master --scm-repo my/repo \
  --target-os ios --target-app-version 1.2.3 \
  --deployment-type in-house --dry-run
```

- 各 flag 的重复次数必须等于 target 数或恰好为 1（广播），否则报 `TIKTOK_GECKO_INPUT_ERROR`；完全相同的 (region, AK, channel) 三元组重复也会被拒绝。
- target 数由 `--channel-name` / `--target-region` / `--target-deployment-ak` 决定，resource path 只能按位置配进去、**不会**凭空造出 target：一个 channel 配三个 `--resource-path` 直接报错，要发三片就给三个 `--channel-name`。
- `--resource-path` 要求 `--apply-type` 含 offline，`--online-resource-path` 要求含 online；给了但对应 apply type 没选会直接报错，不会被静默忽略。
- 聚合的前提是同一个产物来源（`--scm-repo` / branch / version 是工单级的）；`--target-os` / `--target-app-version` / `--issue-type` / `--gray-stages` 也是工单级，对所有 target 生效。可以按 target 变化的只有 resource path。产物来源或发布配置不同的发布仍需拆成多张工单。`--from-scm-version` 时不能把 `us-ttp` 与非 US region 混进同一张工单（`--scm-version-field` 是工单级的），CLI 会直接报错。
- 批量时输出里的 `channel_name` 是逗号聚合的展示值（如 `demo-a,demo-b`）；JSON 消费者请读 `channel_names`（去重数组）或 `targets[].channelName`，不要把 `channel_name` 当单个 channel 名解析。可选的 `--channel-meta-id` 仍是单值提示参数，只在单 channel 场景能保证权限申请链接指向正确的 channel。
- `--deployment-type` 是整单的 risk 声明：批量里只要有任一 target 是线上（online）deployment，就必须用 `--deployment-type online`（或省略走 fail-safe HIGH）走二段式确认，不要因为其他 target 是内测就声明 in-house。

### 5. Online Release（HIGH RISK，必须先 `--dry-run` 再 `--yes`）

```bash
# Step 1: 预览请求体，向用户展示
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  --channel-name demo-channel \
  --apply-type offline+online \
  --description 'launch v2' \
  --target-region row \
  --target-deployment-ak <ak> \
  --from-scm-version 1.2.3 --scm-repo my/repo \
  --target-os android --target-app-version 1.2.3 \
  --online-auto-start-release \
  --deployment-type online --dry-run

# Step 2: 用户明确同意后，agent 把同一条命令加 --yes 重新执行
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko release create \
  ... --deployment-type online --yes
# 若希望权限被拒时拿到 channel 申请链接，可额外加 --channel-meta-id <channel_meta_id>
```

### 6. Online Package Rollback（ALWAYS HIGH RISK）

```bash
# Step 1: 预览（推荐传 --channel-meta-id；CLI 不做客户端预检，但后端拒绝时会用它构造申请会员链接 deep-link）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package online rollback \
  --region row \
  --region-ticket-id <region_ticket_id> \
  --package-id <current_pkg_id> \
  --rollback-package-id <target_pkg_id> \
  --channel-meta-id <channel_meta_id> \
  --dry-run

# Step 2: 用户明确同意后，re-run with --yes
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko package online rollback \
  --region row \
  --region-ticket-id <region_ticket_id> \
  --package-id <current_pkg_id> \
  --rollback-package-id <target_pkg_id> \
  --channel-meta-id <channel_meta_id> \
  --yes
```

### 7. Advanced: Ticket approve / reject / cancel / retry / execute

这些命令是已有工单的生命周期动作，不代表独立 Gecko 产品能力。Agent 不应在普通任务里把它们作为首选入口；只有在用户明确要求处理某个 ticket，或上层业务命令已创建 ticket 且需要继续编排时才使用。

```bash
# 查看工单的候选审批人（只读；先确认谁能审批 / 自己是否在列）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket approver list --ticket-id <ticket_id>

# 审批通过（ALWAYS HIGH RISK，必须先 --dry-run 再 --yes；仅审批人可执行，后端裁决）
# 通过只是解锁工单，不会执行——后续仍需 ticket execute 驱动
# --channel-meta-id 可选，与 cancel/retry/execute 相同：仅用于权限被拒时构造申请会员链接，不发给后端
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket approve --ticket-id <ticket_id> --dry-run
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket approve --ticket-id <ticket_id> --channel-meta-id <channel_meta_id> --yes

# 审批拒绝（ALWAYS HIGH RISK，同样二段式；拒绝会阻断提单人的变更，务必与用户确认）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket reject --ticket-id <ticket_id> --dry-run

# 取消（low risk，可直接执行；推荐先 list/get 确认 ticket）
# --channel-meta-id 可选；CLI 不做客户端预检，权限只由后端裁决，传上后只用于在被拒时构造申请会员链接（不传则 apply URL 降级为首页）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket cancel --ticket-id <ticket_id> --channel-meta-id <channel_meta_id>

# 重试（low risk）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket retry --ticket-id <ticket_id> --channel-meta-id <channel_meta_id>

# 在 in-house 工单上执行（low risk）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket execute --ticket-id <ticket_id> --channel-meta-id <channel_meta_id> --deployment-type in-house

# 在 online 工单上执行（HIGH RISK，必须先 --dry-run 再 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket execute --ticket-id <ticket_id> --channel-meta-id <channel_meta_id> --deployment-type online --dry-run
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket execute --ticket-id <ticket_id> --channel-meta-id <channel_meta_id> --deployment-type online --yes

# 可选：限定到特定 region ticket（repeatable）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket cancel \
  --ticket-id <ticket_id> \
  --region-ticket row:rt_abc \
  --region-ticket eu-ttp:rt_def
```

`ticket cancel --region-ticket` 接收 `region:regionTicketId` 格式；不要传 `nodeId`，cancel 后端会忽略它。`ticket retry` / `ticket execute` 仍接收 `region:regionTicketId[:nodeId]`，可重复传多个；不传则后端默认对所有满足条件的 region ticket 生效。

> 对 release、package rollback 和 ticket lifecycle 写命令，`--channel-meta-id` 是可选的权限错误提示信息；它不会触发客户端预检，CLI 仅在后端返回 `CHECK_PERMISSION_ERROR` 时用它构造申请会员链接。`permission apply|grant` 的 `--channel-meta-id` 是业务必填参数；channel create/update 使用各自的资源定位参数。

### 8. Package Diagnose（low risk，agent 可直接执行）

回答「这个 package 为什么没下发到这台设备」。一个诊断任务针对**一个 region 内的一个 package id**；创建后真实设备通过扫描任务二维码（`diagnose get` 输出的 `scanUrl`）主动加入，把控制面 / server / client 三段检查结果异步回报。纯观测——不改任何分发状态，所以 create/finish/stop 全部 low risk，无需 `--yes`（`--dry-run` 仍可预览请求）。

```bash
# 列出诊断任务（按 region-scoped channel id / 包 id / 状态过滤；状态：doing|normal|abnormal|error|stop|timeout）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose list --channel-id <channel_region_id>
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose list --package-id <package_id> --task-status doing

# 创建诊断任务（唯一必填参数是 region-scoped package id）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose create --package-id <package_id>

# 查看详情：任务摘要 + scanUrl（给测试设备扫码加入用）+ 每台设备的检查结果（失败项排前）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose get --task-id <task_id>

# 完成 / 停止
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose finish --task-id <task_id>
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko diagnose stop --task-id <task_id>
```

Diagnose 端点与多数 gecko 接口不同：**不做 region fan-out**，`--region` 只接受一个 region（默认 `row`，`--site boe` 下默认 `boe-i18n`），跨 region 排查请分次执行。

设备检查结果按 `DiagnoseAuditType` 码表输出符号名（`1xxxxx` 控制面 / `2xxxxx` server 分发决策 / `3xxxxx` 端上），失败项常见处置：

| 符号名 | 含义与处置 |
| --- | --- |
| `SERVER_CHANNEL_NO_HIT_GRAY` / `SERVER_PACKAGE_NO_HIT_GRAY` | 未命中灰度：把设备 did 加进发布灰度 did 列表 |
| `SERVER_CHANNEL_NO_HIT_LIBRA` / `SERVER_PACKAGE_NO_HIT_LIBRA` | Libra 规则未命中：Gecko 平台国家要用 `op_region`（不是 `priority_region`），版本要用 `_version_code` |
| `SERVER_CONF_NO_DOWNLOAD` | 控制面配置了禁止下发，检查 channel 配置 |
| `SERVER_OS_VERSION_NO_MATCHED` | os + appversion 不匹配候选包条件 |
| `SERVER_DOWNGRADE_HIT` | 命中降级策略，查降级配置或发起 oncall |
| `CLIENT_APP_VERSION_LOW` / `CLIENT_APP_NOT_RIGHT` | 端上宿主版本过低 / app 不符 |

设备回报是异步的：`diagnose get` 显示 `No devices have reported yet` 时，把 `scanUrl` 渲染成二维码交给测试设备扫码（同一设备短时间内避免重复扫码），稍后再查。

## Permission denial 错误渲染（server-side single source of truth）

CLI 不再做客户端权限预检。所有写命令直接发请求，由后端 `permission_service.checkCurrentUserPermission`（`@CheckPermission` AOP）裁决。被拒时后端返回 `ResponseCodeEnum.CHECK_PERMISSION_ERROR = 3` 的响应，CLI 客户端把它包装成：

```text
tiktok-gecko API error: [3] Permission denied in regions: row. Username: demo.user, Resource: <channelName>, Url: https://...
```

**`src/services/tiktok_gecko/error_render.ts`** 在 service 层 `await` 每个写 API 时统一捕获并增强：

- 客户端优先把后端 code 3，以及 code 30000 且 message 含 `permission denied` / `no permission` / `don't have permission` 的响应归因为 `TIKTOK_GECKO_PERMISSION_DENIED`；service 层保留对旧 `TIKTOK_GECKO_ERROR` + 权限文案的兼容识别。命中后统一附加 `hint`、`details.applyUrl`、`details.channelMetaId`、`details.site`、`details.originalMessage`。
- message 在原文末尾追加单独一行 `Apply membership/role at: <applyUrl>`，避免被单行日志截断。
- 其他错误（输入校验、`SERVICE_ERROR=10000`、HTTP 4xx/5xx 等）原样透传，保持 stack trace 与实例不变。

申请入口 URL 模板（host 按 `--site` 自动切换；缺 `--channel-meta-id` 时降级为 `/gecko/site/v2`）：

```text
# --site i18n-tt（默认）
https://tiktok-gecko-global.tiktok-row.net/gecko/site/v2/channel/<channel_meta_id>?moduleType=memberManagement
# --site boe
https://tiktok-gecko-global-boei18n.bytedance.net/gecko/site/v2/channel/<channel_meta_id>?moduleType=memberManagement
```

### 行为矩阵

| Action 入口                   | `--channel-meta-id` 默认行为                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------- |
| `channel.create`              | 不接收 `--channel-meta-id`（channel 尚未创建）；权限被拒时 apply URL 降级为 `/gecko/site/v2` 首页 |
| `channel.update`              | 以 `--channel-meta-id` 定位目标 channel；权限被拒时 apply URL 降级为 `/gecko/site/v2` 首页        |
| `release.create`              | 可选；缺省时 apply URL 降级为 `/gecko/site/v2` 首页                                               |
| `ticket.cancel/retry/execute` | 可选；ticket payload 本身不带 channel id，不传则 apply URL 降级为首页                             |
| `package.online.rollback`     | 可选；不传则 apply URL 降级为首页                                                                 |

### 设计决策

- **后端 = single source of truth**：CLI 不再额外打一次 `get-permissions-by-meta-resource`。`channel_master / channel_admin / channel_package_write / channel_approver` 等具体权限规则全部由后端 AOP 维护，避免客户端 / 服务端漂移。
- **god / 管理员账号** 走后端 `assignPermission=true` 通配自动放行，与 CLI 无关。
- **dry-run 不会触发权限校验**（不提交写请求、不跑名称/group 预检；channel create/update 缺省 `--x-target-regions` 时会发一次只读 deployment lookup 推导 region，仅此而已）。如果担心 dry-run 看到 OK 但 `--yes` 被后端拒，就先用低风险或 in-house deployment 验证，或直接 `--yes` 并阅读错误。
- **错误结构化字段**（用于 `--json` 模式 / agent 编程消费）：
  ```json
  {
    "code": "TIKTOK_GECKO_PERMISSION_DENIED",
    "hint": "Apply membership / role on TikTok Gecko channel <channel_meta_id>: https://...",
    "details": {
      "applyUrl": "https://tiktok-gecko-global.tiktok-row.net/gecko/site/v2/channel/<channel_meta_id>?moduleType=memberManagement",
      "channelMetaId": "<channel_meta_id>",
      "site": "i18n-tt",
      "originalCode": "TIKTOK_GECKO_PERMISSION_DENIED",
      "originalMessage": "tiktok-gecko API error: [3] Permission denied in regions: row. Username: ..."
    }
  }
  ```

## Stability Rules（MUST follow）

| 命令                        | 默认风险         | 触发因素                                                                                                     |
| --------------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------ |
| `channel create`            | **HIGH（永远）** | 资源创建、deployment-agnostic（无 `deploymentType` 判级）；risk gating 始终 high，必须 `--dry-run` → `--yes` |
| `channel update`            | **HIGH（永远）** | 资源更新、deployment-agnostic（无 `deploymentType` 判级）；risk gating 始终 high，必须 `--dry-run` → `--yes` |
| `channel update-size`       | **HIGH（永远）** | 创建包大小策略变更工单；仅接受 `1..1048575999` bytes，不支持清除覆盖；必须 `--dry-run` → `--yes`             |
| `channel delete`            | **HIGH（永远）** | 创建不可逆的同名 Channel 删除工单；必须 `--dry-run` → `--acknowledge-same-name-scope --yes`                  |
| `channel scm-config create` | **HIGH（永远）** | repo 驱动的分发配置写入、deployment-agnostic；risk gating 始终 high，必须 `--dry-run` → `--yes`              |
| `channel scm-config update` | **HIGH（永远）** | repo 驱动的分发配置更新、deployment-agnostic；risk gating 始终 high，必须 `--dry-run` → `--yes`              |
| `package create`            | low              | high 当 `--deployment-type online`；不传 `--deployment-type` 也 fail-safe 升 high                            |
| `package enable`            | low              | high 当 `--deployment-type online`；不传 `--deployment-type` 也 fail-safe 升 high                            |
| `package disable`           | low              | high 当 `--deployment-type online`；不传 `--deployment-type` 也 fail-safe 升 high                            |
| `release create`            | low              | high 当 `--deployment-type online`；不传 `--deployment-type` 也 fail-safe 升 high                            |
| `package online rollback`   | **HIGH（永远）** | always destructive，影响线上服务                                                                             |
| `permission apply`          | low              | 只提交审批工单、不改线上；可直接执行，支持 `--dry-run` 预览                                                  |
| `permission grant`          | **HIGH（永远）** | 授权给指定 principal，后端校验 assign 权限后可直接生效；必须 `--dry-run` → `--yes`                           |
| `ticket cancel`             | low              | —                                                                                                            |
| `ticket retry`              | low              | —                                                                                                            |
| `ticket execute`            | low              | high 当 `--deployment-type online`；不传 `--deployment-type` 也 fail-safe 升 high                            |

> Risk gating 与 `--site` 维度无关。`--site boe` 上的 high-risk 命令同样需要 `--dry-run` → 用户确认 → `--yes` 二段式；BOE 也是有真实流量的环境，不要因为名字带 BOE 就降级处理。

### `channel create` / `channel update` 安全规则（MUST follow）

1. **ALWAYS HIGH RISK**：channel 是后续 release 发布的承载资源，且没有 `deploymentType` 可供降级，create 与 update 的 risk gating 始终 high。
2. **必须先 `--dry-run`**：把请求体（`targetDeploymentMetaIdList`、base 字段、可选 config/business 等；update 还要确认改了哪些字段）完整展示给用户，等用户明确确认后再加 `--yes`。
3. **不要默认带 `--yes` 静默执行**；非 TTY 缺 `--yes` 会以 `TIKTOK_GECKO_HIGH_RISK_NEED_YES` 拒绝。
4. **update 用 `--channel-meta-id` 定位、按需传字段**：channel 创建时常常信息没填全/填对，update 只传需要修正的字段即可；`name` / `channelType` / `packageType` / `creator` / 角色成员不可通过 update 修改。
5. **`channel create --dry-run` 不提交、不跑后端 precheck**：预览成功不代表真实提交一定通过；缺省 `--x-target-regions` 时它会发一次只读 deployment lookup 用于推导 region 范围（不是写操作）。JSON 输出的 `warnings` 和文本输出的 `WARNING:` 会明确提示这一点。真实提交（`--yes`）前 CLI 会自动跑名称敏感词与 channel-group 交集两项后端预检（见坑 3），把最常见的执行期失败提前到提交前拦截。
6. **真实 create 先生成后续工单**：`--yes` 提交通常不会立即创建 region channel；需先执行返回的 ticket，执行后才会产生 `regionInfo` 等 region 执行记录。

### `channel scm-config create` / `channel scm-config update` 安全规则（MUST follow）

1. **ALWAYS HIGH RISK**：SCM 仓库配置驱动 channel 的资源分发，且没有 `deploymentType` 可供降级，create 与 update 的 risk gating 始终 high，必须 `--dry-run` → 用户确认 → `--yes`。
2. **必须先 `--dry-run`**：把请求体（`targetDeploymentMetaIdList`、`channelMetaId`、`scmRepo`、`data` 下的 offline/online 配置列表；update 还要确认 `data.id` 与改了哪些明细）完整展示给用户，确认后再加 `--yes`。
3. **典型时序**：通常在 `channel create`/`channel update` 的工单执行完成后再配置 SCM 仓库；不要把 channel 写入和 scm-config 写入混在同一次未经确认的批处理里。
4. **配置明细用 JSON 传入**：`--offline-config` / `--online-config`（或 `--*-config-file`）每个元素至少含 `configType` 与 `resourcePath`；create 与 update 都要求至少提供一个配置列表，否则会以 `TIKTOK_GECKO_INPUT_ERROR` 拒绝（避免静默提交空工单）。

### `release create` 安全规则（MUST follow）

1. **online deployment 必须先 `--dry-run`**：把请求体（包括 SCM 源、target 列表、apply-types 等）完整展示给用户，等用户明确确认后才允许加 `--yes` 真正提交。
2. **不要默认带 `--yes` 静默执行**：即使是脚本场景，遇到 high risk 也要让用户先看 dry-run。
3. **不传 `--deployment-type` 会被强制视为 HIGH RISK**（fail-safe）；agent 在调用前应主动从上下文（如 `deployment get` 的 `typeName`）确认目标 deployment 的属性。

### `package create` / `package enable` / `package disable` 安全规则（MUST follow）

1. **online/prod 必须先 `--dry-run`**：创建 / 启用 / 禁用线上资源包会影响发布链路，必须把 URL、headers、body 展示给用户。
2. **in-house / 用户测试场景可直接执行**：显式传 `--deployment-type in-house` 时 risk = low；如果不传 `--deployment-type`，CLI fail-safe 视为 HIGH。
3. **prod package 默认走业务流水线**：只有用户明确要求直接调用 Gecko package API，或场景是用户测试 / 排障 / in-house 验证时，才使用 `package create`。
4. **`package create` body 使用后端原始 schema**：不要臆造默认字段。若字段来自控制台抓包或业务流水线配置，优先用 `--body-file` 保存完整 JSON，再 dry-run 给用户确认。
5. **enable/disable 先确认 package id 类型**：`packageRegionId` 是 region 资源包 id，`packageType` 必须是 `offline_package` 或 `online_package`；不要把 meta package id 当 region package id 使用。

### `permission apply` 安全规则（MUST follow）

0. **先自查再申请**：`permission list --channel-meta-id <channel_meta_id>` 只读列出当前用户在该 channel 各 region 的角色与是否可授权（`assignPermission`）。写命令动手前先自查，已有对应角色就不用提申请单。

```bash
bytedcli --site i18n-tt tiktok-gecko permission list --channel-meta-id <channel_meta_id>
```

1. **low risk，可直接执行**：`tiktok-gecko permission apply` 只创建一张权限审批工单（ticket_type 1，`/gecko/api/permission/create-apply-permission-ticket`），不改线上服务，因此判 low、可直接提交；仍支持 `--dry-run` 预览请求体。
2. **申请人由登录态决定**：后端使用当前 authenticated user 作为申请人，`permission apply` 不再接收 `--username`。
3. **角色取值固定**：`--role` 必须是 `channel_master | channel_admin | channel_package_write | channel_approver`（可重复），非法值会抛带 `hint` 的 `TIKTOK_GECKO_INPUT_ERROR`。
4. **与 permission-denied 闭环**：任一写命令被后端拒（`TIKTOK_GECKO_PERMISSION_DENIED`）后，可直接用 `permission apply --channel-meta-id <id> --deployment-meta-id <deployment_meta_id> --role <role> --x-target-regions <r>` 提单申请，再等审批。

```bash
# 给自己申请某 channel 的 package 写权限（先 dry-run 预览）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko permission apply \
  --channel-meta-id <channel_meta_id> \
  --deployment-meta-id <deployment_meta_id> \
  --role channel_package_write \
  --x-target-regions row \
  --dry-run

# 确认后直接提交（low risk，无需 --yes）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko permission apply \
  --channel-meta-id <channel_meta_id> --deployment-meta-id <deployment_meta_id> --role channel_package_write --x-target-regions row
```

`--deployment-meta-id` 可重复。仅当 `--channel-meta-id` 是数字 channel meta id 时才可省略；CLI 会先读取
`channel get` 的 `relatedDeploymentIds` 自动填充 `formData.target.deployments`。如果 `--channel-meta-id`
不是数字或无法自动解析，会提示显式传 `--deployment-meta-id`。这是 Gecko 后端生成 channel 权限工单
ResourceItems 的必需字段。`--x-target-regions` 只作为请求 header 限定目标区域；它不会写入申请单 body。

### `permission grant` 安全规则（MUST follow）

> **Advanced**：grant 是 channel owner / 管理员给他人授权的入口；为自己申请权限用 `permission apply`。

1. **ALWAYS HIGH RISK**：`tiktok-gecko permission grant` 创建授权工单（ticket_type 2，`/gecko/api/permission/create-grant-permission-ticket`），后端校验当前用户有 `CHANNEL_ASSIGN` 后可直接授权给目标 principal，必须先 `--dry-run` 再 `--yes`。
2. **`--username` 是被授权对象**：grant 不默认当前用户；必须显式传 `--username <sso>`（可重复）。非用户主体可配合 `--principal-type service_account|organization|custom_group`。
3. **target 明确写入 regions + deployments**：grant 要求 `formData.target.regions` 和 `formData.target.deployments`；`--deployment-meta-id` 可重复，省略时 CLI 尝试从 `channel get` 的 `relatedDeploymentIds` 自动填充。`--x-target-regions` 未传时默认使用 `--region` 列表。
4. **角色取值固定**：`--role` 必须是 `channel_master | channel_admin | channel_package_write | channel_approver`（可重复）。

```bash
# 给指定用户授予某 channel 的 package 写权限（先 dry-run）
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko permission grant \
  --channel-meta-id <channel_meta_id> \
  --deployment-meta-id <deployment_meta_id> \
  --role channel_package_write \
  --region row \
  --username <grantee_sso> \
  --dry-run

# 用户确认后执行 high-risk 授权
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko permission grant \
  --channel-meta-id <channel_meta_id> \
  --deployment-meta-id <deployment_meta_id> \
  --role channel_package_write \
  --region row \
  --username <grantee_sso> \
  --yes
```

### `package online rollback` 安全规则（MUST follow）

1. **ALWAYS HIGH RISK**：无论 `--deployment-type` 是什么、无论目标 region 是哪一个，回滚都会立即影响线上服务，必须二次确认。
2. **必须先 `--dry-run`**：把 `region / region-ticket-id / package-id → rollback-package-id` 映射完整展示给用户，等用户确认后再加 `--yes`。
3. **每次只回滚单个 package**：CLI MVP 只支持 `--region` + 一组 `--package-id` / `--rollback-package-id`；不要在一条命令里编排多 region 多 package 的批量回滚——逐个串行执行，每次都重新预览 + 确认。
4. **`--package-id` 与 `--rollback-package-id` 必须不同**：service 层会校验，agent 在生成命令前也应主动校验。
5. **回滚前先用 `package online list` 与 `ticket get` 确认线上包现状与原发布单**：避免用过期 / 模糊匹配的 packageId 触发回滚。

### `ticket execute` 安全规则（MUST follow）

1. **online deployment 工单必须先 `--dry-run`**：执行 online 工单等同于触发线上发布，必须把请求体展示给用户。
2. **不传 `--deployment-type` 时 fail-safe 视为 HIGH**；agent 在调 `ticket execute` 之前应主动用 `ticket get` 或上下文确认目标工单是 in-house 还是 online。
3. **`PASS(3)` 状态可以执行**：控制台执行按钮会在 `PASS(3)` / `PENDING_EXECUTE(4)` 展示；CLI 对 `PASS(3)` 会自动兼容控制台同款 meta ticket execute。带 `--region-ticket` 的 region node 推进仍走 V2，不做该兼容。
4. **`ticket cancel` / `ticket retry` 是 low risk**，但仍建议先用 `ticket get --ticket-id` 确认工单状态、避免误操作。

## `ticket get --watch` — 内置终态轮询（agent 等待优先用这个）

`tiktok-gecko ticket get` 支持 `--watch` 模式：CLI 内部按固定间隔轮询 ticket 详情，直到 ticket 跑到终态（成功 / 失败 / 取消 / 回滚）或超时。Agent / 用户不需要再自己写 sleep loop。

- 需要后端返回 region 子单详情时，给 `ticket get` 追加 `--include-region-ticket-detail=true`；CLI 会透传 `isIncludeRegionTicketDetail=true`。该 flag 对普通查询和 `--watch` 轮询都生效。

```bash
# 默认 5s 间隔、600s 超时
bytedcli --site i18n-tt --auth-site tiktok tiktok-gecko ticket get \
  --ticket-id <ticket_id> --watch

# 自定义节奏（JSON 模式输出 NDJSON 状态变化流 + 最终 envelope）
bytedcli --json --site i18n-tt --auth-site tiktok tiktok-gecko ticket get \
  --ticket-id <ticket_id> --watch --watch-interval 10 --watch-timeout 1800
```

### Flags

| Flag                         | 默认值         | 校验                                                                                             |
| ---------------------------- | -------------- | ------------------------------------------------------------------------------------------------ |
| `--watch`                    | off            | 启用后才会进入 polling；不传 `--watch` 时 `--watch-interval/--watch-timeout` 会被忽略并打印 warn |
| `--watch-interval <seconds>` | 5              | 1 ≤ value ≤ 60 整数                                                                              |
| `--watch-timeout <seconds>`  | 600（10 分钟） | 5 ≤ value ≤ 3600 整数；且必须 > `--watch-interval`                                               |

### Ticket 状态码（与后端 `ticketStatus` 完全对齐）

| Code | Name            | 终态 | 说明                               |
| ---: | --------------- | :--: | ---------------------------------- |
|    0 | INIT            |      | 初始                               |
|    1 | PENDING_AUDIT   |      | 待审                               |
|    2 | REJECT          |  ✓   | 失败终态：审核被拒                 |
|    3 | PASS            |      | 审核通过但还没执行（不算成功终态） |
|    4 | PENDING_EXECUTE |      | 待执行                             |
|    5 | RUNNING         |      | 执行中                             |
|    6 | FAILED          |  ✓   | 失败终态：执行失败                 |
|    7 | CANCELING       |      | 取消中                             |
|    8 | CANCELED        |  ✓   | 失败终态：已取消                   |
|    9 | ROLLING_BACK    |      | 回滚中                             |
|   10 | ROLLBACK        |  ✓   | 失败终态：已回滚                   |
|   11 | SUCCESS         |  ✓   | **成功终态**                       |

> `regionTicketStatus`（每个 region 子工单的状态）是另一套枚举，watch 命令只看 top-level `ticketStatus`，不会混用。

### 退出码

| Exit | 触发条件                                                  |
| ---: | --------------------------------------------------------- |
|    0 | 终态 = SUCCESS(11)                                        |
|    1 | 终态 = REJECT(2) / FAILED(6) / CANCELED(8) / ROLLBACK(10) |
|    2 | 超时未到终态                                              |
|  130 | SIGINT (Ctrl+C)；退出前会打印当前观测到的最后状态         |

### 输出格式

**文本模式**（默认）：每次状态变化打印一行；中间相同状态不重复打印；终态后追加 summary：

```
[2026-05-15T22:50:00.000Z] ticket <ticket_id> status=5 RUNNING (initial observation, elapsed=12ms, poll=1)
[2026-05-15T22:50:15.000Z] ticket <ticket_id> status=11 SUCCESS (transition from RUNNING, elapsed=15012ms, poll=3)
Ticket <ticket_id> finished: SUCCESS (15s, polls=3)
```

**JSON 模式**（`-j` / `--json`）：先输出每条状态变化的 NDJSON 行：

```json
{"kind":"ticket_status_change","ticket_id":"<ticket_id>","status":5,"status_name":"RUNNING","at":"2026-05-15T22:50:00.000Z","poll_count":1}
{"kind":"ticket_status_change","ticket_id":"<ticket_id>","status":11,"status_name":"SUCCESS","at":"2026-05-15T22:50:15.000Z","poll_count":3}
```

最后一行是常规的 `outputResult` envelope（`status: success | error`），`data` 字段包含：

- `action: "ticket_watch"`
- `terminal_status` (number) / `terminal_status_name` (string)
- `outcome`：`success` / `failure` / `timeout` / `aborted`
- `polls`、`elapsed_ms`
- `last_detail`：最后一次 `getTicketDetail` 的完整响应

## release / package / ticket 关系说明

CLI 的 `release scm-repo list` 用于查询 channel 可用的 SCM 发布源仓库；release 工单本质上是 ticket，因此不再单独提供 `release get / release cancel`：

- **查询可用 SCM 仓库** → `tiktok-gecko release scm-repo list --channel-name <channel_name>`
- **取消 release 工单** → `tiktok-gecko ticket cancel --ticket-id <release_ticket_id>`
- **查询 release 工单详情** → `tiktok-gecko ticket get --ticket-id <release_ticket_id>`
- **列出 release 工单** → `tiktok-gecko ticket list --type package-release,package-release-offline,package-release-online,package-release-customized`（可逗号分隔多个类型）。

  `--type` 取后端 `TicketType` 成员名的 kebab 形式（大小写与下划线都会被归一，`PACKAGE_RELEASE` 与 `package-release` 等价），不接受数值码。发布相关的成员：

  | 语义值 | 含义 |
  | --- | --- |
  | `package-release` | 发布单**同时含在线 + 离线**时用的类型，**不是** offline/online 的父集 |
  | `package-release-offline` | 仅离线发布 |
  | `package-release-online` | 仅在线发布 |
  | `package-release-customized` | 仅用于审批的发布单 |
  | `package-release-rollback-online` | 在线包回滚发布 |
  | `package-release-v2` / `package-release-v2-offline` / `package-release-v2-online` | 发布 V2 的三种形态 |
  | `package-create` / `package-enable` / `package-disable` | 建包 / 启用 / 停用 |

  **要查「全部发布单」必须把上面的发布类型一起传**，只传 `package-release` 会漏掉绝大多数单子。非发布类工单同样用成员名，例如 `channel-create` / `channel-update` / `channel-scm-config-create` / `authority-apply`。完整 70 个取值不在文档里维护（会与代码漂移）：传一个非法值，报错的 `details.allowed_values` 会返回全集，`-j` 模式下可直接读取，例如 `bytedcli --site i18n-tt -j tiktok-gecko ticket list --type invalid-type-probe | jq -r '.error.details.allowed_values[]'`。
- **重试 / 执行 release 工单** → `tiktok-gecko ticket retry/execute --ticket-id <release_ticket_id>`（注意 risk gating）
- **重新提交 release** → `tiktok-gecko release create`（不要尝试用 ticket retry 来"重发"失败的 release，retry 仅在工单内重试节点逻辑）

Package 与 release 是上下游关系：

- `PACKAGE_CREATE`：创建资源包 / 产物入库，对应 `tiktok-gecko package create --type offline|online`。
- `PACKAGE_ENABLE` / `PACKAGE_DISABLE`：启用 / 禁用已有资源包，对应 `tiktok-gecko package enable|disable`。
- `PACKAGE_RELEASE*`：把已有资源包发布到 offline / online / offline+online 分发链路。
- `release create` 不能被当成完整 package 发布链路；它只表达 release 阶段。若没有资源包，先走 `package create` 或业务流水线。prod package 发布链路通常应由业务流水线负责。

## 产品反馈与人工支持

先排查参数、凭据、网络和外部业务问题。确认产品问题后，由当前任务唯一责任方整理摘要并委托 CLI 提交，不另行征求确认。默认由直接承接用户请求的 Agent 负责；子上下文只返回候选，明确接收责任后才提交。转交时移交已有 Feedback ID，原责任方停止提交。

每次描述一个问题：组件及版本（未知则注明）、目标、实际和期望表现。摘要去除首尾空白后须为 1–1000 Unicode code points，不截断；排除凭据、完整日志、业务响应、截图及文件正文。摘要会出现在进程命令行中。

```bash
bytedcli tiktok-gecko feedback submit --help
bytedcli tiktok-gecko feedback submit --summary "组件：TikTok Gecko，版本未知。目标：查询资源。实际：命令失败。期望：返回资源。"
bytedcli tiktok-gecko oncall
```

成功后告知并保留 Feedback ID。失败后告知用户并继续原任务，不自动重试或触发 Oncall。旧版缺少命令时，说明尚未提交，按上文方式升级并重新检查命令。

两个命令不依赖业务登录、App 选择或业务站点配置。仅在用户明确要求人工支持时调用 Oncall，返回链接和模板；只填入用户明确选择披露的内容，不自动打开链接、入群或发消息。

## Agent-facing 协议

> 这一节面向 Claude Code、Cursor、其他 LLM agent。在自动化场景下严格按以下流程使用本 skill。

1. **低风险命令**（risk = low）
   - 对应：`*list / *get` 等只读命令、`package create|enable|disable --deployment-type in-house`、`release create --deployment-type in-house`、`permission apply`、`ticket cancel`、`ticket retry`、`ticket execute --deployment-type in-house`
   - Agent 行为：可直接调用 CLI 执行，输出结果给用户。

2. **高风险命令**（risk = high）
   - 对应：`channel create` / `channel update` / `channel update-size` / `channel delete`（始终高风险）、`channel scm-config create` / `channel scm-config update`（始终高风险）、`package create|enable|disable --deployment-type online`（或缺省 `--deployment-type`）、`release create --deployment-type online`（或缺省 `--deployment-type`）、`package online rollback`（始终高风险）、`permission grant`（始终高风险）、`ticket execute --deployment-type online`（或缺省 `--deployment-type`）
   - Agent 行为：
     1. **MUST 先用 `--dry-run` 调一次**，从输出里拿到完整的 request body 与 risk 等级。
     2. **把 dry-run preview 完整展示给用户**（包括 URL、headers、body、影响范围）。
     3. **等用户在对话里明确同意**（"go" / "确认" / "yes" 等）。
     4. **agent 把同一条命令去掉 `--dry-run`、加上 `--yes` 重新执行**，并把响应交回用户。
   - **不要在用户没明确同意时自动加 `--yes`**；不要把高风险命令藏在脚本/批处理里悄悄跑。

3. **如何判断目标是 online 还是 in-house**
   - `tiktok-gecko deployment get --deployment-meta-id <id>` 的 `Type` 字段、或 `ticket get --ticket-id <id>` 详情里的 `deploymentType`：`1 = online`、`2 = in-house`。
   - 把判断结果作为 `--deployment-type` 参数显式传入；不要省略它。

4. **等待工单跑完**
   - 触发 `package create|enable|disable` / `release create` / `package online rollback` / `ticket execute|retry|cancel` 之后想等结果时，**MUST** 用 `tiktok-gecko ticket get --ticket-id <id> --watch`，**不要自己写 sleep loop**。
   - 退出码已经按"成功 0 / 失败 1 / 超时 2 / 中断 130"约定好，shell / agent / CI 都能直接消费。
   - 在 `--json` 模式下读 NDJSON 状态变化行可以做实时反馈，最后一行 envelope 给最终判定。

5. **ticket 动作降级原则**
   - `ticket execute/cancel/retry` 是 API 层工单生命周期动作，不是产品级主场景。不要把它们单独推荐给普通用户。
   - 优先使用上层业务命令表达用户意图；只有用户明确给出 ticket 操作诉求，或上层命令需要继续编排时才调用。
   - 统计 skill 使用场景或 UV 天花板时，不把 `ticket execute/cancel/retry` 作为独立场景计入。

## 常用操作指南

1. **先拿列表再查详情**：先用 `list` 命令确认资源 ID，再用 `get` 命令拉详细信息，避免手填错误 ID。
   - `channel get --channel-meta-id` 需要传 **channel meta id**（例如 `channel list` 返回里的 `metaIdList`），不是 deployment 下的 channel region id。
2. **先按条件缩小范围**：`channel list` 可用 `--region` / `--name`；`ticket list` 可用 `--creator` / `--reviewer` / `--status` / `--type`。`--status` 取语义值（`init` / `pending-audit` / `reject` / `pass` / `pending-execute` / `running` / `failed` / `canceling` / `canceled` / `rolling-back` / `rollback` / `success`），`--type` 取 `TicketType` 成员名的 kebab 形式（见上文发布工单一节的对照表），两者都支持逗号分隔、都不接受后端数值码；`--reviewer` 按审批人（approver）过滤。`ticket list` / `ticket get` 输出的 Type、Status 列就是这些成员名，可以直接抄回过滤条件。
   - 查询某个 channel 的资源包时，优先使用 `channel package list`（底层接口为 `channel/package-meta/list`）。
   - 查询某个 channel 的线上包（已下发到 CDN 的包）时使用 `package online list`。
3. **排查部署关联关系**：先 `deployment get` 看部署基本信息，再用 `deployment channel list` 看挂载 Channel。
4. **结构化输出给自动化流程**：在全局参数添加 `--json`，例如 `bytedcli --json --site i18n-tt tiktok-gecko app list`。

## Notes

- Flag 硬切（无兼容别名）：不再接受 `--channel-id`（改用 `--channel-meta-id` / `--channel-region-id`）、`--deployment-id` / `--target-deployment-meta-id`（统一 `--deployment-meta-id`）、channel create 的 `--package-type`（改用 `--channel-package-type`）、package enable/disable 的 `--package-type`（改用 `--resource-package-type`）、`--size-bytes`（统一 `--pkg-max-size`）。
- Deployment access key 两种 flag 名语义相同：只读 `deployment get/region-channel list` 用 `--access-key`；`release create` 用 `--target-deployment-ak`。值都来自 deployment 的 access key。
- `channel package list` 的 Meta Package ID 与 Region Package IDs 是两套 id；只有后者（及 `package online list` 的 Package ID）可喂给 `channel package get --package-id`。
- `tiktok-gecko` 当前覆盖只读查询 + 产品级写操作（channel create / channel update / channel scm-config create|update / package create / package enable|disable / release create / package online rollback / permission apply|grant）。`ticket cancel/retry/execute` 已暴露但属于 advanced troubleshooting / workflow orchestration，不是主入口。
- 当前未覆盖的常见工单能力包括：customized release 专门入口、release template 创建/更新/删除、channel prefix、清除 channel size override、SCM config delete、channel group/change/clean/push、host app/settings/resource-loader、GeckoNG 相关工单等。
- `release create` 只能覆盖 release 阶段，不能作为完整 package 发布链路。`package create` 已暴露底层 package 创建 API，但 prod package 发布通常走业务特定流水线；skill 更适合用户测试、内测、排障和已有 package/SCM source 的辅助发布。
- `tiktok-gecko` 支持 `--site i18n-tt`（TikTok ROW prod，TikTok SSO 默认）与 `--site boe`（BOE i18n 分区，bytedance SSO 默认）。也可通过 `BYTEDCLI_CLOUD_SITE` 环境变量设置。两站点的 base URL、JWT 颁发 host 与 permission URL 都按 site 自动切换；显式传入与该 site 不匹配的 `--auth-site`（例如 `--site i18n-tt --auth-site bytedance`）会被入口校验直接拒绝。
- BOE 不需要手动传 `--vregion`：`--site boe` 时 CLI 内部会按隐式 `boei18n` 分区选择 ByteDance SSO，并把 JWT 取自 `cloud-boei18n.bytedance.net`；不要使用 BOE-CN 的 `cloud-boe.bytedance.net`。
- `tiktok-gecko ticket list` 的时间筛选参数使用 epoch 毫秒：`--create-start-time` / `--create-end-time`。
- `deployment channel list` 默认 `--type all`，与控制台部署详情页默认筛选一致。
- 资源包环境可通过 `deploymentName` 快速判断：`online_deployment` 通常为线上包，`in_house_deployment` 通常为测试包。
- `package online list` 只接受 `--channel-region-id`（从 `channel get` 的 `regionDetails.items[].regionId` 获取），不接受 channel meta id；`--issue-status` 支持语义值 `unpublished | published | abandon | abnormal`（数字 0-3 兼容）。
- 写操作的 `--deployment-type` 参数 **仅用于 CLI 端 risk gating**，不会转发到后端；后端会从 target 里自行推导。
- 写操作的 `--x-target-regions` 转发为 `x-target-regions` 请求头（与控制台调试一致）。
- 高风险命令在非 TTY 环境下若没有 `--yes`，CLI 会以结构化错误码 `TIKTOK_GECKO_HIGH_RISK_NEED_YES` 拒绝执行；TTY 下会弹 `Proceed with HIGH RISK ... [y/N]` 交互 prompt。
