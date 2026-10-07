---
name: bytedance-agw
description: "Operate AGW (API Gateway) via bytedcli: products, services, configs, envs, publish flows, IDL updates, route sync, and BFFv2 route creation/rendering/grouping. Use when tasks mention AGW, API Gateway, gateway product/service/config, register env, publish, IDL update, route sync, BFFv2, BFF2.0 route, route group, render DSL, or DSL workspace."
---

# bytedcli AGW

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

- AGW 产品搜索、收藏产品列表、产品详情查看
- AGW 服务搜索、服务详情、服务列表、接入状态检查、新建服务、生效地域添加
- AGW 配置列表、配置详情、新配置版本生成
- AGW 多环境查询、注册与部署（BOE/PPE feature env 首次使用前注册）
- AGW 发布、发布单创建与发布历史查询
- AGW BFFv2 模板查询/设置、BFF2.0 路由新建/批量新建/分组管理/解释、IDL/DSL 渲染、DSL workspace、客户端 IDL 导出到 BAM
- AGW IDL 更新与发布（BOE/PPE 环境）
- AGW IDL + 路由同步更新（自动从 IDL 注解补齐缺失路由）

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `agw product`, `agw service`, `agw config`, `agw env`, `agw publish`, `agw bffv2`, and `agw idl`. Old flat names (e.g. `agw list-starred-product`, `agw register-env`, `agw update-idl`) still work as hidden aliases.

```bash
# 收藏产品列表
bytedcli agw product list

# 搜索产品
bytedcli agw product search --keyword "api"

# 产品详情
bytedcli agw product get --product "my-product"

# 搜索服务（按 PSM / 路径关键词）
bytedcli agw service search --keyword "example.service"

# 获取服务详情 / 配置详情
bytedcli agw service get --service-id <service-id>
bytedcli agw config get --service-id <service-id> --version <version>

# 注册泳道环境（首次使用前）
bytedcli agw env create --service-id <service-id> --type boe_feature --name demo-lane

# 注册泳道环境并启用自动部署
bytedcli agw env create --service-id <service-id> --type boe_feature --name demo-lane --auto-deploy --branch feat/example

# 发布 PPE 配置 / 创建线上发布单 / 查询发布工单详情
bytedcli agw publish execute --target ppe --service-id <service-id> --version <version> --env ppe_demo
bytedcli agw publish order create --target online --service-id <service-id> --version <version>
bytedcli agw publish order get --publish-id <publish-id>

# BFFv2 模板查询、路由解释与 DSL 渲染
bytedcli agw bffv2 template search --psm example.service.api
bytedcli agw bffv2 route list --service-id <service-id> --version <version>
bytedcli agw bffv2 dsl create --service-id <service-id> --version <version> --template default --backend-api thrift:example.backend:GetItem --req-idl-file http-input.thrift --purpose create
bytedcli agw bffv2 dsl-workspace import --bff-config-file render-dsl.json --output-dir ./bffv2-dsl
bytedcli agw bffv2 dsl-workspace export --workspace ./bffv2-dsl --output-file reviewed-bff-config.json

# 协议转换服务：更新 IDL 并自动发布
bytedcli agw idl update --service-id <service-id> --env boe_default

# 协议转换服务：更新 IDL 同时自动从 IDL 注解同步路由
bytedcli agw idl update --with-router --service-id <service-id> --env boe_default
```

## BFFv2 Route Workflow

当用户要新增、复制或修改 BFF2.0/BFFv2 路由时，先读：

- `references/bffv2-create-route.md`：端到端新建路由流程
- `references/bffv2-dsl-workspace.md`：DSL workspace 与 `TYPE_DSL`/`HANDLE_DSL` review 规则
- `references/bffv2-troubleshooting.md`：常见问题

关键约定：

