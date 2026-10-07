# FundEye 命令说明

## 目录

- [当前覆盖能力](#当前覆盖能力)
- [参数约定](#参数约定)
  - [Risk-O 业务变更分析](#risk-o-业务变更分析)
  - [规则详情](#规则详情)
  - [规则列表](#规则列表)
  - [创建规则](#创建规则)
  - [Fullink 子规则 creategetupdate](#fullink-子规则-creategetupdate)
  - [Fullink 双流子规则整体调试](#fullink-双流子规则整体调试)
  - [Govaluate 脚本生成与校验](#govaluate-脚本生成与校验)
  - [Fullink Go 函数生成与编译检查](#fullink-go-函数生成与编译检查)
  - [发布规则deploy](#发布规则deploy)
  - [业务归属查询](#业务归属查询)
  - [diff 明细](#diff-明细)
  - [diff 列表](#diff-列表)
  - [diff 处理update](#diff-处理update)
  - [告警列表](#告警列表)

## 当前覆盖能力

- `fundeye risko trigger [--repo-dir <path>] [--psm <psm>] [--git-repo <repo>] [--branch <branch>] [--commit-id <commit>] [--mr-url <url>] [--user-name <name>] [--meego-id <id>] [--meego-url <url>] [--dry-run]`
- `fundeye rule get --rule-id <rule-id>`
- `fundeye rule list`
- `fundeye tag search`
- `fundeye rule single create|get|update`
- `fundeye rule double create|get|update`
- `fundeye rule double debug --rule-id <rule-id> --rule-version <version> --edge-seq <seq> (--upstream-data '<json>' | --upstream-data-file <file>) (--downstream-data '<json>' | --downstream-data-file <file>)`
- `fundeye rule udf create|get|update`
- `fundeye rule create --product-type fullink|tcheck --rule-owner <owner> --params '<json>'`
- `fundeye rule full-create --params '<json>'`
- `fundeye rule save-draft --product-type tcheck --rule-id <rule-id> --params '<json>'`
- `fundeye rule deploy --product-type tcheck --rule-id <rule-id> [--skip-recommend] [--skip-check]`
- `fundeye tag search --name <keyword> [--product tcheck]`
- `fundeye biz get --path '<层级1-层级2>'`
- `fundeye diff get --diff-id <diff-id> --rule-id <rule-id>`
- `fundeye diff list --rule-id <rule-id>`
- `fundeye diff update --reason <parent||child> (--diff-list '<json>' | --alarm-order-id-list '<json>')`
- `fundeye diff retry --try-list '<json>'`
- `fundeye alarm list`
- `fundeye check-record list --rule-id <rule-id>`
- `fundeye check-record rerun --rule-id <rule-id> --business-time <time>`

## 参数约定

### Risk-O 业务变更分析

```bash
bytedcli --json fundeye risko trigger \
  --psm example/demo_order_service \
  --git-repo 'git@example.invalid:example/demo_order_service.git' \
  --branch feature/demo-analysis \
  --commit-id 0123456789abcdef0123456789abcdef01234567 \
  --user-name demo-user
```

```bash
bytedcli --json fundeye risko trigger --repo-dir /path/to/repo --dry-run
```

- `task_type` 固定为 `REQUIREMENT_DIMENSION_ANALYSIS`
- `trigger_source` 固定为 `cli`
- 若未显式传 `--git-repo`、`--branch`、`--commit-id`，CLI 会从 `--repo-dir`（默认当前目录）的 git 仓库自动读取
- 若未显式传 `--psm`，CLI 会尝试从 git remote 的最后两个路径段推断，例如 `example/demo_order_service`
- 若未显式传 `--user-name`，CLI 会回退到当前 bytedcli 登录用户；若仍拿不到则直接报错，要求传 `--user-name` 或先登录
- `--dry-run` 只输出最终 snake_case payload，不真正触发分析
- 返回结果会原样保留服务端响应，并额外提取 `base.status_code`、`base.status_message`、`is_success`、`task_id`、`task_detail_url`、`trigger_msg` 等常用字段
- 当成功返回 `task_id` 时，CLI 会额外拼出任务详情链接 `task_detail_url`，格式类似 `https://fundeye.bytedance.net/scene_risk/scene/requirement-defense?taskId=<task_id>&step=codeAnalysis`
- 当返回 `is_success: false` 时，CLI 会把 `trigger_msg` 作为错误信息抛出，不会误判成成功

### 规则详情

```bash
bytedcli --json fundeye rule get --rule-id 2604202570843580
```

- 对外参数统一使用 `--rule-id`
- 规则详情默认查询 `fullink`；查询 `tcheck` 时使用 `--product-type tcheck`
- 支持预留参数 `--site`、`--tenant`；当前仅占位，不影响请求逻辑
- `fullink` 保持原有返回结构，JSON 输出不包含 `layoutInfo`、`raw`
- `tcheck` 返回原生字段，例如 `rule_id`、`name`、`period`、`sql`、`receiver`

### 规则列表

```bash
bytedcli --json fundeye rule list \
  --product-type fullink \
  --name "demo-rule" \
  --owner "demo-owner" \
  --status RUNNING \
  --status DRAFT \
  --business-ownership demo-biz \
  --page 1 \
  --page-size 10
```

```bash
bytedcli --json fundeye rule list \
  --product-type tcheck \
  --name "demo-rule" \
  --owner "demo-owner" \
  --status unpublished \
  --status open \
  --period daily \
  --business-ownership demo-biz \
  --page 1 \
  --page-size 10
```

- 默认产品类型是 `fullink`
- CLI 使用重复 `--status`；`fullink` 映射成 `status`，`tcheck` 映射成 `status[]`
- `fullink` 支持：`--name`、`--owner`、`--status`、`--business-ownership`
- `tcheck` 额外支持：`--period`、重复 `--tag-id`

### 创建规则

```bash
bytedcli --json fundeye rule create \
  --product-type fullink \
  --rule-owner "demo-owner" \
  --params '{"owner":"demo-owner","business_ownership":"demo-biz","lark_no":"","rule_type":"double_check","data_sources":[{"vertex":"up","db_name":"sample_upstream_db","tb_name":"sample_upstream_table","filter_logic":"status == 98","is_trigger":true},{"vertex":"down","db_name":"sample_downstream_db","tb_name":"sample_downstream_table","filter_logic":"pay_status == \"SUCCESS\"","is_trigger":true}],"join":[{"from_vertex":"up","to_vertex":"down","join_info":"[{\"upstream\":\"order_id\",\"downstream\":\"out_order_no\"}]"}],"check_logic":"[up.total_amount] == [down.total_amount]"}'
```

```bash
bytedcli --json fundeye rule create \
  --product-type tcheck \
  --rule-owner "demo-owner" \
  --params '{"data_source_type":"krypton","check_tables":["sample_db.sample_table_a","sample_db.sample_table_b"],"user_check_requirement":"关联键: sample_key_a 和 sample_key_b; 核对规则: 筛选上游有记录但下游无匹配记录的异常数据; 输出字段: sample_field_a、sample_field_b"}' \
  --poll \
  --max-retries 30 \
  --interval 3
```

- `--product-type` 支持 `fullink`、`tcheck`

- 新建 Fullink 时，默认优先判断子规则链路：`fundeye rule double create`、`fundeye rule udf create`、`fundeye rule single create`；尽量不要先用 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`
- 只有在用户明确要求整条 Fullink 规则一次创建，或输入天然就是 legacy `data_sources/join/check_logic` 结构时，才回退到 `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'`
- 规则创建支持 `cn` 和 `sinf`（火山云/volc）；传入 `--sitename sinf`、`--sitename volc` 或 `--sitename 火山云` 时，后端收到 `site_name: "sinf"`；`sg`、`ttp`、`eu-ttp` 等其他站点会被直接拒绝
- `fundeye rule full-create` 目前仅支持 `cn`；它直接走 tcheck 底层 create + update 接口

- `--params` 必须是 JSON 对象字符串；CLI 会把它再次序列化成接口要求的字符串字段 `params`
- CLI 会自动把 `--params` 包装进请求体 `{"source":"platform_api","agent_task_list":[{"task_type":...,"rule_owner":...,"params":"..."}]}`，不需要手动传整段外层 JSON
- `fullink` 的 `--params` 至少包含：`owner`、`rule_type`、`data_sources`、`join`、`check_logic`
- `fullink` 的 `data_sources` 至少 2 个数据源；每项至少包含 `vertex`、`db_name`、`tb_name`
- `fullink` 的 `join[].join_info` 需要传字符串，字符串内容通常仍是 JSON 数组
- `tcheck` 的 `--params` 至少包含：`data_source_type`、`check_tables`、`user_check_requirement`
- `tcheck` 的 `data_source_type` 合法值为 `"krypton"` 或 `"hive"`；用户未指定时根据 `check_tables` 推断：
  - 库名前缀命中 `noveldb`/`novel_op`/`novel_original`/`novel_bookdb`/`novelsale_distributordb`/`parallel_commerce`/`lvideo_compass`/`pgcincome`/`ocean_story`/`ocean_story_split`/`dpa_data` → `"krypton"`
  - 表名含 `ods_`/`dwd_`/`dim_`/`dm_`/`ads_`/`dwm_`/`dwa_` 分层前缀 → `"hive"`
  - 库名前缀命中 `webcast`/`open`/`aweme`/`pgc`/`ies_wallet`/`ad_star`/`dm_ttgame`/`dm_effect_platform`/`toutiao_dw`/`caijing_dw` → `"hive"`
  - 均不命中时主动询问用户
- `tcheck` 的 `check_tables` 必须是非空列表
- 如果规则或子规则涉及脚本，先区分 `govaluate` 与 Go/Yaegi：前者用于表达式约束，后者用于核对主逻辑
- 推荐 Agent 流程：先生成脚本，再调用现有校验/编译接口确认通过，最后再发 `create` / `update`
- 若环境中已安装 `govaluate_script_gen`，生成 `govaluate` 时优先使用；若不可用，则先参考现有脚本手册或向用户追问字段与约束
- `--poll` 会继续调用 `query_tasks`，直到拿到 `rule_link`、失败或超时
- 轮询参数使用 `--max-retries`、`--interval`

### TCheck 全量创建

```bash
bytedcli --json fundeye rule full-create \
  --params '{"name":"demo-tcheck-rule","illustration":"demo desc","period":"daily","daily_run_time":"00:00:00","owner_list":["demo-owner"],"member_list":["demo-member"],"permission_group":["group.demo"],"business_ownership":"demo-biz","receiver":"demo-owner","lark_group_id":"oc_demo_group","priority":"P1","diff_limit":100,"sql":"select 1","check_tables":["sample_db.ods_demo_table"],"depend":{"upstream_depend":[{"dorado_id":123,"name":"demo task","frequency":"daily","offset_type":"set","offset":[0]}]}}'
```

- 仅支持 `tcheck`
- `--params` 必须是前端编辑页 update body 风格的 JSON 对象字符串
- CLI 会先调 `/api/t_check/rule` 创建空壳规则，再调 `/api/t_check/rule/:rule_id` 完成完整配置
- `data_source_type` 可省略；CLI 会按 `check_tables` 推断 `hive`/`krypton`，显式传入时会先统一转成小写
- `owner_list` 可省略；缺省时回退到当前登录用户
- `period` 必填；当 `period=daily` 时需提供 `daily_run_time`，当 `period=hourly` 时需提供 `hourly_run_minute`
- `task_run_time`、默认 `task_pending_alarm` 等依赖字段无需手填，CLI 会按前端逻辑推导；其中 `krypton/clickhouse` 的 `task_pending_alarm` 固定为 `1`
- 当前仅支持 `cn`；显式传入非 `cn` 的 `--sitename` 会直接报不支持

### 保存规则草稿（save-draft）

```bash
bytedcli --json fundeye rule save-draft \
  --product-type tcheck \
  --rule-id 20260601_1234567890000 \
  --params '{"tag_ids":["tag-a","tag-b"]}'
```

- 当前仅支持 `tcheck`
- 该命令只保存草稿，不会发布规则
- `--params` 必须是 JSON 对象字符串
- CLI 会先调用 `fundeye rule get` 读取当前规则，再把 `--params` 里的字段覆盖到最新规则体上，然后调用保存草稿接口
- 因此日常只需要传这次要更新的字段，例如：
  - 只改标签：`{"tag_ids":["tag-a","tag-b"]}`
  - 只改接收人：`{"receiver":"demo-owner"}`
  - 同时改多个字段：`{"tag_ids":["tag-a"],"priority":"P1"}`
- 支持 `--sitename volc/火山云` 路由到火山环境

### Fullink 子规则 create/get/update

```bash
# 创建 Fullink 时优先先看 double create
bytedcli --json fundeye rule double create \
  --scene-name "demo-scene" \
  --payload '{"edge_table_join":{"edge_seq":1,"from_vertex":1,"to_vertex":2},"vertex_table_list":[{"vertex_seq":1,"vertex_name":"up"},{"vertex_seq":2,"vertex_name":"down"}]}'

bytedcli --json fundeye rule udf create \
  --scene-name "demo-scene" \
  --payload-file /tmp/demo-udf.json

bytedcli --json fundeye rule single create \
  --scene-name "demo-scene" \
  --payload-file /tmp/demo-single.json
```

- 三类子规则都支持 `create`、`get`、`update`
- 新建 Fullink 时，Agent 默认按这个顺序先判断可行性：`double create` → `udf create` → `single create`
- `fundeye rule create --product-type fullink --rule-owner <owner> --params '<json>'` 只作为 legacy/兜底路径，不作为默认首选
- `create` 支持 `--payload` 或 `--payload-file`，两者二选一
- `create` 不传 `--scene-id` 时会创建新 scene，传了则追加到现有 scene
- `create` 可选补充 `--scene-name`、`--business-ownership`、重复 `--owner`、`--priority`
- `get`/`update` 必须传 `--scene-id` 与 `--sub-rule-id`
- `single get/update` 的 `--sub-rule-id` 对应 `single_ds_check_id`
- `double get/update` 的 `--sub-rule-id` 对应 `edge_seq`
- `single` 的 payload 直接透传 open single_rule 所需字段
- `double` 的 payload 需要包含 `edge_table_join`，可附带 `vertex_table_list`
- `udf` 的 payload 需要包含 `udf`，可附带 `vertex_table_list`；若是多数据源 UDF，还应提供 `edge_table_join_list`。CLI 会默认把这些 edge 的 `upstream_trigger_type/downstream_trigger_type` 补成 `NOTRIGGER`，对应触发逻辑补成 `false`。
- `double` 中若某个 vertex 是 MQ 类型（RocketMQ/Kafka/Tea），且未显式传 `mq_uniq_index`，CLI 会优先按 `join_expression` 的同侧关联键自动补齐该字段
- 涉及脚本时，先判断字段属于哪类：`govaluate` 常见于 `filter_script`、`join_expression`、`vertex_table_list[].filter`、`mq_uniq_index`、触发条件；Go/Yaegi 常见于 `single.golang_check_script.script`、`double.edge_table_join.check_logic`、`udf.script`
- 推荐 Agent 工作流：确定脚本类型 → 生成脚本 → 调现有校验/编译接口 → 校验通过后再 `create/update`
- 对 `govaluate` 不要凭空拼复杂语法；如果 `govaluate_script_gen` 不可用，优先让用户补字段说明、样例数据或现有脚本
- 安全 payload 样例见 `references/subrule-payload-examples.md`
- JSON 输出统一包含 `scene_id`、`sub_rule_id`（更新接口只返回 `base_resp`）

### Fullink 双流子规则整体调试

准备 `/tmp/demo-upstream.json`：

```json
{
  "id": "sample-1",
  "status": 1
}
```

准备 `/tmp/demo-downstream.json`：

```json
{
  "id": "sample-1",
  "status": 2
}
```

执行：

```bash
bytedcli --json fundeye rule double debug \
  --rule-id demo-rule \
  --rule-version 7 \
  --edge-seq 1 \
  --upstream-data-file /tmp/demo-upstream.json \
  --downstream-data-file /tmp/demo-downstream.json
```

- 必须提供 `--rule-id`、`--rule-version` 和 `--edge-seq`；CLI 会读取指定版本规则并自动选择该边及其上下游节点
- 上游样例使用 `--upstream-data` 或 `--upstream-data-file`，下游样例使用 `--downstream-data` 或 `--downstream-data-file`；每侧二选一
- 样例必须是非空且可解析的 JSON 对象或数组；CLI 保留原始 JSON 文本，避免大整数重新序列化后丢失精度
- 用户不需要也不应手工提供 `edge_table_join` 或 `vertex_table_list`
- `aggregation_type=NO_AGGREGATION` 时，上下游调试数据都传单个 JSON 对象
- 聚合核对时，按 `UP_1_TO_DOWN_N` / `UP_N_TO_DOWN_1` 把 N 侧调试数据传成 JSON 对象数组
- JSON 输出包含 `code`、`err_msg`、`debug_result_list`、`log_info`；每个场景包含 `scene_name`、`hint_symbol` 和 `detail_info_list`
- 服务端返回 `code != 0` 时，CLI 会以 `FUNDEYE_ERROR` 返回 `err_msg`

### Govaluate 脚本生成与校验

- 只用于表达式脚本，不替代 Go/Yaegi 核对主逻辑
- 先分 3 类场景：单数据源筛选、双数据源核对、Binlog 变更
- 单数据源直接用字段名；双数据源用 `up.` / `down.`；Binlog 变更使用 `before__field` 与 `field`
- 最终交付前必须先进入当前 skill 目录执行：

```bash
node -r ts-node/register/transpile-only scripts/check_govaluate.ts "<脚本内容>"

如需走 PPE，只能通过 bytedcli 全局 `--http-header` 透传 `x-tt-env` / `x-use-ppe`；不要在脚本或命令模板里写死具体 PPE lane。
```

- 若返回 `data.ok = false`，要根据错误信息修正后重试
- 输出脚本代码块时统一使用 `javascript`
- 细节规则见：
  - `references/govaluate-script-gen.md`
  - `references/udf_functions.md`
  - `references/govaluate-syntax.md`

### Fullink Go 函数生成与编译检查

- 用户提到 Filter / Generate / Verify、Fullink Go 函数、主动查数时，优先阅读：
  - `references/fullink-go-func.md`
  - `references/external-apis.md`
- 先确认函数场景与入参类型：
  - 场景：筛选条件 / 关联键 / 双参数核对 / 聚合核对 / 单流核对
  - 入参：`map[string]interface{}` 或 `string`
- 生成代码时要遵守：
  - 不写 `package`
  - 不 import 已预导入包
  - 只用 `log.Info`
  - 只允许 import 未预导入的 Go 标准库
- 最终交付前必须先进入当前 skill 目录执行：

```bash
node -r ts-node/register/transpile-only scripts/compile_check.ts \
  --script "func Verify(up map[string]interface{}, down map[string]interface{}) (bool, error) { return true, nil }" \
  --param-types "map[string]interface{}" "map[string]interface{}" \
  --func-name "Verify"
```

- 若返回 `data.ok = false`，要根据错误信息修正后重试

### 发布规则（deploy）

```bash
bytedcli --json fundeye rule deploy \
  --product-type tcheck \
  --rule-id 20260601_1234567890000

# 跳过依赖推荐（非 hive 数据源时自动跳过，也可手动指定）
bytedcli --json fundeye rule deploy \
  --product-type tcheck \
  --rule-id 20260601_1234567890000 \
  --skip-recommend

# 跳过合法性校验，直接发布
bytedcli --json fundeye rule deploy \
  --product-type tcheck \
  --rule-id 20260601_1234567890000 \
  --skip-check

# 同时跳过依赖推荐和合法性校验
bytedcli --json fundeye rule deploy \
  --product-type tcheck \
  --rule-id 20260601_1234567890000 \
  --skip-recommend --skip-check
```

- 当前仅支持 `tcheck`
- 走平台鉴权 headers（`x-jwt-token` + `UserName`）
- 支持通过 `--sitename sg` 切到新加坡机房，或通过 `--sitename us-ttp` 切到 TTP US 机房，或通过 `--sitename eu-ttp` 切到 TTP EU 机房；默认仍为 `cn`
- 火山云（`--sitename volc/火山云`）暂不支持

#### Deploy Workflow

发布前默认执行完整校验流程（与前端一致），可通过 `--skip-recommend` / `--skip-check` 跳过对应步骤：

1. **获取规则** — 拉取当前规则完整数据
2. **查询依赖推荐**（仅 hive 数据源）— 检查上游表依赖（`--skip-recommend` 跳过）
3. **添加依赖**（如有新推荐）— 自动合并推荐依赖并保存
4. **合法性校验** — 引擎校验（权限 + SQL 合法性）（`--skip-check` 跳过）
5. **发布** — 启动规则

#### 权限不足处理

当校验返回 `status_code: 1004`（权限不足）时：

- 错误码：`FUNDEYE_PERMISSION_DENIED`
- JSON 输出包含 `permission_apply_urls`（Triton 权限申请链接数组），预填申请人、表/列/行级权限、标准理由
- 文本模式直接打印带编号的申请链接

JSON 输出示例：

```json
{
  "status": "error",
  "data": {
    "rule_id": "20260601_1234567890000",
    "permission_apply_urls": [
      "https://data.bytedance.net/triton/auth_manage/application/create?apply=true&params=..."
    ],
    "tables": [{ "db": "example_db", "table": "example_table" }],
    "username": "example-user"
  },
  "error": {
    "code": "FUNDEYE_PERMISSION_DENIED",
    "hint": "权限不足，请通过以下链接申请权限:\nhttps://..."
  }
}
```

### 标签查询

```bash
bytedcli --json fundeye tag search --name '风险' --product tcheck --page 1 --page-size 10
bytedcli --json fundeye tag search --exact-name '会员' --product tcheck
```

- 用于按标签名模糊/精确查询标签 ID
- 支持 `--product`、`--tag-type`、`--page`、`--page-size`
- JSON 输出包含 `tags`、`current_page`、`page_size`、`total`

### 业务归属查询

```bash
bytedcli --json fundeye biz get --path '财经-数据平台'
bytedcli --json fundeye biz get --path '财经-数据平台-会员'
```

- 用于把业务归属名称路径解析成 `business_ownership` ID
- `--path` 使用 `-` 拼接层级名称
- 兼容旧参数 `--name`
- 支持预留参数 `--site`、`--tenant`；当前仅占位，不影响请求逻辑
- JSON 输出包含 `businessOwnership.path` 与 `businessOwnership.value`
- 返回的 `value` 可直接透传给 `fundeye rule list --business-ownership`
- 业务归属树中可能存在同名节点；若只传单层标题，可能返回歧义错误，优先传完整路径

### diff 明细

```bash
bytedcli --json fundeye diff get \
  --diff-id "DOUBLE_DS_CHECK#^#0#^#demo-diff" \
  --rule-id 2601142357560097
```

- `fundeye diff` 是分组命令，详情查询必须走 `diff get`
- `diff get` 会同时返回 diff 基础详情，以及该 diff 最近一次处理记录（若存在）
- 最近一次处理记录来自 diff process list，适用于人工标记原因和智能归因最终落库后的读取
- JSON 输出包含：
  - `latestProcess.reason`
  - `latestProcess.remark`
  - `latestProcess.operator`
  - `latestProcess.createTime`
  - `latestProcess.status`
  - `latestProcess.isHelpful`
  - `processList[]`
- `latestProcess` 会按 `createTime` 取最近一条处理记录，不依赖上游返回顺序
- 若 diff process list 查询失败，`diff get` 仍返回基础 diff 详情，并回退为：
  - `latestProcess: null`
  - `processList: []`
- `latestProcess.isHelpful` / `processList[].isHelpful` 取值说明：
  - `0`：无帮助 / 系统默认过程记录
  - `1`：有帮助
  - `2`：未评价或未显式填写
- JSON 输出不再包含 `raw`

### diff 列表

```bash
bytedcli --json fundeye diff list \
  --rule-id 2601142357560097 \
  --product-type fullink \
  --rule-version 11 \
  --start "2026-04-21 00:00:00" \
  --end "2026-04-21 23:59:59" \
  --alarm-order-id "2601142357560097##20260421065000##1_2##11" \
  --page 1 \
  --page-size 20
```

- `--rule-id` 必填
- `fullink` 推荐显式传 `--rule-version`；未传时 CLI 会自动从规则详情解析最新版本
- 默认产品类型是 `fullink`；查 `tcheck` 差异列表时使用 `--product-type tcheck`
- 排查 `fullink` 告警、尤其按 `--alarm-order-id` 缩小时，推荐显式传 `--start`、`--end`
- `tcheck` 的 `--rule-version` 可省略；未传时默认按 `0` 请求上游
- `--alarm-order-id` 可选
- JSON 输出当前保留：
  - `diffs`
  - `current`
  - `page_size`
  - `total`
  - `actual_diff_cnt`
  - `diff_money`
  - `alarm_condition`
- JSON 输出不再包含：
  - 每个 diff item 的 `raw`
- `--json` 模式下 `diffs[]` 的字段名为 snake_case（例如 `diff_id`、`rule_id`），不再输出 camelCase 版本（例如 `diffId`、`ruleId`）

### diff 处理（update）

```bash
bytedcli --json fundeye diff update \
  --reason "BIZ_ISSUES||NEW_BIZ_DEPLOY" \
  --remark "demo remark" \
  --diff-list '[{"diff_id":"DOUBLE_DS_CHECK#^#0#^#demo","diff_version":1}]'

bytedcli --json fundeye diff update \
  --reason "BIZ_ISSUES||NEW_BIZ_DEPLOY" \
  --remark "demo remark" \
  --alarm-order-id-list '["TCheck##demo-alarm-order-id"]'
```

- `--diff-list` 与 `--alarm-order-id-list` 二选一
- `--diff-list` 使用 JSON 数组字符串；每项结构为：
  - `diff_id`: string
  - `diff_version`: number
- `diff_version` 可通过 `fundeye diff list --json` 获取：返回的 `diffs[].diff_version` 字段即为 `diff_version` 入参
- `--reason` 必填，格式为 `PARENT||CHILD`（或仅 `PARENT`）：
  - `BIZ_ISSUES||<child>`，child 允许值：
    - `WRONG_SCRIPT` / `NEW_BIZ_DEPLOY` / `BIZ_ISSUES_DATA_DELAY` / `BIZ_ISSUES_ALTER` / `BIZ_ISSUES_DATA_LOSS`
    - `BIZ_ISSUES_REAL_DIFF` / `IDEMPOTENT_FAILED` / `AMOUNT_UNIT_ERROR` / `INTERFACE_SEMANTICS_MISUNDERSTAND`
    - `BIZ_ISSUES_BUG` / `BIZ_ISSUES_TEST`
  - `PLATFORM_ISSUES||<child>`，child 允许值：
    - `PLATFORM_ISSUES_DELAY` / `PLATFORM_ISSUES_LIMIT` / `PLATFORM_ISSUES_CIRCUIT_BREAKER`
    - `PLATFORM_ISSUES_STABILITY` / `PLATFORM_ISSUES_BUG`
  - `OTHER_ISSUES||<child>`，child 允许值：
    - `STRESS_TEST` / `DISASTER_RECOVERY_DRILL` / `MIDDLEWARE_FAILED` / `THIRD_PARTY_ISSUES`
    - `FUND_DRILL` / `EXCEEDED_SNAPSHOT_STORAGE_TIME`
  - `CUSTOM_ISSUES`：当前无预置 child（如需可与后端约定扩展）
- `--alarm-order-id-list` 使用 JSON 数组字符串，元素为告警单 ID，例如 `TCheck##demo-alarm-order-id`
- status 固定为 `PROCESS_RESULT`。

### diff 重试（retry）

`--try-list` 是 diff_id 的 JSON 数组字符串，可从 `fundeye diff list --json` 返回的 `diffs[].diff_id` 获取。

```bash
bytedcli --json fundeye diff retry \
  --try-list '["DOUBLE_DS_CHECK#^#0#^#demo"]'
```

### 告警列表

```bash
bytedcli --json fundeye alarm list --page 1 --page-size 20
bytedcli --json fundeye alarm list --alarm-priority P1 --alarm-priority P2
bytedcli --json fundeye alarm list --alarm-user demo-user
bytedcli --json fundeye alarm list --start '2026-08-01 00:00:00' --end '2026-08-31 23:59:59'
```

- 支持分页
- 支持按产品和优先级过滤
- `--alarm-priority <level>` 按告警优先级正选，可重复传入（如 `--alarm-priority P1 --alarm-priority P2`）
- `--alarm-user <username>` 按告警人筛选（通过覆盖 UserName header 实现）
- `--start` / `--end` 指定时间范围，CN 最长 30 天、海外最长 7 天

## 使用建议

- 需要机器可读结果时，优先加 `--json`
- 当用户只有业务归属名称路径时，推荐流程是：
  - `fundeye biz get --path '<层级1-层级2>'`
  - `fundeye rule list --business-ownership <value>`
- 需要按标签名查标签 ID 时，单独使用 `fundeye tag search --name <keyword> [--product tcheck]`
- 先看告警，再查 diff 时，推荐流程是：
  - `fundeye alarm list`
  - `fundeye diff list`
  - `fundeye diff get`
- 按规则查 TCheck 核对记录或重跑历史时段时，推荐流程是：
  - `fundeye check-record list --rule-id <rule-id>`
  - `fundeye check-record rerun --rule-id <rule-id> --business-time <yyyy-MM-dd HH:mm:ss>`

补充：也支持 `fundeye risko trigger`、`fundeye rule full-create`、`fundeye rule save-draft`、`fundeye tag search`、`fundeye check-record list` 与 `fundeye check-record rerun`。
