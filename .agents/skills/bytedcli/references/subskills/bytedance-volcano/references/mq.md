# 消息队列服务说明

## Kafka 与 RocketMQ 需要分页参数

Kafka、RocketMQ 的 `DescribeInstances` 要求 `PageNumber` 和 `PageSize`：

```bash
ve kafka DescribeInstances --body '{"RegionId":"cn-beijing","PageNumber":1,"PageSize":10}'
ve rocketmq DescribeInstances --body '{"RegionId":"cn-beijing","PageNumber":1,"PageSize":10}'
```

不要假设 RabbitMQ、BMQ 与它们具有相同参数结构，以各自 `--help --detail` 为准。

## 更安全的 smoke test

AllowList 的创建/删除通常比 Broker 实例生命周期风险低，但仍是写操作，需要明确批准并最终回查清理。不要为通用验证创建计费 Broker 实例。
