---
name: bytedance-xpa
description: "Operate XPA agent platform via bytedcli: log in (folds bytedcli ByteCloud session into an XPA token), inspect the current user via the gateway, run system status checks, and manage tasks / workflows / devices / dataset (task list/get/status/running/subtask/create/start/pause/stop/device/export-result, workflow list/get/marketplace workflows/marketplace components/meta-node list/export-dsl/update/copy/publish/unpublish/create/delete/debug (start/get/list/stop)/device (bind/unbind/list), device list/idle/get/tasks/unbind/delete, dataset reset/rerun). Use when tasks mention XPA, XPA workflow marketplace, XPA workflow components, XPA MetaNode, xpa task, xpa workflow, xpa device, xpa dataset, xpa whoami, xpa system, or migrating from the standalone xpa-cli. All write commands are dry-run by default; add --yes to execute."
---

# bytedcli XPA

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

- XPA 任务管理：list / get / status / running / subtask list / subtask stop / create / start / pause / stop / task device add / task device remove / export-result
- XPA 工作流（workflow）管理：list / get / marketplace workflows / marketplace components / meta-node list / export-dsl（读）；update / copy / publish / unpublish / create / delete（写）；debug start / get / list / stop（调试运行子树）；device bind / unbind / list（设备绑定子树）。写命令默认 dry-run。
- XPA 设备管理：list / idle / get / tasks / unbind / delete（mobile / pc 两种 device type）
- XPA 数据集维护：reset / rerun
- 用户与连通性：whoami（网关侧用户视角，含 roles）、system status（网关 + env 路由自检）
- 鉴权：login / status / logout（复用 bytedcli ByteCloud 登录态，自动 exchange + 60s 内提前 refresh，refresh 失败降级重新 exchange）

## Do not use

- 独立 npm 包 `@bytedance-dev/xpa-cli`（`xpa <cmd>`）已并入 bytedcli。新用户优先 `bytedcli xpa ...`，不再单独装 `xpa-cli`。
- 设备 / 任务自身的执行（mobile-use / autopilot 等运行时能力）：不在本 skill 范围。
- xpa-cli 历史的 `xpa update` 自升级命令未移植；bytedcli 的自升级走 `bytedcli self update`。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 鉴权链路：bytedcli ByteCloud JWT → POST 换 XPA token → 落盘；首次跑 `bytedcli xpa whoami` 等命令时静默 exchange。命令报「请重新登录」时跑 `bytedcli xpa auth login`。
- BOE 联调：网关当前只在特性泳道部署，跑 `--xpa-env boe --xpa-tt-env <feature-lane>`（具体泳道名跟后端确认；基准环境部署后可省 `--xpa-tt-env`）。prod 默认即可。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 鉴权
bytedcli xpa auth login
bytedcli xpa auth status
bytedcli xpa whoami
bytedcli xpa system status

# 任务（读）
bytedcli xpa task list --status running --page-size 20
bytedcli xpa task list --task-id 1234567890
bytedcli xpa task get --id 1234567890
bytedcli xpa task status --id 1234567890
bytedcli xpa task running
bytedcli xpa task subtask list --id 1234567890 --status failed
bytedcli xpa task subtask list --id 1234567890 --serial-number SN-DEMO-001

# 任务（写：默认 dry-run，加 --yes 执行）
bytedcli xpa task start --id 1234567890
bytedcli xpa task start --id 1234567890 --yes
bytedcli xpa task pause --id 1234567890 --yes
bytedcli xpa task stop --id 1234567890 --yes

# 子任务终止（owner / super-admin 权限，先看 status 是 running）
bytedcli xpa task subtask stop --id 1234567890 --sub-id 9876543210 --yes

# 创建任务
bytedcli xpa task create \
  --name "demo-task" \
  --workflow-id 1234567890 \
  --device-ids 100001,100002 \
  --lark-file-url "https://example.feishu.cn/sheets/demoSheetToken"
