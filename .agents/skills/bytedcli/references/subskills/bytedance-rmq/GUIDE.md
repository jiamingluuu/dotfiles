---
name: bytedance-rmq
description: "Operate RMQ (RocketMQ): use bytedcli for topic and consumer discovery/diagnostics, submit Topic creation approvals on existing clusters, send China-BOE topic messages, and safely prepare or submit topic permission applications for PSMs through the RMQ console API. Use when tasks mention RocketMQ/RMQ topics, consumers, producers, producer/write access, consumer/read access, PSM authorization, or message queues."
---

# bytedcli RMQ (RocketMQ)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- RocketMQ / RMQ 话题搜索与详情查看
- 查询 Topic 实际生产限额 / 生产配额（按 DC），区分基础信息与实际流量上限
- 在已有集群上预览或提交 Topic 创建审批
- Topic 消息预览：按最早/最新 offset，或指定 offset/时间戳查看完整消息正文
- Topic 消息投递：China-BOE 区域向指定 Topic 发送一条测试或业务消息
- 消费组列表查询
- 消费组存储的 SDK 配置查询，包括消费限流开关、QPS 和修改时间
- 消费状态（TPS、Lag、Queue 详情）诊断，支持按 Lag 排序截取 Top N 队列
- Queue 分配状态排查，支持按 Broker/Queue 筛选对应 Proxy 信息
- 客户端连接状态查看，支持按 Proxy IP 筛选
- 为一个或多个 PSM 申请 Topic 的 producer/write 或 consumer/read 权限
- 判断权限申请是否已有现成 skill：直接使用本 skill 的权限申请流程，不要切换到 Neptune ACL

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `rmq topic` and `rmq consumer`.

```bash
# Topic 列表（按名称搜索）
bytedcli rmq topic list --vregion "China-BOE" --search "demo_topic"
# 生产网机器上的 i18n-tt 查询，支持全局 --vregion
BYTEDCLI_NETWORK_PROFILE=prod bytedcli --site i18n-tt --vregion Singapore-Central rmq topic list --search "demo-topic" --all
bytedcli rmq topic list --vregion "China-BOE" --page 1 --page-size 20
# 跨 Owner 搜索全部可见 Topic
bytedcli rmq topic list --vregion "China-BOE" --search "demo_topic" --all

# Topic 详情（按 ID 查询）
bytedcli rmq topic get --topic-id 132991 --vregion "China-BOE"

# Topic 详情（按名称查询；同名 Topic 用 Cluster 消歧）
bytedcli rmq topic get --topic-name "demo_topic" --vregion "China-BOE"
bytedcli rmq topic get --topic-name "demo_topic" --cluster-name "demo_cluster" --vregion "China-BOE"

# 实际生产配额（独立于 Topic 基础信息；按 DC 返回）
bytedcli --site cn rmq topic quota get --topic-name "demo_topic" --vregion China-North
bytedcli --site cn rmq topic quota get --topic-name "demo_topic" --cluster-name "demo_cluster" --vregion China-North
bytedcli --json --site cn rmq topic quota get --topic-id 12345 --vregion China-North

# Topic 创建审批 dry-run；只解析已有集群并输出最终 payload
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

# 确认 dry-run 后追加 --yes，提交 Topic 创建审批
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
# 从每个 queue 的最新位置预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" --position latest
# 精确读取指定 broker/queue 的 offset，并向更新消息方向预览
bytedcli rmq topic preview --topic "demo-topic" --cluster "demo-cluster" \
  --offset 1 --direction after --count 5 \
  --idc "demo-idc" --broker "demo-broker" --queue 0

# Topic 消息投递（默认 dry-run；确认请求体后加 --yes 真实投递）
bytedcli --site boe rmq topic send --topic "demo-topic" --cluster "demo-cluster" \
  --body '{"foo":"bar"}'
# 投递时指定 tag、env 和显式 logid
bytedcli --site boe rmq topic send --topic "demo-topic" --cluster "demo-cluster" \
  --body '{"foo":"bar"}' --env boe --tag "demo-tag" \
  --logid "sample-logid" --yes
# 泳道二期投递：CLI 自动把 topic 改成 demo-topic__RMQ_LANE
bytedcli --site boe rmq topic send --topic "demo-topic" --cluster "demo-cluster" \
  --body '{"foo":"bar"}' --env "boe_demo_lane" --swim-lane-v2 --yes

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
```

