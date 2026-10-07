# Byteconf MVP 命令说明

## 命令分组

Byteconf 支持配置查询、更新、PPE/BOE 发布，以及业务线 PPE 泳道查询和追加登记。

命令结构：

```bash
bytedcli [全局选项] byteconf conf <list|get|update|deploy> [命令选项]
```

## `conf list`

用于查询配置项列表，对应底层接口 `/byteconf/conf/list/v2`。

```bash
bytedcli --json byteconf conf list --ns-key "demo"
bytedcli --json byteconf conf list --ns-key "demo" --biz-tree-path "a/b/c" --keyword "feature" --page 1 --page-size 20
bytedcli --json byteconf conf list --from ./query.json --query-json '{"page_size":50}' --region "sg"
```

支持参数：

| 参数 | 说明 |
| --- | --- |
| `--ns-key` | namespace key，对应 `ns_key` |
| `--biz-tree-path` | 业务树路径，对应 `biz_tree_path` |
| `--keyword` | 关键字搜索，对应 `key_word` |
| `--page` | 页码，1-based，默认 `1` |
| `--page-size` | 分页大小，默认 `20` |
| `--from` | 从 JSON 文件读取基础 query |
| `--query-json` | 追加 query JSON（对象） |
| `--region` | 底层 `x-bcgw-tenant-id`，默认 `bytedance` |

## `conf get`

用于读取单个配置项详情，对应底层接口 `GET /byteconf/conf`。

```bash
bytedcli --json byteconf conf get --id 123 --version 1 --ns-key "demo"
bytedcli --json byteconf conf get --id 123 --version 7 --name "demo_conf" --biz-tree-path "a/b/c" --region "boe"
# 配置在非默认集群时，加全局 --vregion 路由到目标集群
bytedcli --site i18n-tt --vregion SG --json byteconf conf get --region "sg" --id 123 --ns-key "demo"
```

支持参数：

| 参数 | 说明 |
| --- | --- |
| `--id` | 配置 ID，必填 |
| `--version` | 版本号，默认 `1` |
| `--name` | 配置名称，可选 |
| `--ns-key` | namespace key，可选 |
| `--biz-tree-path` | 业务树路径，可选 |
| `--region` | 底层 `x-bcgw-tenant-id`，默认 `bytedance` |

建议：当用户描述为“查最新配置”但没有明确版本时，先用 `conf list` 找到目标版本，再调用 `conf get`。

## `conf update`

用于更新配置项，对应底层接口 `PUT /byteconf/conf`。

```bash
# 先检查 payload
bytedcli --json byteconf conf update --id 123 --version 7 --body-json '{"base":{"k":"v"}}' --dry-run

# 从文件更新
bytedcli --json byteconf conf update --id 123 --version 7 --from ./payload.json --region "sg"
```

支持参数：

| 参数 | 说明 |
| --- | --- |
| `--id` | 配置 ID，必填 |
| `--version` | 版本号，必填 |
| `--from` | 从 JSON 文件读取 body |
| `--body-json` | 追加 body JSON（对象） |
| `--region` | 底层 `x-bcgw-tenant-id`，默认 `bytedance` |
| `--dry-run` | 只输出最终 payload，不发请求 |

说明：

- `--from` 与 `--body-json` 至少要提供一个
- body 必须是 JSON 对象
- 显式传参的 `--id` / `--version` 会覆盖 body 中同名字段

## 多区域路由

`--region` 不只是展示字段，它会同时影响：

1. 请求头 `x-bcgw-tenant-id`
2. 请求头中的 `origin` / `referer`
3. 最终访问的底层网关地址

常见示例：

| `--region` | 路由目标示例 |
| --- | --- |
| `bytedance` / `cn` | `https://paas-gw.byted.org` |
| `boe` | `https://paas-gw-boe.byted.org` |
| `sg` | `https://paas-gw-i18n.byted.org` |
| `sinf` | `https://paas-gw.sinf.net` |

如果 region 未命中预置映射，CLI 会回退到当前 ByteCloud 站点对应的默认 host。

## 集群路由（x-bcgw-vregion）

Byteconf 配置按集群/机房分片存储。`--region` 只决定 `x-bcgw-tenant-id`（租户）与网关地址，并不选择集群；集群由请求头 `x-bcgw-vregion` 决定。

- 全局 `--vregion` 设置 `x-bcgw-vregion`，与 `--region` / `x-bcgw-tenant-id` 相互独立。
- 未带 `--vregion` 时，请求落到默认集群；如果目标配置位于其他集群，读/写会返回 `record not found`。
- 海外配置典型传 `--vregion SG`。
- `x-bcgw-vregion` 区分大小写，请使用控制台对应的原始值（海外集群为大写 `SG`，小写 `sg` 不会命中目标集群）。

```bash
bytedcli --site i18n-tt --vregion SG --json byteconf conf get --region "sg" --id 123 --ns-key "demo"
bytedcli --site i18n-tt --vregion SG --json byteconf conf list --region "sg" --ns-key "demo"
```

少数站点（如 `boe`、`i18n-bd`）会按站点强制集群覆盖，此时无需手动传 `--vregion`，CLI 会自动带上对应集群。排查 `record not found` 时，确认 `--vregion` 是否指向配置真实所在集群。

## 鉴权

