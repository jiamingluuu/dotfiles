---
name: bytedance-dolphin
description: "Operate Dolphin (dynamic decision platform) via bytedcli's built-in commands with bytedcli auth: inspect and mutate events, rule groups, rules, event vars/params, factor name-list items, feature envs (泳道) including create/list/rule write/diff and opening the lane-to-production approval ticket (deploy), testcases, deployments, and raw Dolphin API paths. Use when tasks mention Dolphin, event_id/group_id/rule_id/factor_id, rule group history, name-list factors, feature env, 泳道, ppe_/boe_ lane, check_testcases, settings/configuration, create/update/delete/deploy/publish operations, or Dolphin console URLs."
---

# bytedcli Dolphin（动态决策平台）

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

- 查询 Dolphin 的 **事件（event）**、**规则组（group）**、**规则（rule）**。
- 查询名单型 factor 的条目，或向名单增量追加条目。
- 创建、更新、删除 Dolphin event / group / rule / var / param / testcase，或部署规则组。
- 查看某个 **feature env（泳道）** 下的规则组规则（环境差异）。
- 新建泳道、列出某个资源的泳道、把规则写进泳道、对比泳道与线上的规则差异。
- 为泳道开上线工单（`feature-env deploy`），由具名审核人审批后才生效。
- 列出测试用例或执行 `check_testcases` 并拿到结构化结果。
- 已有语义命令覆盖时，优先使用 `dolphin event|group|rule ...`；只有需要复现尚未建模的 Dolphin OpenAPI 接口时，才使用内建 `dolphin api execute`，它复用 bytedcli 登录态且仅接受 `/open_api/` 路径。

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `dolphin event`, `dolphin factor`, `dolphin group`, and `dolphin rule`. Within these groups, subcommands follow the `<resource> <verb>` pattern (e.g. `event group list`, `event var list`, `factor name-list add`, `group factor list`). Old flat names (e.g. `dolphin event groups`, `dolphin event vars`, `dolphin event params`, `dolphin group factors`, `dolphin group testcases`) still work as hidden aliases.

```bash
# 事件元信息
bytedcli dolphin event get --event-id 12345

# 事件下规则组列表
bytedcli dolphin event group list --event-id 12345 --page-size 10

# 事件变量列表
bytedcli dolphin event var list --event-id 12345

# 事件参数列表
bytedcli dolphin event param list --event-id 12345

# 查询名单型 factor 的全部条目
bytedcli dolphin factor name-list list --factor-id 23456

# 增量追加名单条目；命令会直接提交，auditor 是业务审核人
bytedcli dolphin factor name-list add \
  --event-id 12345 \
  --factor-id 23456 \
  --item 'sample-entry' \
  --auditor sample.reviewer \
  --remark 'sample change'

# 查询规则组详情（可选带 rules/testcases/template）
bytedcli dolphin group get --group-id 67890 --with-rules --with-testcases

# 查询 feature env 下的规则组规则
bytedcli dolphin group feature-env get --group-id 67890 --env-name demo_env

# 列出某个规则组已有的泳道
bytedcli dolphin feature-env list --type group --group-id 67890

# 新建规则组泳道；不带 --yes 只打印 payload，不提交
bytedcli dolphin feature-env create --type group \
  --bizline-id 23456 --event-id 12345 --group-id 67890 \
  --env-name demo_env --expire-days 14 --description 'sample lane'
bytedcli dolphin feature-env create --type group \
  --bizline-id 23456 --event-id 12345 --group-id 67890 \
  --env-name demo_env --expire-days 14 --yes

# 把规则写进泳道（全量替换该泳道快照）；同样不带 --yes 只预览
bytedcli dolphin feature-env rule update \
  --bizline-id 23456 --event-id 12345 --group-id 67890 \
  --env-name demo_env --rules-file ./sample-lane-rules.json --yes

# 确认改动真落在泳道：对比泳道与线上规则
bytedcli dolphin feature-env diff --group-id 67890 --env-name demo_env

# 把泳道发到线上：开上线工单。不带 --yes 只打印工单 payload
bytedcli dolphin feature-env deploy \
  --bizline-id 23456 --event-id 12345 --group-id 67890 \
  --env-name demo_env --auditor demo-user --remark 'sample change'

# 规则组 factor 列表
bytedcli dolphin group factor list --group-id 67890

# 列出 event 级测试用例（scope=1）
bytedcli dolphin event testcase list --event-id 12345 --bizline-id 23456 --scope 1

# 执行 check_testcases（body 较复杂，推荐用 --body-file）
bytedcli dolphin event testcase check --body '{"bizline_id":1,"event_id":12345,"test_case_id":10001}'

# 创建 / 更新 / 删除事件、规则组、规则
bytedcli dolphin event create --body-file ./sample-event.json
bytedcli dolphin group update --group-id 67890 --body-file ./sample-group.json
bytedcli dolphin rule delete --rule-id 11111

# 部署规则组
bytedcli dolphin group deploy --group-id 67890 --body-file ./sample-deploy.json

# 未显式建模的 Dolphin OpenAPI 接口：走内建 API 请求兜底；已建模操作优先用上面的语义命令
bytedcli --json dolphin api execute --method POST --path /open_api/v2/group/67890/deploy --body-file ./sample-deploy.json --unwrap
```

## Notes

