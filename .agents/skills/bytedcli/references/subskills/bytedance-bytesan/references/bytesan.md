# `bytedcli bytesan` 命令接口说明

本文说明 ByteSan 只读命令的选择方式、参数、输出、分页、站点限制与示例。分析规则与完整流程位于 ByteSan skill 主文档。

## 目录

- [命令矩阵](#命令矩阵)
- [通用调用约定](#通用调用约定)
- [控制台 URL 识别](#控制台-url-识别)
- [`bytesan task list`](#bytedcli-bytesan-task-list)
- [`bytesan scan list`](#bytedcli-bytesan-scan-list)
- [`bytesan task-bug list`](#bytedcli-bytesan-task-bug-list)
- [`bytesan run-bug list`](#bytedcli-bytesan-run-bug-list)
- [`bytesan bug-build-report list`](#bytedcli-bytesan-bug-build-report-list)
- [`bytesan report-content get`](#bytedcli-bytesan-report-content-get)
- [`bytesan build-metadata get`](#bytedcli-bytesan-build-metadata-get)
- [错误处理](#错误处理)

## 命令矩阵

| bytedcli 命令                   | 必填业务参数  | 关键输出                        |
| ------------------------------- | ------------- | ------------------------------- |
| `bytesan task list`             | 无            | `tasks[].task_id`               |
| `bytesan scan list`             | 无            | `scans[].run_id`                |
| `bytesan task-bug list`         | `--task-id` 或 `--url`，二选一 | `bugs[].bug_id`                 |
| `bytesan run-bug list`          | `--run-id` 或 `--url`，二选一 | `bugs[].bug_id`                 |
| `bytesan bug-build-report list` | `--bug-id` 或 `--url`，二选一 | `runs[].build_id`、`report_id`  |
| `bytesan report-content get`    | `--report-id` | `content`                       |
| `bytesan build-metadata get`    | `--build-id`  | Git 地址、commit 与依赖仓库信息 |

## 通用调用约定

### 全局参数

| 参数            | 默认值                        | 说明                                                                                      |
| --------------- | ----------------------------- | ----------------------------------------------------------------------------------------- |
| `--site <site>` | `BYTEDCLI_CLOUD_SITE` 或 `cn` | 写在 `bytedcli` 与 `bytesan` 之间；支持 `cn`、`i18n-tt`、`us-ttp`、`eu-ttp`。             |
| `--json`        | `false`                       | 写在 `bytesan` 前；输出标准 `{status,data,error,context}` envelope，业务字段位于 `data`。 |

Task、Run、Bug 与 Report 必须持续使用资源所属的同一个 site，并使用该 site 的用户 ByteCloud JWT；不得跨控制面 fallback。`bytesan build-metadata get` 是例外：它使用共享的无鉴权 BuildCloud metadata 入口，不读取或发送 ByteSan JWT，global site 不改变请求目标。

使用 `--url` 时，链接中的 ByteCloud host 决定本次请求的 site，优先于全局 `--site` / `BYTEDCLI_CLOUD_SITE`，不会修改全局配置。`task-bug list`、`run-bug list`、`bug-build-report list` 对 ID 和 URL 输入都在 JSON 结果中返回实际请求站点 `data.site`，文本结果打印 `Site`。后续只拿 ID 查询时，必须将这个 site 显式传给 `--site`。

在生产开发机查询 `i18n-tt`、`us-ttp` 或 `eu-ttp` 时，先设置：

```bash
export BYTEDCLI_NETWORK_PROFILE=prod
```

办公网环境不要设置该变量。`us-ttp-bdee` 与 `us-ttp-usts` 不受支持，也不能静默映射到 `us-ttp`。

### 分页

五个列表命令都支持：

| 参数              | 必填 | 默认值 | 取值         | 说明               |
| ----------------- | ---- | ------ | ------------ | ------------------ |
| `--page <n>`      | 否   | `1`    | 正整数       | 从第几页开始读取。 |
| `--page-size <n>` | 否   | `20`   | `1` 到 `100` | 每页条数。         |

只在 `data.has_more=true` 时读取下一页。`total_count=null` 表示上游没有返回总数；此时 CLI 根据当前页是否达到 `page_size` 保守计算 `has_more`，不能把当前页条数当作总数。

## 控制台 URL 识别

ByteSan 的共同 path 前缀是 `/byteq/bytesan`。先匹配该前缀，再按下表识别资源；host 仅用于从已支持的 ByteCloud 域名推断 `cn`、`i18n-tt`、`us-ttp` 或 `eu-ttp`。办公网与生产网域名均可识别，实际 API 入口仍由 `BYTEDCLI_NETWORK_PROFILE` 选择。

| 优先级 | path / URL 参数特征 | 标识 | 对应命令 |
| ------ | ------------------- | ---- | -------- |
| 1 | `/byteq/bytesan` 下任一路径包含非空 `runId` 参数，常见 `/task/detail?runId=demo-build.1.2` | 完整 Run ID | `bytesan run-bug list --url <完整链接>` |
| 2 | `/byteq/bytesan/mission/detail?id=demo-task` | Task ID | `bytesan task-bug list --url <完整链接>` |
| 3 | `/byteq/bytesan/task/bug?id=demo-bug` | Bug ID | `bytesan bug-build-report list --url <完整链接>` |

- `/mission/detail` 与 `/task/bug` 都使用 `id`，必须结合 path 区分 Task 与 Bug，不能只看 query 名称。
- `runId` 优先于页面中的 `id`；保留完整字符串，不按 `.` 截断，也不转换为数字。提取 Build ID 是后续 Bug / Run 映射步骤的独立行为。
- Query 参数顺序不影响识别，允许无关 query、页面锚点与结尾 `/`。所需 ID 参数必须恰好出现一次且非空；出现空 `runId` 时不会回退到 `id`。
- URL 必须来自已支持的 ByteCloud 控制面且使用 HTTPS；未知 host、错误 path、缺少 ID 或将 Bug URL 传给任务命令时，会返回带修复提示的 `BYTESAN_INPUT_ERROR`，不发起查询。
- 分页继续使用同一条 URL；查询关联 Bug / Report 时沿用 `data.site`。不同 URL 的 ID 应按 `(site, ID)` 去重。

以下示例中的 `example.com` 是占位 host，实际执行时使用从浏览器复制的完整 ByteCloud URL：

```bash
bytedcli --json bytesan task-bug list --url 'https://example.com/byteq/bytesan/mission/detail?id=demo-task'
bytedcli --json bytesan run-bug list --url 'https://example.com/byteq/bytesan/task/detail?runId=demo-build.1.2'
bytedcli --json bytesan bug-build-report list --url 'https://example.com/byteq/bytesan/task/bug?id=demo-bug'
# 假设 URL 查询返回 data.site=us-ttp，后续 Report 查询沿用该 site
bytedcli --site us-ttp --json bytesan report-content get --report-id demo-report
```

## Agent 快速选择

| 已有输入  | 首选命令                        | 后续动作                                    |
| --------- | ------------------------------- | ------------------------------------------- |
| 仓库名    | `bytesan task list --repo ...`  | 筛选任务并读取 Task ID                      |
| PSM/仓库  | `bytesan scan list`             | 筛选扫描并读取 Run ID                       |
| ByteSan URL | 按上表选择命令并传入 `--url` | 根据 path / query 识别资源，并保留返回的 site |
| Task ID   | `bytesan task-bug list`         | 读取唯一 Bug ID，再查询 Build / Report 列表 |
| Run ID    | `bytesan run-bug list`          | 读取唯一 Bug ID，再查询 Build / Report 列表 |
| Bug ID    | `bytesan bug-build-report list` | 直接读取 Build、Run 与 Report ID            |
| Report ID | `bytesan report-content get`    | 直接保存原始报告，不先扫描 Task / Run / Bug |
| Build ID  | `bytesan build-metadata get`    | 直接读取主仓与依赖仓库 Git metadata         |

优先从用户已经给出的最下游 ID 开始。已有 Report ID 时不要为了“补流程”反查 Bug；已有 Build ID 时不要先查询 Report。

仓库名和 PSM 由用户通过命令参数直接输入；这些命令不提供候选值查询、自动补全或模糊猜测。

## `bytedcli bytesan task list`

分页读取 ByteSan 任务。可使用用户直接提供的 Git 仓库名筛选；不传筛选参数时读取全部任务。

### 参数

| 参数              | 必填 | 默认值 | 说明                                   |
| ----------------- | ---- | ------ | -------------------------------------- |
| `--repo <repo>`   | 否   | 无     | Git 仓库名；可重复传入或使用逗号分隔。 |
| `--page <n>`      | 否   | `1`    | 正整数页码。                           |
| `--page-size <n>` | 否   | `20`   | 每页 `1` 到 `100` 条。                 |

### 输出

```json
{
  "status": "success",
  "data": {
    "tasks": [
      {
        "task_id": "demo-task",
        "task_type": "PreBuild",
        "creator": "demo-user",
        "created_at": 1700000000,
        "bug_count": 2,
        "scm_repo": "demo-scm",
        "scm_version": "v1",
        "git_repo": "example/repository",
        "git_branch": "main",
        "git_commit": "abcdef123456"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site cn --json bytesan task list \
  --repo example/repository,example/dependency \
  --page 1 \
  --page-size 100
```

## `bytedcli bytesan scan list`

分页读取 ByteSan 扫描。可使用用户直接提供的 PSM、Git 仓库名或两者共同筛选；不传筛选参数时读取全部扫描。

### 参数

| 参数              | 必填 | 默认值 | 说明                                   |
| ----------------- | ---- | ------ | -------------------------------------- |
| `--psm <psm>`     | 否   | 无     | PSM；可重复传入或使用逗号分隔。        |
| `--repo <repo>`   | 否   | 无     | Git 仓库名；可重复传入或使用逗号分隔。 |
| `--page <n>`      | 否   | `1`    | 正整数页码。                           |
| `--page-size <n>` | 否   | `20`   | 每页 `1` 到 `100` 条。                 |

### 输出

```json
{
  "status": "success",
  "data": {
    "scans": [
      {
        "run_id": "demo-build.1",
        "psm": "example.service",
        "sanitizer_name": "ASAN",
        "bug_occurrence_count": 3,
        "creator": "demo-user",
        "created_at": 1700000100,
        "task_id": "demo-task",
        "policy_id": null,
        "scm_repo": "demo-scm",
        "scm_version": "v1",
        "git_repo": "example/repository",
        "git_branch": "main",
        "git_commit": "abcdef123456"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site cn --json bytesan scan list \
  --psm example.service,example.worker \
  --repo example/repository,example/dependency \
  --page 1 \
  --page-size 100
```

## `bytedcli bytesan task-bug list`

根据 Task ID 或 `/byteq/bytesan/mission/detail?id=...` 控制台 URL 分页读取缺陷列表。

### 参数

| 参数              | 必填 | 默认值 | 说明                   |
| ----------------- | ---- | ------ | ---------------------- |
| `--task-id <id>`  | 二选一 | 无   | ByteSan Task ID，与 `--url` 互斥。 |
| `--url <url>`     | 二选一 | 无   | 任务详情 URL，自动识别 Task ID 与 site。 |
| `--page <n>`      | 否   | `1`    | 正整数页码。           |
| `--page-size <n>` | 否   | `20`   | 每页 `1` 到 `100` 条。 |

### 输出

```json
{
  "status": "success",
  "data": {
    "site": "cn",
    "task_id": "demo-task",
    "bugs": [
      {
        "bug_id": "demo-bug",
        "bug_type": "heap-use-after-free",
        "sanitizer_name": "ASAN"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site cn --json bytesan task-bug list \
  --task-id demo-task \
  --page 1 \
  --page-size 100
```

## `bytedcli bytesan run-bug list`

根据 Run ID 或带 `runId` 的 ByteSan 控制台 URL 分页读取缺陷列表。

### 参数

| 参数              | 必填 | 默认值 | 说明                   |
| ----------------- | ---- | ------ | ---------------------- |
| `--run-id <id>`   | 二选一 | 无   | ByteSan Run ID，与 `--url` 互斥。 |
| `--url <url>`     | 二选一 | 无   | 含 `runId` 的 ByteSan URL，自动识别完整 Run ID 与 site。 |
| `--page <n>`      | 否   | `1`    | 正整数页码。           |
| `--page-size <n>` | 否   | `20`   | 每页 `1` 到 `100` 条。 |

### 输出

返回结构与 `task-bug list` 相同，但 `data.task_id` 替换为 `data.run_id`：

```json
{
  "status": "success",
  "data": {
    "site": "i18n-tt",
    "run_id": "demo-run",
    "bugs": [
      {
        "bug_id": "demo-bug",
        "bug_type": "data-race",
        "sanitizer_name": "TSAN"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total_count": null,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site i18n-tt --json bytesan run-bug list \
  --run-id demo-run \
  --page 1 \
  --page-size 100
```

## `bytedcli bytesan bug-build-report list`

根据 Bug ID 或 `/byteq/bytesan/task/bug?id=...` 控制台 URL 分页读取相关 Run、Build 与 Report ID。

### 参数

| 参数              | 必填 | 默认值 | 说明                   |
| ----------------- | ---- | ------ | ---------------------- |
| `--bug-id <id>`   | 二选一 | 无   | ByteSan Bug ID，与 `--url` 互斥。 |
| `--url <url>`     | 二选一 | 无   | Bug 详情 URL，自动识别 Bug ID 与 site。 |
| `--page <n>`      | 否   | `1`    | 正整数页码。           |
| `--page-size <n>` | 否   | `20`   | 每页 `1` 到 `100` 条。 |

### 输出

`build_id` 取 `run_id` 第一个 `.` 之前的部分；没有 `.` 时取完整 `run_id`。首段为空（例如 `.1`）时返回 `BYTESAN_PARSE_ERROR`。

```json
{
  "status": "success",
  "data": {
    "site": "eu-ttp",
    "bug_id": "demo-bug",
    "runs": [
      {
        "report_id": "demo-report",
        "build_id": "demo-build",
        "run_id": "demo-build.1",
        "sanitizer_name": "ASAN"
      }
    ],
    "page": 1,
    "page_size": 100,
    "total_count": 1,
    "has_more": false
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site eu-ttp --json bytesan bug-build-report list \
  --bug-id demo-bug \
  --page 1 \
  --page-size 100
```

## `bytedcli bytesan report-content get`

根据 Report ID 获取缺陷报告正文，解析行为与 byteq-fe 报告弹窗一致。

当上游 JSON 含非法转义 `\x00`、导致严格解析失败时，命令按前端方式删除响应文本中的字面量 `\x00` 后重新解析。合法 JSON 的正文保持原样；清理后仍非法、HTTP 失败或上游业务失败时继续报错。该兼容只作用于报告内容接口。

### 参数

| 参数               | 必填 | 默认值 | 说明                |
| ------------------ | ---- | ------ | ------------------- |
| `--report-id <id>` | 是   | 无     | ByteSan Report ID。 |

### 输出

JSON 模式把原始报告放在 `data.content`；文本模式直接打印报告正文。

```json
{
  "status": "success",
  "data": {
    "report_id": "demo-report",
    "content": "ERROR: AddressSanitizer ..."
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --site us-ttp --json bytesan report-content get \
  --report-id demo-report
```

保存和分析 `data.content` 原文；不要在证据台账里用摘要替换原始报告。

## `bytedcli bytesan build-metadata get`

根据 Build ID 获取主仓库和依赖仓库的 Git metadata。

### 参数

| 参数              | 必填 | 默认值 | 说明               |
| ----------------- | ---- | ------ | ------------------ |
| `--build-id <id>` | 是   | 无     | ByteSan Build ID。 |

### 输出

`git_address` 与 `commit_hash` 表示当前构建主仓库；`dependencies` 保留 BuildCloud 返回的原始结构，可能包含依赖仓库的 Git 信息，不猜测或丢弃字段。

```json
{
  "status": "success",
  "data": {
    "build_id": "demo-build",
    "git_address": "example/repository",
    "commit_hash": "abcdef123456",
    "dependencies": []
  },
  "error": null,
  "context": {
    "execution_time_ms": 12,
    "timestamp": "2026-01-01T00:00:00+08:00",
    "api_endpoint": "ByteSan API"
  }
}
```

### 示例

```bash
bytedcli --json bytesan build-metadata get --build-id demo-build
```

该命令不依赖 global site，也不发送 ByteSan JWT。`git_address`、`commit_hash` 或依赖信息缺失时，把字段保留为缺失证据，不要据此猜仓库或版本。

## 错误处理

| 错误码                     | 含义                       | 处理方式                                                                  |
| -------------------------- | -------------------------- | ------------------------------------------------------------------------- |
| `BYTESAN_INPUT_ERROR`      | ID、URL、页码或页大小非法 | 按 `error.hint` 修正参数；检查 URL 的 host、path、资源类型与 query。 |
| `BYTESAN_API_ERROR`        | 上游明确返回失败           | 记录命令、ID 与错误；不要降级为空列表。                                   |
| `BYTESAN_PARSE_ERROR`      | 上游响应不符合当前字段契约 | 保留响应诊断信息并报告契约漂移；不要猜测缺失字段。                        |
| `BYTESAN_SITE_UNSUPPORTED` | 当前 global site 不支持    | 改用资源实际所属的规范 site；不要通过替换 host 或跨控制面 fallback 绕过。 |

单个 ID 失败时继续处理其他唯一 ID，但最终文档必须列出失败清单，并说明缺失证据是否影响根因或修复结论。
