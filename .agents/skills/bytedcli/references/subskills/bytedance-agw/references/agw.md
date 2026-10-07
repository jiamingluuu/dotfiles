# AGW (API Gateway)

## 站点与路由

AGW 不使用 `--site boe`。查看或发布 BOE 环境/配置时使用线上站点，例如：

```bash
bytedcli --site cn agw config get --service-id <id> --boe
bytedcli --site cn agw publish execute --target boe-feature --service-id <id> --version <version> --env <boe_env>
```

AGW 特定站点路由：

| 参数                                | 请求 host                          |
| ----------------------------------- | ---------------------------------- |
| `--site cn --vregion sinf`          | `https://cloud.sinf.net`           |
| `--site i18n-bd --vregion sinfi18n` | `https://cloud-i18n.sinf.net`      |
| `--site us-ttp`                     | `https://cloud.tiktok-us.net`      |
| `--site eu-ttp`                     | `https://bc-iedt-gw.tiktok-eu.net` |

## 产品管理

```bash
# 收藏产品列表
bytedcli agw product list [--page <n>] [--page-size <n>]

# 搜索产品
bytedcli agw product search --keyword <keyword> [--page <n>] [--page-size <n>]

# 产品详情
bytedcli agw product get --product <product>
```

| 命令             | 参数          | 说明                |
| ---------------- | ------------- | ------------------- |
| `product list`   | `--page`      | 页码（默认 1）      |
|                  | `--page-size` | 每页条数（默认 20） |
| `product search` | `--keyword`   | 搜索关键词（必填）  |
|                  | `--page`      | 页码（默认 1）      |
|                  | `--page-size` | 每页条数（默认 20） |
| `product get`    | `--product`   | 产品名称（必填）    |

## 服务管理

```bash
# 模糊搜索服务（按 PSM / 路径关键词）
bytedcli agw service search --keyword <keyword>

# 获取服务详情
bytedcli agw service get --service-id <id>
bytedcli agw service get --product <product> --psm <psm>

# 获取服务列表
bytedcli agw service list [--product <product>] [--psm <psm>] [--page <n>] [--page-size <n>] [--boe]

# 判断 PSM 是否已接入 AGW
bytedcli agw service status --psm <psm> [--need-deprecated]

# 新建服务（大请求体）
bytedcli agw service create --body-file service.json

# 添加生效地域
bytedcli agw service active-area create [--product <product>] --psm <psm> --region <region> --cluster <cluster>
```

| 命令                         | 参数                                            | 说明                                     |
| ---------------------------- | ----------------------------------------------- | ---------------------------------------- |
| `service search`             | `--keyword`                                     | 搜索关键词，支持 PSM、路径等（必填）     |
| `service get`                | `--service-id`                                  | AGW 服务 ID；与 `--product --psm` 二选一 |
|                              | `--product`, `--psm`                            | 产品与服务 PSM；与 `--service-id` 二选一 |
| `service list`               | `--product`, `--psm`                            | 按产品或 PSM 过滤                        |
|                              | `--page`, `--page-size`                         | 分页参数                                 |
|                              | `--boe`                                         | 查询 BOE 版本视角                        |
| `service status`             | `--psm`                                         | 服务 PSM（必填）                         |
|                              | `--need-deprecated`                             | 包含已废弃服务                           |
| `service create`             | `--body-json`, `--body-file`                    | 新建服务请求 JSON，字段以 AGW 接口为准   |
| `service active-area create` | `[--product]`, `--psm`, `--region`, `--cluster` | 添加生效地域参数，product 可选           |

## 配置管理

```bash
# 配置版本列表
bytedcli agw config list --service-id <id> [--page <n>] [--page-size <n>] [--minimal]

# 获取线上/指定版本/泳道配置；不传 --version 时默认获取当前线上配置，可用 --yaml 在本地把响应渲染为 YAML
bytedcli agw config get --service-id <id> [--version <version>] [--boe] [--env <env>] [--yaml]

# 创建新配置版本（大请求体）
bytedcli agw config create --body-file config.json [--description <text>]

# BFFv2 场景：复用指定配置版本的 backends 配置
bytedcli agw config create --body-file config-without-backends.json --bff-backends-from-cfg-ver <base-version>
```

