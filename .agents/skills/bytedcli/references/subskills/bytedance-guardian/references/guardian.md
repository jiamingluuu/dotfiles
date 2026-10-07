# Guardian（星环 / 小 R）命令面

Guardian 是固定 CN、当前用户身份的内置 domain。查询与写入都使用 `bytedcli guardian ...`；不要手写请求。

## 写入通用规则

所有写命令都要求 `--reason`，默认只生成 10 分钟有效的计划。提交时原参数必须不变，并增加 `--confirm-token <token> --yes`。

```bash
# 预演
bytedcli --json guardian <resource> <action> ... --reason "Change isolated test config"

# 提交同一计划
bytedcli --json guardian <resource> <action> ... --reason "Change isolated test config" \
  --confirm-token "<confirm-token>" --yes
```

可选 `--max-modified-fields <n>` 和 `--max-deleted-items <n>` 只能收紧内置预算。`--timeout-ms <ms>` 可设置本次 mutation 的正整数毫秒超时，确认时必须与预演保持相同值。写请求不重试；`GUARDIAN_WRITE_OUTCOME_UNKNOWN` 表示已经尝试写入但无法确认结果，必须先查远端和本地回执，禁止原样重发。MCP 不允许真实提交。本地计划、回执及完整性密钥只允许当前用户读取；内容或密钥损坏时会失败关闭。

## 写命令

| 范围      | 命令                                   | payload 形态                | 额外约束                                                                 |
| --------- | -------------------------------------- | --------------------------- | ------------------------------------------------------------------------ |
| 生成规则  | `generation-rule update`               | `--enabled true/false`      | 单规则                                                                   |
| 生成规则  | `generation-rule create/update`        | 规则对象                    | 更新显式传 `--rule-id`；等级与条件同时变化通常超过高风险预算             |
| 生成规则  | `generation-rule delete`               | 无                          | 单规则删除                                                               |
| 聚合      | `config aggregation-policy update`     | 对象 patch                  | 仅服务端 IDL 字段                                                        |
| 时段      | `config time-period update`            | 非空数组                    | 整组替换；空数组与隐式删除拒绝                                           |
| 响应人    | `config responder update`              | 非空数组                    | 整组替换；每项为 `role + details`                                        |
| 群名/语言 | `config chat update`                   | 对象 patch                  | `chat_name_config`、`lan`                                                |
| 直播群    | `config live-chat update`              | 非空数组                    | `id/name/type/chat_id/level/avatar`                                      |
| 自动升级  | `config auto-upgrade update`           | 非空数组                    | `id/config_type/level/duration/level_list`                               |
| 状态流    | `config status-flow update`            | 非空数组                    | `type/value/threshold/frequency/event_levels`                            |
| 预案      | `config runbook create/update/delete`  | 文档对象或精确 ID           | 更新显式传 `--id`                                                        |
| 租户规范  | `config standard update`               | 对象 patch                  | Guardian 全局管理员                                                      |
| 订阅      | `subscription create/update/delete`    | 规则对象、状态或精确 ID     | 创建时只能省略 `status` 或传 `status:1`；更新显式传 `--id`；只能绑定当前 `--biz-id` |
| TODO      | `todo create/update/delete`            | TODO 对象或精确 ID          | 创建/更新需 `record_id`、描述、级别、执行人、完成时间；更新显式传 `--id` |
| 业务线    | `business create/update/delete`        | 业务线对象或精确 ID         | 创建会初始化默认配置；删除只允许叶子节点且会删除关联配置                 |
| 关注      | `business update --focused true|false` | 精确 ID                     | 仅影响当前用户                                                           |
| 根因分类  | `meta root-cause create/update/delete` | 分类对象或精确 ID           | Guardian 全局管理员；有子分类时禁止删除或改名                            |
| 事件标注  | `incident label update`                | 标注对象                    | 单事件；禁止 `operator`；只做标注，不关单                                |
| 事件时间  | `incident time update`                 | 时间字段 patch              | 单事件；至少一个时间字段                                                 |
| 报警静默  | `incident alarm update`                | `{rule:[...],silence_time:<minutes>}` | 每次只允许一条精确规则                                                   |

示例：

```bash
bytedcli guardian config chat update --biz-id "<business-id>" \
  --data '{"lan":2}' --reason "Use English for isolated test business"

bytedcli guardian incident label update --id "<incident-id>" \
  --data-file ./incident-label.json --reason "Complete incident classification"

bytedcli guardian incident alarm update --id "<incident-id>" \
  --data '{"rule":[{"rule_id":"sample-rule","alert_group_id":"sample-group","v_region":"cn"}],"silence_time":30}' \
  --reason "Silence one test alarm for 30 minutes"
```

`business clone`、事件创建/ACK/恢复/解决/重开/升降级/邀请/角色调整/合并/解除/换主没有开放：现有后端接口缺少满足本安全模型的稳定单目标读回或恢复边界。

## 读取命令

```bash
bytedcli guardian auth status [--probe]
bytedcli guardian space list
bytedcli guardian business list --tenant-id "<tenant-id>" [--keyword sample]
bytedcli guardian business get --id "<business-id>"
bytedcli guardian incident list --business-id "<business-id>" --start <rfc3339> --end <rfc3339>
bytedcli guardian incident get --id "<incident-id>"
bytedcli guardian incident child list --id "<incident-id>"
bytedcli guardian incident timeline list --id "<incident-id>"
bytedcli guardian incident label get --id "<incident-id>"
bytedcli guardian incident alarm list --id "<incident-id>" --view raw
bytedcli guardian incident alarm get --id "<incident-id>" --alarm-id "<alarm-id>"
bytedcli guardian incident todo list --id "<incident-id>"
bytedcli guardian meta level list
bytedcli guardian meta unit list
bytedcli guardian meta source list
bytedcli guardian meta root-cause list --tenant-id "<tenant-id>"
bytedcli guardian policy get --biz-id "<business-id>"
bytedcli guardian config get --tenant-id "<tenant-id>"
bytedcli guardian statistics get --tenant-id "<tenant-id>"
bytedcli guardian subscription list --biz-id "<business-id>"
bytedcli guardian todo list --incident-id "<incident-id>"
bytedcli guardian todo get --id "<todo-id>"
bytedcli guardian audit-log list --biz-id "<business-id>"
```

## 恢复与限制

```bash
bytedcli --json guardian restore get --receipt-id "<receipt-id>"
```

恢复计划提供写前快照和反向差异，但不会自动写回。更新类操作可以把 `restore_to` 整理为原命令输入，再重新预演；删除类资源能否重建取决于创建接口和服务端副作用。业务线删除尤其会清理关联配置，应视为人工恢复，不承诺一键回滚。

创建命令只有在后端返回稳定资源 ID 且可按 ID 读回时才标记为 `verified`；若接口未返回 ID，则记录回执并返回 `GUARDIAN_WRITE_OUTCOME_UNKNOWN`，不会用名称或列表内容猜测新对象。

订阅创建接口会由服务端补齐默认时间字段，并把新订阅置为 running。CLI 因此拒绝直接创建 paused 订阅；如需暂停，先创建并确认读回，再单独执行 `guardian subscription update --status paused`。

RCA/Goalkeeper 结果、智能诊断和专家知识仍不在本命令面内；`--with-raw` 也会过滤这些字段及凭据形态字段。