## Topic 创建审批

- `rmq topic create` 首版仅支持 `--site cn --vregion China-North`，并且只支持已有 RMQ 集群；集群名必须精确匹配
- ByteTree 必须是目录节点；当前登录用户固定为 owner，集群第一个 owner 作为审核人，固定单 broker queue、无序消息与 RocketMQ 类型
- Topic 名只允许字母、数字、下划线和连字符；安全级别默认为 `L2`，`--description` 缺省取 `--purpose`
- 默认 dry-run 不提交工单；显式追加 `--yes` 后返回 `approval_pending`、ticket ID 和审批链接。该结果只表示审批已提交，Topic 尚未完成创建

## Topic 权限申请

`bytedcli rmq` 当前未提供权限申请写命令。当用户要为 PSM 申请 Topic 权限时：

1. 用 `rmq topic list` 找到精确 Topic，仅保留 `topicName` 完全匹配项。
2. 通过 RMQ 控制台只读接口检查现有权限，跳过已授权项。
3. 展示最终 Topic / cluster / vregion / PSM / 权限方向 / review user 列表，等用户明确确认。
4. 确认后才调用 RMQ 控制台写接口创建审批单，并返回可复制的审批链接。

任何写请求前必须先读取 `references/permission-apply.md`。其中定义了权限码、站点隔离、精确匹配、确认门禁、接口参数和部分成功时的回传要求。

## 多站点支持

RMQ 支持多个站点，通过 `--site` 切换：

- `boe`: BOE 环境 (`cloud-boe.bytedance.net`)
- `cn`: 中国站 (`cloud.bytedance.net`)
- `i18n-bd`: ByteIntl (`cloud.byteintl.net`)
- `i18n-tt`: TikTok ROW（办公网 `cloud.tiktok-row.net`；生产网机器设置 `BYTEDCLI_NETWORK_PROFILE=prod` 后为 `cloud-i18n.bytedance.net`）

```bash
# BOE
bytedcli --site boe rmq topic list --vregion "China-BOE" --search "demo"

# 中国站
bytedcli --site cn rmq topic list --vregion "CN" --search "demo"
```

## 实际生产限额

- 使用 `rmq topic quota get` 查询实际生产流量配额。`topic get` 的 `produceQuota` /
  `consumeQuota` 是基础元数据，`qps` 是预期 QPS，不代表实际限流阈值。
- `--topic-id` 与 `--topic-name` 二选一；按名称查询可加 `--cluster-name` 精确定位，
  省略时自动搜索并对同名 Topic 报消歧错误。`--cluster-name` 只用于名称查询。
- 输出每个 DC 的 `bytesPerSecond` 和 `mibPerSecond`，后者等于原始值除以 `1024²`；
  文本标作 MiB/s，控制台将同一数值标作 MB/s。各 DC 配额分别展示，不汇总成全局限额。
- `burst` 保留原始配置值，不推算瞬时峰值；`invalid` 对应后端 `inValidate`，缺失时为 null。
- `configured: false` 表示成功响应中的配额映射为空，不代表无限流或零配额。
  权限不足、后端未配置错误及响应异常保持错误，不转换成空结果。
- 默认 vregion 与其他 Topic 查询一致为 `China-BOE`；查询 CN 生产环境显式使用
  `--site cn --vregion China-North`。查询只读，不修改配额。

## Notes

