# Dolphin CLI Reference

## Commands

- 用例写入（`event testcase` 与 `group testcase` 的 create / update / delete）走 `/open_api/v2/testcase/*`，写之前 CLI 会按 `--event-id` / `--group-id` 查出所属事件或规则组：
  - create / update 的 body 只写用例内容（`input`、`expect`、`scope`、`description` 等）；CLI 补进 `bizline_id`、`event_id`（规则组命令还有 `group_id`，update 还有用例 `id`），body 里自带的 id 与参数不一致会直接报错。update 按完整用例内容传，后端会校验 `input` 等必填字段。
  - delete 没有 body，CLI 把 `bizline_id` 作为 query 带上。
  - update / delete 前会确认 `--testcase-id` 属于该规则组（`group testcase`），或是该事件的事件级用例（`event testcase`，scope 1）；不属于就报 `DOLPHIN_TESTCASE_NOT_FOUND`，不会发出写请求。组级用例用 `group testcase` 命令写。
  - 写接口成功时不回数据：create 输出里的 `id` 为 `null`，要拿新用例 id 就再跑一次 `testcase list`。

### event

- `bytedcli dolphin event get --event-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event create [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event update --event-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event delete --event-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event groups --event-id <id> [--pattern <kw>] [--page N] [--page-size N] [--with-rules] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event vars --event-id <id> [--need-ref-info] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event var create --event-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event var update --event-id <id> --factor-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event var delete --event-id <id> --factor-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event params --event-id <id> [--need-ref-info] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event param create --event-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event param update --event-id <id> --factor-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event param delete --event-id <id> --factor-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event testcases list --event-id <id> --bizline-id <id> [--scope 0|1] [--env-name <name>] [--draft-user <prefix>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event testcase check [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event testcase create --event-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event testcase update --event-id <id> --testcase-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin event testcase delete --event-id <id> --testcase-id <id> [--env prod|boe|i18n-bd|i18n-tt]`

### factor

- `bytedcli dolphin factor name-list list --factor-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin factor name-list add --event-id <id> --factor-id <id> (--item <value>...|--items-file <path>) --auditor <username> [--remark <text>] [--env prod|boe|i18n-bd|i18n-tt]`
- `add` 只接受 `f_type=nl` 的 factor，并通过 event 元数据派生 `bizline_id`；已有的完全相同条目不会重复提交。
- `add` 会直接提交官方 OpenAPI，不提供 `--yes` 或默认 dry-run。提交前必须确认目标和名单语义；返回 workflow 时表示待审批，不表示立即生效。
- `--auditor` 是业务审核人，不是当前登录调用人；必须显式传入。

### group

- `bytedcli dolphin group get --group-id <id> [--with-rules] [--with-template] [--with-testcases] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group create [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group update --group-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group delete --group-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group deploy --group-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group testcases --group-id <id> [--env-name <name>] [--user-draft <prefix>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group testcase create --group-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group testcase update --group-id <id> --testcase-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group testcase delete --group-id <id> --testcase-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group factors --group-id <id> [--need-ref-info] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group feature-env --group-id <id> --env-name <name> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group history get --group-id <id> --version <n> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin group history list --group-id <id> [--page N] [--page-size N] [--env prod|boe|i18n-bd|i18n-tt]`

### feature-env（泳道）

