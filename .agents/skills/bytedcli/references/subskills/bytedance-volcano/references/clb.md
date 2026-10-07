# CLB 服务说明

## 可用区与 EIP

`DescribeZones` 返回主/备可用区配对，不是扁平可用区列表。写入单可用区字段前必须先确定目标主备关系。

私网 CLB 测试不要设置 `EipBillingConfig.*`。创建接口暴露了 EIP 计费字段，直接复制公网示例可能意外分配公网地址。

删除接口支持强制删除：

```bash
ve clb DeleteLoadBalancer --LoadBalancerId <clb-id> --ForceDelete true
```

CLB 会产生费用并可能创建依赖资源，不得把完整生命周期创建当作普通 smoke test。
