# Vela Command Reference

Vela commands query one-machine VM metric series through Vela office sites.

## Sites

Use global `--site`. Known Vela monitor-view URL hosts can also infer the site.

| Site      | Scope              |
| --------- | ------------------ |
| `cn`      | CN office site     |
| `i18n-tt` | I18N TikTok site   |
| `i18n-bd` | I18N NonTT site    |
| `us-ttp`  | US-TTP office site |
| `eu-ttp`  | EU-TTP office site |

## Commands

```bash
bytedcli vela one-machine query --url 'https://vela.example/vela/monitor-view/one-machine?selectedName=sample-host&curCount=1&mount=*&time=86400000'
bytedcli --site eu-ttp vela one-machine query --selected-name sample-host --cur-count 1 --time 86400000
bytedcli --json --site eu-ttp vela one-machine query --selected-name sample-host --metric cpu.busy --time 1700000000000-1700000600000
```

## API Mapping

| CLI                       | API path                            |
| ------------------------- | ----------------------------------- |
| `one-machine query`       | `POST /vm/v1/internal/query_multi`  |

## Request Mapping

| CLI / URL input                    | API field                  |
| ---------------------------------- | -------------------------- |
| `selectedName` / `--selected-name` | `ip`                       |
| `time` / `timeDate`                | `start`, `end`             |
| `curCount` / `--metric`            | `counters[].metric`        |
| computed or `--step`               | `counters[].step`          |

## Notes

- Authentication reuses ByteCloud JWT and sends `X-Jwt-Token`.
- `--metric` is repeatable and is not comma-split, because Vela metric filters can contain commas.
- `--cur-count 10` expands Vela's GPU counter group for gpu0-gpu7 memory utilization, utilization, UE, temperature, and power metrics.
- TTP sites use the same proxy base selected by the Vela frontend, while the command still accepts monitor-view office URLs for site inference.
- `mount` and `iface` are preserved for the Grafana URL shown in the result; metric selection comes from `curCount` or explicit `--metric`.
- `--time` uses milliseconds; `--time-date` uses Unix epoch seconds. Negative time values are rejected.
