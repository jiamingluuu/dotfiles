---
name: bytedance-goofy-deploy
description: "Operate Goofy Deploy and Goofy Preview via bytedcli. Use when tasks mention Goofy Deploy, Goofy Preview, quick preview, frontend deployment, BFF deployment or environment configuration, deployment diagnosis/retry/cancel/rollback, cross-region bulk deploy, VMOK producer publishing with a Tag, or VMOK consumer deployment with tagged remotes. Route VMOK producer publishing to `goofy deploy publish`; add `--vmok-remote <module=tag>` to `deploy-new` or `deploy-version` when deploying a consumer."
---

# bytedcli Goofy Deploy / Preview

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

- Web 应用部署
- 前端项目部署
- 本地构建目录 quick preview
- 查看部署历史
- 诊断部署失败原因
- 取消/重试/回滚部署
- 查看项目/团队/频道信息
- 查看项目构建配置
- 触发新版本部署（支持 --wait 轮询等待）
- 搜索 Goofy Deploy 项目
- 发布 Vmok 生产者版本
- 跨 Region 克隆部署与 Region（bulk deploy，如 China-North → Singapore-Central）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- Goofy Deploy / Preview 需要个人 ByteCloud JWT。在生产网且存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH` 时，CLI 会按当前 Goofy 路由的 JWT credential host 解析 credential site，并优先执行 ZTI→个人 JWT；交换不可用或失败时自动回退该 credential site 的原有登录链路。办公网仍使用原有 SSO 链路。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

### Quick Preview / 快速预览部署

把本地构建好的目录快速部署，并产生一个可访问的预览链接，可用于日常 Demo 演示，快速部署本地产物等场景。

```bash
# 部署项目根目录（自动检测 dist/build/out 构建产物）
bytedcli goofy preview deploy . --alias demo-preview
# 列出所有快速预览环境
bytedcli goofy preview list --page 1 --page-size 20
```

> 支持的目录类型与详细说明见 `references/preview-directory.md`。

### Normal Project Deploy / 普通项目部署

对已有的正式 Goofy Deploy 项目进行搜索、查看、部署等。

```bash
# 列出支持的站点和相应 VRegion 信息
bytedcli goofy deploy list-sites

# 搜索
## 根据项目名搜索项目
bytedcli goofy deploy project search --mode by-name --query tiktok
## 根据 SCM 名称搜索项目
bytedcli goofy deploy project search --mode by-scm --query toutiao
## 根据 Git 仓库搜索项目
bytedcli goofy deploy project search --mode by-git --query toutiao
## 根据路由搜索项目
bytedcli goofy deploy project search --mode by-route --query deploy.bytedance.net

# 团队
## 列出当前账号可见团队
bytedcli goofy deploy team list
## 获取团队信息
bytedcli goofy deploy get-team --team-id 4317
# 列出团队下的项目
bytedcli goofy deploy project list --team-id 4317
# 按 FaaS PSM 查项目
bytedcli goofy deploy project list --psm example.demo.node
# 创建 Web / Node App
bytedcli goofy deploy project create --team-id 4317 --english-name demo_app --name demo --app-type web --scm-name example/demo --framework web-default --artifact-source scm
bytedcli goofy deploy project create --team-id 4317 --english-name demo_node --name demo-node --app-type node --scm-name example/demo --framework node-default --psm example.demo.node

# 项目
## 查询项目信息
bytedcli goofy deploy get-project --app-id 131716
## 列出部署历史
bytedcli goofy deploy list-deployments --app-id 131716

# 部署区域
## 列出项目的部署区域
bytedcli goofy deploy region list --app-id 131716
## 创建 Region
bytedcli goofy deploy region create --app-id 131716 --region-name China-North --app-type web --deploy-config-source config-file --deploy-service csr --config-file deploy/sg.yml --domain-prefix demo-preview
bytedcli goofy deploy region create --app-id 131716 --region-name China-North --app-type node --deploy-config-source direct --runtime nodejs22
## 补 Region 域名
bytedcli goofy deploy region update --region-id 224335 --app-type web --domain-prefix demo-preview

