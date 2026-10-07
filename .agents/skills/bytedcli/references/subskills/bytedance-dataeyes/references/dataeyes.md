# Dataeyes

Dataeyes data validation testing capabilities. Refer to the [Dataeyes documentation](https://cloud.tiktok-row.net/docs/product/dataeyes?from=cloud&cdc_fallback=1&region=Singapore-Central&x-bc-region-id=bytedance) for details.

## Commands

### Project Management

**List projects**

```bash
bytedcli dataeyes project list
bytedcli --json dataeyes project list --page 1 --page-size 20
bytedcli --json dataeyes project list --all --keyword demo-project --page 1 --page-size 50
```

- 默认只列出当前用户负责的项目；`--all` 会列出当前用户可见的全部项目。
- `--keyword <keyword>` 按项目关键字过滤，可与 `--all` 组合用于只读查找现有配置。

**Get project details**

```bash
bytedcli dataeyes project get --project-id 12345
bytedcli --json dataeyes project get --project-id 12345 --detail
```

- 使用 `--detail` 可以获取项目的完整配置和变量信息。

**Create a project**

```bash
bytedcli dataeyes project create --payload-file ./new_project.json
```

**Update a project**

```bash
bytedcli dataeyes project update-config --project-id 12345 --payload-file ./update.json
bytedcli dataeyes project update-config --project-id 12345 --qps 300
bytedcli dataeyes project update-config --project-id 12345 --qps 300 --read-qps 500
```

- 支持更新任意项目配置字段（以 API 支持为准）。
- `--qps` 会同时设置 scan/read/write，`--scan-qps`/`--read-qps`/`--write-qps` 可单独覆盖。
- QPS 快捷参数与 `--payload-file` 不能同时使用。
- Boei18n 示例：`bytedcli --site boe --vregion US-BOE dataeyes project update-config --project-id 12345 --qps 300 --write-qps 500`

**Update validation config (validationConfig)**

```bash
bytedcli dataeyes project update-validation-config --project-id 12345 --payload-file ./validation_config.json
```

- validationConfig 由该接口统一配置。
- 常见字段：writeMode / scanQPS / readQPS / writeQPS / rules。
- 示例（validation_config.json）：

  ```json
  {
    "writeMode": 1,
    "scanQPS": 100,
    "readQPS": 100,
    "writeQPS": 100,
    "rules": [
      { "field": 0, "threshold": 5 },
      { "field": 1, "threshold": 600 },
      { "field": 2, "threshold": 200 },
      { "field": 3, "threshold": 10 }
    ]
  }
  ```

  - field 说明：0 代表运行时间；1 代表已处理数据数量；2 代表修复数据数量；3 代表异常 Key 占比（百分比）。

### Authorization Tickets

`ticket create` 和 `ticket update` 仅支持 DB-owner authorization ticket，不支持 Fix、ApplyOwner 或其他授权工单类型。

**Get an authorization ticket**

```bash
bytedcli dataeyes ticket get --ticket-id 10001
bytedcli --json dataeyes ticket get --ticket-id 10001
```

- 这是只读命令。执行任何工单操作前，先读取工单并核对工单 ID、类型、发起人、审批人和当前状态。

**Set a pending DB-owner authorization ticket to Canceled**

```bash
# 默认仅预览，不会撤回工单
bytedcli --json dataeyes ticket update --ticket-id 10001 --status canceled

# 确认预览内容后才实际撤回
bytedcli --json dataeyes ticket update --ticket-id 10001 --status canceled --yes

# 回读旧工单，确认状态已变为 Canceled
bytedcli --json dataeyes ticket get --ticket-id 10001
```

- `ticket update` 默认为 dry-run；仅当目标是 DB-owner authorization ticket 且显式传入 `--yes` 时才会调用写接口。
- `--status canceled` 仅用于当前状态为 `Pending` 的 DB-owner authorization ticket。执行后应回读同一个工单，等待状态变为 `Canceled`，不要在状态仍为 `Pending` 时基于它创建新工单。

**Create a new ticket from a Canceled or Rejected DB-owner authorization ticket**

```bash
# 确认旧工单已经是 Canceled 后，先预览派生创建计划
bytedcli --json dataeyes ticket create --from-ticket-id 10001

# 确认后创建新的审批工单
bytedcli --json dataeyes ticket create --from-ticket-id 10001 --yes

# 使用操作结果返回的新工单 ID 回读；此处 10002 仅为示例
bytedcli --json dataeyes ticket get --ticket-id 10002
```

- `ticket create --from-ticket-id` 仅用于状态为 `Canceled` 或 `Rejected` 的 DB-owner 授权工单。它会创建新工单；不要假设旧工单 ID 会被复用。
- 检查操作结果没有逐项失败或错误信息，并使用返回的新工单 ID 回读，确认新工单状态为 `Pending`。
- 状态更新与派生创建之间不使用固定等待时间；以 `ticket get` 的状态回读结果为准。派生创建后，如需启动项目任务，再用 `project get` 核对项目权限状态和 `canStartTask`。
- 基于旧工单的创建会延续已有的内部工单链路，不会重新解析数据库 owner。它适用于审批被撤回/驳回后的原链路重发，不适用于刷新 stale owner 快照。

**Create a fresh DB-owner ticket for a project DB index**

```bash
# 先运行 TaskStart 权限检查并预览；不会提交
bytedcli --json dataeyes ticket create --project-id 12345 --db-index 0

# 仅当 dry-run 返回 ready=true 时提交
bytedcli --json dataeyes ticket create --project-id 12345 --db-index 0 --yes
```

- `ticket create --project-id ... --db-index ...` 用于全新创建 DB-owner 工单，并在提交后回读新工单及项目关联。该输入形态与 `--from-ticket-id` 互斥。
- 写入前必须同时满足 `permissionCheckResult=NotPass`、`initiateStatus=CanInitiate` 且不存在 `dbOwnerTicketInfo`；`Pending` / `Undefined` 等中间态会 fail closed。
- 只要权限检查仍返回 `dbOwnerTicketInfo`，即使旧工单已经 Canceled/Rejected，命令也会拒绝提交，防止产生重复或未关联工单。
- owner 快照陈旧时，先由 DataEyes Oncall 清除/reset 旧 ticket association；再次 dry-run 确认 `ready=true` 后才执行 `--yes`。不要用反复的旧工单派生创建代替 owner 刷新。

### Validation & Tasks

**Start validation**

```bash
bytedcli dataeyes validation start --project-id 12345
```

- 启动项目的数据验证测试。
- validationConfig 通过 `project update-validation-config` 统一配置。

**List validation tasks**

```bash
bytedcli dataeyes validation list --project-id 12345
```

**Get validation report**

```bash
bytedcli dataeyes validation get-report --task-id 98765
```

- 获取已完成任务的验证报告。

**Create tasks**

```bash
bytedcli dataeyes task create --project-id 12345
bytedcli dataeyes task create --project-id 12345 --validation
bytedcli dataeyes task create --project-id 12345 --simulate-fix
bytedcli dataeyes task create --project-id 12345 --fix
```

- --validation 用于小流量 validation 任务。
- 正式任务三种模式：仅对比（不加 --fix/--simulate-fix）、对比 + 模拟修复（--simulate-fix）、对比 + 真实修复（--fix）。

**Manage tasks**

```bash
# 获取任务详情
bytedcli dataeyes task get --task-id 98765

# 暂停任务
bytedcli dataeyes task pause --task-id 98765

# 恢复任务
bytedcli dataeyes task continue --task-id 98765

# 终止任务
bytedcli dataeyes task kill --task-id 98765
```

**Process inconsistent data (post-fix)**

```bash
# Dry-run: preview request without calling the API
bytedcli dataeyes task post-fix --task-id 987654321
bytedcli dataeyes task post-fix --task-id 987654321 --simulate-fix

# Submit with --yes
bytedcli dataeyes task post-fix --task-id 987654321 --fix --yes
```

- 对应 UI 的"继续处理不一致数据"按钮，调用 `POST /api/v1/dataeyes/v3/platform/task/post_fix`。
- `--task-id` 必须是 taskType=0 的主对比任务 ID；它基于已有对比结果触发处理，不会重新扫描全量 key。
- 模式三选一：不传 flag（compare-only，不修复）、`--simulate-fix`（模拟修复）、`--fix`（真实修复；后端同时置 `isSimulateFix=true`）。
- 写接口默认 dry-run，必须显式 `--yes` 才提交。

### Fix Pipeline (workflow)

**Start a fix pipeline**

```bash
# Dry-run: preview request body without calling the API
bytedcli dataeyes workflow start --task-id 987654321 --config-file ./pipeline.json

# Submit with --yes
bytedcli dataeyes workflow start --task-id 987654321 --config-file ./pipeline.json --yes
```

- 对应 UI 的"发起修复流水线"按钮，调用 `POST /api/v1/dataeyes/v3/platform/workflow/start`。
- `--task-id` 是 taskType=0 的主对比任务 ID。
- `--config-file` 指向一个 JSON 文件，文件内容会作为请求体的 `config` 字段发送（即请求体为 `{"taskID":<id>,"config":<文件内容>}`）。文件包含 `targetDiffTypes`、`grayScaleList`、`stepList`、`autoNext`、`strategy`、`qps`、`validationConfig`。示例：

  ```json
  {
    "targetDiffTypes": [255],
    "grayScaleList": [1, 25, 100],
    "stepList": [200, 400, 500],
    "autoNext": false,
    "strategy": {
      "type": 3,
      "name": "example.dataeyes_common",
      "faasConfig": {},
      "hotKeyConfig": { "retryLimit": 2, "delayTime": 2 }
    },
    "qps": { "scanQPS": 1000, "readQPS": 1000, "writeQPS": 100 },
    "validationConfig": {
      "writeMode": 0,
      "scanQPS": 100,
      "readQPS": 100,
      "writeQPS": 100,
      "rules": [{ "field": 0, "threshold": 5 }]
    }
  }
  ```

- 写接口默认 dry-run，必须显式 `--yes` 才提交。提交前建议先从浏览器 DevTools 复制目标项目的真实 config，避免灰度比例/step 与项目预期不符。

**Get workflow detail**

```bash
bytedcli dataeyes workflow get --workflow-id 111
```

- 调用 `GET /api/v1/dataeyes/v3/platform/workflow/info?workflowID=<id>`。
- 返回 workflow 的 `status`、`curStepIdx`、`steps`（每步含 `stepID`/`status`/`type`/`taskID`/`grayScale`）以及生效中的 `workflowConfig`。
- 只读命令，无 dry-run。

**Stop a running workflow**

```bash
# Dry-run
bytedcli dataeyes workflow stop --workflow-id 111

# Submit with --yes
bytedcli dataeyes workflow stop --workflow-id 111 --yes
```

- 调用 `POST /api/v1/dataeyes/v3/platform/workflow/stop`，请求体 `{"workflowID":<id>}`。
- 写接口默认 dry-run，必须显式 `--yes` 才提交。

### Export inconsistent data

```bash
# Dry-run
bytedcli dataeyes task export-difflog --task-id 987654321

# Submit with --yes
bytedcli dataeyes task export-difflog --task-id 987654321 --yes
```

- 对应 UI 的"导出不一致数据"按钮，调用 `GET /api/v1/dataeyes/v3/platform/task/difflog_export_to_file?taskID=<id>`。
- `--task-id` 必须是 taskType=0 的主对比任务 ID；后端会基于最新一次对比结果导出 diff 明细文件。
- diff 结果过期时后端返回 `no diff log to export, please retry later`，需要先重新跑一次 compare（`dataeyes task create`）再导出。
- 导出的文件下载链接在 DataEyes UI 的任务页查看；CLI 只触发导出动作。
- 写接口默认 dry-run，必须显式 `--yes` 才提交。

**Task types (`taskType`)**

DataEyes 项目页「任务管理」下有三个 tab，对应后端 task list 接口的 `taskType` 取值：

| taskType | UI tab | 说明 |
| --- | --- | --- |
| `0` | 对比任务 | 主对比任务，扫描并比对全量 key |
| `1` | 不一致数据处理任务 | 基于主对比结果对不一致 key 做处理；返回体里带 `parentTask` 指向派生它的 taskType=0 主任务 |
| `2` | 不一致数据导出任务 | 导出不一致数据明细 |

- 同一项目的任务需要按 `taskType` 分别拉取：`GET /api/v1/dataeyes/v3/platform/task/list?projectID=<id>&taskType=<0|1|2>&offset=0&limit=100`。
- 判断任务是否仍在运行时，以 `status` 是否为非终态为准（`7` = Finished 是终态之一），并结合 `permission.canRun/canPause/canKill`；不要只看最近一条任务的更新时间。

**Repair modes (`isFix` / `isSimulateFix`)**

任务详情里的修复模式按以下优先级判定，与 UI「修复类型」列对应：

| 条件 | 修复类型 |
| --- | --- |
| `isFix: true` | 真实修复 |
| `isFix: false` 且 `isSimulateFix: true` | 模拟修复 |
| 两者均为 `false` | 不修复（仅对比） |

- `task create --fix` 会同时置 `isFix=true` 与 `isSimulateFix=true`；`--simulate-fix` 只置 `isSimulateFix=true`；不传两者则是仅对比。

## Notes

- API 访问需要配置相应的 ByteCloud site 和认证信息。
- 如果命令抛出 `Not Found` 或权限错误，请确认传入的 `project-id` 和 `task-id` 是否正确，以及当前登录用户是否有该项目的访问权限。
