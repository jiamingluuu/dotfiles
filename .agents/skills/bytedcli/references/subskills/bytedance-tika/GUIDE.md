---
name: bytedance-tika
description: "Use bytedcli Tika to chat with the Tika AI knowledge platform, search internal knowledge bases, list conversations and available AI models. Trigger when the user asks questions that should be answered by Tika (TikTok internal knowledge search), wants to chat with Tika AI, or needs to manage Tika conversations/spaces/models. Do not use for Meego work items, Codebase code search, or BitsAI engineering Q&A — use the corresponding domain skill instead."
---

# bytedcli Tika

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

Tika 是 TikTok 内部 AI 知识平台（internal Tika workspace），集成内部知识库、Lark 文档搜索、Oncall 工单与 Web 搜索等数据源，支持多模型（Gemini、GPT、DeepSeek 等）对话。

## When to use

- 与 Tika AI 对话，获取字节/TikTok 内部知识问答（如平台使用、最佳实践、内部工具介绍）
- 需要搜索内部知识库文档并获得 AI 总结时
- 查看 Tika 支持的 AI 模型列表
- 查看或管理 Tika 知识空间
- 查看最近的 Tika 对话历史

## Do not use

- 不要用于 Meego 工作项查询 — 使用 `bytedance-meego`
- 不要用于 Codebase 代码搜索 — 使用 `bytedance-codebase`
- 不要用于 BitsAI 研发资产问答（如发布单、TCE/TCC 元信息）— 使用 `bytedance-bitsai`
- 不要用于直接执行部署、审批等操作

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 先确保 bytedcli 已登录（`bytedcli auth login`）
- 认证自动通过 i18n-tt ByteCloud JWT（`cloud.tiktok-row.net` / prod `cloud-i18n.bytedance.net`，region: `i18n`）获取，无需额外登录；若未登录过 i18n-tt，先执行 `bytedcli --site i18n-tt auth login`
- 需要机器可读输出时，把 `--json` 放在 `tika` 前面

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 列出知识空间
bytedcli tika spaces

# 列出可用模型
bytedcli tika models

# 与 Tika 对话（自动创建会话，流式输出）
bytedcli tika chat --message "What is TCE?"

# 指定模型对话
bytedcli tika chat --message "redis 大 key 治理最佳实践" --model gpt_4.1_mini

# 在已有会话中继续追问
bytedcli tika chat --message "Tell me more about its architecture" --conversation-id <conversation_id>

# 非流式输出（等待完整回答）
bytedcli tika chat --message "Explain TCC config management" --no-stream

# 查看最近对话
bytedcli tika conversations
bytedcli tika conversations --page-size 5

# Show every turn of one conversation
bytedcli tika conversation --id <conversation_id>

# Also print the model reasoning for each turn
bytedcli tika conversation --id <conversation_id> --show-reasoning
```

## Workflow

### 1. 选择对话方式

- 单轮问答：直接使用 `tika chat --message "..."`，自动创建新会话
- 连续追问：保留 `--conversation-id` 传入后续调用

### 2. 选择模型

默认使用 `gemini_2.5_pro`。可通过 `tika models` 查看所有可用模型，然后 `--model <name>` 指定。

内部模型（如 `tika-deepseek-v3.2`、`tika_seed_2.0_lite`）数据不出域，推荐处理敏感信息时使用。

### 3. 组织最终回答

- 默认用中文回答
- 结论优先，再补必要要点
- Tika 会在回答中标注引用来源
- 不向最终用户暴露 JWT、内部 endpoint、实现细节

## Notes

- `tika chat` 文本模式默认流式输出；`--json` 模式返回完整回答
- 认证复用 ByteCloud SSO，JWT 通过 i18n-tt 分区（`cloud.tiktok-row.net` / prod `cloud-i18n.bytedance.net`，region: `i18n`）获取
- 默认知识空间 ID 为 `6732288003`（Tika 公共知识库），可通过 `BYTEDCLI_TIKA_DEFAULT_SPACE_ID` 环境变量覆盖
- 默认模型为 `gemini_2.5_pro`，可通过 `BYTEDCLI_TIKA_DEFAULT_MODEL` 环境变量覆盖
- 对话历史通过 `tika conversations` 查看，包含问答内容摘要
- `tika conversations` returns only one preview message per conversation. To read every turn, use `tika conversation --id <conversation_id>`
- `tika conversation` hides model reasoning in text output by default. Add `--show-reasoning` to print it. JSON output always includes reasoning
- `tika chat --conversation-id <id>` keeps the model that conversation already uses. Pass `--model` to change it. The Agent of a conversation never changes

- Conversation IDs are trimmed before use. An explicitly empty or whitespace-only `--conversation-id` is rejected; omit the option to start a new conversation.

## References

- `../../invocation.md`
- `references/tika.md`
