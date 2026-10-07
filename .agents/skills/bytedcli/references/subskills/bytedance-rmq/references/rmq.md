# RMQ (RocketMQ)

```bash
# Topic 列表（按名称搜索）
bytedcli rmq topic list --vregion "China-BOE" --search "demo_topic"
bytedcli rmq topic list --vregion "China-BOE" --page 1 --page-size 20
# 跨 Owner 搜索全部可见 Topic
bytedcli rmq topic list --vregion "China-BOE" --search "demo_topic" --all

# Topic 详情（按 ID 查询）
bytedcli rmq topic get --topic-id 132991 --vregion "China-BOE"

# 实际生产配额（独立于 Topic 基础信息；按 DC 返回）
bytedcli --site cn rmq topic quota get --topic-name "demo_topic" --vregion China-North
bytedcli --site cn rmq topic quota get --topic-name "demo_topic" --cluster-name "demo_cluster" --vregion China-North
bytedcli --json --site cn rmq topic quota get --topic-id 12345 --vregion China-North

# Topic 创建审批 dry-run；只支持中国站 China-North 的已有集群
bytedcli --site cn rmq topic create \
  --topic-name "demo_topic" \
  --cluster-name "demo_cluster" \
  --service-tree-id 123456 \
  --message-size 1024 \
  --qps 100 \
  --purpose "示例事件" \
  --produce-quota 20 \
  --priority P1 \
  --lane-type standard \
  --vregion China-North

# 确认 payload 后追加 --yes，提交 Topic 创建审批
bytedcli --site cn rmq topic create \
  --topic-name "demo_topic" \
  --cluster-name "demo_cluster" \
  --service-tree-id 123456 \
  --message-size 1024 \
  --qps 100 \
  --purpose "示例事件" \
  --produce-quota 20 \
  --priority P1 \
  --lane-type standard \
  --vregion China-North \
  --yes

# Topic 消息预览（只读；默认从最早 offset 开始，每个 queue 返回 1 条）
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" --vregion "China-BOE"
# 从最新位置预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" --position latest
# 指定 broker/queue/offset，并向更新消息方向预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" \
  --offset 1 --direction after --count 5 \
  --idc "demo-idc" --broker "demo-broker" --queue 0

# Consumer Group 列表（按 Topic ID 查询）
bytedcli rmq consumer list --topic-id 132991 --vregion "China-BOE"

# 消费组存储的 SDK 配置（group ID 从同站点、同 vregion 的 consumer list 获取）
bytedcli --site cn rmq consumer list --topic-id 12345 --vregion China-North
bytedcli --site cn rmq consumer config get --group-id 23456 --vregion China-North
bytedcli --json --site cn rmq consumer config get --group-id 23456 --vregion China-North

# 消费状态（TPS、Lag、Queue 详情）
bytedcli rmq consumer stats --topic demo-topic --group demo-group --cluster demo-cluster --vregion "China-BOE"
# 查看 Lag 最高的前 5 个队列
bytedcli rmq consumer stats --topic demo-topic --group demo-group --cluster demo-cluster --top-lag-queue 5

# Queue 分配状态（按 Broker Cluster → Proxy 展示）
bytedcli rmq consumer allocation --topic demo-topic --group demo-group --cluster demo-cluster --vregion "China-BOE"
# 筛选指定 Broker 和 Queue 对应的 Proxy 信息
bytedcli rmq consumer allocation --topic demo-topic --group demo-group --cluster demo-cluster --broker demo-broker --queue 0

# 客户端连接状态（按 Broker Cluster → Proxy → Client 连接串展示）
bytedcli rmq consumer clients --topic demo-topic --group demo-group --cluster demo-cluster --vregion "China-BOE"
# 筛选指定 Proxy 的 Client 信息
bytedcli rmq consumer clients --topic demo-topic --group demo-group --cluster demo-cluster --proxy 10.0.0.1

# 多站点（中国站）
bytedcli --site cn rmq topic list --vregion "CN" --search "demo"

# BOE 站点
bytedcli --site boe rmq topic list --vregion "China-BOE" --all

# TTP 站点
bytedcli --site us-ttp rmq topic list
bytedcli --site eu-ttp rmq topic list --vregion eu-ttp2
```

`topic preview` 返回完整消息正文，不创建 Consumer Group，也不修改 Consumer
offset。`--offset`、`--timestamp-ms` 与显式 `--position` 只能选择一种；精确 queue
定位时必须同时传 `--idc`、`--broker`、`--queue`。`--offset` 和
`--timestamp-ms` 都必须大于 0；读取 offset 0 使用默认 earliest 模式。消息查看还
需要 Topic 读权限。文本输出会剥除不安全终端控制序列，JSON 输出保留原始 body。

`rmq topic create` 默认 dry-run，不提交工单；`--yes` 返回 `approval_pending`、ticket ID 和审批链接，只表示审批已经提交。命令要求 ByteTree 目录节点，安全级别默认 `L2`，`--description` 缺省取 `--purpose`。Topic 完成创建需要等待审批及平台流程。

`topic quota get` 使用独立配额接口，返回各 DC 的生产限额；不能用 `topic get`
的 `produceQuota` 或预期 `qps` 替代。JSON 保留 bytes/s 与 MiB/s
（bytes/s / 1024²，控制台标作 MB/s），以及原始 burst / invalid 配置。
空配额映射不表示无限流，后端失败保持错误。查询不修改配额。

## Topic 查询注意点

- 生产网机器先确认已设置 `BYTEDCLI_NETWORK_PROFILE=prod`；返回 403 且响应体含
  `network_segregation_rejected` 时，是网络与 profile 不匹配，先核对再做下面的搜索。
- `topic list` 默认只查当前用户 owner 范围；跨 Owner 查询全部可见 Topic 时增加
  `--all`。
- 如果平台显示 Topic 存在，但列表为空或详情提示不存在，保留已确认的 `--site` 和
  `--vregion`，先用精确 Topic 名配合 `--all` 搜索，再按名称读取详情。不要根据平台
  跳转后的域名自行猜测或切换 site。
- 权限或认证错误仍是失败，不要解释为 Topic 不存在或空结果。

```bash
bytedcli --site <site> rmq topic list \
  --vregion <vregion> \
  --search "demo_topic" \
  --all

bytedcli --site <site> rmq topic get \
  --vregion <vregion> \
  --topic-name "demo_topic"
```

`consumer config get` 查询存储的 SDK 配置及元数据，`--group-id` 来自同站点和
vregion 的 `consumer list`。配置键值保持字符串原样，包括 `consumer.rate.limit.enable`
和 `consumer.rate.limit.qps`。该结果不代表运行态生效状态；空 map 或缺失键不等于
无限流，后端失败及畸形响应保持为错误。
