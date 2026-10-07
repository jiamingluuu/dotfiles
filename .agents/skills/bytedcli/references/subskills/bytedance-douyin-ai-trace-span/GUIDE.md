# Douyin AI Trace Span

Use this route when the user asks for Douyin AI Trace Span details, flat spans, LogID-based trace pagination, or the total Span count for a Douyin AI trace.

The complete command guidance is maintained with the official plugin Skill:
https://code.byted.org/open/bytedcli-plugin-douyin-ai/blob/master/skills/bytedance-douyin-ai-trace-span/SKILL.md

## Bootstrap

1. Install and validate the official plugin if its Trace Span command is unavailable:

```bash
bytedcli self plugin install --name douyin-ai
bytedcli self plugin doctor --name douyin-ai
```

The official package is `@bytedance-dev/bytedcli-plugin-douyin-ai` and requires bytedcli `>=0.131.0`.

2. Reuse the bytedcli CN Mango session. The plugin has no separate credential flow; never request or hand-write a Cookie.
3. Restart the Agent or MCP session after installation so the bundled Skill and command catalog are refreshed.
4. Load the bundled `bytedance-douyin-ai-trace-span` Skill for the exact command, pagination, time-range, and output contract. Do not substitute workspace-scoped `douyin-ai trace list/get`.
5. Use runtime help if the installed plugin and the Skill disagree:

```bash
bytedcli douyin-ai trace span --help
```