Byteconf 的底层鉴权基于 Bytecloud SSO JWT：

- CLI 通过 `SSOClient().getBytecloudJwtForSite(site)` 获取 JWT
- 请求头自动注入 `x-jwt-token`
- 执行前建议先检查 `bytedcli auth status`

## 建议的 Agent 行为

- 机器消费结果时，优先使用 `--json`
- 更新操作默认先 `--dry-run`
- 用户只给出名称、namespace 或业务树路径时，不要直接猜 `id`；先做 `conf list`
- 用户提到 BOE、海外机房或特定租户时，显式设置 `--region`
- 按 `--region` 路由后仍返回 `record not found` 时，补全局 `--vregion`（海外典型值 `SG`）把请求路由到目标集群，再重试同一条命令

## PPE / BOE 发布与业务线泳道

`conf deploy` 发布 namespace、业务树路径、名称和明确版本共同指定的单个配置。
它复用现有 Bytecloud SSO 与网关路由，调用 `POST /byteconf/conf/publish_ppe`
或 `POST /byteconf/conf/publish_boe`。`--region` 选择源配置网关租户，
`--publish-region` 是发布请求中的目标区域，二者不是同一参数。
不会创建审核工单、自动批准审核或修改线上版本；平台权限和发布校验失败会原样报错。

```bash
# 查询业务线及已登记泳道
bytedcli --json byteconf bizline list --ns-key example.namespace
# 预览追加登记；保留已有泳道、另一环境规则、QA 审核要求
bytedcli --json byteconf bizline update --ns-key example.namespace --bizline-id 123 --ppe-channel ppe_demo
# 有管理员权限时提交；重复登记已启用泳道不写入
bytedcli --json byteconf bizline update --ns-key example.namespace --bizline-id 123 --ppe-channel ppe_demo --yes
# BOE 泳道登记使用业务线的 boe_ppe_channel_list
bytedcli --json byteconf bizline update --ns-key example.namespace --bizline-id 123 --ppe-channel ppe_demo --target boe --yes
# 预览指定版本的 PPE 发布
bytedcli --json byteconf conf deploy --ns-key example.namespace --biz-tree-path / --name demo_config --version 2 --target ppe --ppe-channel ppe_demo
# 提交并回读；--dry-run 始终优先于 --yes
bytedcli --json byteconf conf deploy --ns-key example.namespace --name demo_config --version 2 --target ppe --ppe-channel ppe_demo --yes
# 普通 BOE 发布（当前支持 publish-region boe）
bytedcli --json byteconf conf deploy --ns-key example.namespace --name demo_config --version 2 --target boe --yes
# BOE 泳道发布仍走 PPE 接口，显式指定发布区域
bytedcli --json byteconf conf deploy --ns-key example.namespace --name demo_config --version 2 --target ppe --publish-region boe --ppe-channel ppe_demo --yes
```

所有新增写命令默认只预览，只有 `--yes` 且未带 `--dry-run` 才提交。
`bizline update` 只登记已经存在的 ENV 泳道，不创建环境；环境创建、查询使用
`bytedcli env`。缺管理员权限时请由平台管理员授权，不能用配置写权限替代。
业务线接口全量替换发布规则且没有版本锁；命令会重新读取并拒绝已观察到的并发修改，
但不能消除最后一次读取与提交之间的竞态，需避免多人同时修改同一业务线。

提交成功后输出 `submitted: true`，回读比较单独输出 `readback_matches`。
PPE 查询可能回退到线上配置，因此匹配结果表示管理面回读匹配，不能替代应用运行时验证。
回读失败时错误包含 `submitted: true`，应先查询状态，避免盲目重发。

### 自动登记与分步错误

PPE 发布读取配置的 `/byteconf/conf/basic` 当前绑定，再检查该业务线的对应泳道列表。
缺失或未启用时，`conf deploy --yes` 先追加泳道、回读确认，再发布；默认预览同时展示
`registration` 和发布 payload。已有且启用的泳道不会发业务线写请求。配置没有绑定业务线
或绑定在准备期间变化时停止，不默认挑选 namespace 下第一条业务线。

失败输出保留平台原始错误，并提供 `error.code`、`error.hint`、`error.details.operation`：

- `BYTECONF_BIZLINE_UPDATE_*`：业务线/PPE 泳道登记失败；权限问题联系业务线或 namespace 管理员。
- `BYTECONF_PPE_DEPLOY_*`：发布 PPE 配置失败；权限问题申请配置和目标泳道的发布权限，审核问题按平台流程处理。
- `BYTECONF_CONF_UPDATE_*`：配置内容更新失败；权限问题申请配置写权限。
- HTTP 403 使用 `PERMISSION_DENIED` 后缀；其它错误使用 `FAILED` 并保留平台原始原因。
  不依据超时、空结果或模糊错误推断无权限。
- `write_result: unknown` 表示请求是否生效未知，应先查状态，不能盲目重发。
- 业务线登记成功但发布失败时，错误保留 `registration`；修复发布权限或审核阻塞后再重试。
  不回滚、删除可能被其它配置使用的已登记泳道。

命令修改的是 ByteConf 业务线的泳道登记，不创建或编辑 ENV 环境本体。
不要绕过失败步骤调用其它接口，也不要自动修改权限、批准审核或发布线上环境。
