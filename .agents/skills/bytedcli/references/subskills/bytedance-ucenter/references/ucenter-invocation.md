# UCenter 调用方式

## 固定站点

UCenter 当前只支持 CN。可以使用默认站点，也可以显式传 `--site cn`：

```bash
bytedcli --json ucenter account get \
  --app-id 123 \
  --uid demo-uid

bytedcli --site cn --json ucenter profile get \
  --app-id 123 \
  --uid demo-uid
```

不要为 UCenter 尝试 `i18n-bd`、`i18n-tt`、`eu-ttp` 或 `boe`，也不要改写 host、region 或资源账号。

## JSON 与全局参数

`--json`、`--site`、代理和超时参数都是全局参数，放在 `ucenter` 前面。Agent 默认使用 JSON：

```bash
bytedcli --json ucenter account-log list \
  --app-id 123 \
  --uid demo-uid
```

每次调用都显式传 `--app-id`，不要从其他命令、缓存或上下文猜测 App ID。
