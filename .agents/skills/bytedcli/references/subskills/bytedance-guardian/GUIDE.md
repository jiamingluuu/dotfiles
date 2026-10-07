---
name: bytedance-guardian
description: "Use the built-in bytedcli guardian domain whenever users mention Guardian or 星环, or mention 小 R/小R together with incident-management intent. Supports CN read operations plus guarded single-target writes for emergency rules/configuration, business configuration, incident labels/times/alarm silence, subscriptions, TODOs, and root-cause categories. Does not support RCA/Goalkeeper execution, AI diagnosis, or unverified incident lifecycle mutations."
---

# Guardian（星环 / 小 R）

## 使用边界

1. 先读取公共 `bytedcli` skill，复用其安装、认证、全局参数和错误处理规则。
2. Guardian 固定使用 CN 当前用户身份；不要传 Cookie/JWT，不切到 app 或 AI identity。
   Guardian 是小 R 的应急管理模块，服务已接入团队，实际范围受当前用户权限限制。裸“小 R”先澄清；聊天、机器人或转发意图不进入本命令。
3. 查询使用 `guardian auth|space|business|incident|meta|policy|config|statistics|subscription|todo|audit-log`。
4. 已开放的写操作包括：
   - 应急配置：事件生成规则、聚合策略、通知时段、响应人、群名/语言、直播群、自动升级、状态流、预案文档、租户达标规范。
   - 业务线：创建、更新、删除、关注、取消关注。
   - 事件运营：单事件标注、关键时间、单条报警规则静默、订阅规则、TODO、根因分类。
5. 不要猜测未开放命令。事件创建、ACK、恢复、解决、重开、升降级、邀请、角色调整、合并/解除/换主，以及 RCA/Goalkeeper/AI 诊断仍不支持。业务线复制也不开放，因为现有接口会跨多类配置复制且不能可靠读回新 ID。

## 写入安全流程

```text
第一次执行（不带 --yes）
  读取当前值 -> 计算 before/after/diff -> 预算校验 -> 返回 10 分钟 confirm_token

第二次执行（相同参数 + --confirm-token + --yes）
  权限门禁 -> 再读当前值 -> 快照一致 -> 消费一次性 token
  -> 写请求只发一次 -> 读回校验 -> 保存 0600 本地回执
```

- 不带 `--yes` 永远只预演；`--yes` 没有同一 payload 生成的 token 也不会提交。
- 写请求不自动重试、不在 401 后刷新并重放。返回错误或写后读回失败时视为结果未知，保存回执并报错；不要自动重试。
- 目标必须是单个明确 ID。空数组、隐式删除、修改/删除超预算、跨业务线订阅、payload 与 CLI ID 不一致都会被拒绝。
- `--max-modified-fields`、`--max-deleted-items` 只能把内置预算收紧，不能放宽。
- 写请求可能超过全局 HTTP 超时时，可用正整数 `--timeout-ms <ms>` 设置本次 mutation 超时；确认时该参数必须与预演保持一致。
- 配置写入要求业务线管理员；租户规范和根因分类要求 Guardian 全局管理员；事件相关写入要求当前用户出现在明确事件角色字段。权限证据缺失时 fail closed。
- 业务线删除只允许叶子节点；业务线移动/改名若会影响子节点路径则拒绝；根因分类删除或改名若会级联子分类则拒绝。
- 共享 MCP 可预演，但不能真实提交 Guardian 写操作。
- 本地计划和回执使用仅当前用户可读的文件，并校验完整性；文件或完整性密钥损坏时会拒绝确认或生成恢复计划。
- `restore get` 只生成恢复数据，不自动回滚；恢复必须重新走原写命令的预演与确认。

## 推荐调用方式

```bash
# 先看目标当前状态
bytedcli --json guardian generation-rule list --biz-id "<business-id>"

# 第一次：预演，记录返回的 confirm_token
bytedcli --json guardian generation-rule update \
  --biz-id "<business-id>" --rule-id "<rule-id>" \
  --data-file ./generation-rule.json --reason "Change one test rule"

# 第二次：参数完全相同，加一次性 token 和 --yes
bytedcli --json guardian generation-rule update \
  --biz-id "<business-id>" --rule-id "<rule-id>" \
  --data-file ./generation-rule.json --reason "Change one test rule" \
  --confirm-token "<confirm-token>" --yes

# 写后若需恢复，先生成恢复计划（不会写入）
bytedcli --json guardian restore get --receipt-id "<receipt-id>"
```

完整命令树、payload 字段和约束见 [Guardian 命令面](references/guardian.md)。

## Agent 规则

- 用户没有明确要求提交时，只运行预演，不得自行追加 `--yes`。
- 即使用户明确要求写入，也必须先把预演结果和 token 给用户；只有用户确认同一计划后，才使用 `--yes`。
- 看到 `GUARDIAN_WRITE_OUTCOME_UNKNOWN` 时停止，不自动重试；先读回远端状态并检查回执。
- 真实测试只在用户明确指定的隔离测试业务线中进行，不修改任何既有业务线。
- 机器读取使用 `bytedcli --json guardian ...`，且 `--json` 放在 `guardian` 前。
- 所有 ID 按字符串保存和传递；只使用 help 中存在的参数。
- 只有用户明确要求检查登录/连通性时才运行 `guardian auth status --probe`。

## 参考

- [Guardian 命令面](references/guardian.md)
- [通用调用方式](../../invocation.md)
- [Guardian 排障](references/guardian-troubleshooting.md)
