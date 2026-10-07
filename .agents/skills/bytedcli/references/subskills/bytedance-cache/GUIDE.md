---
name: bytedance-cache
description: "Operate Cache platform via bytedcli: list/search cache services, inspect clusters and realtime hot/big keys, locate current or historical high-CPU Redis instances, resolve Host/IP/Port/PID, analyze PID-filtered ByteDog flamegraphs, execute Redis commands, query slow logs, manage Redis auth tickets, and inspect support tickets. Use when tasks mention cache services or clusters, Redis CPU high, ByteDog/flamegraphs, hot or big keys, slow logs, Redis auth, IDC topology, tickets, latency, performance, memory usage, abnormal keys, or service health. Do not use for general Redis programming questions, non-Bytedance Cache resources, or concept-only explanations that do not require bytedcli."
---

# bytedcli Cache

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

- 缓存服务搜索 / 收藏 / 详情
- 缓存集群详情 / 实例列表
- Redis 支持命令列表 / 命令执行
- 慢查询、大 Key、热 Key 查询
- 多 region 集群健康汇总、高 CPU 实例根因与 ByteDog 火焰图（`cache cpu analyze`）
- 高 CPU 集群的实时大/热 Key 关联排查（`cache hot-key list`）
- Redis 鉴权 PSM 增删工单
- 工单管理
- 支持国内站（prod）和海外站；使用全局 `--site` 选择站点：`i18n-tt`（SG）、`ttp-us-limited`（US TTP）、`ttp-eu`（EU TTP）

## Do not use

- 不适用于通用 Redis 编程问题
- 不适用于 Bytedance Cache 平台以外的资源问题
- 不适用于无需 bytedcli 的概念性解释问题

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 服务列表
bytedcli cache list-starred-service --page 1 --page-size 20
bytedcli cache search-service --keyword "example.cache" --page 1 --page-size 20
bytedcli cache get-service --psm "example.cache"
bytedcli cache get-cluster --psm "example.cache"
# IDC 拓扑（region/idc 的 role 与 follow）
bytedcli cache get-idc-topology --psm "example.cache"

# Redis 命令
bytedcli cache list-commands
bytedcli cache execute-command --psm "example.cache" --command "GET" --args "key"

# 慢查询
bytedcli cache slow-log --psm "example.cache"
# 大 Key
bytedcli cache list-big-keys --psm "example.cache" --date "2026-02-05" --start "00:00:00" --end "23:59:59"
# 热 Key
bytedcli cache list-hot-keys --psm "example.cache" --date "2026-02-05" --start "00:00:00" --end "23:59:59" --type read

# 多 region 集群健康汇总 + 高 CPU 分片 PID/ByteDog 根因分析
bytedcli cache cpu analyze --psm "example.cache" --range 1h
# 无 ByteDog 权限时只统计高水位时间和 PID
bytedcli cache cpu analyze --psm "example.cache" --range 1h --skip-flamegraph
# 消费高 CPU 实例所在集群，查实时大/热 Key
bytedcli cache hot-key list --psm "example.cache" --mode both --max-keys-per-cluster 20

