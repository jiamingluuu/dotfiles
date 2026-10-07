---
name: bytedance-byteconf
description: "ByteConf 配置中心：查询/更新配置、将指定版本部署到 PPE 或 BOE、查询和修改 bizline 业务线的 PPE 泳道。PPE 部署自动检查配置所属业务线，缺少泳道时先追加登记再发布；区分业务线编辑、配置更新和 PPE 发布权限错误。支持 bytedcli byteconf 及 region/vregion 路由。用于 ByteConf、配置中心、PPE 部署/发布、BOE 发布、业务线修改、新 PPE 泳道登记等任务。"
---

# bytedcli Byteconf

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

- 需要将配置部署到 PPE / BOE，或在部署前自动补齐业务线的 PPE 泳道登记
- 需要查询、修改 bizline 业务线，或诊断业务线编辑、配置更新、PPE 发布权限问题
- 需要列出 Byteconf 配置项（`conf list`）
- 需要读取单个配置项详情（`conf get`）
- 需要更新配置项 payload，或先 `--dry-run` 检查最终请求体（`conf update`）
- 需要通过 `--region` 在不同租户/区域网关之间自动路由，例如 `bytedance`、`boe`、`sinf`、`sg`
- 需要通过全局 `--vregion` 指定 `x-bcgw-vregion`，把读/写请求路由到正确集群（典型海外场景 `--vregion SG`）
- 需要确认 Byteconf 请求是否基于 Bytecloud SSO JWT 完成鉴权

## 前置条件

- 按通用调用方式执行命令（含内网 registry）：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

**命令行结构**：`bytedcli [全局选项] byteconf conf <子命令> [命令选项]`

| 类别 | 选项 | 位置 | 说明 |
| --- | --- | --- | --- |
| 全局选项 | `--json`、`--site`、`--http-debug` | `bytedcli` 之后、子命令之前 | 对所有子命令生效 |
| 命令选项 | `--ns-key`、`--biz-tree-path`、`--keyword`、`--id`、`--version`、`--region`、`--from`、`--query-json`、`--body-json`、`--dry-run` | 子命令之后 | 仅对当前子命令生效 |

**推荐格式**：`bytedcli --json byteconf conf list --ns-key "demo" --region "sg"`

```bash
# 列表查询
bytedcli --json byteconf conf list --ns-key "demo" --page 1 --page-size 20
bytedcli --json byteconf conf list --ns-key "demo" --biz-tree-path "a/b/c" --keyword "feature_flag"
bytedcli --json byteconf conf list --ns-key "demo" --region "sg"
bytedcli --json byteconf conf list --from ./query.json --query-json '{"page":2}' --region "sinf"

# 详情读取
bytedcli --json byteconf conf get --id 123 --version 1 --ns-key "demo"
bytedcli --json byteconf conf get --id 123 --version 7 --name "demo_conf" --biz-tree-path "a/b/c" --region "boe"
# 海外配置在非默认集群时，加全局 --vregion 把请求路由到目标集群
bytedcli --site i18n-tt --vregion SG --json byteconf conf get --region "sg" --id 123 --ns-key "demo"

# 更新配置：先 dry-run，再真实发起
bytedcli --json byteconf conf update --id 123 --version 7 --body-json '{"base":{"k":"v"}}' --dry-run
bytedcli --json byteconf conf update --id 123 --version 7 --from ./payload.json --region "sg"
```

## 推荐工作流

1. 不确定目标配置版本时，先执行 `conf list` 缩小范围。
2. 拿到 `id` 后，再执行 `conf get` 读取当前配置详情。
3. 更新前优先用 `conf update --dry-run` 检查最终 payload。
4. 确认 payload 无误后，再执行真实的 `conf update`。
5. 如果用户明确指定海外或测试环境，显式传 `--region`，不要依赖默认路由。
6. 如果按 `--region` 路由后仍返回 record not found，配置很可能在非默认集群上：补全局 `--vregion`（海外典型值 `SG`）把请求路由到目标集群，再重试同一条命令。

## 参数与行为说明

### `byteconf conf list`

