---
name: bytedance-orthrus
description: "Skill for Orthrus 主机权限平台。Use when tasks mention Orthrus、host root permission、临时权限申请、owner_grant、给某机器开 root/tiger 权限、box.bytedance.net 主机权限申请."
---

# Orthrus 主机权限

## 如何调用

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

- 作为服务树 owner / orthrus_loginer，给主机下发 root、tiger 等临时权限
- 想把"每 24 小时手动点一次权限申请"换成可脚本化的命令（再配合 cronjob/launchd 续期）
- cn（内网）主机权限自助申请：直接复用 bytedcli 已有的 ByteCloud 登录态，无需扫码/贴 cookie

## 前置条件

- 你必须是目标主机在服务树上的 owner / orthrus_loginer，否则会返回失败（`intractable_hosts` / `not_owned_hosts` 非空）。
- 单次最大授权时长是 24 小时，由后端强制，无法绕过。要续期请配合 cron 自动重发。
- cn 站点用 bytedcli 的 ByteCloud 登录态（`bytedcli auth login`），无需 orthrus 专属 cookie。
- i18n / ttp 站点用 Orthrus `_cas_sssion` cookie 认证。

## 认证

### cn（推荐，零额外登录）

cn 主机权限申请由 ByteBox 的 Orthrus 网关（`box.bytedance.net`）承载，复用 bytedcli 的 **ByteCloud JWT** 鉴权。只要 `bytedcli auth status` 显示已登录（ByteCloud Auth），`owner-grant --site cn` 即可直接调用，无需 `--cookie`、无需扫码：

```bash
# 若尚未登录，先完成一次 ByteCloud 登录（设备码 / SSO）
bytedcli auth login
# 之后 cn 授权全程零交互
bytedcli orthrus owner-grant --site cn --host 'fdbd:demo::1' --role tiger --timeout 24
```

cn 是「自助授权」：授权对象就是当前登录用户本人，因此 **不需要 `--account`**。

### i18n / ttp（Orthrus cookie）

i18n / ttp 走 Orthrus 自己的 `_cas_sssion` cookie。i18n 支持一次性浏览器登录后自动续 session；ttp 目前需显式 `--cookie`：

```bash
# i18n：一次性浏览器扫码（TikTok SSO），之后自动续 session
bytedcli orthrus auth-login --site i18n

# 显式 cookie（i18n / ttp 通用）
bytedcli orthrus owner-grant --site i18n --account demo-user --host 10.0.0.1 --cookie '_cas_sssion=demo-token'
```

`auth-login`（i18n）会用 puppeteer 打开 Chrome 完成 TikTok SSO，捕获 `_cas_sssion`（~7 天）与 `bd_sso_*`（~14 天，用于免浏览器 CAS 续期）。

## 常用命令

```bash
# 查看帮助
bytedcli orthrus --help
bytedcli orthrus owner-grant --help
bytedcli orthrus auth-login --help

# cn：自助申请 tiger 权限（零登录，复用 ByteCloud JWT，不需要 --account）
bytedcli orthrus owner-grant --site cn --host 'fdbd:demo::1' --role tiger --timeout 24

# cn：批量主机（重复 --host 或逗号分隔）
bytedcli orthrus owner-grant --site cn --host 'fdbd:demo::1,fdbd:demo::2' --role root

# cn：机器可读输出（succeeded_hosts / intractable_hosts / owner_hosts）
bytedcli --json orthrus owner-grant --site cn --host 'fdbd:demo::1' --role tiger

# i18n：一次性浏览器扫码，之后 grant 不再需要 --cookie
bytedcli orthrus auth-login --site i18n
bytedcli orthrus owner-grant --site i18n --account demo-user-1,demo-user-2 --host 10.0.0.1 --role root --timeout 24

# i18n / ttp：显式传 cookie
bytedcli orthrus owner-grant --site i18n --account demo-user-1 --host 10.0.0.1 --cookie '_cas_sssion=demo-token'
bytedcli orthrus owner-grant --site ttp --account demo-user --host demo-host.example.net --cookie '_cas_sssion=demo-token'

# i18n：持久化 cookie 到本地，后续运行不再需要 --cookie
bytedcli orthrus owner-grant --site i18n --account demo-user-1 --host 10.0.0.1 --cookie '_cas_sssion=demo-token' --save-cookie

# i18n：脚本里禁用浏览器自动 fallback（cookie/缓存都没有时直接报错，不打开 Chrome）
bytedcli orthrus owner-grant --site i18n --account demo-user-1 --host 10.0.0.1 --no-interactive
```