# 确认预览请求体后执行；不传 --yes 只预览
bytedcli goofy deploy region update --region-id 224335 --app-type web --domain-prefix demo-preview --yes
## 通过标准 VRegion 查询对应部署区域的枚举值 （例如：Singapore-Central -> 3001）
bytedcli goofy deploy region-name-to-region --region-name Singapore-Central
## 通过部署区域的枚举值查询对应的标准 VRegion （例如：3001 -> Singapore-Central）
bytedcli goofy deploy region-to-region-name --region 3001

# 流量频道 / Channel
## 创建流量频道 Channel（需要 region-id），按 env-name 匹配小流量
bytedcli goofy deploy channel create --region-id 224335 --name test2 --env-name ppe_test2 --site cn
## 创建流量频道 Channel（按请求 header 匹配小流量；--header-key 与 --header-value 必须成对传入，--header-op 默认 1 = equals；此模式不需要 --env-name）
bytedcli goofy deploy channel create --region-id 224335 --name demo-header --header-key fe-env --header-value ppe_demo_header
## 创建按 URL query 命中的流量频道 Channel（不要同时传 --env-name；--query-op 支持 equals、includes、regex，默认 equals）
bytedcli goofy deploy channel create --region-id 224335 --name demo-query --query-key x-tt-env --query-value ppe_demo_query
## 删除非主频道：默认只预览，必须显式 --yes；主频道始终拒绝删除
bytedcli goofy deploy channel delete --channel-id <channel_id>
bytedcli goofy deploy channel delete --channel-id <channel_id> --yes
## 首次部署前合并 Web BFF 或 Node 运行时环境变量；命令自动识别频道类型；敏感值优先使用 KEY=VALUE 文件，默认 dry-run，确认后加 --yes
bytedcli goofy deploy channel update-bff-env --channel-id <channel_id> --bff-env-file <path_to_env_file>
bytedcli goofy deploy channel update-bff-env --channel-id <channel_id> --bff-env-file <path_to_env_file> --yes
## 调整部署单元内流量频道的优先级；--channel-ids 为逗号分隔的有序列表，顺序即优先级从高到低，应包含该部署单元内除「全流量」基线外的全部频道（与控制台行为一致）；默认 dry-run，确认后加 --yes
bytedcli goofy deploy channel update-priority --channel-ids <channel_id_1>,<channel_id_2>
bytedcli goofy deploy channel update-priority --channel-ids <channel_id_1>,<channel_id_2> --yes
## 通过项目 ID列出项目的流量频道 / Channel
bytedcli goofy deploy channel list --app-id 131716
## 按 PPE 环境名或 channel 名称模糊过滤 Channel
bytedcli goofy deploy channel list --app-id <app_id> --env-name <env_name>
bytedcli goofy deploy channel list --app-id <app_id> --keyword <name_substring>
## 按部署单元（region）过滤 Channel（对当前页结果过滤）
bytedcli goofy deploy channel list --app-id <app_id> --region-id <region_id>


# 部署工单
## 获取部署工单列表（--app-id 与 --channel-id 二选一；推荐只传 --channel-id）
bytedcli --site cn goofy deploy list-deployments --app-id 21297
bytedcli --site cn goofy deploy list-deployments --channel-id 3520795
## 同时传 --app-id 与 --channel-id（channel-id 优先，app-id 被忽略并在文本输出有 note）
bytedcli --site cn goofy deploy list-deployments --app-id 21297 --channel-id 3520795
## 获取具体工单的信息 （需要 deploy-id)
bytedcli --site cn goofy deploy get-deployment --deploy-id 24913395
## 创建部署工单
### 通过 Git 分支和 Commit Hash 部署新版本（需要 channel-id + git-branch + commit）
bytedcli goofy deploy deploy-new --channel-id 3520795 --git-branch main --commit-hash abc123def
### 通过 Git 分支和 Commit 部署并等待完成（--wait / --wait-timeout-sec / --poll-interval-sec）
bytedcli goofy deploy deploy-new --channel-id 3520795 --git-branch main --commit-hash abc123def --wait --wait-timeout-sec 900 --poll-interval-sec 15
### 通过已有 SCM 版本部署新版本（需要 channel-id + scm-version）
bytedcli goofy deploy deploy-version --channel-id 3520795 --scm-version 1.0.0.47
### 通过已有 SCM 版本部署并等待完成
bytedcli goofy deploy deploy-version --channel-id 3520795 --scm-version 1.0.0.47 --wait
### US-TTP 部署必须同时指定审核人类型和候选项 username
bytedcli --site us-ttp goofy deploy deploy-version --channel-id sample-channel --scm-version 1.0.0.47 --reviewer-type organization --reviewer sample-reviewer
### 发布 Vmok 生产者：--version 或 --git-branch + --commit-hash 二选一
bytedcli goofy deploy publish --channel-id sample-channel --version 1.0.0.47 --tag preview
bytedcli goofy deploy publish --channel-id sample-channel --git-branch main --commit-hash abc123def --tag preview --wait --wait-timeout-sec 900 --poll-interval-sec 15
### 部署 Vmok 消费者并按 Tag 引入直接依赖；多个依赖重复传 --vmok-remote
bytedcli goofy deploy deploy-version --channel-id sample-consumer-channel --scm-version 1.0.0.47 --vmok-remote '@example/module-a=preview'
bytedcli goofy deploy deploy-new --channel-id sample-consumer-channel --git-branch main --commit-hash abc123def --vmok-remote '@example/module-a=preview' --vmok-remote '@example/module-b=stable' --wait
### 通过 TAR 产物快速部署(quick TAR deployment,仅 Web 应用;自动识别 dist/build/out,不会生成 deploy.yml;也可直接传 .tar.gz)
bytedcli goofy deploy deploy-tar --channel-id 3520795 ./dist --wait

