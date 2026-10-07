---
name: bytedance-tiktok-scheduler
description: "Operate the TikTok Scheduler platform via bytedcli: create/get/list/terminate one-time (onetime) schedules and create/update/pause/unpause/trigger/delete/get/list recurring (cron / interval) schedules, with RPC / HTTP / Workflow actions. One-time schedules support delayed / deferred execution (run once after a delay) via start delay. Also manage namespaces: create/get/delete a namespace, add owners or service permissions, and upsert per-region rate-limit keys. Use when tasks mention TikTok Scheduler, schedule tasks, scheduled/cron/timed jobs, one-time tasks, recurring tasks, delayed/deferred tasks, run-after-delay, namespace management, namespace owners/permissions, rate limit, or creating/managing schedules. 调度任务 / 定时任务 / cron 任务 / 一次性任务 / 周期任务 / 延迟任务 / 延时执行 / 延迟触发 / 命名空间管理 / namespace / 限流。"
---

# bytedcli TikTok Scheduler

通过 `bytedcli tiktok-scheduler` 操作 TikTok Scheduler 控制面 HTTP API。CLI 自身承载鉴权（ByteCloud JWT → `x-jwt-token`）、HTTP 调用与请求体组装；本 skill 指导你怎么用 shell 调用它。

## 平台是什么

TikTok Scheduler 是面向在线业务的可靠任务调度与异步执行平台，提供**延时执行**与**周期执行**能力：用户只描述「做什么」（RPC / HTTP / Workflow 动作）和「何时做」（延迟 / cron / interval），执行、状态追踪、重试与故障处理由平台托管，底层**不依赖 MQ**，可直接调已有 RPC / HTTP 接口。理解命令背后的语义（默认无限重试、异步执行、幂等创建、限流、Context 透传、多机房 VRegion、接入鉴权前置条件、SLA 等）前，先读 [references/platform.md](references/platform.md)。

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

- 报鉴权错误时先 `bytedcli auth login`
- 任何子命令参数不确定时，先看 `bytedcli tiktok-scheduler <group> <command> --help`，不要凭印象猜。

## 核心约定

- 命令级 `--namespace`（必填）：业务隔离单元。
- 命令级 `--region`（必填）：vregion，例如 `Singapore-Central / US-TTP / US-TTP2 / EU-TTP2 / US-EastRed / US-BOE`。可用性按 namespace 而定，CLI 不做硬校验。
- **onetime / recurring 没有单独的 env / `-e` 参数**：环境由 `--region` 决定，要连 BOE 就传含 `BOE` 的 region（如 `US-BOE`），其余 region 走线上。
- 一次性 vs 周期性 vs 命名空间管理：用顶层命令组区分 —— `onetime`、`recurring`、`namespace`。
- **`namespace` 组按 `--env prod|boe`（默认 prod）路由，不按 region**：命名空间以 ns 为键存在控制面、后端自行按部署区域扇出；只有 `namespace create` 用可重复的 `--region` 指定部署区域。
- **延迟任务（延迟/延时执行）= 一次性任务 + `--start-delay-ms`**：让任务在「现在 + N 毫秒」后只跑一次，就用 `onetime create --start-delay-ms <毫秒>`（如 30 分钟 = `1800000`）。不要为「延迟一次」去建 cron/周期任务。`--start-delay-ms 0`（默认）= 立即执行。
- Action 三类：`--action-type rpc|http|workflow`，每类用显式 flag 配置；不接受整段 action JSON/文件（workflow 的单个 task 除外，见 tiktok-scheduler.md 的「Action 入参」一节）。
- 结构化输出用全局 `-j, --json`（放在子命令之前）。

## 写操作二段确认（重要）

`create / update / pause / unpause / trigger / delete / terminate` 都是**写操作**。CLI 默认只打印 dry-run 预览（解析后的 env/method/path/body），**不发送**。

- 用户最初让你"建/删/暂停"任务**不等于**同意执行，那只是任务请求。
- 必须先跑 dry-run（不带 `-y`），把 env / region / namespace / schedule_id / method+path / body 摊给用户。
- 看到 dry-run 输出**之后**，等用户在 chat 里明确说"发 / 执行 / 确认 / go"，再补 `-y/--yes` 真正执行。
- 不允许用"用户已经说要建了 / dry-run 看着对"这类理由直接补 `-y`。

读操作（`get / list`）无需确认，可直接跑。

## 解读响应里的枚举 int（重要）