- 需要结构化输出加 `--json`
- `--vregion` 优先使用子命令显式值，其次逐级继承父命令和全局显式值；都未指定时，`topic list/get/preview` 等查询命令默认为 `China-BOE`，`topic create` 默认且仅支持 `China-North`。
- 在生产网机器查询 `i18n-tt` 时设置 `BYTEDCLI_NETWORK_PROFILE=prod`，Topic 和 Consumer 请求会改用生产网入口 `cloud-i18n.bytedance.net`；办公网不要设置此变量。
- 若返回 403 且响应体含 `network_segregation_rejected`，说明当前网络与 profile 不匹配，先核对再重试；轮换 vregion 或 site 不能解决网络隔离。
- `topic send` 只支持 China-BOE，必须使用 `--site boe`；body 原样传给 RMQ，不校验 JSON
- `topic send` 默认 dry-run 并输出完整请求体；必须显式加 `--yes` 才会真实投递
- `topic send` 的 `--env`、`--tag` 可选；`--logid <logid>` 用于显式指定 `K_LOGID`
- 泳道二期投递使用 `--swim-lane-v2 --env <lane-env>`；CLI 会自动给 topic 加上 `__RMQ_LANE` 后缀
- 消息发送需要 Topic producer/write 权限；权限不足时先申请权限，不要重试掩盖权限错误
- Topic 列表支持 `--search` 按名称模糊搜索和分页（`--page` / `--page-size`）
- Topic 列表默认只查当前用户 owner 范围；跨 Owner 查询全部可见 Topic 时使用 `--all`
- Topic 详情支持 `--topic-id` 或 `--topic-name` 查询；按名称查询遇到同名 Topic 时加 `--cluster-name` 消歧
- `topic preview` 是只读消息查看，不创建 Consumer Group、不消费消息、不修改任何 Consumer offset
- `topic preview` 默认从最早 offset 开始，每个 queue 返回 1 条；可用 `--position latest` 改为最新位置
- 指定位置时使用 `--offset <n>` 或 `--timestamp-ms <ms>`（两者都必须大于 0），并可用 `--direction after|before` 选择向更新或更旧消息方向预览；要读取 offset 0，请使用默认 earliest 模式
- 精确定位单个 queue 时，`--idc`、`--broker`、`--queue` 必须同时传入；`--count` 范围为 1~1000，表示每个 queue 返回的消息数
- 预览返回完整消息正文；文本模式不截断 body，但会剥除不安全终端控制序列，JSON 模式保留原始 body，且 `messages[]` 同时包含 msg ID、broker、queue、offset、时间戳和 properties
- 消息预览除 Topic owner 权限外还需要 Topic 读权限；权限不足时先申请读权限，不要把权限错误解释为 Topic 没有消息
- 当前 `topic preview` 只支持普通 Topic，不支持泳道 Topic、重试队列或死信队列
- Consumer Group 列表需要指定 `--topic-id`
- `consumer config get` 必须传正整数 `--group-id`；从同站点、同 vregion 的
  `consumer list` 返回值中按消费组名称找到 `groupId`。`--vregion` 沿用查询命令的
  `China-BOE` 默认值，CN 查询显式使用 `--site cn --vregion China-North`。
- 配置查询返回 `configId`、`groupId`、`vregion`、`config`、原始 `state`、描述、
  创建人、owners 和创建/修改时间。`config` 保留字符串键值，可读取
  `consumer.rate.limit.enable` 与 `consumer.rate.limit.qps`；不推断单实例/全组限流范围。
- 这是存储的 SDK 配置，不是 Proxy 运行态或实际生效验证。缺失键或空 map 不代表
  关闭限流；权限、未找到或畸形响应保留为错误。文本输出过滤终端控制序列，JSON
  保留配置原值。
- `consumer stats` / `allocation` / `clients` 需要指定 `--topic`、`--group`、`--cluster`
- `consumer stats` 支持 `--top-lag-queue <n>` 按 Lag 倒序截取前 N 个队列信息
- `consumer allocation` 支持 `--broker` 和 `--queue` 筛选指定 Broker/Queue 对应的 Proxy 信息
- `consumer clients` 支持 `--proxy <ip>` 筛选指定 Proxy 的 Client 信息
- allocation 结果按 Broker Cluster → Proxy 层级展示；clients 结果按 Broker Cluster → Proxy → Client 连接串层级展示
- `rmq topic create --yes` 提交的是 Topic 创建审批单；输出不得表述为 Topic 已完成创建
- Topic 权限申请仍需走 RMQ 控制台写操作，不要宣称 `bytedcli rmq` 可以直接申请权限

## References

- `references/rmq.md`：需要完整命令示例或排查 Topic 查询为空时读取
- `references/permission-apply.md`
