# ByteDoc Go SDK 端到端跑通

适用于用户要求“跑通 demo”“本地起一个 Go 项目”“在 DevBox/TCE 验证 ByteDoc SDK 接入”的场景。支持 `local-mac`、`devbox`、`tce`。这里只处理 SDK bootstrap，不扩展到普通 Mongo 查询、慢查询治理或独立权限管理。

## 核心目标

不要只返回 `sdk plan`、代码片段或接入说明。正式入口是：

```bash
bytedcli --json --site <site> [--vregion <vregion>] bytedoc sdk bootstrap execute \
  --service <target.psm> \
  --access-env <local-mac|devbox|tce> \
  --dry-run
```

第一轮先展示完整路线并一次性收集最小必要字段，之后才执行 dry-run。不得让第一次使用 ByteDoc 的用户逐项追问路径、collection、DevBox、TCE、凭据或成功标准。

## 第一轮固定结构

收到请求后，第一轮回复必须包含以下四块。

### 我会做什么

- 运行正式的 `bytedoc sdk bootstrap execute`，而不是停在 `sdk plan`、`sdk generate` 或代码片段。
- 先做结构化 dry-run，解析目标、检查 collection 和正确的授权主体，再准备运行环境。
- 经用户确认相应 gate 后，生成或复用 Go demo，执行有界只读查询并收集证据。

### 需要你确认/准备什么

一次性列出当前 runtime 的全部最小必要字段，并把已知值和缺失值分开：

- 通用：`site`、目标 service、可选 backend/vregion、runtime、collection、caller PSM 或开发用户、是否允许只读控制面预检。
- `local-mac`：本地绝对输出路径；token 链路所需的 doas；Consul 来源；必要时作为 Consul 来源的 DevBox。
- `devbox`：VMID，或 SSH host + user；远程绝对目录；远程目录和凭据材料分别选择 `keep` 或 `cleanup`；Go/doas 状态。
- `tce`：caller PSM、runtime network、TCE site/env、源码 checkout、repo/branch/full commit、SCM repo/version、TCE cluster/deployment ticket、API Test 只读 endpoint。
- 任何 live 授权、凭据创建、doas 安装或标准发布动作都单独列出，不与最终 runtime 执行合并确认。

路径必须按实际执行位置区分：

- `--out` 是本地生成目录。
- `--devbox-remote-dir` 是 DevBox 目录，建议在 `/home/<user>/...` 下由用户确认。
- TCE 不生成临时项目；`--source-dir` 是 Agent 操作的现有本地源码 checkout。
- 不自动清理远程目录或凭据材料。用户必须分别选择 `keep` 或 `cleanup`。

### 我会自动检查什么

- `bytedcli --json auth status` 中目标站点的 ByteCloud Auth；短期 JWT 到期但登录仍有效时不重复要求扫码。
- 目标库解析结果、backend、VRegion、engine version 和 caller runtime network 是否一致。
- collection 是否真实存在。
- Volc 开发用户凭据与 caller PSM 授权是两个不同主体；token/Mesh 场景检查实际 caller PSM，不能拿当前用户权限代替。
- 本地 Go、Consul、doas；DevBox Kerberos/SSH、Go、Consul、doas；TCE 的 SCM 构建、部署、服务实例和 API Test 证据。
- 所有公开结果和日志不包含密码、token 或未脱敏文档。

### 什么才算成功

三项必须同时满足：

- `data.status=success`
- `completionGate.passed=true`
- 同一次最终 runtime 输出包含 `bytedoc readonly check succeeded` 和匹配目标库/collection 的脱敏只读证据

`sdk plan` 成功、代码生成、`go test`、SCM 构建、工单提交或单独出现 marker 都不是最终成功。

## 执行协议

### 1. 先跑 dry-run

把用户已经提供的 selector 和资源全部带入，不要丢掉 backend、vregion 或 caller PSM。

```bash
bytedcli --json --site boe bytedoc sdk bootstrap execute \
  --service example.bytedoc.demo \
  --backend volc \
  --access-env local-mac \
  --collection sample_items \
  --out /tmp/example-bytedoc-demo \
  --dry-run
```

读取并展示：

- `runbook.overview`
- `runbook.resourceChecklist`
- `runbook.missingFields`
- `runbook.liveGates`
- `runbook.executionPhases`
- `runbook.replayNotes`

如果缺字段，一次性询问 `missingFields` 对应的最小必要字段。不要逐项追问。

### 2. 每次只推进一个 gate