- 默认输出文本表格；需要机器可读输出时加全局 `--json`（必须放在 `dolphin` 前面）。
- `--env` 仅用于 Dolphin 模块（`prod|boe|i18n-bd|i18n-tt`），不等同于 bytedcli 的全局 `--site`。`--site i18n-bd` 时默认 env 自动切到 `i18n-bd`。
- 写操作和 `check_testcases` 入参建议用 `--body-file`，避免命令行转义问题；示例 JSON 使用 `sample-*` 占位值，不要写真实线上配置。
- `factor name-list add` 是官方 OpenAPI 的增量追加操作，会直接提交；执行前确认 event/factor、名单语义、条目值和 `--auditor`。可重复传 `--item`，或改用 `--items-file`（每行一项），两者不能同时使用。
- 名单条目被在线规则引用时，成功响应可能是待审批工作流；此时不代表条目已经生效。CLI 只接收最终条目文本，不负责按业务字段拼接名单 key。
- 执行 delete / deploy 前必须先与用户确认目标 `env`、资源 ID 和影响范围；仅当用户在当前任务中已经明确要求删除或发布同一资源时才继续执行。
- `event|group testcase create/update/delete` 走 `/open_api/v2/testcase/*`，写之前 CLI 会按 `--event-id` / `--group-id` 查出所属事件或规则组：
  - create / update 的 body 只写用例内容（`input`、`expect`、`scope`、`description` 等）；CLI 补进 `bizline_id`、`event_id`（规则组命令还有 `group_id`，update 还有用例 `id`），body 里自带的 id 与参数不一致会直接报错。update 按完整用例内容传，后端会校验 `input` 等必填字段。
  - delete 没有 body，CLI 把 `bizline_id` 作为 query 带上。
  - update / delete 前会确认 `--testcase-id` 属于该规则组（`group testcase`），或是该事件的事件级用例（`event testcase`，scope 1）；不属于就报 `DOLPHIN_TESTCASE_NOT_FOUND`，不会发出写请求。组级用例用 `group testcase` 命令写。
  - 写接口成功时不回数据：create 输出里的 `id` 为 `null`，要拿新用例 id 就再跑一次 `testcase list`。

## 泳道（feature env）Agent Guidance

- **泳道是覆盖层，不是环境副本**：规则按 `(资源, env_name)` 覆盖，请求带上泳道标识才读到覆盖版本。线上改规则要走 `feature-env deploy` 工单 + 审批人；泳道直接写、免审批，约 1 分钟缓存生效。所以"先在泳道验证、验完再提线上工单"是常规做法。
- **泳道列表字段随接口而异**：`--type group` / `factor` 走 OpenAPI，只回泳道名，creator 与过期时间显示为 `-`；控制台类型（`global` 等）才有完整字段。
- **`--env-name` 只写裸名**：dolphin 全域统一——`feature-env *`、`group feature-env get`、`group testcase list`、`event testcase list` 都按 `--env` 自动补前缀（`boe` 补 `boe_`，其余补 `ppe_`）。前缀匹配大小写不敏感，**输出时前缀统一为小写**（`PPE_demo` → `ppe_demo`），前缀之后的部分大小写原样保留。传错环境的前缀直接报错。创建泳道时裸名只允许字母、数字、下划线；查询类命令不做该字符集校验。
- **env_name 必须和服务侧实际部署的泳道对得上**，否则请求打不到覆盖版本。
- **泳道有有效期**：`--expire-days` 与 `--expire-time` 二选一，都不传按 14 天，最长 60 天（与控制台一致）。过期泳道会失效。
- **同名泳道会报 `9201 泳道环境名称重复了`**：没有覆盖路径。不要用 `create` 去改已有泳道，改规则用 `rule update`；要换一套内容就换 `--env-name`，或先在控制台删掉旧泳道。
- **`rule update` 是全量替换**该泳道的规则快照，不是增量追加；`--rules-file` 要给完整规则数组。
- **写操作默认 dry run**：`create` 和 `rule update` 不带 `--yes` 时只打印将要提交的 payload。
- **`deploy` 开的是工单，不是直接上线**：Dolphin 没有「泳道直接发线上」的接口，唯一路径是开工单给具名审核人。`--auditor` 必填。审核人通过后才生效。
- **`deploy` 需要用户二次确认**：默认 dry run 打印完整工单 payload，JSON 输出带 `confirmation_required` 与 `confirmation_prompt`。加 `--yes` 前必须把 payload 给用户看并拿到明确确认，不要自行判断。
- **`deploy` 有单测门禁**：CLI 提交前用**泳道规则跑规则组的线上用例**，挂了就拒绝 `--yes` 并列出失败用例；「线上是否也挂」只是附注，不参与判定。泳道持有独立的用例副本，线上改了用例期望不会同步过去。后端开工单时也有单测门禁，只回「单元测试未通过」不说哪条，且它用的是哪一份用例尚未实测确认：若 CLI 门禁通过而后端仍拒绝，先用 `bytedcli dolphin group testcase list --group-id <id> --env-name <lane>` 对比泳道副本与线上用例的 `expect`。
- **`deploy` 前先跑 `diff` 看清差异**：`deploy` dry run 输出里的 `version_conflict` 为真说明泳道基于的版本已落后于线上，发布会覆盖线上较新的规则；此时 `--yes` 会被拒绝，确认无误再加 `--force`。
- **改完必须校验**：`bytedcli dolphin feature-env diff --group-id <id> --env-name <lane>` 给出线上/泳道条数与逐条差异（含 `decision_config`），比翻 UI 可靠；要看泳道全量快照用 `dolphin group feature-env get --group-id <id> --env-name <lane>`。
- **泳道验完 ≠ 上线**：线上生效仍需重新提交规则组工单并等待审批。
- `--type` 支持 `global`（事件级全局泳道，对应控制台「泳道管理」的新建泳道）、`event`、`group`、`factor`、`strategy`、`decision-table`、`group-sort`；不同类型需要的资源 id 不同，缺参数时错误信息会指明该传哪个 `--*-id`。`list` 的 `--bizline-id` 只有 `global`/`event`/`strategy` 用得上。

## References

- `references/dolphin.md`
- `../../invocation.md`
- `../../troubleshooting.md`