## 取消部署工单（需要 deploy-id）
bytedcli --site cn goofy deploy cancel --deploy-id 24913396
## 重试失败的部署（参数同原工单），可选 --wait
bytedcli --site cn goofy deploy retry --deploy-id 24913396 --wait
## 回滚部署工单，回滚到此 Channel 上一次成功的部署（需要 channel-id），可选 --wait
bytedcli --site cn goofy deploy rollback --channel-id 4682611 --wait

# 诊断
## 诊断部署失败原因（聚合部署详情、项目信息和历史部署，输出诊断建议）
bytedcli --site cn goofy deploy diagnose --deploy-id 24913395
## 同时拉取并展示对应 pipeline 节点日志（最后 300 行，自动剥离 trace envelope 并展开多行栈）
bytedcli --site cn goofy deploy diagnose --deploy-id 24913395 --show-deployment-log

# DevServer 实时预览（relay）：Agent 推荐先显式 setup，再后台启动
# --env-name 必填；可传逻辑名，bytedcli 根据目标 Region 解析为 ppe_ / boe_ 前缀
# 首次创建会等待路由配置 Deployment 完成；默认最多 600 秒、每 10 秒轮询
# --json 模式在 stderr 输出 goofy_relay_setup_progress JSONL，最终结果仍在 stdout
bytedcli --json goofy relay setup --app-id 131716 --region China-North --env-name demo_feature
bytedcli --json goofy relay start --channel-id <channel_id> --target http://localhost:5173 --detach --preflight
bytedcli --json goofy relay status --channel-id <channel_id>
bytedcli goofy relay logs --channel-id <channel_id> --tail 100
bytedcli --json goofy relay stop --channel-id <channel_id>

# 本仓维护者：针对仓库内固定测试项目运行真实 CN + BOE Relay E2E
# 会创建并删除真实 DevServer Channel，不属于 npm test 或 CI
# 从 bytedcli 仓库根目录运行；默认先 npm run build:code；需已有 CN 登录态，并允许写 bytedcli 用户数据目录
integration/goofy/run-e2e.sh

