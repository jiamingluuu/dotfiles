# bytedcli 通用调用方式

## 执行

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli --help
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

- 默认使用全局安装的 `bytedcli ...`，不要把 `npx -y @bytedance-dev/bytedcli@latest` 写进自动化或日常调用。
- 仅当目标环境完全无法 `npm install -g`（如临时容器、无写权限的 CI）时，才把示例里的 `bytedcli` 替换为 `NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest`。

## 站点切换

通过全局参数 `--site` 或环境变量 `BYTEDCLI_CLOUD_SITE` 切换 ByteCloud 站点：

| 站点值 | 说明 | SSO | 备注 |
|--------|------|-----|------|
| `cn` | 国内生产（默认） | `sso.bytedance.com` | |
| `i18n-bd` | ByteIntl 国际站 | `sso.bytedance.com` | 通常复用 cn 登录态 |
| `i18n-tt` | TikTok 国际站 | `sso.tiktok-intl.com` | 需单独登录 |
| `eu-ttp` | EU TTP 站 | `sso.tiktok-intl.com` | 需单独登录 |
| `us-ttp` | US TTP 站 | `sso.tiktok-intl.com` | 需单独登录 |
| `us-ttp-bdee` | US TTP（BDEE）站 | `sso.tiktok-intl.com` | 需单独登录 |
| `boe` | BOE 测试 | `test-sso.bytedance.net` | |
| `sandbox`（仅 FaaS） | BOE sandbox 测试 | `test-sso.bytedance.net` | FaaS 直连 sandbox 控制面，JWT 复用 BOE 凭据 |

> `--site i18n-bd` 是 ByteIntl 国际站的规范站点值（`i18n` 也可用作别名）。

**认证隔离按 SSO 环境生效。`i18n-tt`、`eu-ttp`、`us-ttp`、`us-ttp-bdee`（TikTok SSO）需单独 `auth login`；`cn`、`i18n-bd`（ByteDance SSO）通常共享登录态。**

FaaS 场景中，用户提到“BOE sandbox”“FaaS sandbox 测试环境”或 `faas-sandbox.byted.org` 时，使用 `--site sandbox`。这是仅由 `faas` 命令识别的上下文选项：非 FaaS 命令会拒绝该值，也不要设置 `BYTEDCLI_CLOUD_SITE=sandbox`。FaaS 请求会直连 `https://faas-sandbox.byted.org/v2` 并自动复用 BOE JWT；普通 `--site boe` 不会切到 sandbox 控制面。

```bash
# 检查 i18n-tt 站点认证
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth status

# 登录 i18n-tt 站点
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth login
```

## JSON 输出

```bash
bytedcli --json <command> [options]
```

注意：`--json` 是全局参数，必须放在 `<command>` 前面，例如 `--json auth status`，不能写成 `auth status --json`。

## 常用全局参数

- `-j, --json`
- `-d, --debug`
- `--site <site>`
- `--socks5-proxy <url>`
- `--http-proxy <url>`
- `--tls1.2`
- `--http-timeout-ms`
- `--http-retry-count`
- `--http-retry-base-delay-ms`
- `--http-retry-max-delay-ms`
- `--http-debug`
- `--http-print <parts>`
- `--http-trace-file <path>`
- `--http-body-limit <bytes>`
- `--no-auto-upgrade`

HTTP trace 示例：

```bash
bytedcli --http-debug <command> [options]
bytedcli --http-print HBhbmt <command> [options]
bytedcli --http-trace-file /tmp/bytedcli.http.log --http-body-limit 4096 <command> [options]
```

`--http-print <parts>` 的 flag 含义：

- `H`: request headers
- `B`: request body
- `h`: response headers
- `b`: response body
- `m`: meta
- `t`: time

## 自动升级与技能同步

全局安装的 bytedcli 会在普通命令执行时通过 auto-upgrade 自动检查 CLI 和已安装技能版本；auto-upgrade 不会在 `self` 子命令、源码 checkout 执行和 npx 临时执行时触发，因此这些流程不会自动修改全局安装；如需升级请显式执行 `bytedcli self update`。需要关闭自动升级时：

```bash
bytedcli --no-auto-upgrade <command> [options]
export BYTEDCLI_NO_AUTO_UPGRADE=1
```

手动管理随 bytedcli 打包的 agent skills：

```bash
bytedcli self skill list --installed
bytedcli self skill install -s bytedance-codebase -g
bytedcli self skill update -g
bytedcli self skill remove -s bytedance-codebase -g
```

不要只手动删除 `~/.agents/skills/<skill>`。如需避免后续升级重新同步某个技能，用 `bytedcli self skill remove -g -s <skill>` 删除目录并同步清理本地 lock 记录。
