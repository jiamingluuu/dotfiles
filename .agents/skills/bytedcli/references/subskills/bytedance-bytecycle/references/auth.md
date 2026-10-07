# Auth and ByteCycle config

Defaults work inside the corp network: `bytedcli bytecycle` uses the normal ByteCycle service and auto-fetches a ByteCloud JWT when `bytedcli auth` is logged in.

For normal agent workflows, use bytedcli auth and then run the ByteCycle command directly:

```bash
bytedcli auth status
bytedcli bytecycle train get --train-id <train-id>
bytedcli bytecycle ticket get --ticket-id <ticket-id>
```

Do not ask users or agents to paste JWT or Cookie values, and do not guess service domains. If auth fails, fix `bytedcli auth` first.

## Advanced Troubleshooting

These overrides exist for maintainers debugging proxy, BOE, or auth integration issues. Avoid them in normal skills, scenarios, and user-facing examples.

| Environment variable | Default | Purpose |
| -------------------- | ------- | ------- |
| `BYTEDCLI_BYTECYCLE_API_BASE_URL` | production ByteCycle service | ByteCycle service base URL. |
| `BYTEDCLI_BYTECYCLE_DOMAIN` | `canal_delivery_app` | Target domain used when auto-fetching ByteCloud JWT. |
| `BYTEDCLI_BYTECYCLE_JWT_TOKEN` | empty | Explicit ByteCloud JWT; takes precedence over auto-fetch. |
| `BYTEDCLI_BYTECYCLE_COOKIE` | empty | Explicit cookie; useful when temporarily reusing browser auth. |
| `BYTEDCLI_BYTECYCLE_AUTO_JWT` | `1` | Set to `0` to disable automatic ByteCloud JWT fetching. |
| `BYTEDCLI_BYTECYCLE_HTTP_TIMEOUT_MS` | bytedcli global HTTP timeout | ByteCycle HTTP timeout in milliseconds. |

Hidden maintainer flags with matching behavior also exist on `bytedcli bytecycle`; prefer environment variables for repeatable debugging.
