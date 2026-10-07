# Index Service / Model / Viking

## 能力范围

- 查询 Byterec index service 完整概览，包括资源、授权、提醒、事件、成本、拓扑、监控链接、告警和 Kafka 工单（`byterec indexservice product get`）
- 查询服务变量、配置文件元数据或解码后的配置正文（`byterec indexservice config get`）
- 列出或读取 Index Service 集群的 TCE、SCM、资源与配置状态（`byterec indexservice cluster list|get`）
- 列出部署记录或读取单条部署详情（`byterec indexservice operation list|get`）
- 按 namespace/keyword 查询 Byterec 模型配置列表，并判断是否绑定 Viking serving（`byterec model list`）
- 查看 Viking DB database/model/data/pipeline/GDPR/sync 资源（`byterec viking database get`、`byterec viking model-db get` 等）
- 执行 Viking DB debug recall / DSL 查询（`byterec viking debug recall`）或查看 model meta / embedding
- 查询或更新 Viking service 配置文件元数据、正文或单行 flag，并将选中的服务集群配置部署到 ByteKV 生成 review URL（`byterec viking service-config get` / `update` / `deploy --target bytekv`）
- 预览或提交 Viking DB 写请求；默认 dry-run，只有传 `--yes` 才提交
- 需要机器可读结果供脚本或 Agent 继续处理时，使用 `--json`

## 资源选择与操作约束

- Index Service 服务级查询使用 `--psm` 或 `--service-id` 二选一；页面 URL `/index_service/service/<id>/...` 中的数字可直接传给 `--service-id`
- `config get` 默认只列配置文件元数据；用 `--file`、`--conf-id` 或 `--all-files` 显式读取并解码正文，三者互斥
- `cluster get` 通过 `--cluster` 或 `--cluster-id` 精确选择一个集群；查看全部集群使用 `cluster list`
- `cluster get` 可继续用 `--file`、`--conf-id` 或 `--all-files` 读取并解码渲染后的集群配置正文
- `operation get` 必须同时提供 `--operation-id` 和 `--psm` / `--service-id` 之一，并校验部署记录归属
- `byterec indexservice` 只提供 GET 查询，不触发页面的 TCE 状态刷新、配置修改、部署、告警注入或 Kafka 工单写操作
- `byterec viking api post|put|delete` 和 Viking 资源写命令默认只输出 dry-run 计划；传 `--yes` 才会提交写请求
- `byterec viking api get|post|put|delete` 仅允许访问 Viking DB allow-list path；优先使用资源化命令
- `byterec viking service-config get` 面向 `ns_tag=viking` 的 Byterec service 配置；不传 `--file` / `--conf-id` / `--all-files` 时只列配置文件元数据，传选择器时读取并解码配置正文
- `byterec viking service-config update` 修改一个精确的 `-flag=value` 行；必须传 `--flag <name>` 与 `--value <value>`，并用 `--file` 或 `--conf-id` 选中单个配置文件；默认 dry-run，只有传 `--yes` 才提交
- `byterec viking service-config deploy --target bytekv` 基于 `/viking/service/<service_id>/overview` 的服务集群部署配置到 ByteKV；不传集群选择器时列出可选集群，传 `--all-clusters` 或 `--cluster <id-or-name,...>` 选择，默认 dry-run，只有传 `--yes` 才提交并返回 review URL

## Quick start

