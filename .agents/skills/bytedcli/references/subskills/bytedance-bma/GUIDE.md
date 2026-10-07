---
name: bytedance-bma
description: "Operate BMA managed-agent control-plane resources through bytedcli bma. Use when tasks involve BMA Workspace, Agent/Version, Session, Credential, Connector/Schedule, Dataset/Document, Skill/Plugin, or the controlled Runtime event/SSE bridge. Typical requests include: list BMA agents, create BMA workspace, 帮我查一下 BMA Agent 列表, 给这个 BMA session 发条消息, 检查 BMA schedule 状态."
---

# BMA managed-agent platform

## Scope boundary

Do not use this skill to guess undocumented Engine, Runtime, or browser-only endpoints.

## Quick start

```bash
# Discover the installed command tree before choosing a subcommand.
bytedcli bma --help

# Read a BMA resource with structured output.
bytedcli --json bma workspace list --page-size 20
bytedcli --json bma agent get --agent-id "demo-agent"
bytedcli --json bma session event list --session-id "demo-session" --max-events 20

# Put Schedule prompt/config in a POSIX 0600 JSON file, then preview the mutation.
bytedcli --json bma schedule create --workspace-id "demo-workspace" --from-file "/path/to/schedule-0600.json" --dry-run
```

`bma session event list` 使用 `--max-events`（最大 200），不支持 `--page-size`；普通分页列表的 `--page-size` 默认 20、范围是 1-50。AgentBuddy Space 列表是独立 IDL 契约，默认 20、范围是 1-100。

## Safety

- BMA uses fixed documented control-plane operations and targets. Do not add arbitrary hosts, raw paths, raw JSON, or Runtime bootstrap/token/state callbacks.
- Mutations follow **plan → explicit `--yes` → one write → readback**. Do not retry an ambiguous write, prompt, webhook invocation, upload, or Eventhub write.
- Put secrets, prompts, metadata, and credential values in the documented protected-file options; do not put them in argv, plan output, or HTTP traces. On POSIX, protected inputs must use mode `0600`.
- Keep command-specific enum, Runtime, document, and blocked-capability rules in [the BMA command reference](references/bma.md); do not infer variants from nearby resources.

## References

- [BMA command reference](references/bma.md)
- [Invocation](../../invocation.md)
- [Troubleshooting](../../troubleshooting.md)