- 先重新读取目标 env current config，避免把刚创建的新配置版本误当作泳道当前版本。
- 用户提到“批量创建 / 批量新增 / 多条 BFF2.0/BFFv2 路由”时，优先走 `references/bffv2-create-route.md` 的批量创建流程，并使用 `batch-route create` 生成本地 config plan。
- `batch-route create` 当前仅支持一个或多个 thrift backend PSM，每个 thrift backend PSM 下可批量建路由；`--route` 使用 `<thrift-backend-psm>:<METHOD>:<PATH>:<RPC_METHOD>`，暂不支持 http / tcc / rpc-http backend。
- 单个 BFF2.0/BFFv2 路由统一使用 `route create`；默认生成可 review 的 artifact workspace，明确不需要 review DSL 时传 `--auto-render`。不要用 `batch-route create` 创建单个路由。
- 单路由或批量新建时如需放入 BFF 分组，给 `route create` / `batch-route create` 传 `--group <name>`；目标分组不存在时必须显式传 `--create-group`。
- 修改已有 BFF2.0/BFFv2 路由分组时使用 `agw bffv2 group update` 生成本地 config plan；创建空分组用 `agw bffv2 group create`。这些命令都不直接提交配置。
- 批量创建前如果 thrift backend PSM 或 RPC method 不存在，先用 `backend-idl update --backend-idl thrift:<psm>:<version>` 更新后端 IDL，提交中间配置得到 `IDL_UPDATED_VERSION`，再基于该中间版本执行 `batch-route create`。
- 不要给 `batch-route create` 或后续最终 `config create` 补 `--bff-backends-from-cfg-ver`；该流程基于完整 `origin_config` 生成配置。
- `batch-route create` 结构化模式不暴露 timeout / overwrite；如确需 admin DSL 高级字段，使用 `--body-file` pass-through。
- 若要先更新上游 IDL 再新增路由，先用 `backend-idl update` 创建 `IDL_UPDATED_VERSION`，之后 render 新路由、`route create` 或 `batch-route create` 都必须基于该中间版本。
- 强约束：BFFv2 请求解析 IDL 配置与 DSL 类型定义强耦合；任何 IDL 配置变更后，必须基于最新 IDL 重新执行 `agw bffv2 dsl create` 并只更新 `type_dsl`，`handle_dsl` 不受影响且不得被覆盖。
- `--backend-api` 使用 `<protocol>:<psm>:<method>`，例如 `thrift:example.backend:GetItem`。
- `route create` 自动生成唯一 `bff_key`，不要让用户手工指定。
- `--frontend-idl-method-name` 默认不传，只有客户端 IDL method 冲突时才显式指定。
- 用户只 review `*.dsl.ts` 的 `HANDLE_DSL` 区域；`TYPE_DSL` 区域只读且有 hash 校验。
- config plan 文件默认应生成在当前工作目录的可预测文件名，而不是 `/tmp`；单路由默认使用当前工作目录下 `<service_slug>/<method_path_slug>/dsl-workspace` 供用户 review，最终 plan 写入该 artifact 的 `snapshots/route-plan.<timestamp>.json`；`--auto-render` 和 `--bff-config-file` 仍沿用旧的 `agw-bffv2-route-plan-<service>-<version>-<timestamp>.json` 默认文件名。

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json agw product search --keyword "api"`）
- AGW 不使用 `--site boe`；查看或发布 BOE 环境/配置时使用线上站点，例如 `bytedcli --site cn agw config get --service-id <service-id> --boe`
- AGW 站点路由：`--site cn --vregion sinf` 使用 `https://cloud.sinf.net`，`--site i18n-bd --vregion sinfi18n` 使用 `https://cloud-i18n.sinf.net`，`--site us-ttp` 使用 `https://cloud.tiktok-us.net`，`--site eu-ttp` 使用 `https://bc-iedt-gw.tiktok-eu.net`
- `env create` 用于首次使用泳道环境前注册；重复注册会报错但无副作用；`--type` 常用值 `ppe` / `boe_feature`；默认不自动部署，传 `--auto-deploy --branch` 可启用自动部署并绑定 IDL 分支
- `env deploy` 只适用于中心式网关架构服务；分布式 sidecar 网关服务不适用，后端通常返回 `deployment by platform does not support sidecar arch`
- `config create --bff-backends-from-cfg-ver` 用于 BFFv2 场景复用历史版本的 `bff_v2_backends_config`；只有不更新上游 IDL 时才使用，更新上游 IDL 时必须传最新 `bff_v2_backends_config`
- `bffv2 dsl create` 返回结果只取需要的 DSL 字段填回配置；`only_render_type_dsl=true` 时只使用 `type_dsl`，不要覆盖已有 `handle_dsl`。请求解析 IDL 配置发生任何变化后，必须重新执行 `bffv2 dsl create`，只用最新 render 结果更新 `type_dsl`，`handle_dsl` 不受影响。
- `bffv2 dsl-workspace import` 将 `type_dsl` 和 `handle_dsl` 合并成 `*.dsl.ts`；只编辑 `HANDLE_DSL` 区域，`TYPE_DSL` 区域有 hash 校验
- `bffv2 route create`、`bffv2 batch-route create`、`bffv2 group create`、`bffv2 group update` 只生成本地 config plan，真正提交仍需显式执行 `agw config create`
- 目前 AGW CLI 暂不支持配置 diff；提交或发布前应建议用户到 AGW 平台确认配置差异。
- `bffv2 batch-route create` 的 `--routes-file` 格式是 `{ [backendPsm]: [{ http_method, path, rpc_method, group_name? }] }`；不要在示例中使用真实 PSM、路径或线上标识
- `bffv2 backend-idl update` 用于上游 IDL 更新后刷新类型定义；推荐传 repeatable `--backend-idl <protocol>:<psm>:<version>`（或单后端便捷参数），它会获取 BAM IDL、更新/新增 backend config 并生成完整配置文件；若目标版本低于当前配置版本会阻断，确认降级才传 `--allow-downgrade`；不应改写用户维护的 `HttpInput` / `handle` 逻辑
- `idl update` 面向 AGW 协议转换服务的主 IDL 更新；BFF2.0/BFFv2 上游后端 IDL 更新请使用 `agw bffv2 backend-idl update`
- `idl update` 的 `--env` 仅支持 BOE（`boe_xxx`）和 PPE（`ppe_xxx`）环境
- `idl update` 的 `--publish-mode` 支持 `auto`（默认，创建发布工单）和 `manual`（仅更新 IDL 不发布）
- `idl update --with-router` 在 `idl update` 基础上自动解析 IDL 中的 `api.get`/`api.post` 等 Thrift 注解，将缺失的路由补齐到 AGW 配置的 `routes` 中（只增不删）
- 缺少必填参数会自动输出帮助信息

## References

- `references/agw.md`