```bash
# 查询 index service 产品信息
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec indexservice product get --psm example.indexservice.psm

# 从控制台 URL 直接按 service ID 查询完整概览
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec indexservice product get --service-id 12345

# 查询 index service 配置
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec indexservice config get --psm example.indexservice.psm

# 读取并解码指定配置文件正文
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec indexservice config get \
  --service-id 12345 \
  --file task.yaml

# 列出集群，再按 cluster ID 查询完整 TCE / SCM / 配置状态
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec indexservice cluster list --service-id 12345
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec indexservice cluster get \
  --service-id 12345 \
  --cluster-id 67890 \
  --file task.yaml

# 查询部署记录列表与单条详情
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec indexservice operation list --service-id 12345
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec indexservice operation get \
  --operation-id 98765 \
  --service-id 12345

# 以 JSON 形式获取产品信息
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec indexservice product get --psm example.indexservice.psm

# 以 JSON 形式获取配置
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec indexservice config get --psm example.indexservice.psm

# 查询模型配置列表（示例：按 version 关键字过滤）
BYTEDCLI_CLOUD_SITE=us-ttp-bdee bytedcli byterec model list \
  --namespace demo_namespace \
  --keyword 1234 \
  --page 1 --page-size 50

# Viking DB：查看 database / model
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking database get --db-mod-id 1001
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking model-db get --viking-db-id 1001 --db-model-id 2001

# Viking DB：执行 debug recall DSL
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec viking debug recall \
  --model-id 2001 \
  --context-id sample-context \
  --random-emb random \
  --topk 3 \
  --dsl-json '{"op":"and","conds":[{"field":"status","op":"=","value":0}]}'

# Viking service：按 PSM 查询配置文件列表
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config get --psm example.viking.service

# Viking service：读取指定配置文件正文
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec viking service-config get \
  --psm example.viking.service \
  --file viking_service.flags

# Viking service：从控制台 URL 的 service_id/conf_id 直接读取配置正文
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec viking service-config get \
  --service-id 12345 \
  --conf-id 67890

# Viking service：预览单个 flag 修改，默认 dry-run
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config update \
  --psm example.viking.service \
  --file viking_service.flags \
  --flag max_batch_size \
  --value 14

# Viking service：明确传 --yes 才提交修改
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config update \
  --service-id 12345 \
  --conf-id 67890 \
  --flag max_batch_size \
  --value 14 \
  --yes

# Viking service：列出可部署到 ByteKV 的服务集群
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config deploy \
  --target bytekv \
  --service-id 12345

# Viking service：选择部分服务集群部署到 ByteKV，返回 operation review URL
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config deploy \
  --target bytekv \
  --service-id 12345 \
  --cluster 10001,demo-cluster-b \
  --yes

# Viking DB：写请求默认 dry-run；明确传 --yes 才提交
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking data create --body-json '{"db_mod_id":1001,"data":[{"id":"sample-id"}]}'
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking data create --body-json '{"db_mod_id":1001,"data":[{"id":"sample-id"}]}' --yes

# 等价的站点写法
bytedcli --site i18n-tt byterec indexservice product get --psm example.indexservice.psm
```

## Viking service config workflow

Viking service 配置是 `ns_tag=viking` 的 Byterec service 配置，不是 `byterec indexservice config get` 返回的 `ns_tag=index_service` 配置。

推荐流程：

1. 先用 `byterec viking service-config get --psm example.viking.service` 列出配置文件元数据；也可以从控制台 URL 中取 `service_id` 后传 `--service-id 12345`。
2. 需要正文时再用 `--file viking_service.flags`、`--conf-id 67890` 或 `--all-files` 读取并解码配置；JSON 模式读取 `config_files[].decoded_text`。
3. 修改 flag 时先 dry-run：`service-config update --file viking_service.flags --flag max_batch_size --value 14`。`--flag` 只写名称，不写 `-` 前缀，也不要写成 `max_batch_size=14`。
4. 确认输出里的 `Before` / `After` 后再加 `--yes`。命令只替换一个精确匹配的 `-flag=value` 行；缺失、重复匹配或 no-op 都会拒绝。真实提交会读取最新 `versioned_conf`、写回完整 base64 文件，并重新读取同一个 `conf_id` 校验目标行。
5. 部署 ByteKV 前先运行 `service-config deploy --target bytekv --psm example.viking.service` 列可选服务集群；`--cluster` 同时支持 Byterec service cluster id 和集群名，不是 TCE cluster id。真实部署必须选择 `--all-clusters` 或 `--cluster`，并加 `--yes`，成功后查看 `operation.review_url`。

常用命令序列：

