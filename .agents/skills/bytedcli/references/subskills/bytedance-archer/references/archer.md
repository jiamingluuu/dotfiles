# Archer 命令详解

## query-flow

按 PSM + traceId 查询链路级覆盖率数据，返回服务构建信息、按包路径组织的覆盖树（node_trees）和函数调用图（stub_graph）。

```bash
bytedcli archer query-flow --psm "demo.service.api" --trace-id "demo-trace-id"
```

参数说明：

- `--psm`：PSM 名称（必填），例如 `demo.service.api`
- `--trace-id`：Trace ID（必填）

### 输出格式

#### 文本模式

```
PSM: demo.service.api
TraceID: demo-trace-id
Branch: feature-demo
Version: devflow.0.0.1.100
Env: ppe_demo / ppe
Zone: China-North-LF
Covered blocks: 570
Error funcs: 0
Panic funcs: 0
Call graph nodes: 157
Call graph edges: 219
Covered files: 45
  /handler/demo.go: 2 block ranges
  /handler/util.go: 1 block ranges
  /service/process.go: 5 block ranges

Argos log: https://cloud.bytedance.net/argos/streamlog/...

View full report: https://archer.bytedance.net/traffic-query?psm=demo.service.api&traceId=demo-trace-id
```

- 覆盖文件列表最多显示 10 个，超出部分显示 `... and N more files`
- 每个文件的 block ranges 表示覆盖行区间的数量

#### JSON 模式

```bash
bytedcli --json archer query-flow --psm "demo.service.api" --trace-id "demo-trace-id"
```

返回结构化 JSON，`data.data` 字段包含以下主要结构：

##### 顶层元数据

| 字段                 | 类型             | 说明                                               |
| -------------------- | ---------------- | -------------------------------------------------- |
| `psm`                | `string`         | 服务 PSM                                           |
| `traceId`            | `string`         | Trace ID                                           |
| `scmName`            | `string`         | SCM 路径，如 `demo/demo_service/api`               |
| `gitRepo`            | `string`         | Git 仓库地址，如 `code.byted.org/demo_service/api` |
| `commitHash`         | `string`         | Commit Hash                                        |
| `version`            | `string`         | 服务版本，如 `devflow.0.0.1.100`                   |
| `branch`             | `string`         | 分支名                                             |
| `env`                | `string`         | 环境标识，如 `ppe_demo`                            |
| `hostEnv`            | `string`         | 宿主环境，如 `ppe`                                 |
| `zone`               | `string`         | 机房 Zone，如 `China-North-LF`                     |
| `internalIdc`        | `string`         | 内部 IDC 标识                                      |
| `logicalCluster`     | `string`         | 逻辑集群                                           |
| `graphHash`          | `string`         | 调用图 Hash                                        |
| `collectedTime`      | `string`         | 数据采集时间（ISO 8601）                           |
| `coveredBlockSize`   | `number`         | 覆盖 Block 数量                                    |
| `errFuncNum`         | `number`         | 错误函数数                                         |
| `panicFuncNum`       | `number`         | Panic 函数数                                       |
| `circleCallNum`      | `number \| null` | 循环调用数                                         |
| `argosLogUrl`        | `string`         | Argos 日志查询链接                                 |
| `flowTag`            | `string`         | 流量标签，如 `archer_flow`                         |
| `suspiciousAnalysis` | `object \| null` | 可疑分析结果                                       |

##### node_trees（覆盖树）

按包路径组织的层级树结构，每个节点包含：

| 字段                       | 类型             | 说明                        |
| -------------------------- | ---------------- | --------------------------- |
| `label`                    | `string`         | 包路径片段                  |
| `children`                 | `array`          | 子包节点                    |
| `children_node_func`       | `array`          | 叶子节点的文件级覆盖信息    |
| `incremental_covered_rate` | `number \| null` | 增量覆盖率                  |
| `incr_line_total`          | `number \| null` | 增量总行数                  |
| `incr_line_coverage`       | `number \| null` | 增量覆盖行数                |
| `incr_func_line_total`     | `number \| null` | 增量函数总行数              |
| `git_repo`                 | `string \| null` | Git 仓库（仅根节点有值）    |
| `commit_hash`              | `string \| null` | Commit Hash（仅根节点有值） |

`children_node_func` 中每个文件条目包含：

| 字段                       | 类型             | 说明                                            |
| -------------------------- | ---------------- | ----------------------------------------------- |
| `file_path`                | `string`         | 文件相对路径，如 `/handler/demo.go`             |
| `file_name`                | `string`         | 文件名，如 `demo.go`                            |
| `covered_blocks`           | `number[][]`     | 覆盖行范围列表，每个范围 `[startLine, endLine]` |
| `covered_func`             | `object \| null` | 覆盖函数信息                                    |
| `incremental_row`          | `number \| null` | 增量行数                                        |
| `incremental_fn_row`       | `number \| null` | 增量函数行数                                    |
| `incremental_covered_rate` | `number \| null` | 增量覆盖率                                      |
| `incr_line_total`          | `number \| null` | 增量总行数                                      |
| `incr_line_coverage`       | `number \| null` | 增量覆盖行数                                    |
| `incr_func_line_total`     | `number \| null` | 增量函数总行数                                  |

##### stub_graph（调用图）

函数级调用图，包含：

**nodes（函数节点）**