# 工单
bytedcli cache update-permission --psm "example.cache" --change-type allow --target "example.service.psm"
bytedcli cache update-permission --psm "example.cache" --change-type remove --target "example.service.psm" "example.other.psm" --dry-run
bytedcli cache list-my-tickets --psm "example.cache"
bytedcli cache list-service-tickets --psm "example.cache" --page 1 --page-size 20
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json cache list-starred-service ...`）
- Flag rename: `--page-num` is now `--page`; the old name still works as a hidden alias
- 海外 TTP 场景使用全局 `--site ttp-us-limited` 或 `--site ttp-eu`；别名 `us-ttp` / `eu-ttp` 也可用。只访问 cache API 的既有命令保留 hidden `--cache-site` 兼容入口；跨 Cache/APM/ByteDog 的 `cache cpu analyze` 和 `cache hot-key list` 必须使用全局 `--site`，确保所有后端落在同一站点。
- `cache update-permission` 提交 Redis 鉴权变更工单，不直接修改服务字段；`--change-type allow|remove` 分别表示添加 / 删除鉴权，`--target` 传一个或多个目标 PSM，`--dry-run` 只打印请求体不提交。

## Agent Guidance

- 认证（必读）：所有 cache 命令走 `getBytecloudJwtForSite`，依赖 **session JWT cache**。该 cache 只由阻塞式 `bytedcli auth login --session` 兑换并写入（内部 `loginByteCloudSessionAndSaveJwt`）。默认 `auth login`（service-account）会报"非法的应用账号"，`auth login --begin --session` 只复用 SSO 浏览器 session、不兑换 JWT，二者都无法让 cache 命令可用。遇到 `AUTH_REQUIRED` / `http 401` 时，先跑 `bytedcli auth login --session` 再重试，不要反复换登录子命令。注意 `auth status` 顶层可能显示"未登录"，但 session JWT cache 命中时 cache 命令仍可用——以命令实际返回为准，不要被 `auth status` 误导。
- `cache hot-key list` 空结果有结构化字段，不要靠 warning 文案猜：顶层 `scan_status` 为 `scanned`、`idle_no_spike` 或 `target_detection_incomplete`；只有第二种能判定当前没有热点，第三种表示 region/监控输入缺失，需先看 warnings 并重试。每个集群 `status` 是聚合结果，`hot_status` / `big_status` 分别记录各接口的 `ok` / `empty` / `permission_denied` / `endpoint_error`（未请求为 `null`），对应的 `hot_error` / `big_error` 保留结构化错误诊断。每个集群还包含 `limit` / `truncated`；`truncated=true` 时调大 `--max-keys-per-cluster`。该命令只调用真实的集群级实时接口；接口失败会明确返回 `endpoint_error`，不会用 redis-cli flag 伪造 Redis 命令结果。
- `cache cpu analyze` 是 CPU 根因分析的唯一出口。`cache hot-key list` 的 auto 模式会用同一监控逻辑重新定位当前高 CPU 实例或流量/延迟关联信号所在集群；需要指定集群时用 `--cluster-id`（可加 `--shard` 仅作追溯标注）。实时热 Key 只反映命令执行时的集群状态，`--start/--end/--range` 仅用于 auto 模式的监控目标选择，不能回看历史热 Key。`--range` 在未传 `--start` 时生效，可与 `--end` 组合指定回溯锚点；显式 `--start` 优先。
- `cache cpu analyze` 区分当前与历史窗口：默认用 `current`，先以 getCluster 当前 CPU 快照缩小实例范围；快照缺失时回退查询最近完整 CPU 点，再用最近一个已具备完整 ±30 秒窗口且仍超过阈值的 CPU 点确认。显式 `--start/--end` 默认用 `historical`，也可通过 `--time-mode current|historical` 明确选择。实时热 Key API 只有集群粒度，只能做关联证据，不能替代实例 CPU 监控定位 Host/IP/Port。
- CPU 时序同时查询 `cap.redis.used_cpu_sys_process` 和 `cap.redis.used_cpu_user_process`。返回百分比单位时直接使用；返回累计 CPU 时间时先按采样间隔求 rate，再合并 user/sys 为进程 CPU 利用率，不能直接对累计 counter 取最大值。
- CPU 事件时间确定后，先在同一 ±30 秒窗口查询 `cap.redis.process_id`，只接受事件时刻或之前最近的唯一 PID；没有历史点或同一时间存在多个 PID 时拒绝猜测，避免把重启后的 PID 归到旧事件。Host/IP/Port/PID 准备完整后才创建 ByteDog 60 秒 continuous profile；任务仍是 host-wide，不传 PID，下载 bytekd 后按栈根 PID 过滤。
- CPU 指标查询和 ByteDog 任务分别使用固定并发上限，避免大服务同时创建无界任务。输出包含 PSM/region/cluster/shard、Host/IP/Port/PID、当前/历史检测模式、高水位与窗口、监控链接、原始 ByteDog 火焰图 URL、全部已下载原始制品、bytekd 文件、匹配 record/stack、热点函数、结构化根因，以及 `report_path` 指向的 Markdown 报告；显式 `--output-dir` 是基础目录，每次运行先创建权限为 `0700` 的唯一目录，每个实例再使用独立子目录，避免并发或重复运行时制品互相覆盖。`target_detection_complete=false` 表示部分 region 或监控输入缺失，此时不能把未发现热点当作健康结论。单实例失败保留为 `status:"failed"` 与标准结构化 `error`，不丢弃其它分片结果；无权限可用 `--skip-flamegraph` 只解析时间、PID 并生成报告。
- 根因分类覆盖 Lua/script、Redis module、过期删除、RDB/AOF、复制、网络回复、内存分配/拷贝、数据结构和命令执行；未知符号会返回 `unknown_native_path`，应结合 `top_frames` 与 ByteDog `detail_url` 人工确认。

## References

- `references/cache.md` — 缓存相关命令的完整参数与详细说明
- `../../troubleshooting.md` — 常见失败、权限 / 登录、站点选择和命令报错的处理步骤
