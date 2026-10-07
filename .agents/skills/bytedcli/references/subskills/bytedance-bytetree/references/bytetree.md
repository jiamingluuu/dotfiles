# ByteTree 命令参考

以下示例统一使用 `bytedcli bytetree`；全局参数放在 Domain 前面。

## 查询服务树节点

### 搜索节点

```bash
bytedcli bytetree search --keyword "demo-service-tree"
bytedcli --json bytetree search --keyword "sample-node" --page-size 50
```

- 返回匹配节点的 ID、类型、名称、路径和 Owner。
- `--keyword` 是必填的模糊搜索文本。
- 适合先定位节点，再继续下钻。

### 单个查询

```bash
bytedcli bytetree get --node-id 1234567
bytedcli --json bytetree get --node-id 1234567
```

返回节点基础信息、负责人、标签、描述、overview URL 和 `resources`。资源中常见字段：

人类可读模式使用与 bytedcli 一致的 `Field / Value` 详情表；脚本和 Agent 应继续使用 `--json` 消费稳定 Envelope。

JSON 的 Envelope 与文档列出的字段保持稳定。服务端在节点、资源、Provider 或平台对象中返回额外字段时，CLI 会原样保留这些字段；这些未文档化的扩展字段可能随上游变化，自动化脚本不应把它们当作稳定契约。

- `provider`：资源提供方，例如 `tce`、`tcc`、`rds`
- `resource_type`：资源类型
- `resource_id`：资源唯一标识
- `partition`、`env`、`region`：资源环境
- `link.view`：控制台查看地址

### 批量查询

```bash
bytedcli bytetree batch-get --node-id 1234567,2345678
bytedcli --json bytetree batch-get --leaf-node-name arch.bytetree.gateway --node-path '|业务线|服务'
```

- `get` 用于按一个节点 ID 查询；`batch-get` 用于一次提交一组精确选择条件。
- `--node-id`、`--leaf-node-name`、`--node-path` 至少提供一类，均可重复或使用逗号分隔。
- 三类选择条件按 OR 组合，总数最多 10000。
- 该命令调用 `POST /service_meta/api/v4/index/nodes/batch`，不会用逐个 GET 模拟批量查询。

## 查看节点资源

```bash
bytedcli bytetree resources --node-id 1234567 --provider codebase
bytedcli --json bytetree resources --node-id 1234567 --provider tce --offset 20 --page-size 50
```

- 支持通过 `--provider` 精确筛选资源来源。
- 支持 `--offset` 和 `--page-size`。
- 适合查询不会直接出现在子节点列表中的挂载资源。

## 查看子节点

```bash
bytedcli bytetree children --node-id 1234567
bytedcli --json bytetree children --node-id 1234567 --type service,psm --page-size 100
```

- 支持重复传 `--type` 或使用逗号分隔值。
- 支持 `--page`、`--page-size` 和 `--max-level`。

## 查看父链

```bash
bytedcli bytetree parents --node-id 1234567
bytedcli --json bytetree parents --node-id 1234567
```

返回从上层目录到当前节点的完整父链，适合确认归属目录和挂载位置。

## 查看和调整 Owner

`owner` 是 bytedcli 宿主保留的原生命令组，不由 Companion 提供：

```bash
bytedcli bytetree owner list --node-id 1234567
bytedcli --json --site i18n-tt bytetree owner list --node-id 1234567 --role owner.i18n

# 写操作默认只预览 payload
bytedcli bytetree owner add --node-id 1234567 --user demo.owner
bytedcli bytetree owner delete --node-id 1234567 --user old.owner
bytedcli bytetree owner set --node-id 1234567 --user new.owner

# 确认预览后再真实执行
bytedcli --json bytetree owner add --node-id 1234567 --user demo.owner --yes
```

- `owner list` 返回 `person_account`、`service_account` 和角色摘要。
- `owner add/delete/set` 的 `--user` 可重复传入或使用逗号分隔；`--user-type` 支持 `person_account` 和 `service_account`。
- 写操作默认 dry-run；只有显式 `--yes` 才调用 IAM 写接口。
- 默认角色按站点推断：`cn`、`boe`、`eu-ttp` 使用 `owner`，i18n 站点使用 `owner.i18n`，`us-ttp` 使用 `owner.tx`；也可显式传 `--role`。
- `set` 只替换当前 `--user-type`，并保留另一类账号成员。
- 默认抑制 IAM 授权通知；只有明确需要通知时才使用 `--enable-notice`。

## 管理当前用户订阅