## Sites

| --site | 入口 | 鉴权 |
| ------ | ---- | ---- |
| `cn`   | `https://box.bytedance.net`（ByteBox Orthrus 网关） | ByteCloud JWT（bytedcli 登录态） |
| `i18n` | `https://orthrus-i18n.tiktok-row.org` | `_cas_sssion` cookie（TikTok SSO） |
| `ttp`  | `https://orthrus-ttp.bytedance.net` | `_cas_sssion` cookie（显式传入） |

## 认证来源优先级

### cn

复用 bytedcli 的 ByteCloud 登录态（`bytedcli auth login` 建立的 JWT），无 cookie 概念；未登录时按 `bytedcli auth login` 提示先登录。

### i18n / ttp

1. `--cookie` flag
2. `BYTEDCLI_ORTHRUS_COOKIE_<SITE>` 环境变量（site 大写）
3. 已缓存的 session cookie `~/.local/share/bytedcli/data/orthrus_session.<site>.json`
4. 已缓存的 SSO cookies 走 CAS 自动续 session（i18n）
5. 打开浏览器扫码登录（i18n；默认开启，加 `--no-interactive` 可关闭）

## 常见错误

- `Add up to only a maximum of 24 hours` / `Invalid --timeout`：`--timeout` 超过 24，后端硬性限制。
- cn `intractable_hosts` 非空：调用方不是该机器的 owner / orthrus_loginer，或主机不存在。换 owner 发，或让 owner 把你加为 orthrus_loginer。
- i18n `not_owned_hosts` 非空：同上（cookie 链路的等价字段）。
- cn 报 ByteCloud 未登录 / JWT 相关错误：先跑 `bytedcli auth login`，确认 `bytedcli auth status` 已登录再重试。
- i18n `Orthrus login required. Run: bytedcli orthrus auth-login --site i18n`：没有可用 cookie/SSO，且被 `--no-interactive` 阻止开浏览器。按提示运行 `auth-login`。
- `puppeteer or puppeteer-core is required for browser login`（i18n，错误码 `PUPPETEER_NOT_FOUND`）：本机没有 puppeteer —— bytedcli 把它声明为 optional peer，不随安装拉取。临时方案：手动复制 cookie 配 `--cookie`；长期方案：`npm install -g puppeteer-core@24`（走系统 Chrome，不下载 Chromium）。

## Agent Guidance

- cn 主机权限申请**不需要**用户扫码或从浏览器复制 cookie：只要 bytedcli 已登录（`bytedcli auth status`），直接 `orthrus owner-grant --site cn --host <ip> --role <root|tiger>` 即可，全程零交互。cn 不接受 `--account`（自助授权给当前登录用户本人）。
- 要续期 24h 权限，搭配本地 cron / launchd 定时跑 `bytedcli orthrus owner-grant ...`；cron 频率建议 12h 一次或更密，避免 mac 睡眠错过窗口。
- 不要把真实 cookie / token 写进对外文档、commit、issue。示例里只写 `_cas_sssion=demo-token`、`fdbd:demo::1` 这类占位值。
- 如果用户只是登录排查问题、不做破坏性操作，建议 `--role tiger` 而不是 `root`。
