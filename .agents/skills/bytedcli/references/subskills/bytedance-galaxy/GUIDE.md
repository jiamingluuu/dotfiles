---
name: bytedance-galaxy
description: "Query Galaxy asset management and host information via bytedcli: list hosts under a PSM, inspect capacity summaries, and understand host distribution across control planes."
---

# bytedcli Galaxy

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

- 列出当前用户"与我相关 / 我的订阅"的所有 PSM（service node）
- 按 PSM 查询该服务下挂的所有机器列表
- 查看机器容量统计（CPU 核数、内存、磁盘、SSD）和机型分布
- 按 PSM 反查 Galaxy node 路径，自动推断 control plane

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- Galaxy 请求需要 ByteCloud JWT，首次调用前先登录：`bytedcli auth login`
- 国际站（i18n-bd / i18n-tt）请求需要对应站点的 JWT

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 列出"与我相关"的所有 PSM（默认 scope=relation）
bytedcli galaxy psm list

# 列出"我的订阅"的 PSM
bytedcli galaxy psm list --scope subscription

# 列出"我负责的"（我是 owner 的）PSM
bytedcli galaxy psm list --scope owner

# 附带每个 PSM 的真实机器数（会多发一次请求）
bytedcli galaxy psm list --with-host-count

# 拉取全部 PSM（受 MAX_PAGES=50 安全上限保护）
bytedcli galaxy psm list --all

# 按 PSM 列出所有主机（默认分页：page 1, page-size 20）
bytedcli galaxy host list --psm "example.service.api"

# 指定 control plane（自动推断可省略）
bytedcli galaxy host list --psm "example.service.api" --control-plane i18n-bd

# 拉取全部主机（受 MAX_PAGES=50 安全上限保护）
bytedcli galaxy host list --psm "example.service.api" --all

# 自定义分页
bytedcli galaxy host list --psm "example.service.api" --page 2 --page-size 50

# 机器可读输出
bytedcli --json galaxy psm list
bytedcli --json galaxy host list --psm "example.service.api"
```

## Notes

- `--json` 是全局参数，放在 `galaxy` 前面，例如 `bytedcli --json galaxy host list ...`
- `galaxy psm list` 走 `box.bytedance.net` BFF，固定 CN plane；`--scope` 三选一：`relation`（与我相关，默认）= `owner`（我负责的）∪ `subscription`（我的订阅）
- `galaxy psm list` 的机器数默认不查（列表接口 `hostNum` 恒为 0）；需要真实机器数时加 `--with-host-count`
- 后端不支持关键词过滤，`galaxy psm list` 返回当前用户全部 PSM，如需筛选请在客户端处理
- `searchNodes`（PSM 反查）固定走 CN plane 的 `galaxy-api.bytedance.net`，不随 `--control-plane` 变化
- hosts search 按 control plane 路由到不同 host（cn / i18n-bd / i18n-tt）
- control plane 默认按 node path 自动推断：`path` 含 `i18n-bd` → i18n-bd，`i18n-tt` → i18n-tt，其余 → cn
- `--all` 模式会逐页拉取直到全部获取或达到 `MAX_PAGES = 50` 上限；超限时抛 `GALAXY_LIMIT_EXCEEDED` 错误并给出分页提示
- 分页默认值：`page=1`，`page-size=20`；host list 的 `page-size` clamp 到 `[1, 100]`，psm list 的 `page-size` clamp 到 `[1, 500]`
- 鉴权依赖 ByteCloud JWT，请优先用 `auth login` 获取

## References

- `references/galaxy.md`
