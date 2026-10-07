# SCM WebShell 候选验证与准备

本 reference 适用于 SCM/ByteBuild 线索抽取、`source get`、`prepare`、结构化 handoff 和一次 Minimal WebShell Probe。执行额外远端诊断或处理 session 生命周期时, 改读 `scm-webshell-operations.md`。

## 固定入口

- 使用 `bytedcli --site cn --json scm webshell ...`。
- `source get` 只读验证候选; `prepare` 是唯一会创建或复用 WebShell 的入口。
- CLI 只接收结构化 option。Agent 负责从已批准的 URL 或用户文本中抽取候选, 不把 URL 传给 CLI。
- SCM version ID、repository ID 和 ByteBuild source record ID 必须是 `1` 到 `9223372036854775807` 范围内、无前导零的规范十进制字符串。它们始终作为字符串传递, 不经过 JavaScript number。

## 只识别以下 URL grammar

| 类型 | Scheme | Exact host | Path | 必要 query |
| ---- | ------ | ---------- | ---- | ---------- |
| SCM detail | `https` | `cloud.bytedance.net` | `/scm/detail/<repo_id>/versions` | `versionId=<version_id>` |
| SCM artifact | `https` | `bits.bytedance.net` | `/artifacts/publish/scm/<repo_id>/versions` | `versionId=<version_id>` |
| ByteBuild source record | `https` | `bits.bytedance.net` | `/artifacts/build/<source_record_id>/steps/success` | 无 |

按以下规则 fail closed：

- scheme 必须是字面量 `https`, host 必须与上面完全一致, 且没有 userinfo、port、子域或相似后缀。
- path 必须逐段匹配, ID 只能是 `1` 到 `9223372036854775807` 范围内、无前导零的 ASCII 十进制整数。允许零个或一个结尾 `/`; encoded path separator 或更多结尾 `/` 均不匹配。
- SCM URL 必须恰好包含一个大小写敏感的 `versionId`, 值为相同范围内、无前导零的 ASCII 十进制整数。允许其他 query 参数和 fragment。
- ByteBuild URL 的 path ID 是 `source_record_id`, 对应 CLI `--record-id`; 它不是 SCM `version_id`, 也不是 WebShell record ID。
- `cloud.bytedance.net` 或 `bits.bytedance.net` 上看似 SCM、artifact、build 或 build-step 线索但不满足上述 shape 的 URL 是 unsupported related URL。它会阻断工作流, 直到用户提供受支持 URL 或结构化 ID。无关 URL 不阻断唯一的有效候选。

同类候选只有值完全相同时才去重。不同的 version ID、repository ID、repository name、version 或 source record ID 都是 conflicting clues; 先要求用户消歧, 不选择第一个、最后一个或显式值。

## 一次调用统一验证所有候选

把所有兼容 candidate 作为 option 放进 same source/prepare invocation, 让 CLI 统一验证 SCM 与 ByteBuild identity。Agent 不自行声明验证成功, 不拆成互相独立的成功结论, 也不绕开 CLI 的冲突检查。

选择一个 SCM lookup shape：

```bash
# version ID; SCM URL 同时提供 repository 约束时一起传入
bytedcli --site cn --json scm webshell source get --version-id <version_id> --repo-id <repo_id>

# repository ID + version
bytedcli --site cn --json scm webshell source get --repo-id <repo_id> --version <version>

# repository name + version
bytedcli --site cn --json scm webshell source get --repo-name <repo_name> --version <version>

# 已有 ByteBuild source record ID
bytedcli --site cn --json scm webshell source get --record-id <source_record_id>
```

当同一请求同时给出 SCM 线索和 source record ID 时, 把 `--record-id <source_record_id>` 加入同一个调用。`--arch <arch>` 也放入该调用。多架构但没有明确架构时停止并让用户从 `available_architectures` 中选择; 不默认选择架构。

用户只要求检查候选或预览元数据时使用 `source get` 并停止。用户要求准备 WebShell 时, 使用相同的完整 selector 直接调用一次 `prepare`; `prepare` 会在创建准入前重新验证全部候选：

```bash
bytedcli --site cn --json scm webshell prepare --version-id <version_id> --repo-id <repo_id> --record-id <source_record_id> --arch <arch> --step <step_name>
```

只传实际存在的 option。显式 `--step` 优先; 已有 generation 保留原 step; 新 generation 由 CLI 按 source record 选择第一个失败步骤, 否则选择 `building`。Agent 不改写该选择。

如果用户要求 prepare-only 或禁止远端执行, 在 `prepare` 成功后报告 session、source record、WebShell record、step、reuse/replacement 和原始 `next_argv`, 并明确本次尚未验证命令执行。

## 校验结构化 handoff

只有 `prepare` 成功结果中的 `next_argv` 满足全部条件时才可执行：

1. 它是 exact string array, 长度恰好为 7, 每个元素都是字符串。
2. 它与下列数组逐元素完全相等, 其中 `<session_id>` 必须等于同一结果的 `session_id`：

```json
["scm", "webshell", "execute", "--session-id", "<session_id>", "--command", "pwd"]
```

3. 数组中没有额外 option、shell token、控制符或第二条命令。Agent 不 join、eval、修补或重新解释该数组。

校验失败时停止并报告 handoff 无效。不要猜测或自行构造替代 argv。

## 一次 Minimal WebShell Probe

普通 WebShell 准备请求授权一个 `pwd` 远端效果, 无需再次确认。将经过验证的 `next_argv` 作为当前 `bytedcli --site cn --json` 调用的原样命令后缀, 最多自动执行一次。用户的 prepare-only 或禁止远端执行要求优先。

只有 JSON 结果同时满足以下条件时 probe 才成功：

- `command_completed === true`
- `exit_code === 0`
- `timed_out === false`
- `output_truncated === false`
- `archive_truncated === false`
- `clean_output.trim()` 非空

成功时把 trimmed `clean_output` 作为远端工作目录报告, 并保留 session、source record、WebShell record、step、reuse/replacement 身份。不要把成功写成新的持久化可用状态。

任一字段缺失、类型不符、条件不满足、结果不是有效 JSON 或调用报错时, 顶层统一表述为 `执行 pwd 失败`, 随后给出 CLI 返回的具体安全原因。它只证明这一条 `pwd` 失败, 不证明整个 WebShell 永久不可用。停止自动诊断、replacement、recover、cleanup 和其他远端命令。

## 唯一的自动重试例外

只有首次普通权限 probe 的同一次错误同时提供以下完整证据时, 才可申请一次 platform elevation retry：

- error code 恰好是 `SCM_WEBSHELL_NOT_DISPATCHED`;
- error message 明确说明 event archive initialization 失败;
- `details.session_id` 等于 handoff 的 session;
- `details.not_dispatched === true`;
- `details.writer_lease_released === true`。

这些证据共同证明 archive initialization 失败发生在远端派发前, 且 writer lease release 已确认。缺少任一项时, 按 `执行 pwd 失败` 停止。stderr 中的 permission 文本、generic sandbox denial、timeout、WebSocket 错误、非零远端退出或 lease release 未确认都不符合条件。

符合条件时, 提交一次仅覆盖原始调用的 platform 提权请求。获批后以同一用户、环境、working directory 和 exact same argv 重试一次; 不加入 `sudo`, 不修改任何参数。申请动作即消耗唯一重试预算。拒绝、取消、超时或第二次失败均为最终结果。该提权只适用于这一次未派发的 `pwd` 重试, 不延伸到后续诊断或 session 操作。
