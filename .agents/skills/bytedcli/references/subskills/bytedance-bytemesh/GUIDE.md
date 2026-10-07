---
name: bytedance-bytemesh
description: "Read ByteMesh console data via bytedcli. Use for service management, release and batch-upgrade plans, the resource/plugin market, installed plugins, exception handling, or browser-free multi-site ByteMesh API queries."
---

# bytedcli ByteMesh

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

- 服务管理：服务列表、服务详情、环境、集群、版本、默认版本、工单历史
- 升级计划：大版本升级、批量升级及其版本、流水线、bug、stage
- 插件管理：资源市场、资源详情、资源版本、已安装 plugin 和 plugin graph
- 异常处理：升级异常、版本收敛
- 用户提供 ByteMesh 控制台 URL，需要根据网页层级选择等价的只读命令

## 认证与权限

ByteMesh 复用 bytedcli 在目标站点保存的 ByteCloud 用户态 JWT。站点必须与控制台链接一致，不做跨站 fallback：

```bash
bytedcli --site cn auth login
bytedcli --site i18n-tt auth login
bytedcli --json auth status
```

- 不读取 Chrome/浏览器 Cookie、JWT 或其他浏览器凭据。
- 不需要 `auth login --session`；ByteMesh 命令不会回退到浏览器 session。
- 命令只调用只读 `/api/v2/...` 接口，不调用需要 service account 的 `/openapi/v2/...`。
- 通过全局 `--site` 选择 `cn`、`boe`、`i18n`、`i18n-bd`、`i18n-tt`、`us-ttp`、`us-ttp-bdee`、`us-ttp-usts` 或 `eu-ttp`；BOE virtual region 继续使用全局 `--vregion`。
- 登录只证明身份有效，不自动授予 ByteMesh 资源权限。401 时登录同一 `--site`；403 时申请目标 resource/service 的 RBAC 权限。

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 控制台 URL 到命令

CLI 不接收整条控制台 URL。根据 URL pathname 选择命令组，再把 query/path 中的 `resourceId`、`region`、详情 ID 显式传入：

| 控制台 pathname                                                                        | 命令组                                     |
| -------------------------------------------------------------------------------------- | ------------------------------------------ |
| `/service-management/service-list`、`service-detail/*`、`ticket-history`               | `bytemesh service ...`                     |
| `/plan/release/*`                                                                      | `bytemesh plan release ...` / `release-*`  |
| `/plan/batch-upgrade/*`                                                                | `bytemesh plan batch-upgrade ...`          |
| `/resources-management/resources-market`、`resources-detail/*`、`version-management/*` | `bytemesh resource ...`                    |
| `/exception-handling/upgrade`                                                          | `bytemesh exception upgrade get`           |
| `/exception-handling/version-converge`                                                 | `bytemesh exception version-converge list` |

国内 ByteDance 控制台通常对应 `--site cn`，TikTok ROW 控制台通常对应 `--site i18n-tt`。不要把一个站点失败的请求自动改发到 CN。

## Resource

```bash
bytedcli --json bytemesh resource market list --scope all
bytedcli --json bytemesh resource market list --scope mine --category sidecar

bytedcli --json bytemesh resource get --id 123456

bytedcli --json bytemesh resource owner list --resource-id 123456 --unique
bytedcli --json bytemesh resource config get \
  --resource-id 123456 \
  --region China-North
bytedcli --json bytemesh resource bug list --resource-id 123456 --status open
bytedcli --json bytemesh resource commit search \
  --resource-id 123456 \
  --keyword demo-commit
bytedcli --json bytemesh resource recall-version list \
  --resource-id 123456 \
  --region China-North

bytedcli --json bytemesh resource version list \
  --resource-id 123456 \
  --page 1 \
  --page-size 20

bytedcli --json bytemesh resource default-version get \
  --resource-id 123456 \
  --region China-North
bytedcli --json bytemesh resource in-use-service list \
  --resource-id 123456 \
  --region China-North \
  --version 1.2.3
```

## Service

Service metadata 命令使用同一组显式 scope：`--resource-id`、`--region`、`--service-node-id`。cluster/version 查询还需要 `--env`。

```bash
bytedcli --json bytemesh service list \
  --resource-id 123456 \
  --region China-North \
  --page 1 \
  --page-size 20

bytedcli --json bytemesh service get \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567

bytedcli --json bytemesh service env list \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567

bytedcli --json bytemesh service cluster list \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567 \
  --env ppe_demo

bytedcli --json bytemesh service version list \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567 \
  --env ppe_demo

bytedcli --json bytemesh service default-version list \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567
```

