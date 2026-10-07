# VPC 服务说明

## 创建后存在短暂一致性窗口

`CreateVpc` 返回后，VPC 可能暂时不能创建子资源。先轮询：

```bash
ve vpc DescribeVpcs --VpcIds.1 "$vpc_id"
```

直到 `.Result.Vpcs[0].Status == "Available"`，再创建 Subnet 或 SecurityGroup。`CreateSecurityGroup` 后也要等详情可查，再授权 ingress；`InvalidVpc.InvalidStatus` 和 `InvalidSecurityGroup.InvalidStatus` 可做短间隔重试，不能直接重建。

## SecurityGroup 名称过滤是数组参数

`DescribeSecurityGroups` 不接受 `--SecurityGroupName`，该参数可能被忽略并返回未过滤列表。使用：

```bash
ve vpc DescribeSecurityGroups --SecurityGroupNames.1 "demo-security-group"
```

删除后用同一过滤条件确认 `TotalCount: 0`。

## SecurityGroup 操作是异步的

`CreateSecurityGroup`、`AuthorizeSecurityGroupIngress`、`RevokeSecurityGroupIngress`、`DeleteSecurityGroup` 会返回 `AsyncTaskId`。

Ingress 使用 `--PortStart`、`--PortEnd`、`--Protocol`、`--CidrIp` 等展开参数，不要写成 `--SourceCidrIp` 或 `Permissions.*`。默认 egress all 规则不需要在删除 SecurityGroup 前手动撤销。

## EIP 安全

现有 EIP 可能绑定 NAT 网关或其他用户资源。除非 EIP 由当前已批准的测试创建，否则不得释放或解绑。
