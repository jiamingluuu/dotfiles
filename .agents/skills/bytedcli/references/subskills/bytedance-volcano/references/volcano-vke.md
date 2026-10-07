# Volcano VKE（容器服务 / Kubernetes）

VKE 控制面和 Kubernetes apiserver 转发在 `ve 1.1.5+` 已提供。集群、节点池、资源发现、普通资源查询和 Pod 实时日志默认使用 `ve`；只有 TLS 离线日志自动发现和默认 Secret 脱敏保留 bytedcli fallback。

## 能力路由

| 任务                                                          | 入口                                       |
| ------------------------------------------------------------- | ------------------------------------------ |
| 集群、节点池                                                  | `ve vke ListClusters/ListNodePools`        |
| Kubernetes discovery、Pod、Deployment、CRD、raw GET、Pod 日志 | `ve vke ForwardKubernetesApi --Method GET` |
| TLS 中的历史容器日志与 topic 自动发现                         | `bytedcli volcano vke log ...`             |
| 默认脱敏读取 Kubernetes Secret                                | `bytedcli volcano vke resource ...`        |

`ForwardKubernetesApi` 不需要 kubeconfig、客户端证书或集群 VPC 连通性，但调用身份必须同时具备 VKE OpenAPI 权限和集群 RBAC 权限。

## 安全边界

本 reference 只把 `ForwardKubernetesApi` 用于 `--Method GET`。该 Action 也支持 POST、PUT、PATCH、DELETE，但 Action 名不会体现实际写入语义；Kubernetes mutation 必须另行展示完整请求、分析影响并获得明确确认，不得从这里的只读 recipe 推导自动写入。

ve 会原样返回 `Result.Body`，不会像 bytedcli 一样自动做 Secret 脱敏、资源表格转换、kind 消歧和 Kubernetes 错误映射。执行后必须同时检查：

1. `ResponseMetadata.Error` 不存在；
2. `Result.Code` 是 2xx；
3. 再解析 `Result.Body`。

不能只根据 ve 进程 exit code 判断 apiserver 请求成功。

## 地域发现

```bash
ve ecs DescribeRegions --region cn-beijing
```

这是 ECS 地域列表，不是 VKE 开服列表。结果只能作为候选 ID，不能据此拒绝用户明确指定的 VKE 地域；最终以 VKE 官方地域说明和实际 `ListClusters` 为准。

## 集群与节点池

```bash
# 集群列表
ve vke ListClusters --PageNumber 1 --PageSize 20 --region cn-beijing

# 单个集群；VKE 没有 GetCluster Action，通过 ID Filter 查询
ve vke ListClusters \
  --Filter.Ids.1 <cluster-id> \
  --PageNumber 1 --PageSize 1 \
  --region cn-beijing

# 某集群的节点池
ve vke ListNodePools \
  --Filter.ClusterIds.1 <cluster-id> \
  --PageNumber 1 --PageSize 20 \
  --region cn-beijing

# 单个节点池；VKE 没有 GetNodePool Action
ve vke ListNodePools \
  --Filter.Ids.1 <node-pool-id> \
  --PageNumber 1 --PageSize 1 \
  --region cn-beijing
```

## 检查 ForwardKubernetesApi 响应

推荐先保存完整 envelope，再检查 apiserver code：

```bash
response=$(ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> \
  --Method GET \
  --Path '/version' \
  --region cn-beijing)

code=$(printf '%s' "$response" | jq -r '.Result.Code // 0')
if [ "$code" -lt 200 ] || [ "$code" -ge 300 ]; then
  printf '%s\n' "$response" >&2
  exit 1
fi
printf '%s' "$response" | jq -r '.Result.Body'
```

`Result.Body` 对 Kubernetes JSON 接口是 JSON 字符串，可继续交给 `jq`：

```bash
printf '%s' "$response" | jq -r '.Result.Body' | jq .
```

## API discovery

```bash
# Core API versions
ve vke ForwardKubernetesApi --ClusterId <cluster-id> --Method GET --Path '/api' --region cn-beijing

# API groups
ve vke ForwardKubernetesApi --ClusterId <cluster-id> --Method GET --Path '/apis' --region cn-beijing

# Core v1 resources
ve vke ForwardKubernetesApi --ClusterId <cluster-id> --Method GET --Path '/api/v1' --region cn-beijing

# apps/v1 resources
ve vke ForwardKubernetesApi --ClusterId <cluster-id> --Method GET --Path '/apis/apps/v1' --region cn-beijing
```

