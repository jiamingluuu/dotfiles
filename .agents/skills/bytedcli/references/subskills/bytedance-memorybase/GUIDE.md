---
name: bytedance-memorybase
description: "Operate MemoryBase (memory layer for AI agents) via bytedcli: add/search/list/get/update/delete memories, check event status, manage config, and operate Domain Memory graph (domain/schema/entity/relation/graph/traverse resource groups: create, schema, batch-get, upsert, gremlin query, recall, rerank, export, truncate, path/khop/metapath). Use when tasks mention MemoryBase, mem0, AI agent memory, memory search, memory CRUD, graph/domain memory, or memory management."
---

# bytedcli MemoryBase

## When to use

- 为 AI Agent 添加、检索、管理记忆（memory）
- 语义搜索或关键词搜索 Agent 历史记忆
- 查看异步记忆提取任务的状态
- 批量导入记忆数据
- 管理 MemoryBase 连接配置（API key、base URL、默认 user/agent/project ID）

## 前置条件

- 需要 MemoryBase API Key：`--api-key <key>` / `MEMORYBASE_API_KEY` / `bytedcli memorybase config set --key platform.api_key --value <key>`
- 默认 API 地址为 `https://api.mem0.ai`；自建 MemoryBase 后端需通过 `--base-url` 或 `config set --key platform.base_url` 指定
- MemoryBase 后端需要 `--project-id`；mem0 兼容后端可选

## Quick start

```bash
# 配置
bytedcli memorybase config set --key platform.api_key --value <your-api-key>
bytedcli memorybase config set --key platform.base_url --value https://memorybase.example.com
bytedcli memorybase config set --key defaults.user_id --value demo-user
bytedcli memorybase config set --key defaults.project_id --value <your-project-id>

# 检查连接
bytedcli memorybase status

# 添加记忆
bytedcli memorybase add --text "用户偏好深色模式" -u demo-user --agent-id demo-agent
bytedcli memorybase add --messages '[{"role":"user","content":"我喜欢素食"}]' -u demo-user
echo "用户偏好深色模式" | bytedcli memorybase add -u demo-user

# 搜索记忆
bytedcli memorybase search --query "深色模式" -u demo-user
bytedcli memorybase search --query "偏好" --top-k 5 --threshold 0.5
bytedcli memorybase search --query "谁负责这个项目" --graph -u demo-user

# 列出 / 获取 / 更新 / 删除
bytedcli memorybase list -u demo-user --agent-id demo-agent
bytedcli memorybase get --id <memory-id>
bytedcli memorybase update --id <memory-id> --text "更新后的文本"
bytedcli memorybase delete --id <memory-id> --dry-run
bytedcli memorybase delete --id <memory-id> --force

# 异步任务状态
bytedcli memorybase event get --id <event-id>

# 批量导入
bytedcli memorybase import --file memories.json -u demo-user

# 配置管理
bytedcli memorybase config show
bytedcli memorybase config get --key platform.base_url

# Domain Memory 图谱（需 --graph 与 project_id；按 resource 分组，动词在最后一级）
bytedcli memorybase domain-memory domain create --domain demo-domain --graph
bytedcli memorybase domain-memory domain list --graph
bytedcli memorybase domain-memory schema get --graph
bytedcli memorybase domain-memory schema set --schema-file schema.json --check-only --graph
bytedcli memorybase domain-memory graph query --gremlin 'g.V().limit(10)' --graph
bytedcli memorybase domain-memory graph recall --query "谁负责这个项目" --graph
bytedcli memorybase domain-memory graph upsert --entities '[{"entity_name":"alice","entity_type":"person"}]' --graph
bytedcli memorybase domain-memory graph delete --entity-names alice --dry-run --graph
bytedcli memorybase domain-memory graph delete --entity-names alice --force --graph

# Domain Memory 图谱 · 高级查询（均固定 schema_native，需 --graph 与 project_id）
bytedcli memorybase domain-memory entity batch-get --entities '[{"entity_name":"Alice","entity_type":"Person"}]' --graph
bytedcli memorybase domain-memory relation batch-get --relations '[{"src_entity_name":"Alice","src_entity_type":"Person","relation_type":"WORKS_AT","tgt_entity_name":"Acme","tgt_entity_type":"Company"}]' --graph
bytedcli memorybase domain-memory traverse path --source Alice:Person --target Acme:Company --path-query-type all_paths --max-hop 3 --fanout 10 --graph
bytedcli memorybase domain-memory traverse khop --source Alice:Person --fanouts 5,3 --graph
bytedcli memorybase domain-memory traverse metapath --source Alice:Person --metapath '[{"relation_type":"WORKS_AT","fanout":5}]' --graph
bytedcli memorybase domain-memory graph rerank --query "senior engineers" --target-type entity --entities '[{"entity_name":"Alice","entity_type":"Person"}]' --top-k 5 --graph
bytedcli memorybase domain-memory graph export --entity-types Person,Company --all --graph
bytedcli memorybase domain-memory graph truncate --dry-run --graph

# Short-Term Memory（STM，按 resource 分组，动词在最后一级；需 --agent-id）
bytedcli memorybase stm session create --agent-id demo-agent --session-id demo-session
bytedcli memorybase stm session list --agent-id demo-agent --page 1 --page-size 20
bytedcli memorybase stm session get --agent-id demo-agent --session-id demo-session
bytedcli memorybase stm session update --agent-id demo-agent --session-id demo-session --metadata '{"topic":"demo"}'
bytedcli memorybase stm event create --agent-id demo-agent --session-id demo-session --messages '[{"role":"user","content":"hi"}]'
bytedcli memorybase stm event list --agent-id demo-agent --session-id demo-session
bytedcli memorybase stm event get --agent-id demo-agent --session-id demo-session --event-id demo-event
bytedcli memorybase stm event update --agent-id demo-agent --session-id demo-session --event-id demo-event --metadata '{"stage":"done"}'
bytedcli memorybase stm message append --agent-id demo-agent --session-id demo-session --event-id demo-event --content "hello"
bytedcli memorybase stm message query --agent-id demo-agent --session-id demo-session --page-size 50
bytedcli memorybase stm message latest --agent-id demo-agent --session-id demo-session --latest 20
bytedcli memorybase stm transfer create --agent-id demo-agent --session-id demo-session --strategy-name demo-strategy
bytedcli memorybase stm transfer status --agent-id demo-agent --session-id demo-session
bytedcli memorybase stm trim --agent-id demo-agent --session-id demo-session --max-age-hours 24
```

