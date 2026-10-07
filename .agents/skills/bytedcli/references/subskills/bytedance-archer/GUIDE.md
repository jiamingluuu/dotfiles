---
name: bytedance-archer
description: "Operate Archer precision testing platform via bytedcli: query flow-level coverage and PPE E2E trace coverage by PSM and trace ID. Use when tasks mention Archer, 精准测试, 链路覆盖率, PPE 覆盖率, PPE 端到端覆盖率, flow coverage, trace coverage, or precision testing."
---

# Archer (bytedcli)

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

- 按 PSM + traceId 查询链路级覆盖率数据
- 查询 PPE 环境端到端 trace 覆盖率；不要用 codecov/CI UT 覆盖率替代
- 查询流量级函数调用图（stub_graph.nodes / stub_graph.edges）
- 查询按包路径组织的覆盖行明细（node_trees → children_node_func → covered_blocks）
- 还原 Bits coverage-next 增量 MR 覆盖率链接（mrId + showRecord + branch）
- 拉取 Bits coverage-next 文件级增量覆盖率，并展开单文件行级 covered / missed 状态
- 获取服务构建信息（commitHash、branch、version、env、zone 等）
- 精准测试与影响面分析

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要先通过 `bytedcli auth login` 完成 ByteCloud SSO 认证

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 常用命令

```bash
# 按 PSM + traceId 查询链路级覆盖率
bytedcli archer query-flow --psm "demo.service.api" --trace-id "demo-trace-id"

# 查询 PPE E2E trace 覆盖率
bytedcli archer e2e-coverage get --psm "demo.service.api" --trace-id "demo-trace-id"

# 排查非 PPE trace，不作为 PPE 覆盖率判断
bytedcli archer e2e-coverage get --psm "demo.service.api" --trace-id "demo-trace-id" --env prod --no-require-env-match

# 还原 Bits coverage-next 增量 MR 覆盖率链接（不发 HTTP）
bytedcli archer coverage-next get-url --mr-id 714 --show-record 13422975 --branch feat/demo

# 拉取 Bits coverage-next 文件级覆盖率，按 80% 阈值分组
bytedcli archer coverage-next list --report-id 10000001 --threshold 80

# 展开某个文件的行级覆盖状态，默认只打印 changed/effective 行
bytedcli archer coverage-next get --report-id 10000001 --file src/demo/service.go

# JSON 模式输出
bytedcli --json archer query-flow --psm "demo.service.api" --trace-id "demo-trace-id"
```

## 输出说明

### 文本模式

输出服务构建信息（Branch、Version、Env、Zone）、覆盖统计（Covered blocks、Error funcs、Panic funcs）、调用图摘要（Call graph nodes/edges）、覆盖文件列表（最多显示 10 个文件）及每个文件的 block ranges 数量，末尾附 Argos 日志链接和 Archer 控制台报告链接。

### JSON 模式

输出结构化 JSON，`data.data` 字段包含完整覆盖率数据，主要结构：

| 字段               | 类型     | 说明                                                                             |
| ------------------ | -------- | -------------------------------------------------------------------------------- |
| `psm`              | `string` | 服务 PSM                                                                         |
| `traceId`          | `string` | Trace ID                                                                         |
| `scmName`          | `string` | SCM 路径                                                                         |
| `gitRepo`          | `string` | Git 仓库地址                                                                     |
| `commitHash`       | `string` | Commit Hash                                                                      |
| `version`          | `string` | 服务版本                                                                         |
| `branch`           | `string` | 分支名                                                                           |
| `env`              | `string` | 环境（如 ppe）                                                                   |
| `hostEnv`          | `string` | 宿主环境                                                                         |
| `zone`             | `string` | 机房 Zone                                                                        |
| `collectedTime`    | `string` | 数据采集时间                                                                     |
| `coveredBlockSize` | `number` | 覆盖 Block 数量                                                                  |
| `errFuncNum`       | `number` | 错误函数数                                                                       |
| `panicFuncNum`     | `number` | Panic 函数数                                                                     |
| `argosLogUrl`      | `string` | Argos 日志链接                                                                   |
| `flowTag`          | `string` | 流量标签                                                                         |
| `node_trees`       | `array`  | 按包路径组织的覆盖树，叶子节点含 `children_node_func`（文件级 `covered_blocks`） |
| `stub_graph`       | `object` | 调用图，含 `nodes`（函数节点）和 `edges`（调用边）                               |

