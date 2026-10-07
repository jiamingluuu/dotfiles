# bytedcli labelgpt agent version

只读查询 Agent 历史版本，或将某个精确版本的完整工作流图安全导出到新文件。本命令组不恢复版本、不修改备注，也不创建草稿。

## 列出历史版本

```bash
bytedcli labelgpt agent version list --id <AGENT_ID> --format raw
```

- `--id` 必须是正整数 Agent ID。
- 版本按 newest-first 返回。
- `version_id` 是后续查询使用的稳定选择器；不要用 `display_version`、序号或 `latest` 代替。
- 输出包含 `agent_id`、`versions` 和 `total`。每项包含版本 ID、展示版本、来源版本、是否生效、创建信息、备注及引用计数。
- `-o <DIR>` 写入 `agent_versions_<AGENT_ID>.json`。

## 查看精确版本

```bash
bytedcli labelgpt agent version view --id <AGENT_ID> --version-id <VERSION_ID> --format raw
bytedcli labelgpt agent version view --id <AGENT_ID> --version-id <VERSION_ID> \
  --file ./agent-version-graph.json -o ./out --format raw
```

- `--version-id` 必须逐字使用 `version list` 返回的精确 `version_id`，按不透明字符串处理；不要自行把展示标签（例如 `V3`）、序号或 `latest` 转换成其他值。
- 默认输出安全摘要，包括版本元数据和输入、输出、节点、边数量；不包含工作流图内容。
- `--file <PATH>` 额外导出完整工作流图。文件顶层直接包含 `nodes` 和 `edges`，可作为 `agent workflow save --graph-file` 的输入。
- 图文件可能包含节点常量或凭据，权限为 `0600`；目标路径已存在时命令失败，不覆盖。
- `--file` 与全局 `-o <DIR>` 可同时使用：前者写完整图，后者写安全摘要。
- 任何模式下遇到空图、非法图、缺少顶层 `nodes/edges` 或响应版本不一致，命令都 fail closed；不会输出摘要，也不会写图文件。
- `-o <DIR>` 的摘要文件名为 `agent_version_<VERSION_ID>.json`。

两个叶子均按 Agent ID 定位，不强制要求 `space-id`；显式提供时仍会转发。

## Schema

```bash
bytedcli labelgpt schema agent version list --format raw
bytedcli labelgpt schema agent version view --format raw
```
