---
name: bytedance-sip
description: "Use bytedcli SIP/智能运维: sip event 查询时间窗口内线上稳定性/变更事件（LIBRA 实验、Demotion、TCE、Release）；sip release 智能发布平台：repo lock/unlock（代码库锁定/解锁/封禁，适用于 code-freeze 或故障排查期）与 cron pause/resume（发布调度定时任务暂停/恢复）。"
---

# bytedcli SIP

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

## SIP 是一个平台，下辖多个独立子平台（先选对子平台）

SIP（智能运维平台）不是单一功能，而是一个承载多个**技术栈完全不同**的子平台的平台。开始前必须先判断任务属于哪个子平台，**不要混用二者的命令、参数或认证方式**：

| 子平台 | 命令前缀 | 定位 | 后端接口 | 认证栈 |
| --- | --- | --- | --- | --- |
| **事件查询**（stability event） | `sip event ...` | 只读查询线上稳定性事件（LIBRA / Demotion / TCE / Release / recall_center） | `/api/v1/assistant/event/*` | 自签 JWT（`token:` header），支持 `BYTEDCLI_SIP_TOKEN` 覆盖 |
| **智能发布平台**（release） | `sip release ...` | 一整个发布管理子平台；当前已暴露的子功能是**代码库锁定 / 解锁**（`repo lock` / `repo unlock`）与**调度定时任务暂停 / 恢复**（`cron pause` / `cron resume`），后续会有更多发布相关子功能 | `/api/v1/assistant/release/*` | SSO CAS cookie（`/cas/login`，浏览器同源会话），**不吃** `BYTEDCLI_SIP_TOKEN` |

选择指引：

- 任务是"查/看/回溯某段时间发生了哪些变更、某个实验/降级/发布的记录" → 用 **`sip event`**。
- 任务属于发布管理（"代码封禁期 / 故障排查期锁住代码库不让合码、结束后解锁"，或"暂停 / 恢复发布调度的定时任务"）→ 用 **`sip release`**。`sip release` 是一个会持续扩子功能的子平台，`repo lock` / `repo unlock` 与 `cron pause` / `cron resume` 是它当前的两组子命令。
- 两者的鉴权链路不同：`sip event` 的 `BYTEDCLI_SIP_TOKEN` 对 `sip release` 无效；`sip release` 依赖当前 SSO 登录态换取 CAS 会话，无法用事件平台的 JWT 顶替。

> 详细参数、错误处理见 [sip.md](./references/sip.md)。

## When to use

- **`sip event`**：查询指定时间窗口内的 SIP stability events（LIBRA 实验变更、Demotion、TCE 变更、Release 等）；按 region / biz / category / 关键字过滤；根因分析、变更回溯。对应 UI：`https://sip.tiktok-row.net/stability/event`。
- **`sip release`（智能发布平台）**：发布管理子平台。当前子功能 = ①代码库锁定 / 解锁：在代码封禁期或故障排查期锁住 repo 的 master 分支（阻止新 MR）、期满解锁（放开）；②调度定时任务暂停 / 恢复：暂停 / 恢复发布调度的 cron 定时任务。

## Quick start

### 子平台一：事件查询 `sip event`

```bash
# 零交互，按 --site 自动选 SIP region
bytedcli --site i18n-tt sip event list --duration 1h
bytedcli --site cn sip event list --duration 1h --biz aweme
bytedcli --site i18n-tt sip event list --duration 1h --biz tiktok_live

# 最近 24 小时 Demotion 事件（--filter 覆盖 --biz 自动推导的默认）
bytedcli --site i18n-tt sip event list --duration 24h \
  --filter '{"holmes_demotion":{"status":["启用","执行","结束"]}}'

# 按绝对时间窗口 + 指定 region
bytedcli --site i18n-tt sip event list \
  --start 2026-04-14T22:00:00+08:00 \
  --end   2026-04-14T23:00:00+08:00 \
  --region us-ttp --region sg

# 按 category 做客户端过滤（大小写不敏感子串）
bytedcli --site i18n-tt sip event list --duration 6h --category libra

# JSON 输出（agent / 脚本消费）
bytedcli --json --site i18n-tt sip event list --duration 1h --page-size 20

# 查询单个事件详情
bytedcli --site i18n-tt sip event get --id 7628873892584488977
```

### 子平台二：智能发布平台 `sip release`（子功能：代码库锁定 / 解锁 + 调度定时任务暂停 / 恢复）

