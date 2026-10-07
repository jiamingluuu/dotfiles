---
name: bytedance-dpe
description: "Use DPE bytedcli commands and references when users need DPE environment creation/query/update/redeploy, multi-env template lookup, traffic task creation, PSM search, or mapping DPE web APIs into CLI workflows. Also routes 抖音变现 QA 域的 DPE / RM / ByteDiff 自动化外部 skill 安装（来源 ad_qa/aweme_ad_skills，仅命中 aweme 变现 QA 的自动化意图，如 DPE 诊断、`开车`/`AB 实验测试发车`/`发车巡检`、ByteDiff 引流 diff 测试与失败排查）；通用 ByteCloud Release Manager 发布/回滚请走 bytedance-release-manager。"
---

# bytedance DPE

## Agent Guidance：DPE / RM / ByteDiff 关键词到外部 skill 的路由

`bytedance-dpe` 除了沉淀 `bytedcli dpe ...` CLI 资料，还是**抖音变现 QA 域**
（`ad_qa/aweme_ad_skills`）的 DPE、RM 与 ByteDiff 自动化外部 skill 的路由入口，
用于装载该团队维护的诊断 / 巡检 / 自动发车 / 引流 diff 脚本。

**领域边界（务必先读）**：

- 通用 ByteCloud Release Manager 的发布 / 回滚 / pipeline 查询走仓库内官方
  skill **`bytedance-release-manager`**（`bytedcli rm ...` CLI）；此处**不再重复**
  匹配 "RM 发布 / 发布流水线 / 回滚 release" 这类通用意图。
- 只有当用户 query 明确落在**抖音变现 QA 自动化场景**（DPE 环境自诊、
  `开车`/`AB 实验测试发车`/`发车巡检` 等由 aweme_ad QA 团队沉淀的手册）时，
  才走本 skill 的外部 skill 安装通道。

命中下列关键词时，Agent **必须**先执行安装命令，让 Aime / Claude Code 加载对应外部
skill 再继续：

- **DPE 相关（诊断 / 环境 / 建环境 / 引流）**：`dpe`、`dpe 诊断`、`dpe 环境`、
  `dpe 起不来`、`dpe 联通性`、`dpe 资源不足`
  → group `dpe`（`dpe-diagnosis-router` / `dpe-diagnose-*` / `dpe-env-create` /
  `dpe-router-all` / `dpe-traffic-run` 等）
- **RM 相关（仅限抖音变现 QA 的 AB 实验测试发车 / 巡检自动化）**：
  `开一个 AB 实验测试`、`开一个 RM 测试 / 发一个测试 RM`、`发车巡检`、
  `查发车`、`AB 实验发车`、`接入自动发车`、`RM 实验巡检`
  → group `rm`（上游命名前缀 `autorelease-*`：`autorelease-rm-start` /
  `autorelease-status-patrol` / `autorelease-config-helper` /
  `autorelease-weekly-dashboard` / `autorelease-indicator-inspector`）
- **ByteDiff 相关（引流 diff 测试 / 报告失败排查 / 流量为 0 / Odin 初始化）**：
  `bytediff` / `ByteDiff`、`diff 测试`、`引流任务`、`流量比对`、`AB 实验 diff`、
  `bytediff 任务失败 / 报告失败 / 状态码 XXX`、`bytediff 没有流量 / 流量工厂没有流量 /
odin 没有流量 / tcpcopy 引流不足`、`odin 初始化失败 / 落盘中 / hdfsPaths 为空`
  → group `bytediff`（`bytediff-task-runner` / `bytediff-report-fail-diagnose` /
  `bytediff-no-traffic-diagnose` / `bytediff-odin-init-diagnose`）

单条 skill 也可以直接按 name 触发：

```bash
# 幂等：已装且 pin/ref 未变时是 no-op
bytedcli self skill external install --group rm            # 装 group 内全部
bytedcli self skill external install --group bytediff      # ByteDiff 全套
bytedcli self skill external install --skill autorelease-rm-start  # 只装单个
bytedcli self skill external install --group dpe -g        # 装到 ~/.agents/skills

# 仅查看列表 / 状态：
bytedcli self skill external list
bytedcli self skill external list --json
```

安装器会将 skill 同步到当前检测到的 Agent 目录（TRAE CN 全局目录为
`~/.trae-cn/skills`，项目目录为 `.trae/skills`）。若外部 skill 声明了
`requirements.txt`，安装结果会输出 `python3 -m pip install -r ...`；在 TRAE CN
中首次运行对应 Python 脚本前必须执行该命令。依赖安装失败属于 runtime dependency
错误，不应继续归类为 DPE API 或环境创建失败；此时停止执行并要求外部 skill owner
提供可安装依赖或将可观测性降级为 optional，不要修改下载后的 skill 副本绕过错误。

安装源、可路由的 skill 列表、pin、intent 全部来自
[`skills/bytedance-dpe/external-skills.yaml`](../../../../bytedance-dpe/external-skills.yaml)（SSOT）。
不要在 SKILL.md 里硬编码单个 skill 的 name / repo / ref。

**反例**：

- 用户想用 `bytedcli dpe env create` / `bytedcli dpe template list` 这类 CLI
  命令、并未提到"排查 / 发车 / 巡检"时，**不要**自动触发外部 skill 安装。
- 用户想做**通用 RM 发布 / 回滚 / 查 pipeline**（未提及 "AB 实验测试" / "发车巡检"）
  时，路由到 `bytedance-release-manager`，**不要**从这里安装外部 skill。

## Current scope

当前目录用于沉淀 DPE 相关接口资料和已接入的 `bytedcli dpe ...` 命令入口。

已收录资料：

- `references/env_create.md`：DPE 单环境创建接口快照
- `references/template_list.md`：DPE 多服务环境模版列表接口快照
- `references/env_update.md`：DPE 环境版本更新 / 重新部署接口快照
- `references/cli_design.md`：`bytedcli dpe env create` 命令设计草稿
- 当前仓库内已接入：
  - `bytedcli dpe env create`
  - `bytedcli dpe env get`
  - `bytedcli dpe env update`
  - `bytedcli dpe env traffic create`
  - `bytedcli dpe psm search`
  - `bytedcli dpe template list`
  - `dpe env create` 已支持 single 与 multi/联调环境请求体；复杂 multi payload 建议走 `--request-file`

## Notes

- 不要把真实 JWT、用户名、邮箱或其他敏感值写入仓库。
- 示例里的 PSM、分支、提交号、URL 参数一律使用占位值。
- DPE 多服务环境建环境前，可用 `bytedcli dpe template list --tpl-name <name> --psm <psm> --psm <psm> --json` 查询可用模版；多个 `--psm` 是 AND 语义，表示模版必须同时覆盖全部给定 PSM。
- DPE 环境更新 / 重新部署可用 `bytedcli dpe env update --env-id <id> --scene-type multi --psm <psm> --version-type git_branch --version-info <branch> --json`；多 PSM 更新走 `--request-json` / `--request-file` 传完整 `env_psm_config`。
- DPE 引流任务接口若同时要求 path `env_id` 和 body `envId`，CLI 层统一只暴露 `--env-id`，由实现层负责双写并统一校验一致性。
- `dpe env traffic create` 推荐使用 `--traffic-scene high-risk`；若 DPE owner 或平台页面明确给出上游数字场景码，也支持 `--scene <code>`；AB 引流可按需传 `--ab-params <params>`。