## Plugin

对外统一使用 `plugin`，CLI 会在 API 层映射 ByteMesh 上游的 extension 接口。

```bash
# 服务级 plugin 列表
bytedcli --json bytemesh service plugin list \
  --psm example.mesh.service \
  --region China-North \
  --env ppe_demo

# 按多个 cluster 过滤服务级 plugin
bytedcli --json bytemesh service plugin list \
  --psm example.mesh.service \
  --region China-North \
  --env ppe_demo \
  --clusters demo-cluster-a,demo-cluster-b

# 单 cluster plugin；--cluster 与 --cluster-id 二选一
bytedcli --json bytemesh service plugin list \
  --psm example.mesh.service \
  --region China-North \
  --env ppe_demo \
  --cluster demo-cluster-a

# 单 cluster plugin graph；--cluster 与 --cluster-id 必须二选一
bytedcli --json bytemesh service plugin-graph get \
  --psm example.mesh.service \
  --region China-North \
  --env ppe_demo \
  --cluster demo-cluster-a \
  --format dot
```

## Ticket history

```bash
bytedcli --json bytemesh service ticket get --ticket-id 345678

bytedcli --json bytemesh service ticket list \
  --resource-id 123456 \
  --region China-North \
  --service-node-id 234567 \
  --env ppe_demo \
  --page 1 \
  --page-size 20

bytedcli --json bytemesh service ticket-step list --ticket-id 345678
```

## Plan

```bash
bytedcli --json bytemesh plan release list \
  --resource-id 123456 \
  --region China-North
bytedcli --json bytemesh plan release get --id 77
bytedcli --json bytemesh plan release-version list --release-id 77
bytedcli --json bytemesh plan release-version get --version-id 88
bytedcli --json bytemesh plan release-pipeline list \
  --release-id 77 \
  --resource-id 123456 \
  --region China-North \
  --version 1.2.3 \
  --upgrade-mode normal
bytedcli --json bytemesh plan release-bug list --plan-id 66

bytedcli --json bytemesh plan batch-upgrade list \
  --resource-id 123456 \
  --region China-North
bytedcli --json bytemesh plan batch-upgrade get --id 66
bytedcli --json bytemesh plan batch-upgrade-stage get --stage-id 67
```

## Exception

```bash
bytedcli --json bytemesh exception upgrade get \
  --resource-id 123456 \
  --region China-North \
  --psm example.mesh.service \
  --env ppe_demo \
  --cluster demo-cluster \
  --stage canary

bytedcli --json bytemesh exception version-converge list \
  --resource-id 123456 \
  --state running

bytedcli --json bytemesh exception version-converge list \
  --resource-id 123456 \
  --state locked \
  --region China-North \
  --only-prod-env \
  --start 2026-07-31T12:00:00+08:00
```

## Agent guidance

- 需要稳定机器可读输出时，把全局 `--json` 放在 `bytemesh` 前面。
- 已有 ByteMesh URL 时先按 pathname 选择上述语义命令，再显式传入 ID/region；不要把 URL 直接传给 CLI。
- 用户问“插件”时直接用 `service plugin list`；只有明确需要拓扑/图时才用 `service plugin-graph get`。
- 用户问插件市场或“有哪些插件”时用 `resource market list`；该命令与服务上已经安装的 `service plugin list` 语义不同。
- service plugin 列表无需 cluster selector；cluster 级列表和 graph 使用 `--cluster` 或 `--cluster-id`，不要同时传。
- plugin 命令的业务地域使用 `--region`；全局 `--vregion` 只用于 BOE 等站点路由，二者不要混用。
- `service ticket-step list` 会返回 stage/step 的升级类型、实例数、滚动数、比例和错误信息，可用于判断工单实际执行的是热升级还是安全升级。
- service 启用状态使用 `--enable-resource on|off`；release pipeline 当前使用 `--upgrade-mode normal`。
- exception upgrade 的 `--stage` 使用 `canary|single-dc|all-dc`，不要传后端 snake_case 值。
- version convergence 的 `--start` 接受 ISO 8601 或 Unix timestamp，并作为“开始时间不晚于该时刻”的过滤条件。
- 分页 JSON 使用 `page_size`；当后端不返回总数时使用 `page_count` 表示当前页条数，不会用当前页条数冒充 `total`。
- API 返回 401/403 时不要尝试抽取浏览器 Cookie，也不要切换到其他站点碰碰运气；按错误提示登录同站点或申请资源权限。

## References

- `../../invocation.md`
- `../../troubleshooting.md`
