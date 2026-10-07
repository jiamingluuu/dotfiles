# 自查:覆盖率低 / 命中流量少(L1)

目录：[适用现象](#适用现象) · [量化当前覆盖](#第一步量化当前覆盖) · [故障树](#故障树) · [输出](#输出)

## 适用现象

- 采集到了流量,但条数远低于预期;某些接口/场景几乎没覆盖。
- 任务 `task_flow_count` / `case_count` 很小。
- Tesla 测试计划里 `link_calls` 为空,或录制状态没更新。

和“完全没有流量”的区别是：这里**能采到一部分**，只是量少 / 面窄。若一条都没有，必须按
上下文分流：没有任务/回放语境的独立录制问题进入 `diag-record.md`；已有任务 ID/链接、明确回放
语境或 `status=7` 时进入 `diag-replay.md`，由它继续区分实时采集链和非实时来源筛选漏斗。
下列 ID-only 示例固定为 cn；URL 派生 ID 必须复用冻结站点，zg 使用全局前缀
`--site cn --vregion China-Pay`。裸 ID 未附站点时先索取，不得猜测。

## 第一步:量化当前覆盖

```bash
# 任务级流量/用例规模
bytedcli --json --site cn ftf task get --id 1234567 \
  | jq '.data | {task_flow_count, case_count, diff_case_count, case_filter_mode, single_scene_replay_count, nario_task_id, scene_coverage}'

# 某 method 实际命中流量数
bytedcli --json --site cn ftf task flow list --task-id 1234567 --psm example.psm --method GetDemo --page-size 20 \
  | jq '.data | {page_size, page_count:(.flows | length), next_cursor, has_more}'
```

- `case_filter_mode` 说明流量来源类别(见 `enums.md#case_filter_mode`):实时 / 场景 /
  历史 / 手动圈选 / 智选。来源不同,"覆盖低"的解法不同(历史流量看采集窗口,场景流量
  看场景圈选)。
- `scene_coverage` / `nario_task_id` 反映场景覆盖度,场景类回放低覆盖优先看这里。
- `task flow list` 不返回全量总数；`page_count` 只表示当前页命中条数。若
  `has_more=true`，用 `next_cursor` 继续翻页后再累计覆盖面。

## 场景覆盖报告转 Nario

当用户要回答“哪些 Nario 场景没有命中”“低覆盖集中在哪些 method/模板”时,不要继续使用
FTF method 流量条数猜测场景级结论。FTF task 已关联 `nario_task_id` 时,转到 Nario
度量报告:

```bash
# 由 CLI 从 FTF task 解析真实 Nario 度量任务 ID。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report get \
  --ftf-task-id 1234567 \
  --ftf-env cn

# 使用上一步 resolvedTask.taskId,不要把 FTF task ID 直接传给 --task-id。
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario measure report scene-detail \
  --task-id <nario-task-id> \
  --summary
```

- Nario `measure report` / `scene-detail` 是任务级场景 hit/miss 和低覆盖分布的首选证据。`scene-detail --summary` 只提供 Top 分组和每组最多 5 个未覆盖样例；完整精确清单必须分页读取非汇总明细，并筛选命中流量计数为 `0` 的场景行。
- `ftf task flow list` 的 method 流量分布只能解释流量多少,不能精确判定未命中场景。
- 不要改用 Nario raw OpenAPI 试探 task/coverage endpoint,也不要根据场景元数据、创建时间或
  规则形态猜测具体未命中场景。
- 如果缺少 `NARIO_OPENAPI_AUTHORIZATION_TOKEN`,先报告认证阻塞。用户要求继续时,可将 FTF
  task 的目标场景 ID 与各 flow detail 的 `scene_ids` 做集合差,并明确标记为“FTF 数据降级计算”,
  不能表述为 Nario 原生度量报告。

## 故障树

### 1. 采样率把量压低了(sdk)

稳定判据:sdk 默认均匀随机采样,约 **10s 采一条**,量天然不高。采样率 tcc 配置
namespace `pdiqa.ftf.rinnegan`,key `psm_sample_ratio`;单实例录制比例区间 [0.01, 1],
**最高不超过 1qps**。

动作:需要更高频可调 `psm_sample_ratio`(受 1qps 上限约束)。tcc 配置 CLI 不可见,给
用户 key 引导核实。

### 2. 流量本身稀疏 → 用定向采集

稳定判据:某些场景线上流量少,随机采样很难命中。FTF 提供**定向采集**(只能在请求前
决定是否采),以及自定义方法采集。

动作:引导用户按 onepage「定向采集」/「自定义方法采集」接入。属接入改造,CLI 不涉及。

### 3. 接口打到了非默认集群

稳定判据:FTF 默认只采 canary 的 `default` 集群;打到别的集群的接口不会被采,表现为
"部分接口有、部分没有"。

动作:在 `bootstrap.sh` 加对应采集集群条件(同 `diag-record.md` 节点 3)。CLI 不可见。

### 4. `link_calls` 为空 / 录制状态没更新(Tesla 测试计划)

稳定判据(来自 onepage「tesla 测试计划」):

- `link_calls` 为空,自查:① SCM 配置里打开"FTF 录制 Mock 插桩";② 部署的是测试版本 /
  线下版本编译包。
- 录制状态没更新:① 加 SCM 环境变量 `CUSTOM_TESLA_OPEN=1`;② 确认"FTF 录制 Mock 插桩"
  已开;③ 确保编译版本是加了环境变量之后编译的。

动作:均在 SCM 配置 / 编译产物,CLI 不可见,列外部待验证项引导核实。

### 5. 采集窗口 / 流量筛选口径

稳定判据:历史流量 / 场景流量受采集时间窗与圈选口径影响。若 `case_filter_mode` 是历史
或场景流量,低覆盖可能只是窗口太窄或圈选条件太严,不一定是接入问题。

动作:确认采集时间窗与场景圈选范围;必要时放宽后重采 / 重新圈选。

## 与 mock 的区分

覆盖率低有时被误报成"mock 有问题"——实际是流量根本没覆盖到那条链路。先用本文件确认
覆盖面,再决定要不要进 `diag-mock.md`。

## 输出

按 `replay-diagnosis.md#报告口径` 输出。覆盖率类务必:

- 用 `task_flow_count` / `task flow list page_count` / `scene_coverage` 量化当前覆盖,给出"实际 vs
  预期"的差距,而不是笼统说"覆盖低";
- 用户要求 Nario 场景级结果时,补充 `resolvedTask.taskId`、Nario 报告 hit/miss、低覆盖
  method/模板;只有非汇总场景明细已完整分页读取时才列精确未命中场景 ID,否则明确样例
  限制或证据缺口;
- 采样率 / 定向采集 / 集群条件 / Tesla 插桩开关都在 tcc / SCM / bootstrap.sh,列外部待
  验证项 + 对应 key / 开关名;
- 区分"量少但正常抽样"与"接入 / 配置导致的漏采";无果带 task 证据发起 FTF oncall。
