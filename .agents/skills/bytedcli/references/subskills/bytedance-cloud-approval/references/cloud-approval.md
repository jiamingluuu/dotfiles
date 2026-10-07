# Approval 命令参考

以下示例统一使用 `bytedcli cloud-approval`；全局参数放在 Domain 前面。

## 目录

- [查询工单列表](#查询工单列表)
- [查询平台 VRegion](#查询平台-vregion)
- [查询工单详情](#查询工单详情)
- [创建工单](#创建工单)
- [执行审批动作](#执行审批动作)
- [移交审批人](#移交审批人)
- [撤销申请](#撤销申请)
- [催办](#催办)

## 查询工单列表

### 我发起的工单

```bash
bytedcli cloud-approval apply list \
  --start 1770134400 \
  --end 1785859199 \
  --page 1 \
  --page-size 20
```

使用 `--approver` 筛选审批人。

### 与我审批相关的工单

```bash
bytedcli cloud-approval audit list \
  --ticket-status-list 3 \
  --applicant alice \
  --page 1 \
  --page-size 20
```

不传状态过滤时，结果可能同时包含当前身份参与审批的待审和历史工单。只查询审批中的工单时显式传 `--ticket-status 3` 或 `--ticket-status-list 3`。

### 当前身份可见的工单

```bash
bytedcli cloud-approval notice list \
  --approval-source iam,olympus \
  --keyword permission
```

普通用户看到的是本人发起、参与审批或被知会的相关工单。`notice list` 只是当前身份可见工单的检索入口，不是执行知会的命令；知会使用 `ticket execute --action notice`。不要把 `notice list` 理解成无条件的系统级全量查询。

人员过滤与命令对应关系：

| 命令 | 过滤参数 | 含义 |
|---|---|---|
| `apply list` | `--approver` | 按审批人过滤本人发起的工单 |
| `audit list` | `--applicant` | 按申请人过滤本人参与审批的工单 |
| `notice list` | `--applicant` | 按申请人过滤当前身份可见的工单 |

### 列表公共参数

- `--ticket-id`：可重复或使用逗号分隔；每个值按字符串处理。
- `--ticket-status` / `--ticket-status-list`：支持 `1=已完成`、`2=已撤销`、`3=审批中`、`4=失败`、`11=已通过`、`12=部分通过`、`21=已驳回`。
- `--start` / `--end`：非负 Unix 秒；两者都提供时开始时间不得晚于结束时间。
- `--keyword`：按工单 key 或名称模糊搜索。
- `--approval-source` / `--approval-type`：可重复或使用逗号分隔。
- `--additional-remarks`：按附加备注筛选。
- `--search-params`：JSON object 或当前工作目录内的 `@relative-file.json`。
- `--display-param`：请求额外表单字段；必须同时使用 `--full`。
- `--page`：从 `1` 开始，默认 `1`。
- `--page-size`：范围 `1..1000`，默认 `20`。

默认精简结果包含分页信息，以及工单 ID、标题、流程类型、状态、申请人、审批人、创建时间、所属平台和详情链接等核心字段。工单 ID 始终按字符串消费。

### 分页遍历

逐页递增 `--page` 直到返回空列表或已累计的条数达到响应中的 `total`。不要一次请求超大 `--page-size`，保持 ≤100 为宜。

## 查询平台 VRegion

```bash
bytedcli cloud-approval platform vregion list \
  --platform cloud_ticket \
  --platform-site cn,i18n
```

- `--platform` 默认是 `cloud_ticket`。
- `--platform-site` 可重复或使用逗号分隔。
- 精简结果返回 `site`、`site_name`、`vregion`、`vregion_name`。
- 只使用目标平台真实返回的映射。无匹配时返回空结果，不得用全局站点目录推断该平台可用。
- 写操作前确认 VRegion 属于当前 Site；不要把响应中的任意 `site` 字符串直接当作全局 `--site`。

示例输出（`--json`）：

```json
{"status":"success","data":{"data":[{"site":"cn","site_name":"CN","vregion":"default","vregion_name":"默认"}]}}
```

## 查询工单详情

```bash
bytedcli cloud-approval ticket get \
  --ticket-id '1000000000000000001' \
  --flow-type 1
```

- `--ticket-id` 必填，并始终保持字符串。
- `--flow-type` 必填：`1=Cloud Ticket`、`2=BPM`、`3=SINF BPM`、`4=BABI`。
- 从列表或可信工单上下文解析 flow type，不要猜测。
- 默认返回工单核心信息、申请人、时间、操作权限、表单参数和审批摘要。
- 需要完整流程节点、群聊、公告、父子工单或原始响应时追加 `--full`。
- 精简模式优先保留结构化的表单参数；只有缺少结构化参数时才保留兼容字符串。

## 创建工单

先预览：

```bash
bytedcli cloud-approval ticket create \
  --flow-name demo-flow \
  --form-name demo-form \
  --apply-params '{"region":"cn","resource_type":"rds"}'
```

确认后执行：

```bash
bytedcli cloud-approval ticket create \
  --flow-name demo-flow \
  --form-name demo-form \
  --apply-params '{"region":"cn","resource_type":"rds"}' \
  --yes
```

参数规则：

- `--flow-id` 与 `--flow-name` 必须且只能提供一个。
- `--form-id` 与 `--form-name` 必须且只能提供一个。
- `--flow-id`、`--form-id` 和可选的 `--app-id` 在命令行中以十进制字符串传入，并校验为正整数；Agent 不自行转成 JavaScript `Number`。
- `--apply-params` 接受 JSON object、JSON array 或 `@relative-file.json`。
- `--tag key=value` 可重复；同名 key 的后值覆盖前值。
- `--observer` 可重复或使用逗号分隔。
- 可选参数还包括 `--env`、`--ppe`、`--tag-string`、`--sub-apply-list` 和 `--main-ticket-display-config`。
- `--sub-apply-list` 必须是 JSON array；`--main-ticket-display-config` 必须是 JSON object。
- 所有 `@file` 只允许当前工作目录内的相对路径；拒绝绝对路径、`..` 越界和符号链接逃逸。

`ticket create` 是用户明确知道工作流和表单时使用的通用接口。权限错误不得直接调用它；先按 [providers.md](providers.md) 路由。

### 发现可用的工作流和表单

当前 CLI 不提供 flow/form 列表查询命令。`--flow-name` 和 `--form-name` 必须由用户提供或从已有工单详情中提取（`ticket get --full` 返回的 `flow_name` / `form_name`）。不要猜测名称。

## 执行审批动作

先预览：

```bash
bytedcli cloud-approval ticket execute \
  --ticket-id '1000000000000000001' \
  --flow-type 1 \
  --action pass \
  --node-instance-id '2000000000000000001' \
  --desc approved
```

确认后在完全相同的参数后追加 `--yes`。

支持的 `--action`：

```text
pass
reject
revert
insert_pre
insert_next
notice
```

动作约束：

- `--ticket-id` 和每个 `--node-instance-id` 都按字符串处理。节点实例参数可重复或使用逗号分隔。
- `pass`、`reject`、`revert` 未指定节点时，后端可能操作当前身份的全部可审批节点；存在多个进行中节点时先查详情并显式指定范围。
- `insert_pre`、`insert_next` 必须同时提供节点实例和至少一个 `--extra-user`。
- `notice` 必须提供至少一个 `--extra-user`。
- `notice` 是执行知会动作；`notice list` 只是查询当前身份可见的工单。
- `--pass-ratio` 仅用于 `insert_pre` / `insert_next`，范围 `1..100`。
- `--audit-params` 必须是 value 均为字符串的 JSON object；也可使用工作目录内的相对 `@file`。
- 可使用 `--audit-params-string` 传入兼容字符串参数。
- 不使用 `authorize` 移交审批人；改用 `ticket auditor update`。
- `revert` 是审批人退回审批节点；不用它冒充申请人撤销，撤销申请必须使用 `ticket cancel`。

即使顶层请求成功，只要任一节点结果 `success=false`、节点结果为空或结构异常，整条命令都视为失败。先回查工单和失败节点，再决定是否重新预览。

## 移交审批人

先从完整详情中选择可移交的节点实例，再预览：

```bash
bytedcli cloud-approval ticket auditor update \
  --accept-user bob \
  --flow-type 1 \
  --node-instance-id '2000000000000000001' \
  --reason handover
```

确认后在完全相同的参数后追加 `--yes`。

- `--accept-user`、`--flow-type` 和 `--node-instance-id` 必须提供；`--reason` 可选。
- 把节点实例 ID 保持为字符串。它必须来自可信的审批节点上下文。
- 无法确认节点时，使用 `ticket get --full`，从当前节点中选择明确允许移交的节点。
- 不得把 `node_id`、工单 ID 或节点在页面上的顺序当作节点实例 ID。

## 撤销申请

先预览：

```bash
bytedcli cloud-approval ticket cancel \
  --ticket-id '1000000000000000001' \
  --flow-type 1
```

确认后在完全相同的参数后追加 `--yes`。

- `--ticket-id` 和 `--flow-type` 必填。
- 只撤销用户已确认的申请；`cancel` 是申请人撤销，审批动作 `revert` 是退回节点，两者不能替代。

## 催办

```bash
bytedcli cloud-approval ticket reminder send --ticket-id '1000000000000000001'
```

确认后追加 `--yes`。执行时 CLI 会先校验催办状态（`show_remind`），不可催办时直接阻断，不会发送 POST。

## 安全边界

- 写命令不带 `--yes` 时默认 dry-run，不发送写请求。不使用旧 `--confirm`。
- 向用户展示预览并等待明确确认后才追加 `--yes` 执行；参数变化后必须去掉 `--yes` 重新预览。
- 请求超时或结果不明确时，先用 `ticket get` 回查状态，不盲目带 `--yes` 重试。
- 不要在命令参数、日志、错误或结果中暴露 JWT、Cookie 或 Authorization header。
- 没有操作权限时停止并返回结构化错误，不要尝试绕过权限。
- 即使顶层请求成功，只要任一节点结果 `success=false`，整条命令视为失败。
