# ALB 服务说明

## 使用展开参数

ALB 创建接口使用展开参数，不使用 JSON body。嵌套数组采用带序号的点号写法，例如 `--ZoneMappings.1.ZoneId`。

私网 ALB 不要设置 EIP 或公网地址字段，除非任务明确要求验证公网暴露：

```bash
ve alb CreateLoadBalancer \
  --RegionId cn-beijing \
  --LoadBalancerName demo-private-alb \
  --Type private \
  --VpcId vpc-<id> \
  --SubnetId subnet-<id> \
  --ZoneMappings.1.ZoneId cn-beijing-b \
  --ZoneMappings.1.SubnetId subnet-<id> \
  --LoadBalancerBillingType 1 \
  --LoadBalancerEdition Basic \
  --Tags.1.Key publish-by \
  --Tags.1.Value demo-skill
```

ALB 创建会产生费用并依赖真实 VPC/子网。生命周期测试必须使用专用测试资源，记录返回 ID，验证后立即删除并回查。
