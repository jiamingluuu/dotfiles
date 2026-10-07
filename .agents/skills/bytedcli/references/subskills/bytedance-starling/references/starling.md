# bytedcli starling 命令速查

优先用 `bytedcli --json starling ...` 调用 Starling 能力。

## 凭据配置

```bash
bytedcli starling auth config --access-key <ak> --secret-key <sk>
bytedcli starling auth status
```

## Shortcut 命令（推荐）

| 资源     | 常用命令                                                                                                                                         |
| -------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| 项目     | `project +list`、`project +info --project-id <id>`、`project +create --yes`、`project +search --keyword <kw>`                                    |
| 空间     | `namespace +list --project-id <id>`、`namespace +info --namespace-id <id>`                                                                       |
| 翻译 Key | `key +list --namespace-id <id>`、`key +info`、`key +create --yes`、`key +update --yes`、`key +export`、`key +import --yes`、`key +import-status` |
| 任务     | `task +list --project-id <id>`、`task +info --task-id <id>`、`task +create --yes`、`task +update --yes`、`task +add-source --yes`                |
| 译文     | `target +list --namespace-id <id>`、`target +update --yes`、`target +download`                                                                   |
| 发布     | `release +release --yes`、`release +status --ticket-id <id>`                                                                                     |
| 文档项目 | `doc-project +list`、`doc-project +info`、`doc-project +create --yes`、`doc-project +search`                                                     |
| 文档任务 | `doc-task +list`、`doc-task +info`、`doc-task +create --yes`、`doc-task +template-list`                                                          |
| 工作流   | `workflow +list --project-id <id>`、`workflow +create --yes`、`workflow +update --yes`                                                           |

> 写操作（`+create`、`+update`、`+delete`、`+release` 等）需要加 `--yes` 确认。

## 按条件筛选发布

Starling 发布页中的 Key、操作类型、所属任务、所属空间、创建者、最近操作人和操作时间，可直接传给内置 OpenAPI 发布命令。数组参数支持重复传入或使用逗号分隔；操作类型取值为 `create`、`update`、`delete`。

```bash
bytedcli --json starling release publish \
  --project-id <project-id> \
  --namespace-id <namespace-id> \
  --locale zh \
  --search-key welcome,dialog \
  --operation-type create,update \
  --task-id <task-id> \
  --filter-namespace-id <namespace-id> \
  --operator <user-name> \
  --creator <user-name> \
  --operator-time <start-timestamp>,<end-timestamp> \
  --yes
```

带筛选发布必须显式传 `--yes`，且不能与显式 `--key`/`--keys-lang-maps-*` 混用。发布前可用 `release list-pending` 搭配相同的 Key、任务、操作人、创建者、操作时间和操作类型筛选预览命中文案。

## 飞书表格直接导入

```bash
# 默认仅预览并取消临时导入记录，不写入空间
bytedcli --json starling project lark-sheet import \
  --project-id <project-id> \
  --namespace-id <namespace-id> \
  --lark-sheet-url "https://example.larkoffice.com/sheets/xxx"

# 确认预览后导入；发布仍是独立操作
bytedcli --json starling project lark-sheet import \
  --project-id <project-id> \
  --namespace-id <namespace-id> \
  --lark-sheet-url "https://example.larkoffice.com/sheets/xxx" \
  --yes
```

该命令把表格文案导入普通文案空间，不会创建文档翻译任务。多页表格可重复传 `--sheet <name>`。

## API Runner（兜底）

shortcuts 未覆盖的接口，用 API Runner 直接调用：

```bash
# 查找 API
bytedcli --json starling api-list --search "rollback"
bytedcli starling api-schema /project/distributions/rollback

# 执行
bytedcli --json starling api GET /project/members --params '{"projectId":123}'
bytedcli --json starling api POST /project/distributions/rollback --data '{"projectId":123,"namespaceId":456,"batchVersion":"1.0.0"}'
bytedcli --json starling api POST /project/release/retry --data '{"projectId":123,"namespaceId":456,"batchVersion":"1.0.0"}'
bytedcli --json starling api GET /project/release/versions --params '{"projectId":123,"namespaceId":456}'
bytedcli --json starling api GET /project/release/conflict/check --params '{"projectId":123}'
bytedcli --json starling api GET /businesslines --params '{"offset":0,"limit":25}'
```

## 搜索

```bash
bytedcli --json starling search docs --query "how to import translation keys"
bytedcli --json starling search knowledge --query "语种配置"
```

## 工具

```bash
bytedcli starling doctor
bytedcli starling agent-guide
bytedcli starling schema key +create
bytedcli starling upgrade
```

## 常见流程

1. `bytedcli starling auth status` — 确认凭据
2. `bytedcli starling project +list` — 获取项目列表
3. `bytedcli starling namespace +list --project-id <id>` — 获取空间列表
4. `bytedcli starling key +list --namespace-id <id>` — 列出翻译 Key
5. `bytedcli starling key +create --namespace-id <id> --key-name demo.title --yes` — 新建 Key
6. `bytedcli starling task +create --project-id <id> --name demo-task --namespace-id <id> --target-lang zh --yes` — 新建任务
7. `bytedcli starling release +release --namespace-id <id> --locale zh --yes` — 发布
8. `bytedcli starling release +status --ticket-id <id>` — 查询发布状态