# 跨 Region 克隆部署与 Region(bulk deploy):走 Goofy Deploy 平台提供的批量部署流程;
# 需要时向 Goofy Deploy 平台团队获取最新操作指引,本命令面暂未内置该能力。
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json goofy deploy list-sites`）
- Goofy Deploy 站点选择用 `--site`（`cn|boe|i18n|i18n-tt|us-ttp|eu-ttp`），默认 `cn`
- `us-ttp` 请求走 `cloud.tiktok-us.net`，JWT 获取走 `cloud-ttp-us.bytedance.net`
- `us-ttp` 的 `deploy-new`、`deploy-version`、`deploy-tar`、`publish`、`retry` 必须同时传 `--reviewer-type` 与 `--reviewer`；类型使用 `person`、`organization`、`custom-group`，分别对应 USTS 个人、NOC 组、USTS 组，`--reviewer` 传该类型候选项的 username
- 主入口：`goofy deploy *` / `goofy preview *`
- VMOK 生产者入口：`goofy deploy publish`；Tag 不存在时随发布创建，已存在时移动；消费者版本保持不变
- VMOK 消费者：在 `goofy deploy deploy-new` 或 `deploy-version` 上重复传 `--vmok-remote <module=tag>` 指定直接依赖；该参数不发布消费者自身的 VMOK 模块
- 可用别名：`goofy-deploy *`、`gd *`
- `goofy preview *` 只有一个环境，无需区分 `cn` / `boe`
- `goofy preview *` 支持自动识别多种目录结构（`deploy.yml` / Next.js / 静态站点 / 自动检测 `dist`/`build`/`out`），详见 `references/preview-directory.md`
- 创建 channel 需要 region-id：先用 `region list --app-id <app_id>` 获取 Region ID
- 版本部署流程：先获取 channel-id，再使用 `deploy-new` 或 `deploy-version`
- `diagnose` / `get-deployment` / `cancel` / `retry` 除了 `--deploy-id <id>`，也接受直接粘贴 Goofy Web 页 URL（会自动从 URL 中提取 deployment id）

## Deployment Workflow

### Quick Preview / 快速预览部署

#### 工作流

1. 本地完成构建（如 `npm run build`）
2. 部署构建产物或项目根目录：
   - `goofy preview deploy . --alias <alias>`（项目根目录，自动检测构建产物）
   - `goofy preview deploy dist --alias <alias> --override`（指定构建产物目录）
   - `goofy preview deploy .next --alias <alias>`（Next.js 静态导出）
3. 查看 / 删除 preview：
   - `goofy preview list`
   - `goofy preview remove --preview-id <id>`（或 `--alias <alias>`）

#### 支持的目录类型（按识别优先级）

- **带 `deploy.yml` 的项目**：符合 Goofy 部署配置协议，直接按配置部署
- **Next.js 静态导出**：含 `.next/` 目录，自动整理 HTML 与静态资源
- **纯静态站点**：根目录含 `index.html`，自动生成 `deploy.yml` 以 worker 模式部署
- **项目根目录**：含 `package.json` / `src` 等源码标记，自动在 `dist/` / `build/` / `out/` 中查找构建产物

#### 限制与注意事项

- tarball 不超过 50 MB；alias 限字母、数字、连字符（不能以 `-` 开头）
- 默认过期 365 天，可通过 `--expiry-days` 调整

> 完整目录结构、示例与错误排查见 `references/preview-directory.md`。

### Normal Project Deploy / 普通项目部署

1. 获取项目 ID（已知或通过 `project search`、`project list` 查询）
2. 列出区域：`region list --app-id <app_id>`
3. 按需创建通道，并且只选择一种规则：环境名、请求 Header 或 URL Query。环境名模式使用 `--env-name <env_name>`；URL Query 模式使用 `--query-key <key> --query-value <value> [--query-op equals|includes|regex]`，不要同时传 `--env-name`，否则 Goofy 可能按 PPE 规则解析并丢弃显式 Query 条件。
4. 列出通道并选择通道 ID：`channel list --app-id <app_id>`
5. 如需为 Web BFF 或 Node 应用注入隔离配置，在首次部署前执行 `channel update-bff-env --channel-id <id> --bff-env-file <path>` 预览，再加 `--yes` 写入。命令根据频道配置自动选择 Web BFF 或 Node 请求体。文件每行一个 `KEY=VALUE`，敏感内容应设为 `0600` 权限并在使用后删除；非敏感值也可通过可重复的 `--bff-env KEY=VALUE` 传入，两种输入方式不可同时使用。命令采用 merge/upsert 语义，保留未指定的已有变量，并在写入后读回验证完整目标集合；输出包含 `appType`（`web` 或 `node`），不包含变量值。
6. 部署：
   - 通过 Git 分支和 Commit Hash 部署新版本（需要 branch + commit）：`deploy-new --channel-id <id> --git-branch <branch> --commit-hash <hash>`
   - 通过已有 SCM 版本部署新版本：`deploy-version --channel-id <id> --scm-version <version>`

## References

- `references/goofy-deploy.md`
- `references/preview-directory.md` — Goofy Preview 支持的目录结构与项目类型
