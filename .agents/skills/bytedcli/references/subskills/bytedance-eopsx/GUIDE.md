---
name: bytedance-eopsx
description: "Operate EOpsX (e-commerce SRE) via bytedcli: query metadata/service tree/dependency chains (meta), alarm events (alarm), change events (event), stability metrics (fatal), rate-limit sub-configs (limit), VOC perception alerts (voc), link SLA (sla), business-anomaly checkers (bcp), risk inspection (risk), EPS go_guard resources under guard, and local RCA Skill development and draft management (dev). Use when tasks mention EOpsX、电商运维、告警列表、报警事件、变更事件、稳定性度量、事故数、业务 SLA、链路 SLA、不可用事件、限流子配置、VOC 客诉预警、BCP 业务异常检测、错账、风险巡检、风险项、风险工单、服务元数据、调用对、强弱依赖、业务线树、go_guard、权限源树、角色权限、CN→BOE go_guard sync、归因 Skill 开发、草稿管理。"
---

# bytedcli EOpsX

EOpsX（电商运维）平台的只读查询与受控写操作。`meta/alarm/event/fatal/limit/voc/sla/bcp/risk` 子域约 80 个子命令复用 bytedcli 全局 ByteCloud 登录；`guard` 域使用 BDSSO session 访问 EPS go_guard。全部通过 `bytedcli eopsx <domain> <cmd>` 调用，无需安装 eopsx-cli。

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- **meta**：业务线树、风险对象树、服务元数据、链路元数据、调用对/强弱依赖查询
- **alarm**：报警事件列表（含统计汇总），按平台/等级/状态/PSM/服务树过滤；应急标签字段元信息与标签检索
- **event**：变更事件中心（发布/配置/限流等变更记录）、视图 id 搜索
- **fatal**：稳定性度量（事故数、应急效率、业务 SLA 总结与明细）
- **limit**：限流子配置查询（集群限流 / 自定义限流）
- **voc**：VOC 客诉感知预警（事件、规则、agent）
- **sla**：链路 SLA（链路/业务线/下游视角的 SLI/SLO、不可用事件、工单/审批）
- **bcp**：业务异常检测（数据源、核对规则、执行/错账/复核/告警记录、准实时复核 SQL 试跑，含受控写）
- **risk**：风险巡检（风险项、风险工单、风险专项、洞察，含受控写）
- **guard**：EPS go_guard 源树、权限、角色、环境查询和受确认门保护的 CN/BOE 全量同步

- **dev**：本地归因 Skill 开发、空间参考、草稿上传、远端测试和 Session 调试。**处理此类需求前先读 [DevKit 开发与调试指南](references/rca-dev.md)**，按其中四段交互约定回复；普通平台查询无需加载该指南或套用开发格式。

## 前置条件

- 通用调用方式见 `../../invocation.md`
- **认证**：复用 bytedcli 全局 ByteCloud 登录。先 `bytedcli auth status` 确认；未登录用 `bytedcli auth login`。所有 eopsx 命令自动注入 `x-jwt-token`，无需手动传 token，也无需安装 eopsx-cli。
- `--region` 默认 `cn`。`limit` 域使用独立的 `--region-code <n>` 过滤后端数字 region code，无默认。
- `guard` 域使用 BDSSO browser session：先运行 `bytedcli auth login --session`；BOE 目标另用 `bytedcli --site boe auth login --session`。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 元数据：业务线树 / 服务树 / 服务对象 / 链路 / 调用对
bytedcli eopsx meta get-biz-line-node-tree
bytedcli eopsx meta get-service-tree-nodes
bytedcli --json eopsx meta search-arch-chain --service-tree-id-paths "|25|702118|702141"

# 报警事件列表（含统计汇总）
bytedcli eopsx alarm event-list --page 1 --page-size 20
bytedcli --json eopsx alarm event-list --page 1 --page-size 20 \
  --start-timestamp <ts> --end-timestamp <ts> --psm-list demo.service.api \
  --alarm-status-list 持续中 --order-by event_create_time --order desc

# 变更事件中心
bytedcli --json eopsx event homepage --page 1 --page-size 20 --psm-list demo.service.api

# 稳定性度量（condition 用 JSON，period 与 period-value 必须配对）
bytedcli --json eopsx fatal search-stability-summary \
  --condition '{"period":3,"period_value":"2026-01"}' --compare-type 1

# 应急标签元信息与检索
bytedcli --json eopsx alarm list-tag-meta
bytedcli --json eopsx alarm get-tag-meta --field-code event_status
bytedcli --json eopsx alarm tag-search \
  --field event_level --field root_cause \
  --filters-json '[{"field":"event_level","op":"in","values":["P0","P1"]}]'

# 限流子配置（--tce-psm 必填）
bytedcli --json eopsx limit query-cluster-sub-conf --tce-psm demo.service.api --page 1 --page-size 20

# VOC 客诉预警
bytedcli --json eopsx voc search-event-page --start-time <ts> --end-time <ts> --page 1 --page-size 20