bytedcli xpa task create \
  --name "demo-inline-jsonl-task" \
  --workflow-id 1234567890 \
  --device-ids 100001,100002 \
  --jsonl $'{"query":"case one"}\n{"query":"case two"}'
# 确认 dry-run 预览后，在同一条命令末尾加 --yes 执行

# 任务设备增减
bytedcli xpa task device add --id 1234567890 --device-ids 100003,100004 --yes
bytedcli xpa task device remove --id 1234567890 --device-ids 100002 --reason "device offline" --yes

# 导出结果（异步，后端接受后才落表）
bytedcli xpa task export-result --id 1234567890 --all --yes
bytedcli xpa task export-result --id 1234567890 --sub-ids 9876543210,9876543211 --yes
bytedcli xpa task export-result --id 1234567890 \
  --execute-start-from 1719158400 --execute-start-to 1719244800 --yes

# 工作流（读）
bytedcli xpa workflow list --device-type mobile --page-size 20
bytedcli xpa workflow list --name demo-workflow --all-enabled --all-workflows
bytedcli xpa workflow get --id 1234567890 --full
bytedcli xpa workflow marketplace workflows --keyword demo --published
bytedcli xpa workflow marketplace components --level atomic --device-type cloud
# 查看组件目录当前返回的完整结构（含后端返回的 node_param_struct / sub_nodes 等）
bytedcli --json xpa workflow marketplace components --level atomic --device-type cloud
# 独立查询权限范围内的 MetaNode 模板（结果集不保证覆盖 components）
bytedcli --json xpa workflow meta-node list --device-type pc --page-size 50
bytedcli xpa workflow device list --id 1234567890
# 导出前端可导入的 DSL：--out 落盘的文件逐字节可导入（int64 ID 保持数字形态）
bytedcli xpa workflow export-dsl --id 1234567890 --out ./demo-workflow.dsl.json
bytedcli xpa workflow debug list --id 1234567890 --status failed
bytedcli xpa workflow debug get --debug-id 9876543210

# 工作流（写：默认 dry-run，加 --yes 执行）
bytedcli xpa workflow update --id 1234567890 --name demo-renamed --yes
bytedcli xpa workflow copy --id 1234567890 --yes
bytedcli xpa workflow publish --id 1234567890 --yes
bytedcli xpa workflow unpublish --id 1234567890 --yes
# create/update 的 body 很大，先 export（--json 把 body 包在 .data 里，用 jq 取出）再改：
bytedcli --json xpa workflow get --id 1234567890 --full | jq '.data' > workflow.json
bytedcli xpa workflow create --from-json ./workflow.json --name demo-workflow --yes
# 调试运行 → 拿 debug_id → 查结果 / 停止
bytedcli xpa workflow debug start --id 1234567890 --data '{"foo":"bar"}' --device-type mobile --device-id 100001 --yes
bytedcli xpa workflow debug stop --debug-id 9876543210 --yes
# 绑定 / 解绑可执行设备
bytedcli xpa workflow device bind --id 1234567890 --device-ids 100003,100004 --yes
bytedcli xpa workflow device unbind --id 1234567890 --device-ids 100002 --reason "device offline" --yes
# 删除（破坏性、不可逆：需 --confirm-id 等于 --id 再加 --yes）
bytedcli xpa workflow delete --id 1234567890 --confirm-id 1234567890 --yes

# 设备
bytedcli xpa device list --type mobile --device-status online --page-size 50
bytedcli xpa device idle --type pc --os-type Windows
bytedcli xpa device get --type mobile --device-id 100001        # 定位符恰好一个
bytedcli xpa device get --type mobile --serial-number SN-DEMO-001
bytedcli xpa device tasks --type pc --instance-name demo-pc-01
bytedcli xpa device unbind --task 1234567890 --yes
bytedcli xpa device delete --type mobile --device-id 100001 --yes  # 破坏性、不可逆

