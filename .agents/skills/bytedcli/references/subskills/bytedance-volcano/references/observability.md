# 可观测性服务说明

## TLS 使用 bytedcli

当前 `ve` 没有 `tls` 命令，`ve tls --help` 会返回 unknown command。TLS project、topic、index、log 和 trace 操作使用：

```bash
bytedcli volcano tls project list --page-size 20
bytedcli volcano tls topic list --project-id <project-id> --page-size 50
bytedcli volcano tls log search --topic-id <topic-id> --query "level:ERROR" --range 15m
```

不要把缺少 `ve tls` 误判成参数问题。

## CloudMonitor

CloudMonitor 使用 `ve cloudmonitor ...`。先通过 service/Action help 确认参数，不要把历史环境中的空列表当作账号当前状态。
