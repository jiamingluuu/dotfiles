# TeslaX Report OpenAPI

## 用途

`tesla report list` 和 `tesla report case` 走 TeslaX OpenAPI gateway，用于查询 CaseSetReportLite 与单 case 明细。

| CLI 命令 | OpenAPI | 鉴权 |
| --- | --- | --- |
| `tesla report list` | `GET /api/v1/teslax/space/:spaceId/report` | `--bearer-token` |
| `tesla report case` | `GET /api/v1/teslax/space/:spaceId/case_detail` | `--bearer-token` |

```bash
bytedcli --json tesla report list --space-id 1000 --task-id "<task-id>" --bearer-token "<bearer-token>"
bytedcli --json tesla report case --space-id 1000 --task-id "<task-id>" --case-id 123 --bearer-token "<bearer-token>"
```

## 参数规则

- `--space-id`：TeslaX 空间 ID。
- `--task-id`：TeslaX task UUID。
- `--case-id`：`report case` 必填，表示 case ID。
- `--bearer-token`：OpenAPI gateway 鉴权 token。
- `--env cn|boe|i18n|zg`：选择 TeslaX gateway 环境。
