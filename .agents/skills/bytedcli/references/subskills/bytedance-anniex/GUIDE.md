---
name: bytedance-anniex
description: "Use when the user explicitly asks to use, configure, or troubleshoot bytedcli anniex or the anniex CLI. Covers the CLI workflow for domestic JSBridge and Event development: independent SSO login, command and parameter lookup, create-option discovery, template initialization, dry-run creation or iteration, resuming in-flight work orders, and AnyCode download. General AnnieX capability lookup, monitoring, dashboards, Scheme, GlobalProps, and test-case tasks belong to anniex-ability-kit instead."
---

# bytedcli AnnieX

本 Skill 只处理 CLI 能力：登录、查询、新建、迭代或续改在途工单、拉取 AnyCode 代码。
端能力文档检索、线上监控、看板、Scheme / GlobalProps 管理和测试用例创建不在本 Skill 范围内。

## 调用方式

AnnieX 使用自己的 SSO 登录态，不复用 `bytedcli auth login`。

```bash
bytedcli anniex --help
bytedcli anniex jsb --help
bytedcli anniex jsb <command> --help
```

需要机器可读结果时，把 bytedcli 全局参数放在 `anniex` 前：

```bash
bytedcli --json anniex auth status
bytedcli --json anniex jsb list --app-id <app-id> --method x.example
```

安装 bytedcli、全局参数和调用前缀见 [../../invocation.md](../../invocation.md)。
具体参数以当前环境的 `bytedcli anniex ... --help` 为准，不要凭记忆补参数。

## 执行原则

1. 新建前先运行 `create-options`，以能力中心实时返回的候选为准。
2. `create`、`iterate`、`pull-code` 默认先预演；未经用户明确确认，不追加 `--confirm`。
3. 不替用户猜宿主、业务类型、支持端、容器或调用权限，也不制造“推荐配置”。
4. 工单创建成功只表示流程已发起；能力需完成评审、研发和验收后才会生效。
5. 不输出、记录或写入 Session、Cookie、Token 等凭证。

## 流程选择

| 用户目标 | 流程 |
|---|---|
| 首次使用或登录失效 | `auth status` → 两阶段登录 |
| 查询 JSBridge / Event | `jsb list` |
| 新建 JSBridge / Event | `create-options` → 用户选择 → `init` → 补全模板 → `create` 预演 → 确认提交 |
| 修改已发布能力或续改在途工单 | `iterate` 预演 → 确认提交 |
| 拉取 AnyCode 代码 | 定位能力或工单 → `pull-code` 预演 → 确认写入 |

## 登录

先检查登录态：

```bash
bytedcli --json anniex auth status
```

Agent 场景使用两阶段登录，避免运行持续等待的阻塞命令：

```bash
bytedcli --json anniex auth login --begin
bytedcli --json anniex auth login --complete <complete-token>
```

`--begin` 会返回授权地址、`complete_token`、过期时间和建议轮询间隔。把授权地址交给用户；
用户完成授权后，用同一个 token 执行 `--complete`：

- `pending`：授权尚未完成，按建议间隔继续检查同一个 token，不要重新 `--begin`。
- `success`：登录态已保存，可以重试原命令。
- `expired`：challenge 已失效，使用返回的重试命令重新开始。

人工在自己的终端操作时可使用阻塞式 `bytedcli anniex auth login`。退出登录：

```bash
bytedcli anniex auth logout
```

## 查询 JSBridge 与 Event

JSBridge 使用 `caller-method=call`，Event 使用 `caller-method=on`；不传时两类都返回。

```bash
bytedcli --json anniex jsb list --app-id <app-id>
bytedcli --json anniex jsb list --app-id <app-id> --method x.example
bytedcli --json anniex jsb list --app-id <app-id> --caller-method on
```

同名能力可能属于不同宿主。必须使用真实 `app-id` 缩小范围，不要根据代码仓库名或相似能力名猜归属。

## 新建 JSBridge 或 Event

### 1. 读取实时选项