`config get` 不传 `--version` 时默认获取当前线上配置；传 `--boe` 获取 BOE 版本视角，传 `--env <env>` 获取指定泳道配置。

`config create --description` 会覆盖请求体中的配置描述。`config create` 的请求体是完整配置。BFFv2 配置里的 `bff_v2_backends_config` 可能很大：如果本次变更不涉及上游服务 IDL 版本更新，可以使用 `--bff-backends-from-cfg-ver <base-version>` 复用指定配置版本里的 `bff_v2_backends_config`，请求体中可省略该字段；如果更新了上游 IDL，必须传最新 `bff_v2_backends_config`。

## 环境管理

```bash
# 查询登记的多环境
bytedcli agw env list --service-id <id> [--page <n>] [--page-size <n>]
bytedcli agw env list --psm <psm> [--page <n>] [--page-size <n>]

# 注册多环境
bytedcli agw env create --service-id <id> --type <type> --name <name> [--cluster <cluster>...] [--expire-days <days>]
bytedcli agw env create --psm <psm> --type <type> --name <name> [--cluster <cluster>...]

# 注册多环境并启用自动部署
bytedcli agw env create --service-id <id> --type <type> --name <name> --auto-deploy --branch <branch>

# 部署已登记多环境（仅适用于中心式网关架构服务）
bytedcli agw env deploy --service-id <id> --type <type> --name <name> [--cluster <cluster>...]
```

| 参数                        | 说明                                                   |
| --------------------------- | ------------------------------------------------------ |
| `--service-id` / `--psm`    | 服务 ID 或 PSM；注册/查询时二选一                      |
| `--type`                    | 环境类型，如 `ppe`、`boe_feature`                      |
| `--name`                    | 环境名，如 `ppe_demo`、`boe_demo`                      |
| `--cluster`                 | AGW 集群名，可重复；中心化服务常用，分布式服务通常留空 |
| `--expire-days`             | 过期天数                                               |
| `--auto-deploy`, `--branch` | 启用自动部署并绑定 IDL 分支                            |

`env deploy` 只适用于中心式网关架构服务；分布式 sidecar 网关服务不适用，后端通常返回 `deployment by platform does not support sidecar arch`。

## 发布管理

```bash
# 一键发布（不支持线上发布接口）
bytedcli agw publish execute --target boe --service-id <id> --version <version> [--description <text>]
bytedcli agw publish execute --target ppe --service-id <id> --version <version> --env <ppe_env> [--description <text>]
bytedcli agw publish execute --target boe-feature --service-id <id> --version <version> --env <boe_env> [--description <text>]

# 创建发布单
bytedcli agw publish order create --target online --service-id <id> --version <version> [--description <text>]
bytedcli agw publish order create --target boe --service-id <id> --version <version> [--description <text>]
bytedcli agw publish order create --target ppe --service-id <id> --version <version> --env <ppe_env> [--description <text>]
bytedcli agw publish order create --target boe-feature --service-id <id> --version <version> --env <boe_env> [--description <text>]

# 回滚：创建指向历史版本的发布单
bytedcli agw publish order create --rollback --target online --service-id <id> --version <previous_version> [--description <text>]
bytedcli agw publish order create --rollback --target ppe --service-id <id> --version <previous_version> --env <ppe_env>

# 发布单详情 / 发布单列表
bytedcli agw publish order get --publish-id <publish-id>
bytedcli agw publish order list --service-id <id> [--page <n>] [--page-size <n>] [--env-type <type>]
```

`execute` 表示一键执行发布，CLI 内部使用 `publish_mode=2`；`order create` 表示创建发布单，CLI 内部使用 `publish_mode=1` 并自动填充发布单详情页 URL。两条命令都必须显式传 `--target`，避免写操作落到隐式目标。`agw idl update --publish-mode auto` 保持既有语义：自动创建发布工单并按可用结果轮询；`manual` 仅更新 IDL、不发布。不要直接让用户传后端数字编码。线上发布接口只支持创建发布工单流水线，CLI 不暴露 `publish_mode`、`force`、`skip_boe` 参数。

## BFFv2