- `bytedcli dolphin feature-env list [--type global|event|group|factor|strategy|decision-table|group-sort] [--bizline-id <id>] [--event-id <id>] [--group-id <id>] [--factor-id <id>] [--strategy-id <id>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin feature-env create --bizline-id <id> --env-name <name> [--type ...] [--event-id <id>] [--group-id <id>] [--factor-id <id>] [--strategy-id <id>] [--expire-days N|--expire-time <unix|ISO>] [--base-version <version>] [--description <text>] [--yes] [--env ...]`
- `bytedcli dolphin feature-env rule update --bizline-id <id> --event-id <id> --group-id <id> --env-name <name> --rules-file <path> [--yes] [--env ...]`
- `bytedcli dolphin feature-env deploy --bizline-id <id> --event-id <id> --group-id <id> --env-name <name> --auditor <username>... [--release-mode full|canary] [--grey-type instance-stage|custom-key|percent|precise-fuse] [--grey-key <k>] [--grey-ratio <n>] [--grey-value <v>]... [--grey-verify-key <k>] [--remark <text>] [--yes] [--env ...]`
- `bytedcli dolphin feature-env diff --group-id <id> --env-name <name> [--env ...]`
- `--type` 默认 `group`。`create` 每种类型需要的资源 id：`global`/`event`/`group-sort` 要 `--event-id`；`group`/`decision-table` 要 `--event-id` + `--group-id`；`factor` 要 `--factor-id`（`--event-id` 可选）；`strategy` 要 `--strategy-id`。
- `list` 的 `--bizline-id` 只有 `global`/`event`/`strategy` 需要，其余类型不传。
- `--env-name` 传裸名即可，CLI 按 `--env` 补 `ppe_`/`boe_` 前缀。前缀匹配大小写不敏感，输出时前缀统一小写（`PPE_demo` → `ppe_demo`），前缀之后保持原样；传另一个环境的前缀会直接报错，不会拼成 `boe_ppe_xxx`。创建类命令要求裸名仅含字母、数字、下划线，查询类命令不做该校验。该规则在 dolphin 全域一致，`group feature-env get`、`group testcase list`、`event testcase list` 同样适用。
- `--expire-days` 与 `--expire-time` 二选一，都不传时按 14 天；上限 60 天（与控制台一致）。`--expire-time` 接受 unix 秒或 ISO 时间。
- `--base-version` 不作用于 `--type factor`，显式传会报错。同名泳道创建直接报 `9201`，没有覆盖参数。
- `create` 与 `rule update` 默认 dry run，只打印 payload；加 `--yes` 才提交。
- `rule update` 全量替换该泳道的规则快照；`--rules-file` 需要完整规则数组。
- `create` 输出里的 `surface` 说明这次走的是哪层接口：`group`/`factor` 走 `/open_api/v2/*_feature_env/*`，其余类型只有控制台 `/api/v2/feature_env/*` 有。
- `list` 在 OpenAPI 类型（`group`/`factor`）下只回泳道名，creator 与过期时间列显示 `-`。
- `diff` 比较线上规则与泳道规则（含 `decision_config`），输出 `online-only` / `lane-only` / `changed` 三类差异，用来确认改动确实落在泳道。
- `deploy` 新增 `--force`：`version_conflict` 为真时 `--yes` 会被拒绝，确认要覆盖线上较新规则时才加 `--force`。
- `deploy` 开一张上线工单把泳道发到线上，**不是直接上线**：Dolphin 没有直连写接口，具名审核人通过后才生效。`--auditor` 必填，可重复或逗号分隔。`--release-mode canary` 时必须带 `--grey-type`。
- `deploy` 默认 dry run，只打印将要提交的工单 payload；JSON 输出带 `confirmation_required: true` 与 `confirmation_prompt`，text 输出在 payload 后打印同一段提示。**Agent 必须把 payload 给用户看、拿到明确确认后才允许加 `--yes`。**
- `deploy` 提交前会用**泳道规则跑规则组的线上用例**（`testcase_check`）：`all_match` 为假时 dry run 列出失败用例，`--yes` 直接拒绝提交并抛 `DOLPHIN_TESTCASE_CHECK_FAILED`。失败用例附带 `pre_existing`（线上规则是否也挂），只作参考，不参与判定。泳道持有独立的用例副本，线上改了用例期望不会同步过去。后端开工单时也有单测门禁，只回一句「单元测试未通过」不说哪条，且它用哪一份用例尚未实测确认：CLI 门禁通过而后端仍拒绝时，先用 `bytedcli dolphin group testcase list --group-id <id> --env-name <lane>` 对比泳道副本与线上用例的 `expect`。
- `deploy` 输出里的 `version_conflict` 为真表示泳道所基于的版本已不是当前线上版本，发布会用泳道规则覆盖线上；先跑 `diff` 看清差异。

### rule

- `bytedcli dolphin rule get --rule-id <id> [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin rule create [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin rule update --rule-id <id> [--body <json>|--body-file <path>] [--env prod|boe|i18n-bd|i18n-tt]`
- `bytedcli dolphin rule delete --rule-id <id> [--env prod|boe|i18n-bd|i18n-tt]`

### raw API fallback

- `bytedcli dolphin api execute --method <GET|POST|PUT|PATCH|DELETE> --path <path> [--query key=value]... [--body <json>|--body-file <path>] [--unwrap] [--env prod|boe|i18n-bd|i18n-tt]`
- `--path` must start with `/open_api/` and is relative to the Dolphin host, for example `/open_api/v2/group/123`.
- Use `--unwrap` when the endpoint returns the standard Dolphin `{code,message,data}` envelope and you want only `data` in the result.
- Prefer semantic subcommands for modeled operations; use this fallback only for Dolphin page/API operations that are not yet modeled.

## Output

- 默认文本模式输出表格。
- 全局 `--json` 时输出结构化 JSON（注意必须放在 `dolphin` 前面）。
- 写操作统一复用 bytedcli 登录态和 Dolphin `x-jwt-token`。

## Invocation

统一使用：

```bash
bytedcli <command> [options]
```

示例：

```bash
bytedcli dolphin event get --event-id 12345
```