```bash
bytedcli --json anniex jsb create-options --caller-method call
```

新建 Event 时改为 `--caller-method on`。读取返回的 `form.fields`，通过当前运行时的结构化提问
收集未明确字段：

- `businessType`：单选；一个选项同时绑定 `appIdList`、`productionId` 和 `containerId`，不要拆开询问。
- `osList`：多选，至少一项。
- `containerList`：多选，至少一项。
- `auth`：JSBridge 单选；Event 没有此字段。

字段是否多选只看本次返回的 `multiple`。候选没有默认值，数组顺序也不表示推荐；用户已经给出的值
仍需用本次结果校验，但不要重复询问。必填项未确认前，不得执行 `init`。

### 2. 生成并补全模板

```bash
bytedcli anniex jsb init \
  --business-type <container-id> \
  --os <os，可重复> \
  --container <container，可重复> \
  --auth <auth> \
  -o jsb.json
```

Event 增加 `--caller-method on` 并省略 `--auth`。`init -o` 不覆盖已有文件。生成后补齐方法名、
功能说明、请求与返回接口、审核人和需求文档等业务字段。

### 3. 预演并提交

```bash
bytedcli --json anniex jsb create -f jsb.json
bytedcli --json anniex jsb create -f jsb.json --confirm
```

第一条只生成预演结果。向用户展示目标宿主、能力名、支持端、容器、权限和主要接口变更；只有用户
确认本次预演后，才执行第二条提交命令。

## 迭代与续改在途工单

复杂修改优先写入补丁文件：

```bash
bytedcli --json anniex jsb iterate \
  --app-id <app-id> --method x.example \
  --patch-file patch.json
```

参数级修改可重复使用增删参数选项：

```bash
bytedcli --json anniex jsb iterate \
  --app-id <app-id> --method x.example \
  --add-request-param 'foo:string:true:字段说明' \
  --remove-response-param oldField
```

检查预演后，再在同一命令追加 `--confirm`。CLI 会按能力定位在途工单：

- 没有在途工单：创建新的迭代工单。
- 只有一条：续改该工单，并保留已有审核人与开发者。
- 有多条：停止，由用户选择 `--history-id`。
- 指定工单已合入或撤回：停止，不静默新建替代工单。

请求 Interface 变化时必须同时更新对应 Schema；返回 Interface 同理。治理字段、能力归属和状态等
受控字段不能通过补丁修改。

## 拉取 AnyCode 代码

优先用宿主和方法名定位当前可访问的唯一在途工单：

```bash
bytedcli --json anniex jsb pull-code \
  --app-id <app-id> --method x.example \
  --platform ios --lang oc -o <target-dir>
```

也可明确指定来源：

```bash
bytedcli --json anniex jsb pull-code \
  --history-id <history-id> --platform ios --lang swift -o <target-dir>
bytedcli --json anniex jsb pull-code \
  --method-id <method-id> --platform android -o <target-dir>
```

三种定位方式互斥：`--history-id` 指定工单，`--method-id` 固定拉线上已发布版本，
`--app-id + --method` 用于定位当前工单。存在多条在途工单时，必须让用户选择 CLI 返回的
`history-id`，不要自行猜测。

`pull-code` 默认只展示文件清单；用户确认后追加 `--confirm` 才写入。已有文件默认拒绝覆盖，
只有用户再次明确同意覆盖时才追加 `--force`。代码生成只支持 `ios` 和 `android`；iOS 的
`--lang` 可选 `swift`、`oc`、`both`。

## 联调与失败处理

PPE 联调时可为单次命令设置 `ANNIEX_TT_ENV`；未设置时走生产环境。不要把 PPE 配置固化到
用户仓库或全局 shell 配置。

出现参数不识别、命令层级变化或 CLI 版本差异时，先运行对应层级的 `--help`。登录问题使用
`bytedcli --json anniex auth status` 和上述两阶段登录流程处理；不要改用 `bytedcli auth login`，
也不要用通用排障结论替代 AnnieX CLI 返回的具体错误信息。
