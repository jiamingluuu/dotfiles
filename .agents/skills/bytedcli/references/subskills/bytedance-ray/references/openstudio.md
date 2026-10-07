# OpenStudio Ray 服务管理

范围为 CN 的「服务管理 → Ray 服务」，不包含 Ray 集群创建、Ray Job 提交、订阅状态修改、删除服务或禁用 IP。认证复用 `bytedcli auth login --site cn` 的 ByteCloud JWT。项目 ID 与服务名称是必填的显式目标，不复用 Dashboard `--url`。

```bash
bytedcli auth login --site cn
bytedcli --site cn --json ray service list --project-id demo-project --scope mine
bytedcli --site cn --json ray service list --project-id demo-project --scope subscribed
bytedcli --site cn --json ray service list --project-id demo-project --scope all --keyword demo --page 1 --page-size 20
bytedcli --site cn --json ray service get --project-id demo-project --name demo-service
bytedcli --site cn --json ray service version list --project-id demo-project --name demo-service
# 以下仅预览，不提交
bytedcli --site cn --json ray service update --project-id demo-project --name demo-service --file demo-patch.json
bytedcli --site cn --json ray service restart --project-id demo-project --name demo-service --restart-type ALL
bytedcli --site cn --json ray service stop --project-id demo-project --name demo-service
bytedcli --site cn --json ray service rollback --project-id demo-project --name demo-service --version demo-version
```

`mine` 为默认范围，使用登录用户作为创建人；`subscribed` 对应页面「我的订阅」；`all` 对应「所有服务」。`--keyword` 是后端名称搜索，支持与三个范围组合。分页是服务端分页，默认 1/20，page-size 上限 100。结果包含 `total`、`page`、`page_size`、`has_more`，不要把一页当作全量。

## 编辑文件

`--file` 为 UTF-8 JSON，顶层只接受下表字段；省略的配置保留原值，拼写错误会报错。

| 页面区域 | 文件字段 | 行为 |
| --- | --- | --- |
| 基本信息 | `basic.clusterId`、`basic.byteQuotaName`、`basic.script`、`basic.bytep2p` | 按字段修改；项目、服务名不可更改 |
| 镜像配置 | `image.rayImage`、`image.imageConfig`、`image.scm` | 镜像地址与选择方式必须同时给出；SCM 数组整体替换 |
| Header 节点 | `head` | 完整 CPU 节点规格，包含 cpu、memory；可选 socket；gpu 仅允许 null |
| Worker 节点 | `workers` | 普通 CPU Worker 数组整体替换，每项需 cpu、memory、replicas；可选 socket |
| 参数配置 | `parameters`、`environmentVariables` | 按 key 合并；null 删除对应 key；字符串值保留原样 |

例：

```json
{
  "basic": {"byteQuotaName": "demo-queue", "bytep2p": false},
  "image": {"rayImage": "example.com/demo/ray:v2", "imageConfig": {"config": "url"}},
  "head": {"cpu": 4, "memory": {"count": 8, "unit": "GB"}},
  "workers": [{"cpu": 4, "memory": {"count": 8, "unit": "GB"}, "replicas": 2}],
  "parameters": {"demo-option": "true"},
  "environmentVariables": {"DEMO_MODE": "test", "DEMO_OLD": null}
}
```

`imageConfig.config` 可为 `url`、`repository`（同时给 repository/repositoryVersion）或 `center`（同时给 center/centerVersion）；`rayImage` 必须是对应版本已解析的镜像地址。SCM 每项为 `name`、`version`、`path`，path 以 `/opt/tiger/` 开头。CPU/内存必须为正数，内存单位为 GB，replicas 为正整数。普通 Worker 替换不修改原有 Bernard/Auto 资源配置。

当前验证范围为普通 CPU Header/Worker；Bernard、Auto、GPU 资源编辑由人工在平台处理。页面有“备注”输入，但已验证的前端提交 SDK 未发送 `Note`，CLI 因此拒绝 `basic.note`，不宣称备注已保存。

## 人工确认（不可跳过）

编辑提交也会触发重启。仅修改 SCM/入口脚本且服务处于 RUNNING、INTERNAL_FAILED 或 UNHEALTHY 时采用 QUICK，其余配置变更采用 ALL。显式 restart 默认 ALL，QUICK 仅接受 RUNNING。回滚先读取指定版本并输出配置差异，再计算重启方式。

Agent 先生成文件、调用预览并展示项目/服务、当前版本与状态、具体差异、重启类型和控制台链接，明确提示“高风险：可能重启或中断运行中的任务”。**用户针对该预览在聊天中明确回复“确认”等批准语句后，Agent 可以代为执行**，无需让用户再次亲自在终端输入。普通任务请求、沉默、取消或其他操作的确认均不算批准。

收到人工确认后，Agent 可在 PTY 中重跑同一命令并加 `--interactive`（去掉 `--json`），读取终端中的新预览；仅当操作、项目/服务目标、配置差异、当前版本、回滚目标版本、状态与重启方式仍与已批准预览一致时，才代填完整的 `ACTION project/name`。发现任何变化时取消，展示新预览并重新请求人工确认。人工也可自行在终端或平台操作。CLI 没有 `--yes`、`--force`、`--execute` 批准入口；不得绕过预览与复查直接调用写接口。

文件编辑还必须绑定获批的精确输入：生成待审批预览前记录 `--file` 的完整内容或 SHA-256，启动交互命令前、输入确认短语前均再次核对。内容发生变化时重新预览、请求确认；脚本、环境变量或敏感参数即使仍显示相同的 `[REDACTED]`，也不能视为同一变更。不得在预览与提交之间改写已获批文件。

交互提交会再次展示当前预览，要求输入完整的 `ACTION project/name`。JSON/MCP 直接调用、非 TTY、取消、输入不匹配或两分钟超时均不提交；Agent 代为提交使用上述经人工批准的交互路径。确认后复查版本、状态、更新时间和完整配置；发现变化或进程内预览超过五分钟则要求重新审阅。计划仅在当前进程内使用一次，写请求不自动重试。聊天确认由 Agent 按本技能核对，CLI 不验证聊天记录；终端确认是操作流程控制，不是能够鉴别人类与自动化程序的身份认证机制。

详情与预览会脱敏凭据、环境变量和脚本；脱敏后的输出不能作为完整配置回写。敏感字段修改仍会列出字段路径，请人工检查本地输入文件和平台原值。服务端接受请求不等于操作完成，需要通过 `service get` 查看最终状态。读写都保持平台的服务权限校验。