```bash
# 代码库锁定：代码封禁期 / 故障排查期禁止新的 MR 合入 master
# --release-site 默认 TTP，建议每次都显式写出
bytedcli --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP --reason "code freeze"

# 定向锁定：仍允许指定用户合码
bytedcli --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP --allow-users demo-user1,demo-user2

# 解锁：封禁 / 排查结束后放开合码
bytedcli --site i18n-tt sip release repo unlock --psm-id 17 --release-site TTP

# 暂停 / 恢复调度定时任务（--psm 仅用于鉴权，--job-id 定位任务）
bytedcli --site i18n-tt sip release cron pause --job-id 12345 --psm demo.recommend.predict_cpp
bytedcli --site i18n-tt sip release cron resume --job-id 12345 --psm demo.recommend.predict_cpp

# JSON 输出
bytedcli --json --site i18n-tt sip release repo lock --psm-id 17 --release-site TTP
```

## Authentication

两个子平台认证栈不同，切勿混用：

- **`sip event`**：默认零交互，bytedcli 自动用当前 SSO 身份换取事件平台的自签 JWT（`token:` header）。CI / agent 场景可用 `BYTEDCLI_SIP_TOKEN` 传入已准备好的 token 跳过自动签发。认证按 SSO 环境隔离，首次使用某个 site 前先确认登录态，仅当顶层 `authenticated` 为 `false` 时才 login（别重复扫码；以顶层 `authenticated` 为准，不要 grep 嵌套 `bytecloud_auth_sdk.status` 的 `need_login`）：`BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json auth status`，需要时再 `BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login`。

  ```bash
  export BYTEDCLI_SIP_TOKEN='eyJhbGci...'
  bytedcli --site i18n-tt sip event list --duration 1h
  ```

- **`sip release`（智能发布平台）**：走 SSO CAS 同源会话（经 `/cas/login?next=%2F` 换取 host session cookie），**依赖 SSO 浏览器会话登录态**。必须用 **session 登录**建立该会话：

  ```bash
  # 建立 / 刷新 SSO 会话（release 子平台必需，--site 决定 SSO env：row→tiktok，cn/sg→bytedance）
  bytedcli --site i18n-tt auth login --session
  ```

  - ⚠️ **普通 `bytedcli auth login`（不带 `--session`）走的是 ByteCloud Auth device_code 流程，只写 ByteCloud Auth 凭据，不会生成 CAS 所需的 SSO cookie jar**，因此对 `sip release` 无效。
  - **`BYTEDCLI_SIP_TOKEN` 对 `sip release` 无效**（它只用于事件平台自签 JWT）。
  - 401 时：先 `bytedcli auth status` 确认，再 `bytedcli --site <site> auth login --session` 重新登录（不要用普通 `auth login`，也不要用 `BYTEDCLI_SIP_TOKEN`）。
  - Agent / 非阻塞场景可拆成 begin + complete 两步：

    ```bash
    bytedcli --json --site i18n-tt auth login --begin --session
    # scan/approve, then:
    bytedcli --json auth login --complete <token>
    ```

## Notes

`sip event` 的时间窗口、region/vdc、biz/filter、category、分页、mode、字段展平等细节，以及 `sip release`（智能发布平台）当前子功能 `repo lock` / `repo unlock` 的 `--psm-id / --release-type / --release-site / --allow-users` 参数、`cron pause` / `cron resume` 的 `--job-id / --psm` 参数，与"外层网关 code:0 但内层业务失败"的坑，统一见 [sip.md](./references/sip.md)。SIP region（API host）按 `--site` 解析：`cn / boe → sip.bytedance.net`、`i18n / i18n-bd → sip-sg.byteintl.net`、其他站点 → `sip.tiktok-row.net`；可用 `BYTEDCLI_SIP_REGION=cn|sg|row` 或 `BYTEDCLI_SIP_BASE_URL=https://...` 覆盖（两个子平台共用同一 region 解析）。注意 bytedcli 全局默认站点是 `--site cn`，所以不带 `--site` 命中的是 CN region，`sip.tiktok-row.net` 只是非 cn/i18n-bd 站点的兜底而非 CLI 默认——访问 TikTok ROW 必须显式 `--site i18n-tt`。`sip release` 的 SSO env 也按 region 分派：`row → tiktok`，`cn / sg → bytedance`。

## References

- [sip.md](./references/sip.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
