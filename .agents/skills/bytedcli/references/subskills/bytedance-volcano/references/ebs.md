# EBS 服务说明

## 现有云盘通常属于 ECS

`ve storageebs DescribeVolumes` 返回的云盘可能是 ECS 系统盘。所有现有云盘都按用户资源处理，smoke test 中不得卸载或删除。

## 生命周期风险

`CreateVolume` 会产生费用。只有明确批准后才能创建小规格按量数据盘；不得挂载到非测试实例，验证后立即删除，并用 `DescribeVolumes` 确认资源消失。
