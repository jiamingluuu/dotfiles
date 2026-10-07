---
name: bytedance-tsp
description: "Operate TSP Trusted Secret Platform security workflows via bytedcli: manage identities, secrets, IAM users/policies/access keys, roles, and Personal secret permissions across ByteDance, VolcanoEngine, VKE, Lark, and Personal editions. Use when tasks mention TSP, Trusted Secret Platform, TSP secret, TSP identity, or TSP IAM role."
---

# bytedcli TSP

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

## When to use

- 查询、创建、更新或删除 TSP identity。
- 查询、创建、更新、删除 TSP secret，获取/写入 secret value，列 secret version。
- 查询或创建 Volcano/VKE IAM user、policy、access key、托管 secret、service linked role。
- 查询、创建、删除 Lark/VKE role。
- 管理个人凭据权限授权、回收与查询。

## Quick start

```bash
bytedcli tsp site list
bytedcli tsp secret list --tsp-site cn --identity-type ByteDance --psm demo.service --page 1 --page-size 20
bytedcli tsp secret get --secret-name demo-secret --psm demo.service
bytedcli tsp secret create --secret-name demo-secret --secret-type Generic --secret-value demo-value --psm demo.service
bytedcli tsp secret create --secret-name demo-secret --secret-type Generic --secret-value demo-value --psm demo.service --yes
bytedcli tsp secret value get --secret-name demo-secret --psm demo.service
bytedcli tsp identity list --identity-type Lark --account-id cli_demo_app_id
bytedcli tsp identity create --identity-type Lark --account-id cli_demo_app_id --name demo-identity --psm demo.service --yes
bytedcli tsp iam user list --identity-type VolcanoEngine --account-id demo-account-id
bytedcli tsp role list --identity-type Lark --account-id cli_demo_app_id
bytedcli tsp permission list --identity-type Personal --resource-id trn:demo:secret/demo-secret
```

## Notes

- TSP OpenAPI 统一走 `POST /api/v1/tsp/tsp?Action=<Action>&Version=1.0.51`。
- `--tsp-site` 支持 `boe|cn|i18n-bd|i18n-tt|eu-ttp|us-ttp`；别名 `prod/online -> cn`、`sg/va/row -> i18n-tt`、`eu -> eu-ttp`、`ttp-us -> us-ttp`。
- `--identity-type` 只支持精确字符串 `ByteDance|VolcanoEngine|VKE|Lark|Personal`，大小写敏感。
- 写操作默认 dry-run，只打印脱敏后的 payload 和 headers；确认后追加 `--yes`。
- SecretValue、AccessKeySecret 等敏感值在 dry-run 输出中会脱敏。