- `access_apply`：先展示 caller PSM、角色、reviewer、原因和 ticket 目的地；用户确认后才执行。PSM 已授权则跳过。
- `credential_grant`：只用于 Volc 本地/DevBox 开发用户凭据；用户确认 identity 和有效期后才执行。
- `local_doas_install` / `devbox_doas_install`：仅在探测确认缺失后展示安装影响并单独确认。
- `runtime_execution`：前置资源就绪后，再确认生成/使用路径和只读运行。
- live action 一次只执行一个；执行后重新运行 dry-run，不能把授权、安装和 runtime 混成一次调用。

涉及工单时必须返回 ticket id、状态和可点击 URL。平台未返回 URL 时明确说明“平台未返回 URL”，不要只给数字，也不要自行联系 owner。

### 3. local-mac

- 开发账号密码只负责 MongoDB 认证，不提供 Consul 服务发现。
- 必须使用明确标识的本地 loopback Consul endpoint，或由用户确认的 DevBox SSH tunnel。
- 输出目录必须是用户确认的新绝对路径；不得覆盖现有项目。
- token 链路需要 caller PSM 和 doas；缺 doas 时先走独立安装 gate。
- 最终运行 `go mod tidy`、`go test ./...` 和有界只读检查。

### 4. devbox

- VMID 优先；没有 VMID 时同时提供 SSH host 和 user。
- Kerberos/SSH 未就绪时，明确告诉用户要在对应环境完成 `kinit`，然后原参数重试。不要只报 “SSH failed”。
- 远程项目目录、目录生命周期、凭据材料生命周期必须在执行前一次性确认。
- token 链路缺 doas 时走独立安装 gate；密码链路不得伪装成 PSM 授权。
- `keep` 代表保留可继续开发的环境；`cleanup` 只有用户明确选择后才执行，并需给出清理证据。

### 5. tce

TCE 只支持标准发布链路：

```text
已审阅源码 -> SCM build_ok 产物 -> TCE 已完成部署及当前集群版本 -> API Test 只读运行结果
```

- bootstrap 不直接上传源码或二进制，不使用 WebShell，不提供快速/非标部署路径。
- SCM 构建、TCE 配置变更和 TCE 部署使用 bytedcli 现有 SCM/TCE domain 的标准命令，并遵守各自 dry-run/确认协议。
- `runbook.liveGates` 中的 `scm_build`、`tce_deploy` 或配置变更为 `external_action_required` 时，切换到对应 domain 完成该动作，再携带实际 SCM version、deployment ticket 等证据重跑 bootstrap。
- 不在 ByteDoc 层复制 SCM/TCE 业务规则；bootstrap 只验证 repo/branch/full commit、SCM artifact、cluster、deployment ticket、serving runtime 和 API Test 结果彼此一致。
- 最终 `--execute-runtime` 通过 API Test 调用已部署的静态 GET 只读 endpoint。HTTP 200 单独不足以通过 completion gate。

## Blocker 回复模板

阻塞时固定输出三块：

1. **已完成证据**：已解析目标、已验证 collection、已确认授权主体、已完成的 runtime preflight。
2. **当前 blocker**：原样展示 blocker code、原因和相关资源，不把 auth、PSM 授权、开发凭据、Consul 或网络问题混为一类。
3. **下一步**：明确用户需要执行或确认的一个动作；有工单时附 ticket id / URL / status。

终止态错误不换 site/backend/vregion 猜测重试。认证完成后沿用同一组参数继续，不更换资源或重启整条流程。

## 成功后的本次跑通复盘

成功后必须主动输出“本次跑通复盘”，至少包括：

- 目标：site、backend、VRegion、service、database、collection 和 operation。
- 运行环境：`local-mac` / `devbox` / `tce`，以及实际使用的本地路径、远程路径或 source commit。
- 授权与凭据边界：实际 principal、授权状态、凭据有效期；不得输出 secret。
- 可复用材料：生成文件、工作目录、关键命令、必要环境变量和 `runbook.replayNotes`。
- TCE 证据：SCM version/build URL、TCE ticket id/URL/status、API Test route/log evidence。
- 最终证据：completion gate、脱敏只读结果和 `bytedoc readonly check succeeded`。

## 验证要求

修改 SDK bootstrap 的 CLI、Skill 或 runtime 后，除离线测试外，必须按受影响 runtime 跑对应真实场景的 live 验证。真实场景验证只使用用户明确提供的测试资源；不得自行寻找其它数据库、DevBox 或 TCE 服务。保存实际命令、结构化结果、blocker/工单和最终 marker，供人工复核。