```bash
# 获取服务 Extra / BFFv2 模板
bytedcli agw bffv2 template get --service-id <id>
bytedcli agw bffv2 template get --product <product> --psm <psm>

# 设置 / 查询 BFFv2 DSL 模板
bytedcli agw bffv2 template update --body-file templates.json
bytedcli agw bffv2 template search --psm <psm>

# 查看 / 解释配置版本中的 BFFv2 路由
bytedcli agw bffv2 route list --service-id <id> --version <version>
bytedcli agw bffv2 route list --service-id <id> --version <version> --group <group-name>
bytedcli agw bffv2 route get --service-id <id> --version <version> --bff-key <key>
bytedcli agw bffv2 route get --explain --service-id <id> --version <version> --bff-key <key>

# 查看 / 创建 / 修改 BFF 路由分组（生成本地完整配置草案，不提交不发布）
bytedcli agw bffv2 group list --service-id <id> --version <version>
bytedcli agw bffv2 group create --service-id <id> --base-version <version> --group <group-name> --output-file group-config.json
bytedcli agw bffv2 group update --service-id <id> --base-version <version> --group <group-name> --bff-key <key> --output-file group-update-config.json
bytedcli agw bffv2 group update --service-id <id> --base-version <version> --default-group --route GET:/demo --output-file group-default-config.json

# 渲染请求解析 IDL / DSL（推荐 option 化；复杂场景仍支持 --body-file）
bytedcli agw bffv2 request-idl create --service-id <id> --version <version> --template <name> --backend-api thrift:<psm>:<method> --http-method GET
bytedcli agw bffv2 dsl create --service-id <id> --version <version> --template <name> --backend-api thrift:<psm>:<method> --req-idl-file http-input.thrift --purpose create

# 将 DSL 拆成可编辑 TS workspace；只编辑 HANDLE_DSL 区域，再 pack 回 BFFV2RouteConfig
bytedcli agw bffv2 dsl-workspace import --bff-config-file render-dsl.json --output-dir ./bffv2-dsl
bytedcli agw bffv2 dsl-workspace export --workspace ./bffv2-dsl --output-file reviewed-bff-config.json

# 生成新增 BFFv2 路由的本地完整配置草案，不提交不发布
bytedcli agw bffv2 route create --service-id <id> --base-version <version> --path /demo --method GET --bff-config-file reviewed-bff-config.json --output-file new-config.json --copy-route-from <existing-key> --bff-backends-from-cfg-ver <version> [--group <group-name> --create-group]

# 批量生成新增 BFFv2 路由的本地完整配置草案，不提交不发布
bytedcli agw bffv2 batch-route create --service-id <id> --base-version <version> --template <name> --route example.backend.service:GET:/demo:GetItem --route example.other.backend:POST:/demo2:CreateItem --group <group-name> --create-group --output-file batch-route-config.json
bytedcli agw config create --body-file batch-route-config.json --description "batch add BFFv2 routes"

# 上游 IDL 更新后批量刷新 BFFv2 DSL 类型定义
bytedcli agw bffv2 backend-idl update --service-id <id> --version <version> --backend-idl thrift:<psm>:<version> [--backend-idl http:<psm>:<version>] --description <text> --output-file updated-config.json

# 生成客户端 IDL 并导出到 BAM
bytedcli agw bffv2 client-idl export --target bam --service-id <id> --version <version> [--branch <branch>]
```

BFFv2 配置要点：