- 支持 `--ns-key`、`--biz-tree-path`、`--keyword`、`--page`、`--page-size`
- 支持 `--from <path>` 读取基础 query JSON，再用 `--query-json` / 显式参数覆盖
- `--region` 默认值为 `bytedance`

### `byteconf conf get`

- `--id` 必填
- `--version` 默认值为 `1`
- 可选补充 `--name`、`--ns-key`、`--biz-tree-path`
- 当用户只知道名称或 namespace 时，先用 `conf list` 查出正确 `id` 和最新版本

### `byteconf conf update`

- `--id`、`--version` 必填
- `--from` 与 `--body-json` 至少提供一个
- `--dry-run` 只输出最终 payload，不实际发请求
- 支持把 `id`、`version` 放入 body，但更推荐显式传参，避免覆盖错误

## Notes

- 需要结构化输出时，默认加 `--json`，并放在 `byteconf` 之前，例如：`bytedcli --json byteconf conf get --id 123 --version 1`
- `--region` 传给底层 `x-bcgw-tenant-id`，同时用于选择对应网关 origin；它既可能表示默认租户 `bytedance`，也可能表示特定区域/租户，如 `boe`、`sg`、`sinf`
- 当前实现的默认租户是 `bytedance`
- 全局 `--vregion` 设置请求头 `x-bcgw-vregion`，用于选择目标集群，与 `--region` / `x-bcgw-tenant-id` 相互独立。Byteconf 配置按集群分片：未带 `--vregion` 时请求落到默认集群，位于其他集群上的配置会返回 record not found。海外典型场景传 `--vregion SG`（`x-bcgw-vregion` 区分大小写，用控制台原始值，小写 `sg` 不命中）；少数站点（如 `boe`、`i18n-bd`）会按站点强制集群覆盖，无需手动指定
- 底层鉴权使用 Bytecloud SSO JWT，请先确保 `bytedcli auth status` 正常；CLI 会把 JWT 注入到 `x-jwt-token` 请求头
- `conf get` 默认 `version=1`。如果用户要“最新版本”，应先 `list` 确认版本，再读取或更新
- `conf update` 要求输入为合法 JSON 对象；如果 payload 不确定，优先落文件后通过 `--from` 传入

## PPE / BOE 发布

- `byteconf conf deploy`：按 namespace、path、name、version 发布到 PPE 或 BOE。PPE 自动读取配置当前绑定的业务线、检查泳道；缺失或未启用时先追加登记并回读确认，再发布。已有泳道不重复修改。
- 默认预览完整登记与发布计划；`--yes` 执行整个流程，`--dry-run` 始终禁止写入。若用户已经明确要求发布，检查目标无误后可提交，无需为每个内部步骤重复询问。
- 不要凭业务线名称、namespace 下第一条记录或历史版本猜测绑定。配置未绑定业务线时先请管理员确认绑定。
- 某步失败立即停止，不通过直接 HTTP、其它发布接口或跳过业务线检查绕过失败。保留 CLI 返回的 `error.code`、`hint` 和 `details` 向用户解释。
- `BIZLINE_UPDATE` 表示编辑业务线/登记 PPE 泳道失败，联系业务线或 namespace 管理员；`PPE_DEPLOY` 表示 PPE 发布失败，申请配置/泳道发布权限或完成平台要求的审核；`CONF_UPDATE` 表示配置内容更新失败，申请配置写权限。HTTP 403 明确标为 `PERMISSION_DENIED`，其它错误保留原始原因，不能把网络失败说成无权限。
- 业务线登记已成功但发布失败时，结果保留 `registration` 状态；修复阻塞后重试即可，不删除已登记的泳道。
- `byteconf bizline list`：查询业务线及其允许的 PPE 泳道。
- `byteconf bizline update --ppe-channel <lane>`：追加已有泳道，保留原有泳道和 QA 设置；默认预览，管理员权限下 `--yes` 提交。
- `--region` 是源网关租户，`--publish-region` 是发布目标区域；不要混用。完整参数与示例见 `references/byteconf.md`。
- 新 ENV 环境的创建/查询使用 `bytedcli env`；业务线登记不创建环境，也不绕过管理员或审核权限。

## References

- `references/byteconf.md`
- `../../invocation.md`
