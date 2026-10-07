# 命令参考文档

所有能力都由 `bytedcli d2c` 命令提供，请使用 `Bash` 工具执行。

## 1. 发起任务 `d2c segment create`

- **功能**：发起 D2C 视觉切分任务。
- **返回**：`{ success: true, taskId, message }`。

**用法：**

```bash
bytedcli --json d2c segment create \
  --figma-url "https://www.figma.com/design/demoFileKey/demo-page?node-id=123-456" \
  --transform-type "lynx" \
  --repo-name "example/demo-repo" \
  --creator "your.email.prefix" \
  --config '{"unit":"rpx"}'
```

**参数：**

| 参数 | 必需 | 说明 |
|------|------|------|
| `--figma-url` | ✅ | Figma design 链接，原样传递，不要截断 query / hash |
| `--creator` | ✅ | 创建人邮箱前缀，由 agent 从上下文显式传入 |
| `--config` | ✅ | 完整的 segmentation 配置 JSON 对象；当前需包含由合同 `target.unit` 映射的 `unit`，并保留其他配置字段 |
| `--config-file` | 否 | 从文件读取 segmentation 配置 JSON，与 `--config` 二选一 |
| `--figma-token` | 否 | Figma personal access token 覆盖项。不传时命令按 env / 后端按 creator 解析 |
| `--figma-auth-token` | 否 | Figma auth token 形式的覆盖项（云端场景） |
| `--transform-type` | 否 | `lynx`、`h5` 或 `web`，默认 `lynx`（`h5`/`web` 都走 browser 链路） |
| `--repo-name` | 否 | 仓库名如 `example/demo-repo`，建议显式传入 |
| `--package-name` | 否 | 业务组件包名（可选） |
| `--wait` | 否 | 轮询到终态；配合 `--output-dir` 时自动下载并解压产物 |
| `--output-dir` | 否 | 与 `--wait` 搭配，产物落盘目录 |
| `--poll-interval-ms` | 否 | 轮询间隔（毫秒，最小 `30000`） |
| `--timeout-ms` | 否 | 整体等待预算（毫秒，默认 `1200000`） |

> ⚠️ 本命令**不做任何 git 自动推断**。`--creator`、`--repo-name` 等参数全部由调用方（agent）根据上下文显式提供，避免在错误的工作目录下推断出错误的值。

> **Figma token**：不需要 `settings.json`。命令按「显式 flag → 环境变量 `FIGMA_ACCESS_TOKEN` / `FIGMA_PAT` / `FIGMA_TOKEN` / `FIGMA_AUTH_TOKEN` → 后端按 `--creator` 查询」的优先级在内部解析。需要显式覆盖时传 `--figma-token "<your-figma-token>"`。token 只在内存中使用，不写入磁盘、不打日志、不出现在输出里。

**对应字段映射（CLI flag → 接口 body）：**
`--figma-url → figmaUrl`、`--figma-token → figmaToken`、`--figma-auth-token → figmaAuthToken`、`--transform-type → transformType`、`--repo-name → repo_name`、`--package-name → package_name`、`--creator → creator`、`--config → config`（解析后的 JSON 对象，不是字符串）。

`--config` JSON 非对象、缺少 `unit`，或 `unit` 不是 `px/rpx` 时，命令在发起 HTTP 请求前失败。目录不存在时，调用方按目标平台补上默认 `unit`（Lynx=`rpx`、browser=`px`）；合同存在但 `target.unit` 缺失或非法时停止。除当前已校验的 `unit` 外，其余 config 字段保持原结构透传。

## 2. 查询状态 `d2c task get`

- **功能**：查询任务状态。
- **返回**：`{ taskId, status, downloadUrl?, message? }`。
  - `status` 取值：`pending` / `running` / `completed` / `failed` / `cancelled`。
  - `completed` 时带 `downloadUrl`（产物 tar.gz 下载地址）。

**用法：**

```bash
# 单次查询
bytedcli --json d2c task get \
  --task-id "<taskId>" \
  --kind visual-segmentation

# 轮询直到终态（在发起任务时一并等待）
bytedcli --json d2c segment create \
  --figma-url "https://www.figma.com/design/demoFileKey/demo-page?node-id=123-456" \
  --creator "your.email.prefix" \
  --config '{"unit":"rpx"}' \
  --wait \
  --poll-interval-ms 60000 \
  --timeout-ms 1200000
```

**参数：**

| 参数 | 必需 | 说明 |
|------|------|------|
| `--task-id` | ✅ | `d2c segment create` 返回的 taskId |
| `--kind` | 否 | 任务类型，视觉切分用 `visual-segmentation`（默认值） |
| `--timeout-ms` | 否 | 单次请求超时（毫秒，默认 `60000`） |

轮询相关参数属于 `d2c segment create --wait`：`--poll-interval-ms`（毫秒，最小 `30000`，建议 `60000`）与 `--timeout-ms`（默认 `1200000`，约 20 分钟）。终态为 `completed` / `failed` / `cancelled`。

⚠️ `--wait` 模式下 `Bash` 超时必须 ≥ `--timeout-ms`。