后端响应里的枚举字段（如 `schedule_type`、`action_type`、`status`、`overlap_policy` 等）返回的是 **int**（Thrift enum 序号），不是字符串。向用户解释 `get` / `list` 结果前，**先对照 [references/tiktok-scheduler.md](references/tiktok-scheduler.md) 的「枚举值对照」一节把 int 还原成含义**，不要凭印象猜（例如 `action_type: 2` = HTTP，`status: 3` = FAILED）。

## Route By Task

- 平台背景与能力语义（产品定位、任务动作、重试 / 异步 / 限流 / 幂等创建 / 任务治理 / Context 透传 / 多机房 VRegion / 接入前置条件 / SLA）→ [references/platform.md](references/platform.md)
- 命令参考（onetime / recurring 子命令、rpc·http·workflow action flag、响应枚举 int 对照）→ [references/tiktok-scheduler.md](references/tiktok-scheduler.md)
  - 一次性任务：创建（含**延迟/延时执行**）、查询（get / list）、终止执行（terminate）→「一次性任务（onetime）」一节
  - 周期性任务：创建、更新、暂停、恢复（unpause）、手动触发、删除、查询 →「周期性任务（recurring）」一节
  - `onetime list` / `recurring list` 的 `--query` 高级过滤（Temporal list-filter 语法、可用字段 key 对照、onetime/recurring 字段差异、示例）→「list --query 过滤语法」一节
  - 命名空间管理：创建 / 查询 / 删除、加 owner、给服务授权、设置限流（按 `--env` 路由）→「Namespace 管理（namespace）」一节
  - rpc·http·workflow action flag（create / update 共用）→「Action 入参」一节
  - 响应里枚举 int 字段（schedule_type / action_type / status / overlap_policy …）→「枚举值对照」一节
  - 用户要 namespace / schedule / 执行的**控制台详情页链接**（CLI 不返回，需手动拼）→「控制台详情页链接」一节
- 通用调用方式（npx / 全局安装、`--json`、http-debug、版本保鲜）→ [../../invocation.md](../../invocation.md)

## Quick start

```bash
# 一次性任务（onetime）
bytedcli tiktok-scheduler onetime create --namespace my-ns --region Singapore-Central \
  --action-type http --http-url https://my.svc/run        # dry-run 预览
# 延迟任务：30 分钟后只跑一次（1800000 ms）
bytedcli tiktok-scheduler onetime create --namespace my-ns --region Singapore-Central \
  --start-delay-ms 1800000 \
  --action-type rpc --rpc-psm my.psm --rpc-method S.M --rpc-data '{}'    # dry-run
bytedcli tiktok-scheduler onetime list --namespace my-ns --region Singapore-Central
bytedcli -j tiktok-scheduler onetime get --namespace my-ns --region Singapore-Central \
  --schedule-id once-1 --execution-id <eid>

# 周期性任务（recurring）
bytedcli tiktok-scheduler recurring create --namespace my-ns --region US-BOE \
  --schedule-id daily-2am --cron '0 0 2 * * * *' \
  --action-type rpc --rpc-psm my.psm --rpc-method S.M --rpc-data '{}'   # dry-run
bytedcli tiktok-scheduler recurring pause --namespace my-ns --region US-BOE --schedule-id daily-2am -y

# 命名空间管理（namespace，按 --env 路由）
bytedcli tiktok-scheduler namespace create --namespace my_ns \
  --region Singapore-Central --region US-TTP                  # dry-run 预览
bytedcli tiktok-scheduler namespace get --namespace my_ns       # 读操作
bytedcli tiktok-scheduler namespace add-owner --namespace my_ns --owner a@bytedance.com -y
```

## Stop Early

以下情况必须停下说明原因，不要继续猜：

- 第一次读操作（`get` / `list`）就失败（鉴权、namespace、region 等）
- 必要参数无法稳定确定：`namespace`、`region`、`schedule_id`，或 action 的关键字段（如 rpc 的 psm/method、http 的 url）
- 写操作还没跑 dry-run、还没把 body 摊给用户，或用户还没在看到 dry-run 后再确认一次
- 继续执行只会建立在猜测上

## References

- 平台背景与能力语义：[references/platform.md](references/platform.md)
- 命令参考（onetime / recurring / action flag / 枚举对照）：[references/tiktok-scheduler.md](references/tiktok-scheduler.md)
- 通用调用方式、env/region：[../../invocation.md](../../invocation.md)
