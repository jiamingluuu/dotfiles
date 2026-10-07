# KMS 服务说明

## DescribeKeys 必须指定 Keyring

`DescribeKeys` 要求 `KeyringName` 或 `KeyringID`，两者都缺失会返回 `MissingParameter`。先用 `DescribeKeyrings` 查找目标 Keyring。

## 删除是计划任务

KMS Key 和 Secret 不能立即删除。相关 Action 是 `ScheduleKeyDeletion`、`CancelKeyDeletion`、`ScheduleSecretDeletion`、`CancelSecretDeletion`。

除非任务明确接受计划删除及后续清理跟踪，否则只做查询和 help 校验。临时资源使用专用名称前缀。