```bash
# 读取当前订阅
bytedcli bytetree subscription list

# 默认只预览，不写入
bytedcli bytetree subscription create --node-id 1234567,2345678
bytedcli bytetree subscription delete --node-id 1234567

# 核对后执行并回读
bytedcli bytetree subscription create --node-id 1234567,2345678 --yes
bytedcli bytetree subscription delete --node-id 1234567 --yes
```

- `create` 支持一次订阅多个节点；`delete` 每次只接受一个节点 ID，与服务端接口约束一致。
- 不带 `--yes` 时 `dry_run=true`、`applied=false`，不会发送网络请求。
- 带 `--yes` 时执行一次写请求，然后 GET 当前订阅作为 `readback`。

## 查询 Provider

```bash
bytedcli bytetree provider list --page 1 --page-size 100
bytedcli bytetree provider list --mine --sort-key name --sort-order asc
bytedcli bytetree provider search --name tce
bytedcli bytetree provider search --account service_tree
bytedcli bytetree provider get --name tce
bytedcli bytetree provider platform list
bytedcli bytetree provider get-by-cloud-product --cloud-product-id tce
bytedcli bytetree provider resource list --name tce
bytedcli bytetree provider resource list --name tce --latest-3-days=false --page-size 500
```

- `provider search` 的 `--name` 与 `--account` 至少提供一个；两个都提供时同时过滤。
- `provider list --mine` 只返回当前用户拥有的 Provider；默认返回全部可见 Provider。
- `--sort-key` 支持 `name`、`created-at`，`--sort-order` 支持 `asc`、`desc`。
- `provider resource list` 默认只查询最近 3 天创建的资源；用 `--latest-3-days=false` 查询全部。
- Provider 资源分页支持 `--page`、`--page-size` 与游标 `--offset`；非零 offset 优先于页码。

命令与接口对应关系：

- `provider list`：分页列出 Provider，可按名称、服务账号、本人拥有范围和排序条件过滤；对应 `GET /service_meta/api/v4/providers`。
- `provider search`：按 Provider 名称或服务账号模糊搜索；对应 `GET /service_meta/api/v4/providers/search`。
- `provider get`：按名称读取单个 Provider 的详情；对应 `GET /service_meta/api/v4/providers/{provider_name}`。
- `provider platform list`：列出可创建 Provider 的平台及入口链接；对应 `GET /service_meta/api/v4/providers/platform`。
- `provider get-by-cloud-product`：按云产品 ID 查询关联的 Provider；对应 `GET /service_meta/api/v4/providers/byCloudProductID`。
- `provider resource list`：分页列出指定 Provider 注册的资源；对应 `GET /service_meta/api/v4/providers/{provider_name}/resources`。

## 搜索业务树业务域

```bash
bytedcli bytetree biz search --keyword "demo-business"
bytedcli --json bytetree biz search --keyword "sample-business" --limit 50 --expand-bytetree
```

- `--limit` 是结果上限，不是分页参数。
- `--expand-bytetree` 展开关联和排除的服务树节点。
- 不返回 Duty 相关字段。

## 查看业务域详情

```bash
bytedcli bytetree biz get --domain-code demo_domain
bytedcli --json bytetree biz get --domain-code demo_domain --expand-bytetree --include-tags
```

- `get` 同时返回业务域基础信息和 freshness 信息。
- `--include-tags` 额外返回标签。
- `--expand-bytetree` 只展开服务树映射。

## 查看业务域子节点和叶子节点

```bash
bytedcli bytetree biz children --domain-code demo_domain --page 1 --page-size 50
bytedcli --json bytetree biz children --domain-code demo_domain --expand-bytetree

bytedcli bytetree biz leaf list --domain-code demo_domain --page 1 --page-size 50
bytedcli --json bytetree biz leaf list --domain-code demo_domain --expand-bytetree
```

`--page` 从 1 开始。JSON 同时返回页码、页大小、后端页码和 `has_more`。

## 查看业务域标签、权限和资源

```bash
bytedcli bytetree biz tag list --domain-code demo_domain
bytedcli bytetree biz permission check --domain-code demo_domain --permission system_manage
bytedcli bytetree biz resource list --domain-code demo_domain --page 1 --page-size 20
bytedcli --json bytetree biz resource list --domain-code demo_domain --sort-key name --sort-order ASC
```

- `permission check` 只检查一个业务域的一项权限。
- `resource list --sort-key` 支持 `provider_rank` 和 `name`。
- 业务视角资源使用 `biz resource list`；服务树节点资源使用顶层 `resources`。
