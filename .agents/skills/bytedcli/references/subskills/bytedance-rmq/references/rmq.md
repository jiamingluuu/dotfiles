# RMQ (RocketMQ)

```bash
# Mirror 同步链路查询（在目标区域查询，筛选源/目标区域）
bytedcli --site cn rmq mirror list --source-topic "demo-topic"
bytedcli --json --site i18n-tt rmq mirror list --source-vregion US-East \
  --source-topic "demo-topic" --target-topic "demo-target-topic" \
  --target-vregion Singapore-Central --page 1 --page-size 20
bytedcli --site i18n-tt rmq mirror list --source-cluster "demo-source-cluster" \
  --target-cluster "demo-target-cluster" --target-vregion Singapore-Central

# Topic 列表（按名称搜索）
bytedcli rmq topic list --search "demo_topic"
bytedcli rmq topic list --page 1 --page-size 20
# 跨 Owner 搜索全部可见 Topic
bytedcli rmq topic list --search "demo_topic" --all

# Topic 详情（按 ID 查询）
bytedcli rmq topic get --topic-id 132991

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
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster"
# 从最新位置预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" --position latest
# 指定 broker/queue/offset，并向更新消息方向预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" \
  --offset 1 --direction after --count 5 \
  --idc "demo-idc" --broker "demo-broker" --queue 0

# Consumer Group 列表（按 Topic ID 查询）
bytedcli rmq consumer list --topic-id 132991

# 消费组存储的 SDK 配置（group ID 从同站点、同 vregion 的 consumer list 获取）
bytedcli --site cn rmq consumer list --topic-id 12345 --vregion China-North
bytedcli --site cn rmq consumer config get --group-id 23456 --vregion China-North
bytedcli --json --site cn rmq consumer config get --group-id 23456 --vregion China-North

# 消费状态（TPS、Lag、Queue 详情）
bytedcli rmq consumer stats --topic demo-topic --group demo-group --cluster demo-cluster
# 查看 Lag 最高的前 5 个队列
bytedcli rmq consumer stats --topic demo-topic --group demo-group --cluster demo-cluster --top-lag-queue 5

# Queue 分配状态（按 Broker Cluster → Proxy 展示）
bytedcli rmq consumer allocation --topic demo-topic --group demo-group --cluster demo-cluster
# 筛选指定 Broker 和 Queue 对应的 Proxy 信息
bytedcli rmq consumer allocation --topic demo-topic --group demo-group --cluster demo-cluster --broker demo-broker --queue 0

# 客户端连接状态（按 Broker Cluster → Proxy → Client 连接串展示）
bytedcli rmq consumer clients --topic demo-topic --group demo-group --cluster demo-cluster
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

## Mirror 查询注意点

- `--target-vregion` 同时决定请求路由与目标区域过滤；省略时使用已配置的区域，
  否则取站点默认区域。Mirror 不提供独立查询区域参数。
  i18n-tt 下 `SG` / `singapore` 会规范化为 `Singapore-Central`。
- `--source-vregion` 按完整区域名在服务端过滤源区域，省略时包含所有源区域。
  `--site` 决定站点与认证，不会根据目标区域自动切换。
- `--source-cluster` / `--target-cluster` 按大小写敏感的完整集群名精确匹配。
  由于 API 没有已验证的集群过滤字段，传任一集群条件时 CLI 会自动遍历服务端分页，
  再按集群过滤并应用 `--page` / `--page-size`；无集群条件时只请求一页。
- 源/目标 Topic、区域和集群可组合使用；空白过滤值会报输入错误。
- 每次读取一页，默认第 1 页、每页 20 条。JSON 的 `total/page/page_size`
  是全部服务端条件和客户端集群条件共同过滤后的分页信息，可用于继续翻页。
  `context.vregion` 与 `data.vregion` 等于 `data.target_vregion`；
  `data.source_vregion`、`data.source_cluster`、`data.target_cluster` 为对应过滤条件，
  未设置时为 null。
- `mirrors[]` 保留两端 Topic/Cluster/region/vregion、Mirror 集群、状态与策略元数据。
  `state` 为原始数字，`status` 为语义状态，未知状态为 `unknown`，可选元数据缺失为 null。
- 权限或响应错误不会转换为空列表。只读查询，不创建、暂停或删除 Mirror。

## Topic 查询注意点

- 生产网机器先确认已设置 `BYTEDCLI_NETWORK_PROFILE=prod`；返回 403 且响应体含
  `network_segregation_rejected` 时，是网络与 profile 不匹配，先核对再做下面的搜索。
- `topic list` 默认只查当前用户 owner 范围；跨 Owner 查询全部可见 Topic 时增加
  `--all`。
- 没传 `--vregion` 时查的是 `--site` 的默认 vregion，`topic list` 输出里的 `vregion`
  就是实际查询的值；Topic 在同站点其他区（如 `i18n-tt` 的 `Singapore-Central`）时，
  列表和按 ID 查询都要显式传 `--vregion`。
- 多活 Topic 在同站点的多个区各有一份：Topic 名、Cluster 名相同，Topic ID 不同；同名
  消费组在各区各有 ID 和消费状态。不传 `--vregion` 时读的是默认区那份，`--cluster`、
  `--cluster-name` 都不能用来指定区。默认区报错或没有消费记录，不代表其他区也一样，换
  `--vregion` 再查。JSON 的 `context.vregion` 是这次请求用的 vregion，接口报错时也有。
- 如果平台显示 Topic 存在，但列表为空或详情提示不存在，保留已确认的 `--site` 和
  `--vregion`，先用精确 Topic 名配合 `--all` 搜索（`us-ttp` 不加 `--all`），再按名称
  读取详情。不要根据平台跳转后的域名自行猜测或切换 site。
- `us-ttp` 网关不开放 `--all` 背后的全量 Topic 搜索，`topic list --all` 返回
  `RMQ_ALL_TOPIC_SEARCH_UNAVAILABLE`（HTTP 403）。这不是权限问题；在 `us-ttp` 去掉
  `--all` 重试。`topic get --topic-name` 和不带 `--cluster-name` 的
  `topic quota get --topic-name` 在默认 Topic 列表没有精确命中时也返回这个错误码，
  表示只查了默认列表，不能据此判定 Topic 不存在；已知 Topic ID 时改用 `--topic-id`。
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