# 数据集
bytedcli xpa dataset reset --task 1234567890 --yes
bytedcli xpa dataset rerun --task 1234567890 --rerun-type failed_task --yes
bytedcli xpa dataset rerun --task 1234567890 --sub-ids 9876543210 --device-ids 100002 --yes
```

## Notes

- 结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json xpa task list`）。
- 所有写命令默认 dry-run（不真发请求），加 `--yes` 才执行。**没有 `--dry-run` flag,也没有交互式 y/N 确认**——不带 `--yes` 即为 dry-run（退出 0），加 `--yes` 即真发。CI / 非 TTY 一律按此行为,不会卡在确认提示上。迁移自 `xpa-cli` 旧脚本时,把 `--dry-run` 直接删掉即可。
- `task create` 必须在 `--lark-file-url` 与 `--jsonl` 中恰好选择一个。`--jsonl` 直接接收文本，shell 中的多行内容使用 ANSI-C 引号 `$'第一行\n第二行'`，最多 5 MiB；dry-run 只显示字节数，不输出原文。inline 参数可能留在 shell history 或进程列表，不要传敏感内容。每个非空行必须是 JSON object，最多 5000 行、单行不超过 1 MiB，这些内容校验由 Gateway 负责。每行还需包含所选 workflow 开始节点要求的输入字段；遇到 `70024 JSON Lines文件解析错误` 时，先核对必需字段，尤其是字段名，再检查 JSON 语法、错误行号和大小限制。
- env profile：`--xpa-env boe|ppe|prod`（默认 prod）。BOE 暂只在特性泳道有实例，需要再带 `--xpa-tt-env <feature-lane>`。ppe 会自动加 PPE 染色头 `x-use-ppe: 1`。
- **flag 位置(commander 限制)**: `--xpa-env / --xpa-tt-env` 挂在 xpa 父命令上,**只能写在 `bytedcli xpa <这里> <subcmd>` 之间**——写在 `bytedcli` 后 `xpa` 前(`bytedcli --xpa-env boe xpa ...`)或叶子命令后(`bytedcli xpa system status --xpa-env boe`)都会 `error: unknown option --xpa-env`。同样的有 `--xpa-path-prefix / --xpa-base-url / --xpa-use-ppe / --xpa-http-timeout-ms`。位置不便时用环境变量等价: `BYTEDCLI_XPA_ENV / BYTEDCLI_XPA_TT_ENV / BYTEDCLI_XPA_PATH_PREFIX / BYTEDCLI_XPA_BASE_URL / BYTEDCLI_XPA_USE_PPE / BYTEDCLI_XPA_HTTP_TIMEOUT_MS`。
- **与 bytedcli 顶层 `--site` 的关系**: 顶层 `--site cn|boe|i18n|...` 只切 **ByteCloud SSO / OpenAPI 区域**(决定怎么拿 ByteCloud JWT),**不**切 XPA 网关环境。`bytedcli --site boe xpa whoami` 还是打 prod 网关——切 XPA 用 `--xpa-env`。两者独立,语义不同。
- 路径前缀已迁到根（不带 `/api`）：带 `/api` 会被 web BFF 截胡返回 `{code:401,"not login"}`。如果后端将来挪回 `/api`，用 `BYTEDCLI_XPA_PATH_PREFIX=/api` 覆盖,无需改码。
- int64 字段（task_id / sub_task_id / device_id / dataset_id / workflow_id / serial_numbers / sub_task_ids 等）以 string 承载保精度，命令层接受字符串，正整数本地校验。
- 设备定位符校验：mobile 用 `--device-id` 或 `--serial-number` 二选一；pc 还可用 `--instance-name`、`--instance-id`。四选一里恰好一个，多传或全空都直接拒。
- 时间范围（`--execute-start-from/to`、`--execute-end-from/to`、`--collection-from/to`）是**秒级 Unix 时间戳**（与后端一致），CLI 本地严校（拒 NaN/0/负数）。
- delete 设备是破坏性写；task subtask stop / dataset rerun / task stop 也会影响线上数据，都走二次确认。
- workflow 相关：`workflow list` 默认只返回启用且可创建任务的工作流，`--all-enabled` 放开启用过滤、`--all-workflows` 放开可创建过滤；workflow 广场主入口是 `workflow marketplace workflows`，只读 `workflow marketplace [options]` 仍作为兼容入口路由到同一 handler（含旧 `-k`、`--page-num`、`--page-number`），但不在父命令 help 中展示。`marketplace components` 返回按 level 分组的当前用户 marketplace 分类树；需要查看这个目录当前可见的完整结构时，直接以 `bytedcli --json xpa workflow marketplace components ...` 形式重跑原查询，读取后端实际返回的 `node_param_struct`、`sub_nodes`、`exception_handle_config`。`meta-node list` 是另一条独立的权限范围查询视图，不是 components 的详情下钻入口；两条链路的权限 / 发布状态边界不同，即使按 components 的 `meta_node_id` 精确查询也可能为空。`authorized` 是“节点是否需要权限”的后端字段，不能据此在客户端放宽访问控制。组件层级用语义值 `all` / `atomic`，设备类型用 `mobile` / `pc` / `cloud`，命令层映射到后端数字码。`workflow create` body 很大，先 `bytedcli --json xpa workflow get --id <id> --full | jq '.data' > workflow.json` 导出再改（`--json` 把工作流详情包在 `.data` 里，须用 `jq '.data'` 取出裸 body 再喂给 `--from-json`），文件 >5MB 直接拒，防止误传大文件 OOM。`workflow delete` 是破坏性、不可逆写，除 `--yes` 外还必须 `--confirm-id` 精确等于 `--id`（二次输入 ID）。调试运行是 `debug` 子树：`workflow debug start` 触发后拿 `debug_id`，`workflow debug get --debug-id` 查单次详情、`workflow debug list --id` 查某工作流的调试历史、`workflow debug stop --debug-id` 停止；`debug list --status` 只接受单个语义值 `running` / `success` / `failed`（命令层映射到后端调试状态码 8/4/5；后端拒绝多值）。设备绑定是 `device` 子树：`workflow device bind` / `unbind` / `list`。上述管理、调试与设备写命令成功执行后，若网关响应携带链路 `logid`，文本模式会单起一行输出，`--json` 则写入 `logid` 字段；可凭它定位「后端回 success 但状态未真正翻转」（如 publish/unpublish）等问题。`workflow export-dsl --id <id>` 导出前端「导入工作流」可直接用的 DSL：**只有 `--out <path>` 落盘的文件是逐字节可导入的**——文件写的是后端 `data` 原始字节，int64 ID（`agentPlanId`、节点 `MetaNodeId`）保持数字形态；不带 `--out` 时文本模式只打摘要，`--json` 输出的 `dsl` 会把大 int64 转成字符串（仅供查看，不可直接导入）。链路 `logid` 只回显到终端 / JSON，绝不写进文件（保持文件干净可导入）。
- 凭据落盘走 bytedcli 凭据存储约定（`bytedcliDataDir` 下的 `AuthFileCache`），不再使用旧的 `~/.xpa/auth.json`；token 明文绝不打印到终端。
- 历史的独立 `xpa <cmd>` 仍可用，但能力等价；新工作流统一用 `bytedcli xpa <cmd>`。

## References

- `references/commands.md` — XPA 各子命令的参数清单、写确认机制、定位符校验细节
- `../../troubleshooting.md` — bytedcli 通用安装、鉴权与网络问题处理
- `references/xpa-troubleshooting.md` — XPA 鉴权降级、env / 泳道路由、int64、组件目录等域内排障