```json
{
  "status": "success",
  "data": {
    "psm": "demo.service.api",
    "traceId": "demo-trace-id",
    "data": {
      "scmName": "demo/demo_service/api",
      "gitRepo": "code.byted.org/demo_service/api",
      "commitHash": "abc123def456",
      "version": "devflow.0.0.1.100",
      "branch": "feature-demo",
      "env": "ppe_demo",
      "hostEnv": "ppe",
      "zone": "China-North-LF",
      "collectedTime": "2026-04-14T07:08:54.000+00:00",
      "coveredBlockSize": 570,
      "errFuncNum": 0,
      "panicFuncNum": 0,
      "argosLogUrl": "https://cloud.bytedance.net/argos/streamlog/...",
      "flowTag": "archer_flow",
      "node_trees": [
        {
          "label": "demo_service/api",
          "children": [
            {
              "label": "handler",
              "children": [],
              "children_node_func": [
                {
                  "file_path": "/handler/demo.go",
                  "file_name": "demo.go",
                  "covered_blocks": [
                    [10, 15],
                    [20, 25]
                  ],
                  "covered_func": null,
                  "incremental_covered_rate": null,
                  "incr_line_total": null,
                  "incr_line_coverage": null,
                  "incr_func_line_total": null
                }
              ],
              "incremental_covered_rate": null,
              "incr_line_total": null,
              "incr_line_coverage": null,
              "incr_func_line_total": null,
              "git_repo": null,
              "commit_hash": null
            }
          ],
          "incremental_covered_rate": null,
          "incr_line_total": null,
          "incr_line_coverage": null,
          "incr_func_line_total": null,
          "git_repo": "code.byted.org/demo_service/api",
          "commit_hash": "abc123def456"
        }
      ],
      "stub_graph": {
        "nodes": [
          {
            "node_type": "FUNC",
            "node_key": "code.byted.org/demo_service/api/handler#DemoFunc",
            "node_label": "#DemoFunc",
            "call_info": {
              "key": "code.byted.org/demo_service/api/handler#DemoFunc",
              "nodeType": "FUNC",
              "file": "/handler/demo.go",
              "span": [10, 15],
              "startTime": 1776150533380,
              "endTime": 1776150533380
            }
          }
        ],
        "edges": [
          {
            "caller_key": "code.byted.org/demo_service/api#EntryFunc",
            "callee_key": "code.byted.org/demo_service/api/handler#DemoFunc"
          }
        ],
        "err_func_num": 0,
        "panic_func_num": 0
      }
    }
  },
  "context": {
    "execution_time_ms": 200,
    "timestamp": "2026-04-14T12:00:00.000000"
  }
}
```

## coverage-next get-url

`archer coverage-next get-url` 只拼接 Bits 增量 MR 覆盖率链接，不发 HTTP 请求。它用于处理 Bits `coverage-next/incre` 页面参数；`query-flow` 仍用于 PSM + traceId 的精准测试流量覆盖。

```bash
bytedcli archer coverage-next get-url --mr-id 714 --show-record 13422975 --branch feat/demo
# -> https://bits.bytedance.net/quality/measure/coverage-next/incre?branch=feat%2Fdemo&language=1&mrId=714&region=cn&showRecord=13422975&url=coverage%2Fincre&viewId=1
```

## coverage-next list / get

`archer coverage-next list` 拉取 Bits coverage-next 增量报告的文件级覆盖率。推荐优先传 `--report-id`，它对应 coverage-next URL 里的 `showRecord`；没有 `showRecord` 时，也可以传 `--mr-id` + `--psm` 搜索报告。

```bash
bytedcli archer coverage-next list --report-id 10000001 --threshold 80
bytedcli --json archer coverage-next list --report-id 10000001
```

文本输出按阈值分成 `Below threshold` 和 `Passed` 两段；JSON 输出包含 `files`、`under_threshold`、`passed` 与 `counts`。

`archer coverage-next get` 展开一个文件的行级覆盖状态。`--file` 使用 `list` 命令输出的仓库相对路径。文本模式默认只打印 changed/effective 行；需要整文件源码时加 `--all-lines`，或者使用 JSON 输出消费 `lines`、`missed_lines`、`covered_lines`。

```bash
bytedcli archer coverage-next get --report-id 10000001 --file src/demo/service.go
bytedcli archer coverage-next get --report-id 10000001 --file src/demo/service.go --all-lines
```

## Notes

- `--psm` 和 `--trace-id` 均为必填参数
- `coverage-next get-url` 的 `--mr-id`、`--show-record`、`--branch` 来自 Bits coverage-next 增量页 URL；`--os-type` 默认 `server` 并映射 Bits `language` tab
- 认证方式：ByteCloud SSO JWT（`x-jwt-token` Header），需先执行 `bytedcli auth login`
- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json archer query-flow`）
- Archer 报告默认仅支持查询近 7 天数据
- 完整报告可在 Archer 控制台查看：`https://archer.bytedance.net/traffic-query`

## References

- `references/archer.md`
- `../../invocation.md`
- `../../troubleshooting.md`