| 字段         | 类型             | 说明                                                                |
| ------------ | ---------------- | ------------------------------------------------------------------- |
| `node_type`  | `string`         | 节点类型，如 `FUNC`                                                 |
| `node_key`   | `string`         | 节点唯一标识，如 `code.byted.org/demo_service/api/handler#DemoFunc` |
| `node_label` | `string`         | 节点标签，如 `#DemoFunc`                                            |
| `diff_type`  | `string \| null` | 差异类型                                                            |
| `call_info`  | `object`         | 调用详情                                                            |

`call_info` 包含：

| 字段          | 类型             | 说明                          |
| ------------- | ---------------- | ----------------------------- |
| `key`         | `string`         | 函数唯一标识                  |
| `nodeType`    | `string`         | 节点类型                      |
| `file`        | `string`         | 文件路径                      |
| `span`        | `number[]`       | 行范围 `[startLine, endLine]` |
| `startTime`   | `number`         | 调用开始时间（毫秒时间戳）    |
| `endTime`     | `number`         | 调用结束时间（毫秒时间戳）    |
| `panic`       | `string \| null` | Panic 信息                    |
| `coveredInfo` | `array`          | 覆盖信息                      |

**edges（调用边）**

| 字段         | 类型             | 说明             |
| ------------ | ---------------- | ---------------- |
| `caller_key` | `string`         | 调用方函数标识   |
| `callee_key` | `string`         | 被调用方函数标识 |
| `diff_type`  | `string \| null` | 差异类型         |

`stub_graph` 还包含：

| 字段             | 类型     | 说明         |
| ---------------- | -------- | ------------ |
| `err_func_num`   | `number` | 错误函数数   |
| `panic_func_num` | `number` | Panic 函数数 |

### API 详情

- 端点：`POST https://archer-stub-svr.byted.org/stub/query-flow`
- 认证：ByteCloud SSO JWT，通过 `x-jwt-token` Header 传递
- 请求体：`{ "psm": "...", "traceId": "..." }`
- 响应结构：`{ "code": 0, "msg": "", "data": { ... }, "cost": 100, "logId": "..." }`
- 数据限制：仅支持查询近 7 天数据

### Archer 控制台

完整覆盖率报告可在 Archer 控制台查看：

```
https://archer.bytedance.net/traffic-query?psm={psm}&traceId={traceId}
```

## coverage-next get-url

还原 Bits `coverage-next/incre` 增量 MR 覆盖率页链接。该命令只拼接 URL，不发 HTTP 请求；参数来自 Bits 页面 URL 的 `mrId`、`showRecord` 和 `branch`。

```bash
bytedcli archer coverage-next get-url --mr-id 714 --show-record 13422975 --branch feat/demo
# -> https://bits.bytedance.net/quality/measure/coverage-next/incre?branch=feat%2Fdemo&language=1&mrId=714&region=cn&showRecord=13422975&url=coverage%2Fincre&viewId=1
```

参数说明：

- `--mr-id`：Bits MR ID（必填）
- `--show-record`：增量覆盖率页面的 showRecord ID（必填）
- `--branch`：源分支名（必填）
- `--os-type`：技术栈，默认 `server`，映射 Bits `language` tab

## coverage-next list

拉取 Bits `coverage-next/incre` 增量报告的文件级覆盖率。推荐传 `--report-id`，它对应 coverage-next URL 里的 `showRecord`；如果没有 report id，可传 `--mr-id` + `--psm` 搜索报告。

```bash
bytedcli archer coverage-next list --report-id 10000001 --threshold 80
bytedcli archer coverage-next list --mr-id 714 --psm demo.service.api --threshold 80
```

参数说明：

- `--report-id`：增量覆盖率 report/showRecord ID
- `--mr-id`：Bits MR ID；未传 `--report-id` 时需要配合 `--psm`
- `--psm`：PSM 名称；未传 `--report-id` 时必填
- `--project-id`：覆盖率 project ID 覆盖值，通常不需要手传
- `--os-type`：技术栈，默认 `server`
- `--threshold`：文件通过阈值，默认 `80`

文本输出会按阈值分组：

```
Coverage-next demo/repo MR 714: 75% (3/4)
Threshold: 80%

Below threshold (1)
50.00% 1/2 src/demo/low.go

Passed (1)
100.00% 2/2 src/demo/ok.go
```

JSON 输出包含：

- `report`：增量报告详情，包括 `id`、`project_id`、`mr_id`、`psm`、`repo_name`
- `repo`：文件汇总统计，包括总覆盖率、覆盖行、新增行
- `files`：全部文件
- `under_threshold`：低于阈值的文件
- `passed`：达到阈值的文件
- `counts`：文件数量统计

## coverage-next get

展开单个文件的行级覆盖状态。`--file` 使用 `coverage-next list` 输出的仓库相对路径。文本模式默认只打印 changed/effective 行；需要整文件源码时加 `--all-lines`。

```bash
bytedcli archer coverage-next get --report-id 10000001 --file src/demo/service.go
bytedcli archer coverage-next get --report-id 10000001 --file src/demo/service.go --all-lines
```

参数说明：

- `--report-id`：增量覆盖率 report/showRecord ID
- `--file`：仓库相对路径，例如 `src/demo/service.go`
- `--mr-id`、`--psm`、`--project-id`、`--os-type`：同 `coverage-next list`
- `--all-lines`：文本模式打印整文件源码；默认只打印 changed/effective 行

JSON 输出包含：

- `lines`：全量源码行，每行包含 `line_num`、`line_code`、`is_covered`、`is_changed`、`is_effective`、`is_missed`、`status`
- `changed_lines`：changed / covered / missed 相关行
- `missed_lines`：未覆盖行
- `covered_lines`：已覆盖行
