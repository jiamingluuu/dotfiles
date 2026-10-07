# Cache

```bash
# 服务列表
bytedcli cache list-starred-service --page 1 --page-size 20
bytedcli cache search-service --keyword "example.cache" --page 1 --page-size 20
bytedcli cache get-service --psm "example.cache"
bytedcli cache get-cluster --psm "example.cache"
bytedcli cache get-idc-topology --psm "example.cache"

# Redis 命令
bytedcli cache list-commands
bytedcli cache execute-command --psm "example.cache" --command "GET" --args "key"

# 慢查询 / 大 Key / 热 Key
bytedcli cache slow-log --psm "example.cache"
bytedcli cache list-big-keys --psm "example.cache" --date "2026-02-05" --start "00:00:00" --end "23:59:59"
bytedcli cache list-hot-keys --psm "example.cache" --date "2026-02-05" --start "00:00:00" --end "23:59:59" --type read

# 多 region 健康汇总 + 高 CPU 根因分析（唯一入口）
#   海外站点使用全局 --site，确保 Cache/APM/ByteDog 路由一致；不要使用 hidden --cache-site
#   --region 可重复；缺省=服务全部 region
#   --range 1h/6h/1d 在未传 --start 时生效，可与 --end 组合指定回溯锚点；显式 --start 优先
#   --time-mode current|historical；默认当前，显式 --start/--end 时默认历史
#   --spike-cpu 实例 CPU 阈值；traffic/latency 只保留为集群级关联信号
#   --top 来源 PSM Top-N（默认 10）
#   --flamegraph-top PID 过滤后热点函数 Top-N（默认 20）
#   --output-dir 制品基础目录；每次运行创建 0700 唯一目录，再为每个实例建独立子目录
#   （未指定时，每个实例创建独立的系统临时目录）
#   --wait-timeout-sec/--poll-interval-sec ByteDog 任务等待与轮询秒数（默认 120/3）
#   --skip-flamegraph 只统计高水位时间和 PID，不创建 ByteDog task
bytedcli cache cpu analyze --psm "example.cache" --range 1h
bytedcli cache cpu analyze --psm "example.cache" --region eu --region sg --spike-cpu 40 --top 5 --flamegraph-top 20
bytedcli cache cpu analyze --psm "example.cache" --start "2026-02-05T10:00:00+08:00" --end "2026-02-05T11:00:00+08:00" --time-mode historical
bytedcli cache cpu analyze --psm "example.cache" --range 30m --skip-flamegraph

# 默认 end=now，按 getCluster 当前 CPU 快照选热点实例；快照缺失时回退到最近完整 CPU 点，
# 再取最近一个完整的 ±30s 事件点。
# 显式历史 --start/--end 时，按同一历史窗口内归一化后的实例 CPU 利用率选热点和峰值。
# CPU counter 会先按时间求 rate，并合并 process user/sys CPU，不把累计值当百分比。
# 输出同时包含 PSM/region/cluster/shard、Host/IP/Port/PID、监控链接、根因、Top 热点、
# 全部已下载原始制品、bytekd、原始 ByteDog 火焰图 URL 和报告路径。
# target_detection_complete=false 表示部分 region/监控输入缺失，不能把未发现热点当作健康结论。

# 实时大/热 Key（auto 模式会重新执行监控目标选择）
#   海外站点使用全局 --site，确保 Cache/APM 路由一致；不要使用 hidden --cache-site
#   --mode hot|big|both（默认 both）
#   auto 模式：不带 --cluster-id，查询当前高 CPU 实例或流量/延迟关联信号所在集群
#   explicit 模式：--cluster-id 指定集群；--shard <idx...> 仅作追溯标注
#   --start/--end/--range 只控制 auto 模式监控目标选择；返回的 Key 始终是实时结果
#   --max-keys-per-cluster 每种 Key、每个集群最多返回条数（默认 20）
#   JSON 的每个 clusters[] 项包含 hot_status/big_status、hot_error/big_error、limit/truncated；
#   truncated=true 时调大上述参数
#   顶层 scan_status=target_detection_incomplete 表示监控输入不完整，不能当作 idle_no_spike
#   接口失败时返回 endpoint_error，不伪造命令回退结果
bytedcli cache hot-key list --psm "example.cache" --mode both --max-keys-per-cluster 20
bytedcli cache hot-key list --psm "example.cache" --cluster-id 10 --shard 0 --shard 1 --mode hot

# 工单
bytedcli cache update-permission --psm "example.cache" --change-type allow --target "example.service.psm"
bytedcli cache update-permission --psm "example.cache" --change-type remove --target "example.service.psm" "example.other.psm" --dry-run
bytedcli cache list-my-tickets --psm "example.cache"
bytedcli cache list-service-tickets --psm "example.cache" --page 1 --page-size 20

# 海外 SG（--site i18n-tt）
bytedcli --site i18n-tt cache list-starred-service

# 海外 US TTP
bytedcli --site ttp-us-limited cache list-starred-service

# 海外 EU TTP
bytedcli --site ttp-eu cache search-service --keyword "example.cache" --page 1 --page-size 20
bytedcli --site ttp-eu cache get-cluster --psm "example.cache"
bytedcli --site ttp-eu cache execute-command --psm "example.cache" --command "GET" --args "key"
```
