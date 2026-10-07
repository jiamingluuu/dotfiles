# ECS 服务说明

## 资源发现易错点

`DescribeInstanceTypes` 默认只返回较小的一页，不能证明目标可用区有该规格。部署前用 `DescribeAvailableResource` 查询目标 zone，否则某规格即使全局存在，`RunInstances` 仍可能返回 `InvalidInstanceType.NotFound`。

规格库存位于：

```text
.Result.AvailableZones[].AvailableResources[]
| select(.Type == "InstanceType")
| .SupportedResources[]
```

只保留 `Status=Available` 的条目，不要寻找不存在的顶层 InstanceTypes 数组。

veLinux 镜像使用精确名称前缀查询。`velinux` 这种模糊词还会命中 GPU、Docker、ARM 等变体；常用名称包括 `veLinux 2.0 64`、`veLinux 2.0 ARM 64`。

## RunInstances 当前参数形态

当前 CLI 使用 `--ZoneId`；旧示例可能写 `--Placement.ZoneId`。始终以本机 `RunInstances --help --detail` 为准。

`RunInstances` 即使不开放 SSH，也要求 `--Password` 或 `--KeyPairName`。只使用 Cloud Assistant 的部署可以生成一次性强密码，但不得打印或持久化。

不分配 EIP 时移除所有 `EipAddress.*` 参数，并先执行 `--DryRun true`。成功 DryRun 会以非零退出并输出 `DryRunOperation`，不会创建实例。

内联 EIP 的 `ChargeType` 常用值为 `PayByBandwidth`、`PayByTraffic`、`PrePaid`，仍需用当前 help 确认。

如果 VPC、Subnet、SecurityGroup 刚刚创建，先等待资源可用。过早创建子网/写 ingress 可能分别返回 `InvalidVpc.InvalidStatus`、`InvalidSecurityGroup.InvalidStatus`。

## DeleteInstance 状态大小写

`DescribeInstances` 可能返回 `CREATING`、`RUNNING` 等全大写状态，不要只比较 Title Case。

实例还在 `CREATING` 时删除会返回 `InvalidInstanceStatus`。轮询到产品允许删除的状态后再操作，删除后按测试资源 ID 或精确名称确认不存在。

## Cloud Assistant 易错点

`InstallCloudAssistant` 后 Agent 可能显示 `ReadyReboot`，此时 `RunCommand` 会持续超时。创建实例时优先使用 `--InstallRunCommandAgent true`。

`RunCommand` 必须显式设置 `--InvocationName`：最长 64 字符，只能含中文、字母、数字、下划线、连字符，且不能以数字或连字符开头。保持简短稳定，例如 `deploy-check`。省略后部分 CLI 会从 base64 CommandContent 派生名称并触发长度错误。

`--Timeout` 最小值为 60 秒。`--CommandContent` 必须是 base64 shell 内容，直接传 `echo OK` 会返回 `InvalidBase64Content.Malformed`。

`RunCommand` 只表示已调度，需要轮询 `DescribeInvocationResults`。状态字段为 `.Result.InvocationResults[0].InvocationResultStatus`，终态包括 `Success`、`Failed`、`Timeout`；同时检查 ExitCode，并对 Output 做 base64 解码。

```bash
command_b64=$(printf '%s' 'systemctl is-active --quiet demo-app && echo OK' | base64 | tr -d '\n')
invocation_id=$(ve ecs RunCommand \
  --Type Shell \
  --InstanceIds.1 "$instance_id" \
  --InvocationName deploy-check \
  --Timeout 60 \
  --CommandContent "$command_b64" \
  | jq -r '.Result.InvocationId')

for _ in $(seq 1 30); do
  result=$(ve ecs DescribeInvocationResults \
    --InvocationId "$invocation_id" --InstanceId "$instance_id")
  result_status=$(printf '%s' "$result" | jq -r '.Result.InvocationResults[0].InvocationResultStatus // empty')
  exit_code=$(printf '%s' "$result" | jq -r '.Result.InvocationResults[0].ExitCode // empty')
  case "$result_status" in
    Success|Failed|Timeout) break ;;
  esac
  sleep 5
done

if [ "$result_status" != Success ] || [ "$exit_code" != 0 ]; then
  echo "RunCommand failed or timed out" >&2
  exit 1
fi
printf '%s' "$result" | jq -r '.Result.InvocationResults[0].Output // ""' | base64 -d
```

## veLinux 部署 Docker

veLinux 2 可能返回 `VERSION_CODENAME=lyra`，但 `lyra` 不是 Docker 官方 Debian 仓库 codename。快速部署优先使用发行版包：

```bash
apt-get update
apt-get install -y docker.io
systemctl enable --now docker
```

中国地域访问 Docker Hub、GHCR 可能超时。优先使用火山 CR、用户提供的 Registry，或镜像服务详情页明确给出的拉取命令；不要假设某个镜像站支持任意 `<registry>/<image>` 路径。
