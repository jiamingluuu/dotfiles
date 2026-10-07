---
name: bytedance-tt-dts
description: TT-DTS(DES-MQ) 跨机房数据同步的统一入口：查询同步通道与运行状态、排查同步延迟/断流、告警自助、带双重确认的通道启停与位点重置、存储同步边巡检、同步拓扑规划、概念与接入咨询。当用户提到 DES-MQ、TT-DTS、ByteDTS、数据同步、同步延迟、同步通道、跨区/跨 VGeo 同步时使用。命令面为 `bytedcli tt-dts <子命令>`，首次使用自动准备运行时。
---

# TT-DTS / DES-MQ 数据同步

所有操作统一走 `bytedcli tt-dts <子命令>`。

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli tt-dts <subcommand> [options]
```

## 首次使用（自动准备，无需手动步骤）

首次执行任意 `bytedcli tt-dts` 命令时，运行时会自动准备（独立环境，不改动全局
Python 环境；需要本机 Python ≥3.9，macOS 自带的 python3 即满足）。

- 自动准备失败时（如无 Python）会报错并给出修复提示，按提示处理后重试原命令即可。
- 升级：`bytedcli tt-dts self upgrade`（日常命令也会自动提示新版本）。

可选增强：`bytedcli tt-dts skills install --force` 会把随包分发的完整版 tt-dts skill
（含排障工作流与参考文档）铺到 `~/.claude/skills` 等 agent 目录；在 bytedcli 内使用不是必需。

## When to use

- 同步通道查询：按 owner/源/目标检索通道、查看通道详情与运行状态
- 同步延迟/断流排查：延迟诊断、追平时间预估
- 通道运维：启动、停止、位点重置、owner 变更（写操作须先把预览复述给用户、获明确同意再执行，见「写操作红线」）
- 存储同步边巡检、同步拓扑规划、告警自助
- TT-DTS / DES-MQ / ByteDTS 概念与接入咨询

## Quick start

命令按 `channel` / `diagnose` / `edge` / `topology` / `audit` / `alarm` 分组。

```bash
# 通道列表（按 owner 过滤）
bytedcli tt-dts channel list --owner example.username

# 通道详情与运行状态
bytedcli tt-dts channel detail 1234567890
bytedcli tt-dts channel status 1234567890

# 同步延迟诊断 / 追平预估
bytedcli tt-dts diagnose delay 1234567890
bytedcli tt-dts diagnose eta 1234567890

# 写操作（必须先把预览复述给用户、获同意后再带 token 执行；见「写操作红线」）
bytedcli tt-dts channel start 1234567890
bytedcli tt-dts channel stop 1234567890

# 完整命令树
bytedcli tt-dts --help
```

agent 场景查询类命令普遍支持 `--json` 输出。

## 写操作红线（不可跳过）

- **必须把 CLI 打印的变更预览完整复述给用户**（改什么、从什么值改成什么值、风险提示），
  获得**明确同意**后再执行。两阶段 confirm token 只保证「预览生成过、且目标状态未变」，
  **不代表人看过**——它挡不住 agent 自己两步自证。人在环由你负责：不得跳过复述直接拼
  `--yes --token`，执行后按 CLI 的复查结果（`✓ 复查已生效` / 退出码 3）如实回报。
- **接口白名单纪律**：只调用 `bytedcli tt-dts` 已封装的子命令；**绝不**因为「看起来只读」
  就去 curl 或直连未核过的 Console 原始接口（实测存在 GET 即建群、GET 带写副作用的接口），
  也不要给用户提供这类「顺手查一下」的原始接口调用。

## 使用边界

- 查询失败（含自动安装失败）时不要臆造结果：把报错和给出的安装/修复指引如实转述给用户。
- 权限由 DES-MQ Console 后端按 owner 判定。
- 认证自动取票（已注入的分区票据 `TT_DTS_JWT_<区>`/`GDPA_JWT_<区>` → gdpa 共享登录态 → bytedcli → gdpa-cli → `TT_DTS_JWT` 环境变量 → 本地票据文件），通常无需手工传 `--jwt`；跨合规区的腿走同一条链但不自动登录，缺票即刻降级并提示补票。