## Commands

| 命令                                          | 说明                                                                                     |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `memorybase add`                              | 添加记忆（`--text` / `--messages` JSON / `--file` / stdin 管道）                         |
| `memorybase search`                           | 语义或关键词搜索（`--keyword-search`），`--graph` 返回图谱实体/关系                      |
| `memorybase list`                             | 列出记忆（分页、日期过滤）                                                               |
| `memorybase get`                              | 获取单条记忆                                                                             |
| `memorybase update`                           | 更新文本或 metadata                                                                      |
| `memorybase delete`                           | 删除单条记忆（`--dry-run` 预览 / `--force` 执行）                                        |
| `memorybase event get`                        | 查看异步任务状态                                                                         |
| `memorybase import`                           | 从 JSON 文件批量导入                                                                     |
| `memorybase domain-memory domain create`      | 创建 Domain Memory 图谱 domain（需 `--graph`）                                           |
| `memorybase domain-memory domain list`        | 列出项目下的图谱 domain                                                                  |
| `memorybase domain-memory schema get`         | 查看 Domain Memory 图谱 schema                                                           |
| `memorybase domain-memory schema set`         | 设置或校验图谱 schema（`--schema` / `--schema-file` / `--check-only`）                   |
| `memorybase domain-memory entity batch-get`   | 按 key 精确批量取实体（`--entities` JSON 数组，`--return-meta`）                         |
| `memorybase domain-memory relation batch-get` | 按 key 精确批量取关系（`--relations` JSON 数组，`--return-meta`）                        |
| `memorybase domain-memory graph query`        | 用 Gremlin 查询图谱存储（别名 `gremlin`）                                                |
| `memorybase domain-memory graph recall`       | 按自然语言召回图谱实体与关系                                                             |
| `memorybase domain-memory graph upsert`       | 写入图谱实体与关系（`--file` / `--entities` / `--relations`）                            |
| `memorybase domain-memory graph delete`       | 删除图谱实体与关系（`--dry-run` 预览 / `--force` 执行）                                  |
| `memorybase domain-memory graph rerank`       | 候选实体/关系重排（`--query` / `--target-type` / `--top-k`）                             |
| `memorybase domain-memory graph export`       | 分页导出图谱（`--entity-types` / `--relation-types` / `--all` 聚合翻页）                 |
| `memorybase domain-memory graph truncate`     | 清空图谱（`--all` 循环清空 / `--dry-run` / `--force`）                                   |
| `memorybase domain-memory traverse path`      | 两点路径查询（`--source` / `--target` / `--path-query-type` / `--max-hop` / `--fanout`） |
| `memorybase domain-memory traverse khop`      | K-hop 扩展（`--source` / `--fanouts` / `--relation-types`）                              |
| `memorybase domain-memory traverse metapath`  | Metapath 关系序列遍历（`--source` / `--metapath` / 可选 `--target`）                     |
| `memorybase stm session create`               | 创建 STM 会话（`--session-id` 可省，由服务端生成）                                       |
| `memorybase stm session list`                 | 列出 STM 会话（`--limit` / `--offset` / `--page` / `--page-size`）                       |
| `memorybase stm session get`                  | 获取单个 STM 会话                                                                        |
| `memorybase stm session update`               | 更新 STM 会话 metadata                                                                   |
| `memorybase stm event create`                 | 创建 STM event（必须带消息：`--messages` / `--file` / `--content`）                      |
| `memorybase stm event list`                   | 列出会话下的 STM event                                                                   |
| `memorybase stm event get`                    | 获取单个 STM event                                                                       |
| `memorybase stm event update`                 | 更新 STM event metadata                                                                  |
| `memorybase stm message append`               | 追加 STM 消息到指定 event（`--event-id` 必填）                                           |
| `memorybase stm message query`                | 查询会话内 STM 消息（可用 `--event-id` 过滤、分页）                                      |
| `memorybase stm message latest`               | 查询最近 N 条 STM 消息（`--latest`，默认 10）                                            |
| `memorybase stm transfer create`              | 发起 STM→LTM 转存任务（`--strategy-name` 或 `--custom-strategy` 二选一）                 |
| `memorybase stm transfer status`              | 查询 STM→LTM 转存任务状态                                                                |
| `memorybase stm trim`                         | 按时间阈值裁剪 STM 消息（`--max-age-hours` 必填）                                        |
| `memorybase config show`                      | 显示当前配置                                                                             |
| `memorybase config get`                       | 获取指定配置项                                                                           |
| `memorybase config set`                       | 设置配置项                                                                               |
| `memorybase status`                           | 检查 API 连接状态                                                                        |

