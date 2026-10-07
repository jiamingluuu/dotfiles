# VKE 服务说明

## 集群接口使用 JSON body

`CreateCluster`、`DeleteCluster` 使用 `--body`：

```bash
ve vke CreateCluster --body '{
  "Name": "demo-cluster",
  "ClusterConfig": {"SubnetIds": ["subnet-<id>"]},
  "PodsConfig": {
    "PodNetworkMode": "Flannel",
    "FlannelConfig": {"PodCidrs": ["172.16.0.0/16"]}
  },
  "ServicesConfig": {"ServiceCidrsv4": ["172.20.0.0/16"]},
  "Tags": [{"Key":"publish-by","Value":"demo-skill"}]
}'
ve vke DeleteCluster --body '{"Id":"<cluster-id>","Force":true}'
```

## 生命周期风险

集群创建耗时、成本高，还会创建 ECS、网络、日志和 addon 依赖，不得作为普通 smoke test。明确批准后要记录所有返回 ID 和保留/删除策略。新集群在 Creating 或 addon Progressing 时可能拒绝删除；轮询到产品文档定义的可删除状态后再清理，最后确认 `ListClusters` 不再返回测试集群。

## 影响基础工作负载的 Addon

- `core-dns` 提供集群 DNS/Service 发现；服务名解析失败时先查 addon 状态。
- `cr-credential-controller` 支持免密拉取火山 CR；未启用时私有镜像可能需要 `imagePullSecret`。
