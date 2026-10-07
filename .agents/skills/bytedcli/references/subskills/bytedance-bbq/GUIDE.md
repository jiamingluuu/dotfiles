---
name: bytedance-bbq
description: "Operate the BBQ test automation platform. If the current agent has the bbq-cli skill available, use that skill for BBQ tasks; otherwise use this skill and bytedcli bbq. Covers BBQ test cases, schemas, plans, executions, reports, environments, configurations, variables, accounts, interfaces, actions, scripts, and FaaS. Do not use for generic test-strategy discussion or unrelated SmartQ/Tesla tasks."
---

# bytedcli BBQ

BBQ（Build Brilliant Quality）是 PDI-Seed 主要的接口自动化测试平台，支持代码和低代码自动化。平台按空间组织测试资源并隔离权限，提供用例、模版、计划、执行报告及相关配置管理。通过 `bytedcli bbq` 可以在命令行完成资源发现、维护、调试运行和结果排查。

平台资料：[BBQ 测试平台使用指南](https://bytedance.larkoffice.com/wiki/wikcnGFi8keCiKScNCLDdoqhsfg)；[BBQ 主页](https://lark-bbq.bytedance.net/bbq/#/)。

## Skill 选择

- 当前 Agent 的可用 Skill 中有 `bbq-cli` 时，直接使用 `bbq-cli` Skill 的流程与命令，不混用本 Skill 的 `bytedcli bbq` 参数或鉴权说明。
- 没有 `bbq-cli` Skill 时，使用下文的 `bytedcli bbq`；用户只说“BBQ”也适用，不要求用户知道或安装 `bbqcli`。
- 用户明确指定 `bbqcli` 或 `bytedcli` 时，遵从用户指定的 CLI。判断依据是当前 Agent 可用的 Skill，不是本机是否同时安装了两个 CLI。

## 调用与鉴权

- 通用调用、全局参数位置和 JSON 输出见 `../../invocation.md`。
- 需要机器可读结果时使用 `bytedcli --json bbq ...`；`--json` 必须放在 `bbq` 前。
- `bytedcli bbq ping` 检查平台连通性（无需登录）；`bytedcli bbq whoami` 查看当前 BBQ 用户。
- 默认直接执行 BBQ 命令，由 bytedcli 获取 CN 站点的 ByteCloud 用户 JWT；不要在每次调用前额外执行登录或鉴权检查。BBQ 仅支持 CN，不受全局 `--site` 影响。
- 除公开的 `ping` 外，BBQ 请求由 CLI 将该 JWT 写入 `x-bbq-jwt-token`。BBQ domain 不维护独立 token，也不回退旧 `bbqcli` 的 `USER_TOKEN` / `BUILD_TOKEN` / 本地配置。不要索取、展示或把 token 写入命令参数、Skill、日志或仓库。
- BBQ 自有的 `--ppe-env`、`--use-proxy` 等参数按 `bytedcli bbq --help` 使用；不要改用旧 `bbqcli` 的安装、登录或配置文件流程。
- 参数、默认值和条件必填项以当前 `bytedcli bbq <domain> <operation> --help` 为准，不凭记忆猜测，也不复制旧 `bbqcli` 参数手册。

## 工作原则

- 大多数资源受空间隔离；所有需要 `space-node-id` 的流程先按下方“空间选择”确定空间。
- 查询或详情返回多个候选时，先用名称、标签、PSM、协议类型等条件收敛，再进行更新、运行、切换、拆分、认领、释放或删除。
- 用户明确要求创建、更新、运行等写操作时可直接执行，不添加 CLI 不支持的 `--yes` 或 `--dry-run`。目标或影响范围不明确时先查询确认。
- BBQ 的布尔参数保持一比一语义；如果帮助要求显式值，就传 `true` 或 `false`，不要擅自改成 presence flag。
- 命令没有返回有效资源时，明确说明搜索过的空间和条件，不用不相关结果补位。
- `case-id`、`schema-id`、`plan-id`、`execution-id`、`case-report-id`、case execution ID 和 `config-id` 含义不同，只使用上一步响应中与目标字段明确对应的值。

## 空间选择（新人执行前置）

`space-node-id` 是 BBQ 的资源隔离范围。新人通常不知道空间 ID，不要在尝试自动推荐前要求用户自行查找。

1. 用户明确给出 `space-node-id` 时直接使用，不再推荐其他空间。
2. 用户未指定时，在第一个需要空间的命令前执行：

   ```bash
   bytedcli --json bbq space recommendation list
   ```

   该命令承载底层 space guess/recommend 语义，返回当前身份可访问且可能有用的空间。

3. 根据用户描述中的业务、产品、模块、PSM 和空间名称对结果排序。存在唯一高置信候选时可直接继续，并在结果中说明采用的空间名称和 `space-node-id`。
4. 多个候选同样合理时，优先展示不超过 3 个候选让用户选择。不要猜 ID，也不要使用写死的公共空间兜底。
5. 读操作或资源搜索在首选空间没有结果时，可以继续尝试其余高相关候选；创建、更新、运行等操作确定一个目标空间后，不得静默切换空间。
6. 一次任务确定空间后，后续 case/schema/config/var/account/plan 等命令复用同一个 `space-node-id`；只有出现明确的跨空间需求才重新推荐或选择。
7. `space recommendation list` 无结果或失败时，说明当前登录身份没有取得可用空间，并先处理鉴权或空间权限，不伪造候选。

## 命令域

保留 BBQ 的资源域和能力，公开入口统一采用 bytedcli 的“资源在前、动作在末”结构：集合用 `list`，关键词模糊检索用 `search`，单个资源用 `get`，非 CRUD 运行用 `execute`。BBQ 旧操作名仍用于内部接口映射，不作为 CLI 命令或隐藏别名。分页参数使用 `--page`，时间范围使用 `--start` / `--end`；账号数据驻留地和接口拓扑 GEO 保留 BBQ 的 `--geo`，不要误写成 `--region`。

| Domain        | Operations                                                                                                                                                                                                                        | 用途                                     |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `case`        | `list/create/update/get/execute`; `snapshot list`; `run-record list`; `review-record list`; `tag create/delete`; `status update`; `split execute`                                                                                 | 用例查询、维护、调试执行、记录与版本操作 |
| `schema`      | `list/create/update/get/execute/import`; `snapshot list`; `recommendation list`; `sharing create`; `review-record list`; `status update`                                                                                          | 可复用测试模版的搜索、维护、执行与分享   |
| `plan`        | `list/create/update/execute/rerun`; `copy create`                                                                                                                                                                                 | 测试计划维护与执行                       |
| `execution`   | `list`; `report list`; `case-record list`; `case-report get`; `plan-report get`; `argos-log get`; `log get`                                                                                                                       | 执行状态、报告、失败明细和日志           |
| `space`       | `recommendation list`                                                                                                                                                                                                             | 获取当前身份可访问的候选空间             |
| `environment` | `list`                                                                                                                                                                                                                            | 查询执行环境枚举                         |
| `config`      | `create/list/get`                                                                                                                                                                                                                 | 管理空间执行配置                         |
| `var`         | `list/create/update`; `topology get`; `generation execute`                                                                                                                                                                        | 管理变量、依赖拓扑并触发变量生成         |
| `account`     | `get/list/update`; `session update`; `credential create/execute`; `tenant create`; `user create/import`; `doubao-user create/import`; `doubao-session update`; `ownership claim/delete`; `reservation delete`; `whitelist update` | 测试账号、租户和凭证生命周期             |
| `action`      | `search`                                                                                                                                                                                                                          | 按关键词搜索 case/schema 中的接口动作    |
| `interface`   | `list/update`; `metadata get`; `idl get`; `pb-command-mapping get`; `security-relevance update`; `topology get/update`                                                                                                            | 接口、IDL/PB 映射、安全属性和调用拓扑    |
| `debug`       | `list`                                                                                                                                                                                                                            | 查询历史调试记录                         |
| `setting`     | `list`                                                                                                                                                                                                                            | 查询平台级设置                           |
| `script`      | `list/create/update/delete/execute`                                                                                                                                                                                               | 管理和运行 Bash 脚本                     |
| `faas`        | `list/create/update/get`                                                                                                                                                                                                          | 管理低代码函数                           |

## 资源发现

用户按自然语言寻找 BBQ 资源时：

1. 没有空间时按“空间选择”执行 `space recommendation list`；读场景可在最多 3 个高相关候选空间中搜索。
2. 在候选空间中优先使用 `schema recommendation list` 和 `action search`；需要按协议收敛时再增加 HTTP、PB 或 RPC 条件。
3. 召回不足或不匹配时，再使用 `case list`、`schema list`。
4. 对最相关的少量候选执行 `case get` 或 `schema get`，核对名称、描述、步骤、接口和入参后排序。
5. 没有符合要求的资源时如实说明；只有用户要求新建时才进入创建流程。

## 创建和更新 Case / Schema

- 优先复用 `get` 返回的现有结构做局部修改；创建 case 时，如果命令支持且需求简单，优先使用 `easy-json`，避免手写完整 `graph-json`。
- 更新前先读取目标详情。`case update` 即使不改名也可能要求 `case-name`；以当前帮助为准。
- 自动生成或修改 `graph-json` 时，先读取 `references/graph-json.md`。不要凭空发明 schema、函数或 PB command ID；引用必须来自平台查询结果。
- `schema import` 的源 schema 必须已公开；目标空间来自用户输入或 `space recommendation list` 的明确选择。
- `case status update` / `schema status update` 会改变上线状态，必须使用用户指定的目标和显式布尔值。

## 执行与报告闭环

### Case 或 Schema 调试运行

1. 用 `case get` 或 `schema get` 核对目标。
2. 用 `config list` 获取与目标空间、环境相符的 `config-id`；需要时查看 `config get`、`environment list` 和相关变量。
3. 依赖登录态时先 `account list` 选择候选，再用 `account get` 获取执行所需的真实凭证；不要使用列表中的脱敏展示值。
4. 使用 `case execute` 或 `schema execute`。Schema 运行参数优先通过 `config-id` 或局部修改后的 `graph-json` 注入，不假设存在旧式 `in-params` 直传。
5. 根据返回的执行标识继续使用 `execution list`、`execution report list`、`execution case-record list`、`execution case-report get`、`execution log get`；按 LogID 排查时使用 `execution argos-log get`。

`case run-record list` 使用 `--page-size` 控制最近记录的返回上限；底层映射服务端 `limit`，该接口不支持 `--page` 翻页。

### Plan 执行

1. 用 `plan list` 或 `case list` 确认计划及选例范围。
2. 创建或更新计划时，静态 case 列表使用查询结果中的 `caseHashNoVersion`，不要用裸 case ID 猜接后端格式；动态选例表达式保持合法 JSON。
3. 使用 `plan execute` 或用户明确要求的 `plan rerun`，保存响应中的 execution 标识。
4. 用 `execution list` 跟踪状态，并用 `execution report list`、`case-report get`、`plan-report get` 和日志命令完成结论。

## 账号与敏感数据

- `account list` 用于筛选候选，真实会话或凭证只从 `account get` 获取。
- 凭证、session、手机号、密码等敏感字段只在当前命令链内部使用；不要复制到日志、Skill 或仓库。账号接口的 HTTP trace 会整体隐藏请求和响应 body。
- `account update` 若使用整表覆盖模式，必须先查询并保留未修改字段；只改局部配置时使用命令支持的局部模式。
- `ownership claim/delete`、`reservation delete`、`session update`、`credential execute`、`whitelist update` 和各类创建命令会产生真实资源变化，执行前必须确保账号、租户、unit、环境和目标空间已经明确。

## 错误处理

- `AUTH_REQUIRED`、401 或 JWT 过期：优先按 CLI 返回的 `error.auth_command` 恢复 bytedcli 统一登录态，然后最多重试一次；正常调用前不主动触发登录。
- 403：停止重试，说明当前身份缺少目标空间或资源权限。
- 参数错误：读取报错中的 `hint`，再查看对应命令 `--help`。
- 命令成功不等于测试成功；最终结论以 execution 状态、报告和 case 明细为准。
- 通用认证、网络和调试排查见 `../../troubleshooting.md`。

## References

- `references/graph-json.md`：创建或修改 case/schema 图结构时读取。
- `../../invocation.md`：不确定全局参数位置、JSON 输出或 HTTP 调试参数时读取。
- `../../troubleshooting.md`：认证、权限或网络错误排查时读取。
