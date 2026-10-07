# bytedcli labelgpt update

`update` 用于更新 CLI，并同步对应的 `bytedcli labelgpt` skill。

## 快速导航

- [update](#update)：更新 CLI，并同步名为 `bytedcli labelgpt` 的基础 skill。
- [update skill](#update-skill)：只同步名为 `bytedcli labelgpt` 的基础 skill。
- [Schema 查询索引](#schema-查询索引)：查询更新命令契约。

## update

更新 CLI 到最新版本或指定版本。版本已匹配时可以跳过更新；CLI 更新后只同步名为
`bytedcli labelgpt` 的基础 skill。

### 用法

```bash
bytedcli labelgpt update [选项]
```

### 示例

```bash
bytedcli labelgpt update
bytedcli labelgpt update --version v0.1.0
bytedcli labelgpt update --force
bytedcli labelgpt update --format raw
```

### 参数说明

- `-h, --help`：显示帮助信息并退出。
- `--version <version>`：指定要安装的 CLI 版本；不传时更新到 latest。
- `--force`：强制更新 CLI 并同步 skill。

### 输出

`raw/json` 输出字段：

- `current_version`：当前运行的 CLI 版本。
- `target_version`：解析后的目标版本。
- `updated`：是否完成 CLI 更新。
- `path`：当前安装的二进制路径。
- `skill`：skill 同步结果，包含：
  - `target_version`：目标 CLI 版本。
  - `status`：`updated`、`skipped` 或 `failed`。
  - `updated`：本次是否执行并成功完成同步。
  - `skill_name`：安装的 skill 名称。
  - `error`：同步失败信息，成功或跳过时省略。

### 输出文件

- `-o <DIR>`：写入 `update.json`。

### 注意事项

- skill 同步失败不会撤销已完成的 CLI 更新；结果中的 `skill.status` 会标记为 `failed`。
- 进度和恢复提示写 stderr；`raw/json` stdout 只包含最终 JSON 结果。

## update skill

单独同步平台托管、名为 `bytedcli labelgpt` 的基础 skill。

### 用法

```bash
bytedcli labelgpt update skill [选项]
```

### 示例

```bash
# 安装平台托管的 bytedcli labelgpt skill
bytedcli labelgpt update skill

# 强制同步平台托管的 bytedcli labelgpt skill
bytedcli labelgpt update skill --force

# 输出结构化结果
bytedcli labelgpt update skill --format raw
```

### 参数说明

- `-h, --help`：显示本子命令帮助信息并退出。
- `--force`：强制执行 skill 同步。

### 输出

`raw/json` 输出字段：

- `target_version`：目标 CLI 版本。
- `status`：`updated`、`skipped` 或 `failed`。
- `updated`：本次是否执行并成功完成同步。
- `skill_name`：安装的 skill 名称。
- `error`：同步失败信息，成功或跳过时省略。

### 输出文件

- `-o <DIR>`：写入 `update_skill.json`。

### 注意事项

- 直接执行 `update skill` 时，同步失败返回非零退出码。
- 同步失败时，按 stderr 中的恢复提示处理。

## Schema 查询索引

```bash
bytedcli labelgpt schema update --format raw
bytedcli labelgpt schema update skill --format raw
```