同名 kind 可能属于多个 API group。ve 不会自动消歧，必须从 discovery 响应确定 group、version、plural 和是否 namespaced，再构造 Path。

## 常用 Kubernetes 资源

```bash
# default namespace 的 Pod
ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> --Method GET \
  --Path '/api/v1/namespaces/default/pods?limit=100' \
  --region cn-beijing

# 全部 namespace 的 Pod
ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> --Method GET \
  --Path '/api/v1/pods?limit=100' \
  --region cn-beijing

# 单个 Deployment
ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> --Method GET \
  --Path '/apis/apps/v1/namespaces/default/deployments/demo-app' \
  --region cn-beijing

# CRD 实例；group/version/plural 必须来自 discovery
ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> --Method GET \
  --Path '/apis/example.io/v1/namespaces/default/demoresources?limit=100' \
  --region cn-beijing
```

labelSelector、fieldSelector、continue 等 query value 必须做 URL 编码，不能直接拼接包含空格、`&`、`=` 或特殊字符的原值。

## Kubernetes 分页

列表没有页码。解析 Body 中的 `.metadata.continue`，URL 编码后传入下一次 Path：

```text
/api/v1/pods?limit=100&continue=<url-encoded-token>
```

`continue` 为空才表示结束；当前页零条不能代替分页终止判断。

## Pod 实时日志

```bash
ve vke ForwardKubernetesApi \
  --ClusterId <cluster-id> --Method GET \
  --Path '/api/v1/namespaces/default/pods/demo-pod/log?tailLines=100&timestamps=true' \
  --region cn-beijing
```

多容器 Pod 加 URL 编码后的 `container=<name>`；时间过滤使用 `sinceSeconds=<seconds>`；上一实例日志使用 `previous=true`。日志是文本，成功后直接读取 `Result.Body`。

## TLS 离线日志 fallback

`ForwardKubernetesApi` 只能读取 apiserver/当前容器日志，不能自动发现 TLS destinations 或查询已删除 Pod 的历史日志。此能力继续使用 bytedcli：

```bash
bytedcli volcano vke log target list --cluster-id <cluster-id>
bytedcli volcano vke log search --cluster-id <cluster-id> --range 15m
bytedcli volcano vke log search --cluster-id <cluster-id> --namespace demo-ns --pod demo-pod --query ERROR --limit 20
```

复杂 glob、topic 覆盖、continuation、查询正文脱敏等行为以当前 `bytedcli volcano vke log search --help` 为准。

## Secret fallback

ve 的 `ForwardKubernetesApi` 会原样返回 Kubernetes Secret 的 `.data` / `.stringData`。默认脱敏查询继续使用：

```bash
bytedcli volcano vke resource get --cluster-id <cluster-id> --kind Secret --namespace default --name demo-secret
```

只有用户明确要求查看 Secret 明文时，才可使用该命令的 `--reveal`；不得为了统一成 ve 而绕过默认脱敏。

## 排错

| 现象               | 原因                                           | 处理                                                    |
| ------------------ | ---------------------------------------------- | ------------------------------------------------------- |
| `Result.Code=401`  | apiserver 未认证转发身份                       | 先检查 ve 当前身份和 VKE 权限                           |
| `Result.Code=403`  | 已认证，但缺少目标集群 RBAC                    | 在 VKE 为当前身份授权集群权限，不要盲目换 AK/SK         |
| `Result.Code=404`  | namespace/path/version/plural 错误或资源不存在 | 重新读取 `/api`、`/apis` 和对应 group/version discovery |
| Body 不是预期 JSON | 请求的是日志等文本接口，或网关返回异常内容     | 先检查 Code，再按接口类型处理 Body                      |
| 请求卡住           | Path 包含 watch/follow streaming               | 去掉 streaming 参数，改用有界轮询                       |

`watch=true`、`follow=true` 等 streaming 请求不适合该请求-响应式网关，不要使用。
