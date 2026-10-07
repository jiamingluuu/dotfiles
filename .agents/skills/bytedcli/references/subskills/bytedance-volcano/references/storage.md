# 存储服务说明

## TOS 使用 bytedcli

当前 `ve` 没有 `tos` 命令。TOS bucket/object 查询与下载使用 `bytedcli volcano tos ...`，完整说明见 [volcano-tos.md](volcano-tos.md)。不要把 unknown command 误判成参数错误。

如任务明确要求 `tosutil`，再按其独立命令和认证规则操作，不要把 bytedcli 与 tosutil 的参数混用。

## 文件系统创建会计费

EFS、FileNAS、vePFS 查询可使用 `ve`。创建会计费，并可能受可用区与售卖状态限制；选择可用区前先查询对应 zone/status 接口。