- `routes[].bff_key` 与 `bff_v2_config` 中的 `bff_key` 对应；`routes[].bff_type=2` 表示 BFFv2。
- `bff_v2_config` 保存每条 BFFv2 路由的模板名、请求解析 IDL、编排 DSL、响应组装 DSL 等。请求解析 IDL 配置与 DSL 类型定义强耦合，任何 IDL 配置变更后都必须重新执行 `dsl create`，只更新 `type_dsl`，`handle_dsl` 不受影响。
- `bff_v2_backends_config` 保存上游服务 IDL 元信息，体积可能很大；不更新上游 IDL 时优先用 `config create --bff-backends-from-cfg-ver` 复用历史版本。
- `bff_group_config.groups[].bff_keys` 管理 BFF 路由分组；`route list` 可用 `--group` 过滤，新增 route plan 可用 `--group <name>` 指定分组，缺失分组时需显式加 `--create-group`。
- `dsl create` 返回 `BFFV2RouteConfig`，只取需要的 DSL 内容填回配置；当 `only_render_type_dsl=true` 时，只使用返回的 `type_dsl`，不要覆盖已有 `handle_dsl`。请求解析 IDL 配置发生任何变化后，必须基于最新 IDL 重新执行 `dsl create`，只更新 `type_dsl`，不能覆盖或改写既有 `handle_dsl`。
- `dsl-workspace import` 会把 `type_dsl` 和 `handle_dsl` 合并成 `*.dsl.ts`；只编辑 `HANDLE_DSL` 区域，`TYPE_DSL` 区域带 hash 校验，修改后 `dsl-workspace export` 会失败。
- `route create` 只生成本地 config plan 文件，真正提交仍需显式执行 `agw config create`；无上游 IDL 变化时配合 `--bff-backends-from-cfg-ver` 复用历史 backend 配置。若未显式传 `--output-file`，默认应使用当前工作目录下带 service/version/timestamp 的可预测文件名，避免覆盖。需要把新 route 放入分组时传 `--group <name>`；目标分组不存在时加 `--create-group`。
- `group create` 和 `group update` 只生成本地 config plan，用于创建分组或移动已有 BFFv2 route；移动到默认分组使用 `--default-group`。
- `batch-route create` 当前仅支持 thrift backend PSM 批量新增路由，暂不支持 http / tcc / rpc-http backend；`--route` 格式是 `<thrift-backend-psm>:<METHOD>:<PATH>:<RPC_METHOD>`；`--routes-file` 格式是 `{ [thriftBackendPsm]: [{ http_method, path, rpc_method, group_name? }] }`。可用全局 `--group <name>` 给本次批量新增 route 指定同一分组，单条 route 的 `group_name` 会覆盖全局分组。
- `batch-route create` 只生成本地 config plan，不提交不发布；后续用 `agw config create --body-file <plan>` 显式提交，不要给该流程追加 `--bff-backends-from-cfg-ver`。
- 如果批量 route 的 thrift backend PSM 或 RPC method 不在当前配置的 BFFv2 thrift backend IDL 中，先用 `backend-idl update --backend-idl thrift:<psm>:<version>` 更新后端 IDL 并提交中间配置，再基于 `IDL_UPDATED_VERSION` 运行 `batch-route create`。
- `backend-idl update` 用于上游 IDL 更新后批量刷新类型定义，支持 repeatable `--backend-idl <protocol>:<psm>:<version>` 一次更新多个后端；如果目标版本低于当前版本会阻断，确认降级才传 `--allow-downgrade`；不应改写用户维护的 `HttpInput` / `handle` 逻辑。

## 协议转换服务 IDL 更新与发布

`agw idl update` 面向 AGW 协议转换服务的主 IDL 更新；BFF2.0/BFFv2 上游后端 IDL 更新请使用 `agw bffv2 backend-idl update`。

```bash
bytedcli agw idl update --service-id <id> --env <env> [options]
```

| 参数                 | 说明                                                       |
| -------------------- | ---------------------------------------------------------- |
| `--service-id`       | AGW 服务 ID（必填）                                        |
| `--env`              | AGW 环境名，如 `boe_default`、`ppe_xxx`（必填）            |
| `--bam-psm`          | 覆盖 BAM PSM（默认从 AGW 配置推断）                        |
| `--bam-version`      | 目标 BAM IDL 版本（默认最新）                              |
| `--branch`           | 目标 git 分支（选取该分支上最新版本）                      |
| `--description`      | 配置描述（默认 "bytedcli update idl"）                     |
| `--publish-mode`     | 发布模式：`auto`（默认，创建发布工单）/ `manual`（不发布） |
| `--poll-interval-ms` | 自动发布后轮询间隔（默认 2000）                            |
| `--max-wait-ms`      | 自动发布后最大等待时间（默认 30000）                       |

## 协议转换服务 IDL + 路由更新与发布

在更新协议转换服务主 IDL 的同时，自动解析目标 IDL 中的 Thrift 路由注解（`api.get`、`api.post`、`api.put`、`api.delete`、`api.patch`），将缺失的路由补齐到 AGW 配置的 `routes` 数组中（只增不删）。

```bash
bytedcli agw idl update --service-id <id> --env <env> --with-router [options]
```

与不带 `--with-router` 的区别：`--with-router` 会额外解析 IDL 中的路由注解并将新路由追加到配置中；已有路由不会被删除或修改。