# 链路 SLA
bytedcli --json eopsx sla search-link-list
bytedcli --json eopsx sla get-unavailable-event-detail --event-id <id>

# BCP 业务异常检测（只读）
bytedcli --json eopsx bcp query-checker-list --page 1 --page-size 20
bytedcli --json eopsx bcp get-checker-detail --checker-id <id>
bytedcli --json eopsx bcp get-nrt-snapshot-dry-run-result \
  --executor-task-id <task-id> --checker-id <id>

# 风险巡检（只读）
bytedcli --json eopsx risk get-risk-item-table --page 1 --page-size 20
bytedcli --json eopsx risk get-risk-category-tree

# EPS go_guard
bytedcli --json eopsx guard source-tree get --system-id <id> --env-id <id> --terminal default
bytedcli --json eopsx guard env list --system-id <id> --page 1 --page-size 20
bytedcli --json eopsx guard role list --system-id <id> --env-id <id>
bytedcli --json eopsx guard perm list --system-id <id> --env-id <id>
bytedcli --json eopsx guard source create --system-id <id> --env-id <id> --source-type cli --cli-name "Sample CLI resource" --cli-menu-id <menu_id> --cli-account-type all --cli-keys "bytedcli eopsx guard source list"
bytedcli --json eopsx guard source create --system-id <id> --env-id <id> --source-type skill --skill-name "Sample Skill resource" --skill-menu-id <menu_id> --skill-account-type all --skill-keys "api-to-cli"
```

`guard env change-table-get --publish-id 0` 表示查询当前环境未发布变更；`guard env publish-info-get` 和 `guard env publish-change-list-get` 的 `--publish-id` 必须为大于 0 的发布 ID。

## 写操作安全规则（Agent Guidance）

下列 `bcp`（9 个写命令）和 `risk`（10 个写命令）含写操作；`dev` 的初始化、参考下载、草稿保存、测试、追问及停止同样先预览确认，具体流程见 [DevKit 指南](references/rca-dev.md)。**所有写命令默认 dry-run：只打印将提交的 payload 预览，必须显式加 `--yes` 才真正提交。** `guard` 的 source/perm/role/env CRUD 命令沿用后台接口语义，会直接提交，不支持 `--yes`。

- 首次执行不要加 `--yes`，先展示 payload 给用户，确认无误后再加 `--yes` 提交。
- 写操作应由用户明确要求触发；不要把"查询/排查"自动升级为写操作。
- 执行 `guard perm source-relation-update` 前必须确认完整关系集合；该命令会清除所有未传入的资源类型和资源 ID。

```bash
# 先 dry-run 预览
bytedcli --json eopsx risk add-comment --record-id <id> --comment "demo comment"
# 确认后提交
bytedcli --json eopsx risk add-comment --record-id <id> --comment "demo comment" --yes
```

写命令清单：

- **bcp**：`submit-nrt-snapshot-dry-run`、`batch-update-diff-record`、`execute-batch-compensate`、`execute-instance-compensate`、`create-checker`、`batch-update-checker`、`ascribe-alarm`、`create-note`、`transit-status`
- **risk**：`add-risk-item`、`update-risk-item`、`add-risk-issue`、`update-risk-issue-fixers`、`add-comment`、`update-risk-issue`、`update-risk-record-priority`、`create-meego`、`create-gw-tag`、`delete-gw-tag-relation`

## Notes

- `--json` 是全局选项，放在 domain 之前（如 `bytedcli --json eopsx alarm event-list ...`）。
- 分页统一使用 `--page`/`--page-size`。`event homepage` 会把 `--page-size` 映射为后端 `size`；BCP 两个列表命令会把 `--page` 映射为后端 `page_number`。
- 复杂请求体（对象/数组字段）优先用 `--body-string '<json>'` 整体透传；一般命令中显式 option 会覆盖同名字段。`batch-update-diff-record` 与 `execute-instance-compensate` 为防止绕过 ID/枚举校验，会拒绝 `--body-string` 中与专用 option 对应的保留字段；这些字段必须使用专用 option 传入。
- 时间入参通常使用 Unix 秒级时间戳；`alarm tag-search --start-time/--end-time` 按后端协议使用 Unix 毫秒。空结果不等于成功，需结合 `total` / 列表长度判断。
- `alarm list-tag-meta` 查询字段元信息集合，JSON 返回 `{fields, current_count, has_more}`（后端一次性返回全量、无分页）；`alarm get-tag-meta --field-code <code>` 查询单字段详情，JSON 返回 `{field}`，未命中为 `null`。
- `alarm tag-search` 返回 `process_timeline` 或 `extern_process_timeline` 时，CLI 已在每个节点补充 `category_label` / `source_label`（未知枚举为 `null`）。原样使用后端节点，不做冲突检查、内容复核、合并或重新分类。
- 各子命令的方法映射、字段字典、枚举码表、jq 路径见 `references/eopsx.md`。

## References

- [DevKit 开发与调试](references/rca-dev.md)：仅在归因 Skill 开发、草稿管理及远端验证场景读取。
- `references/eopsx.md`
- `../../invocation.md`
- `../../troubleshooting.md`
