---
name: bytedance-obric-coverity
description: "Obric 内部研发工具集中的 Coverity issue 查询与 triage 更新指南。用户提供 Coverity issue URL 或 CID，要求查看源码事件链，或修改 Classification、Severity、Action、Impact、Owner、Ext. Reference、comment 时使用。"
---

# bytedcli obric coverity

使用 `bytedcli obric coverity issue` 查询 Coverity 静态扫描问题并安全更新 triage 字段。

## 查询

```bash
# CID 仅在重复时才需要 project 消歧。
bytedcli --json obric coverity issue get --cid <cid>
bytedcli --json obric coverity issue get --cid <cid> --project-name <project-name>
bytedcli --json obric coverity issue get --url '<coverity-issue-url>'
```

选择器约束：

- 恰好传一个 `--cid` 或 `--url`。
- CID 在多个项目重复时，增加一个 `--project-id` 或 `--project-name`。
- `--url` 不与 project 消歧参数组合。
- 用户提供页面 URL 时优先原样传给 `--url`。

## 更新

更新默认只生成 dry-run：

```bash
bytedcli --json obric coverity issue update \
  --cid <cid> \
  --project-name <project-name> \
  --classification Bug \
  --severity Major \
  --action 'Fix Required'
```

只有用户明确确认同一 issue 和最终值后才添加 `--yes`：

```bash
bytedcli --json obric coverity issue update \
  --url '<coverity-issue-url>' \
  --classification Intentional \
  --yes
```

提交前检查 dry-run 输出中的 `reference`、`before`、`after`、`changes` 和 `request`。
提交成功必须同时满足 `applied: true`、HTTP acceptance 成功且 `readback` 与目标值一致。

## Triage 字段

| Option             | 已观测值或语义                                                              |
| ------------------ | --------------------------------------------------------------------------- |
| `--classification` | `Unclassified`、`Pending`、`False Positive`、`Intentional`、`Bug`           |
| `--severity`       | `Unspecified`、`Major`、`Moderate`、`Minor`                                 |
| `--action`         | `Undecided`、`Fix Required`、`Fix Submitted`、`Modeling Required`、`Ignore` |
| `--impact`         | 当前已观测值：`高`                                                          |
| `--owner`          | 精确可分配用户名或 `Unassigned`                                             |
| `--ext-reference`  | 非空自由文本                                                                |
| `--comment`        | 追加到 triage history 的非空文本                                            |

枚举值只用于发现，不是全局硬编码契约。CLI 会读取目标 issue 的实时 triage 元数据；
不支持或有歧义的值会在提交前被拒绝，实际候选值见错误
`COVERITY_TRIAGE_VALUE_INVALID` 的 `details.available_values`。

清空字段：

- `--clear-ext-reference` 与 `--ext-reference` 互斥。
- `--clear-impact` 与 `--impact` 互斥。

## Agent Guidance

- 不要为了绕过 dry-run 自动添加 `--yes`。
- 不要自动重试结果未知的写请求。
- `COVERITY_ISSUE_AMBIGUOUS`：使用 `--project-id` 或 `--project-name` 消歧。
- `COVERITY_OWNER_INVALID`：从返回候选中选择一个精确用户名。
- `COVERITY_TRIAGE_NO_CHANGE`：目标值与当前值相同，无需提交。
- `COVERITY_TRIAGE_READBACK_MISMATCH`：报告不一致，不要自动重试。
- 认证复用 CN ByteDance SSO 浏览器 session；失效时运行
  `bytedcli auth login --begin --session`。

使用 `bytedcli obric coverity issue update --help` 查看当前参数。
