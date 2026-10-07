---
name: bytedance-vela
description: "Use bytedcli to query Vela one-machine VM metric series from monitor-view URLs across CN, I18N, NonTT, US-TTP, and EU-TTP office sites. Covers one-machine query with ByteCloud JWT auth."
---

# Vela

Use this skill when the task mentions Vela one-machine, Vela monitor-view URLs, single-machine VM metrics, or querying metric series from a Vela page.

## Authentication

Vela commands reuse bytedcli ByteCloud JWT authentication.

```bash
bytedcli --json auth status
bytedcli auth login
```

## Sites

Use the global `--site` flag. When `--url` points at a known Vela office domain, bytedcli can infer the site from the URL host.

| Site      | Scope              |
| --------- | ------------------ |
| `cn`      | CN office site     |
| `i18n-tt` | I18N TikTok site   |
| `i18n-bd` | I18N NonTT site    |
| `us-ttp`  | US-TTP office site |
| `eu-ttp`  | EU-TTP office site |

## One-Machine Query

Query directly from a Vela monitor-view URL:

```bash
bytedcli vela one-machine query --url 'https://vela.example/vela/monitor-view/one-machine?selectedName=sample-host&curCount=1&mount=*&time=86400000'
bytedcli --json vela one-machine query --url 'https://vela.example/vela/monitor-view/one-machine?selectedName=sample-host&curCount=1&time=86400000'
```

Query by explicit host or IP:

```bash
bytedcli --site eu-ttp vela one-machine query --selected-name sample-host --cur-count 1 --time 86400000
bytedcli --json --site eu-ttp vela one-machine query --selected-name sample-host --metric cpu.busy --time 1700000000000-1700000600000
```

## Output

Use `--json` before `vela` for machine-readable output. JSON includes the resolved query (`selectedName`, `start`, `end`, `step`, counters) and metric series points. Text mode renders a compact query summary and previews the returned series.

## Notes

- `--url` parses `selectedName`, `curCount`, `time`, `timeDate`, `mount`, and `iface` from Vela monitor-view one-machine URLs.
- When `--metric` is omitted, bytedcli expands `--cur-count` with Vela one-machine counter groups.
- `--cur-count 10` follows Vela's GPU group and expands GPU memory utilization, utilization, UE, temperature, and power metrics for gpu0-gpu7.
- The backend request body follows the page request shape: `POST /vm/v1/internal/query_multi` with `ip`, `start`, `end`, and `counters[]`. TTP sites use the same proxy base selected by the Vela frontend.
- `--time` accepts a non-negative duration in milliseconds, or a non-negative `<startMs>-<endMs>` epoch-millisecond range.
- `--time-date` accepts a non-negative `<startSec>-<endSec>` epoch-second range.