```bash
# 1. 按 PSM 找到 Viking service，并列出配置文件
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config get \
  --psm example.viking.service

# 2. 读取 flags 文件正文；也可以把 --psm + --file 换成 --service-id + --conf-id
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec viking service-config get \
  --psm example.viking.service \
  --file viking_service.flags

# 3. 先 dry-run 修改一个 flag，检查输出里的 Before / After
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config update \
  --psm example.viking.service \
  --file viking_service.flags \
  --flag max_batch_size \
  --value 14

# 4. 确认无误后提交；如果来自控制台 URL，推荐用 service-id + conf-id 精确选择文件
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config update \
  --service-id 12345 \
  --conf-id 67890 \
  --flag max_batch_size \
  --value 14 \
  --desc 'demo flag update' \
  --yes

# 5. 先列出可部署 ByteKV 的服务集群，确认 Byterec cluster id / TCE cluster id
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec viking service-config deploy \
  --target bytekv \
  --psm example.viking.service

# 6. 选择集群部署到 ByteKV，并从输出读取 operation.review_url
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec viking service-config deploy \
  --target bytekv \
  --service-id 12345 \
  --cluster 10001,demo-cluster-b \
  --yes
```

## 输出说明

- `product get` 文本输出包含服务与资源摘要、集群、提醒、事件、授权、Kafka 工单、成本、拓扑、监控链接、告警规则和配置文件；JSON 还保留 `section_errors`
- `config get` 文本输出包含平台常量、平台环境、平台服务变量、用户服务变量、环境变量、分发层变量与配置文件；显式选择的文件会输出解码正文
- `cluster list|get` 输出 TCE 状态、分片、实例、副本、CPU/MEM、SCM 版本、配置状态和变量；`get` 保留完整集群响应
- `cluster list` 的 JSON 结果显式返回 `page=1`、`page_size`、`page_count/current_count`、`has_more=false` 和 `truncated=false`；集群来自服务详情的完整快照
- `operation list` 输出后端单次最多 100 条的部署记录快照；JSON 结果返回 `page=1`、`page_size=100`、`page_count/current_count`、`has_more=null`，满 100 条时 `truncated=true`，不宣称已知总数或可翻页
- `operation get` 返回并展示解码后的参数、日志、消息和步骤数据
- `viking service-config get` 文本输出包含 `Byterec Viking Service`、`Byterec Platform Constants`、配置文件表；读取正文时会附带解码后的配置文本块，JSON 模式返回 `decoded_text`
- `viking service-config update` 文本输出包含 dry-run/submitted 模式、service/config 标识、版本、校验状态，以及修改前后的 `-flag=value` 行；JSON 模式返回结构化 `change`
- `viking service-config deploy --target bytekv` 文本输出包含 dry-run/submitted 模式、服务标识、可选服务集群表、已选集群、operation id 和 review URL；JSON 模式返回结构化 `clusters`、`selected_clusters`、`operation.review_url`
- JSON 模式会返回完整结构化结果，适合脚本或 Agent 继续处理
- 部分表格块在数据为空时可能不会显示，这是正常行为

## Notes

- 当前覆盖四组 Byterec Index Service 查询：`product get`、`config get`、`cluster list|get`、`operation list|get`，以及模型/Viking 相关能力
- `--json` 是全局参数，必须放在 `byterec` 之前
- Byterec 侧会按全局站点自动路由控制面，默认建议使用 `i18n-tt`
- Byterec index service 配置与 Viking service 配置是不同 `ns_tag` 的服务配置；查询或更新 Viking service 配置时使用 `byterec viking service-config get` / `update`，不要用 `byterec indexservice config get`
- 更新 Viking service config 时先运行不带 `--yes` 的 dry-run，确认 `Before` / `After` 后再加 `--yes`；命令会读取最新配置、只替换一个精确匹配的 `-flag=value` 行、提交完整 base64 配置文件，并重新读取同一个 `conf_id` 校验目标行
- 部署 Viking service config 到 ByteKV 时以 service overview 的服务集群为准；`--cluster` 同时支持 Byterec 服务集群 id 和集群名，不是 TCE cluster id。先不带选择器运行 `deploy --target bytekv` 查看可选集群，再用 `--cluster` / `--all-clusters` 选择并加 `--yes` 部署

## 实现参考

- `src/cli/commands/byterec/index.ts`
- `src/cli/handlers/byterec/indexservice.ts`
- `src/cli/commands/byterec/viking.ts`
- `src/cli/handlers/byterec/viking.ts`
