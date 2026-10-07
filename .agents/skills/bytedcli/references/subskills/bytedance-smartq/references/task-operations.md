# 任务与计划

本页使用 SmartQ OpenAPI 的 `Platform`、`TestIDE-Token` 认证。写命令默认预览，只有 `--yes` 才提交；预览时需要显式提供请求体必需的用户身份，正式提交可使用当前登录用户。

## 查询任务与计划用例

```bash
bytedcli --json smartq task list --space-id 1000 --page 2 --page-size 20
bytedcli --json smartq task list --space-id 1000 --plan-id 2000 --name demo --belongs demo-user
bytedcli --json smartq plan case list --plan-id 2000

# 此处 username 是完整邮箱，mnt-run-id 来自执行结果中的 mntRunId
bytedcli --json smartq task result-url get --mnt-run-id 3000 --username demo-user@example.com
```

任务列表返回 `tasks`、`page`、`page_size` 和当前页条数；只有后端提供总数时才返回 `total`。计划用例列表保留用例集 ID、自动化叶子节点 ID 和完整节点路径。

## 从计划创建任务

`plan create` 与 `task create` 接收完整 JSON 文件。`filter_type=0` 的固定选择数据放在 `multi_case_scope`（字符串数组）、`multi_case_detail`（对象）、`tree_select_detail`（对象数组）中，至少一项非空；复制平台已有的完整结构并保留内部字段。

条件筛选 `filter_type=1` 接受 `case_filter_conditions` 或 `case_filter_conditions_v2` 对象数组。条件分配 `assign_type=2|3` 同样接受 `case_assign_conditions` 或 `case_assign_conditions_v2`。空数组或 `null` 不会遮住另一代非空条件；CLI 不重命名这些字段。

纯手工 `exe_type=0` 无需自动化包、安装与调度配置，但仍需要任务名、空间、场景、平台、用例选择与分配。Task 需要 `trigger_type`，手工 Plan 可省略。自动化模式沿用完整调度校验。

```bash
bytedcli smartq task create --body-file ./demo-manual-task.json --operator demo-user --dry-run
bytedcli smartq plan create --body-file ./demo-fixed-plan.json --operator demo-user --dry-run
```

## 从已有计划触发执行

```bash
# BITS 流水线触发：平台支持 android、ios、harmony
bytedcli smartq plan task create --plan-id 2000 --source bits --device-platform android --username demo-user --job-id demo-job --aid demo-app --package-url https://example.com/demo.apk

# 复杂 BITS 字段可放到文件；显式 option 覆盖文件里的对应字段
bytedcli smartq plan task create --plan-id 2000 --source bits --body-file ./demo-bits-task.json

# ByCaps：header 仅对 Web 任务生效
bytedcli smartq plan task create --plan-id 2000 --source bycaps --space-id 1000 --operator demo-user --header-json '{"x-demo":"sample-value"}'

# ByCaps 整个任务重试，返回的任务 ID 与链接保持不变
bytedcli smartq task retry --id 4000 --source bycaps --space-id 1000 --operator demo-user
```

BITS 字段映射：`--device-platform` 转为大写字段 `Platform`，值为 `ANDROID`、`IOS` 或 `HARMONY`。此外支持 `--callback-addr`、`--channel`、`--apk-mapping`、`--apk-resmapping`、`--inner-version-name`、`--version-name`、`--stage-name`、`--bits-task-name`、`--harmony-hap`、`--source-maps`。完整请求可通过 `--body-json` 或 `--body-file` 提供，两者互斥。

ByCaps 请求使用 `operator`、`space_id` 和可选 `header`。`--header-json` 与 `--header-file` 互斥，内容必须是字符串值组成的 JSON 对象。不要把 BITS 的包参数混入 ByCaps 请求。

创建结果保留 `taskId`；`taskUrl` 在后端已生成时返回。可使用 `smartq task wait --id <taskId>` 等待执行，再用 `task result list/get` 或 `task evidence` 获取结果和证据。创建成功只表示任务已提交。

`task retry` 是 ByCaps 整个任务重试。单条用例运行重试使用 `task result retry --id <taskId> --run-id <caseRunId> --device-platform <platform>`。
