# Tika 命令参考

## 命令列表

### tika chat

与 Tika AI 对话（自动创建会话 + 流式输出）。

```bash
bytedcli tika chat --message <message> [options]
```

| 参数 | 说明 |
|------|------|
| `--message <message>` | **必填** 问题文本 |
| `--conversation-id <id>` | 续用已有会话 |
| `--space-id <space_id>` | 知识空间 ID（默认: Tika 公共知识库，可通过 `BYTEDCLI_TIKA_DEFAULT_SPACE_ID` 覆盖） |
| `--model <model>` | AI 模型名（如 `gemini_2.5_pro`、`gpt_4.1_mini`、`tika-deepseek-v3.2`，默认: `gemini_2.5_pro`，可通过 `BYTEDCLI_TIKA_DEFAULT_MODEL` 覆盖）。当使用 `--conversation-id` 且未传 `--model` 时，将复用该会话当前使用的模型 |
| `--no-stream` | 等待完整回答后再输出 |
| `--search-mode <mode>` | 搜索模式（默认: `fast_agent`） |
| `--timeout-sec <seconds>` | 请求超时（秒） |

### tika conversations

列出最近的 Tika 对话及消息摘要。Returns only one preview message per conversation, not the full history.

```bash
bytedcli tika conversations [options]
```

| 参数 | 说明 |
|------|------|
| `--space-id <space_id>` | Limit to one knowledge space ID (default: the public default space plus all your spaces, deduplicated) |
| `--page-size <size>` | 返回条数（默认: 20） |
| `--agent-id <agent_id>` | Filter to conversations started with a specific Agent (default: no filter) |

### tika conversation

Show every turn of one conversation: the question and the answer for each turn.

```bash
bytedcli tika conversation --id <conversation_id> [options]
```

| 参数 | 说明 |
|------|------|
| `--id <conversation_id>` | **Required.** Conversation ID. Get one from `tika conversations` |
| `--show-reasoning` | Also print the model reasoning for each turn (default: hidden) |

### tika models

列出 Tika 可用的 AI 模型。

```bash
bytedcli tika models
```

### tika spaces

列出 Tika 知识空间。

```bash
bytedcli tika spaces
```

## 可用模型

| 模型名 | 显示名 | 推理 | 备注 |
|--------|--------|------|------|
| `gemini_2.5_pro` | Gemini 2.5 Pro | ✓ | 默认模型 |
| `gemini_2.5_flash` | Gemini 2.5 Flash | | 快速响应 |
| `gpt_4.1` | GPT-4.1 | | |
| `gpt_4.1_mini` | GPT-4.1 mini | | 快速响应 |
| `gpt_5_mini` | GPT-5 mini | ✓ | |
| `tika-deepseek-v3.2` | DeepSeek V3.2 | ✓ | 内部模型，数据不出域 |
| `tika_seed_2.0_lite` | Doubao Seed 2.0 Lite | ✓ | 内部模型，数据不出域 |

> 完整列表通过 `bytedcli tika models` 获取。

## 认证

Tika 复用 ByteCloud SSO 认证，JWT 通过 i18n-tt 分区获取（`cloud.tiktok-row.net`；`BYTEDCLI_NETWORK_PROFILE=prod` 时为 `cloud-i18n.bytedance.net`；JWT `region=i18n`）。

```bash
# 先登录 i18n-tt（Tika 需要 region=i18n 的 JWT）
bytedcli --site i18n-tt auth login

# 验证（应返回用户信息）
bytedcli tika spaces
```

## 错误处理

| 错误 | 原因 | 解决 |
|------|------|------|
| HTTP 401 / X-Jwt-Token decode failed | JWT 过期，或拿到了 `i18n-bd`（`region=i18nbd`）而非 `i18n-tt`（`region=i18n`）凭证 | 执行 `bytedcli --site i18n-tt auth login` 后重试 |
| Tika API error | 业务层错误 | 检查参数，确认 space_id 有效 |
| TIKA_TIMEOUT | 请求超时 | 用 `--timeout-sec` 增加超时 |