## 通用参数

| 参数                 | 环境变量                | 说明                              |
| -------------------- | ----------------------- | --------------------------------- |
| `--api-key <key>`    | `MEMORYBASE_API_KEY`    | API 密钥                          |
| `--base-url <url>`   | `MEMORYBASE_BASE_URL`   | API 地址                          |
| `-u, --user-id <id>` | `MEMORYBASE_USER_ID`    | 用户 ID                           |
| `--agent-id <id>`    | `MEMORYBASE_AGENT_ID`   | Agent ID                          |
| `--project-id <id>`  | `MEMORYBASE_PROJECT_ID` | Project ID（MemoryBase 后端必填） |
| `--app-id <id>`      | `MEMORYBASE_APP_ID`     | 应用 ID                           |
| `--run-id <id>`      | `MEMORYBASE_RUN_ID`     | 运行 ID                           |

优先级：命令行参数 > 环境变量 > `~/.memorybase/config.json` > 默认值

## Agent Guidance

- `add` 默认异步处理，返回 `event_id`，用 `event get --id <event_id>` 查状态
- `add` 无 `--text`/`--messages`/`--file` 时读取 stdin 管道内容作为记忆文本（`echo "..." | ... add`）
- 搜索默认语义搜索，`--keyword-search` 切换关键词搜索
- `--graph` 开启图谱搜索，JSON 返回 `{results, entities, relations}`，文本/表格追加 Graph Entities / Graph Relations 段（需后端项目开启 graph options）
- `delete --dry-run` 仅预览不执行，`--force` 才真正删除
- `--threshold 0.5` 过滤低相似度结果（0-1）
- `--no-infer` 跳过 AI 推理，直接存储原文（仅设置 `infer=false`）
- `--sync` 禁用异步处理，等待结果返回（仅设置 `async_mode=false`）；可与 `--no-infer` 组合使用
- 导入文件为 JSON 数组，每项支持 `text`、`memory` 或 `messages` 字段
- 所有命令支持 `-j` 输出 JSON
- MemoryBase 后端（`org_id` 为空）会自动检测并要求 `--project-id`
- `domain-memory`（别名 `knowledge-memory`）是图记忆子系统：当前仅支持 graph 类型，所有子命令必须加 `--graph`，且必须提供 `--project-id`（或配置 `defaults.project_id`）
- `domain-memory` 按 resource 分组，动词在最后一级：`domain create|list`、`schema get|set`、`entity batch-get`、`relation batch-get`、`graph upsert|delete|export|truncate|query(gremlin)|recall|rerank`、`traverse path|khop|metapath`
- `domain-memory` 走 `memory_layer=domain, memory_type=graph`；`--graph-schema-version` 目前仅接受空或 `schema_native`
- `domain-memory schema set` 用 `--schema` 传 JSON 字符串或 `--schema-file` 传文件，二选一；`--check-only` 仅校验不写入
- `domain-memory graph recall` 默认按语义召回图谱实体/关系；`--option` 可传 JSON 形式的召回选项
- `domain-memory graph upsert` 写入图谱：`--file` 传整份 subgraph JSON，或用 `--entities` / `--relations` 传 JSON 数组，二选一；内部固定 `infer=false`
- `domain-memory graph delete` 删除图谱实体/关系：支持 `--entity-names`（逗号或 JSON 数组）、`--entities`、`--relations`、`--auto-delete-related-relations`；`--dry-run` 预览、`--force` 才真正执行
- 高级查询（`entity batch-get` / `relation batch-get` / `traverse path|khop|metapath` / `graph rerank|export|truncate`、`domain list`）服务端固定要求 `schema_native`，命令内部自动 pin，无需手传 `--graph-schema-version`
- 实体 key 参数（`--source` / `--target`）支持 `name:type` 简写或 `{"entity_name":..,"entity_type":..}` JSON 对象；`--fanouts` 支持逗号分隔或 JSON 数组，长度即遍历跳数
- `graph export --all` 自动跟随 `next_cursor` 翻页并把所有页聚合成**单个** JSON 结果；`graph truncate --all` 循环单步清空直到 `finished=true` 并聚合成单个 JSON，`--dry-run` 预览、`--force` 才执行（遵守每命令一个 JSON 输出契约）
- `graph rerank` 不做召回也不做图遍历：`--target-type entity` 传 `--entities`、`--target-type relation` 传 `--relations`，`--top-k` 必须大于 0
- `stm` 是短期记忆子系统，按 resource 分组、动词在最后一级：`session create|list|get|update`、`event create|list|get|update`、`message append|query|latest`、`transfer create|status`，外加会话级 `trim`
- `stm` 所有命令都需要 `--agent-id`（或环境变量 / 配置默认值），除 `session create|list` 外还需要 `--session-id`
- `stm message append` / `event create` 三种传消息方式互斥且按优先级取：`--messages` JSON 数组 > `--file` JSON 文件 > `--role`+`--content` 单条；`--role` 缺省为 `user`；两者都**至少要有一条消息**
- `stm message append` 的 `--event-id` **必填**：服务端要求消息必须挂在某个 event 上，先用 `stm event create` 拿到 event_id 再 append
- `stm message query` 走普通列表接口，`stm message latest` 走 `/messages/query/latest` 并额外传 `--latest`（默认 10）
- `stm message latest` **不支持** `--event-id`：服务端禁止 `event_id` 与 `latest` 同时出现；要按 event 过滤请改用 `stm message query --event-id`
- STM 列表命令统一只用标准分页参数 `--page`（默认 1）/ `--page-size`（默认 20），不暴露 `--limit` / `--offset`
- `stm transfer create` 必须且只能给 `--strategy-name` 或 `--custom-strategy` 之一；`--custom-strategy` JSON 里必须带非空 `strategy_name`，`type` 只接受 `native` 或 `graph`；Citus 后端项目还要求 `--user-id`；`--dry-run` 只预览不落长期记忆
- `stm transfer create` 对同一 session/event 是幂等的：已有排队或运行中的任务会直接复用并在结果里回传 `reused=true`
- `stm trim` 目前只支持 `--strategy time_based`（默认值），`--max-age-hours` 必填且必须为正整数

## References

- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
