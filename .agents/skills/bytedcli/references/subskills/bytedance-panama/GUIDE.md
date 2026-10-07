---
name: bytedance-panama
description: "Operate Panama via bytedcli only when an RPC must be invoked through compliance IDC routing; Panama returns log/assertion results, not the RPC response body. For normal RPC interface testing, use api-test RPC commands instead."
---

# bytedcli Panama

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

- 需要通过 Panama 平台在合规机房链路里执行一个 RPC 方法
- 已经知道 RPC 的 PSM、method、IDC 和 request body
- 需要复用 Panama assertion JSON 判断执行结果
- 只需要 Panama 的 log/assertion 结果，不需要查看 RPC 原始返回值

## When not to use

- 需要正常测试 RPC 接口、查看 response payload、调试字段返回或验证业务返回体时，不要路由到 Panama。
- Panama 平台不展示 RPC 原始返回值；它适合合规机房 RPC 执行与断言，不适合通用接口测试。
- 普通 RPC 接口测试优先使用 `bytedcli api-test rpc-call` 或 bytedcli 中对应的接口测试工具。

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- Panama 当前调用时使用 `--site i18n`
- 首次调用前先登录目标站点：`bytedcli --site i18n auth login`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 直接传 RPC request body
bytedcli --site i18n panama rpc execute \
  --psm "example.service" \
  --method "DemoMethod" \
  --idc TTP \
  --body '{"id":"1234567890123456789"}' \
  --assert-json '{"1":{"value":"1","operator":"="}}'

# 从文件读取 RPC request body 和 assertion
bytedcli --json --site i18n panama rpc execute \
  --psm "example.service" \
  --method "DemoMethod" \
  --env prod \
  --idc NO1A \
  --body-file ./request.json \
  --assert-file ./assert.json
```

## Notes

- `--env` 默认是 `prod`，需要调用其他环境时显式传入。
- `--idc` 支持 `TTP`、`TTP2`、`GCP`、`NO1A`、`USEAST2B`。
- `--idc` 使用 Panama UI 展示的标签；CLI 发给 Panama API 时会映射为后端 IDC：`TTP=useast5`、`TTP2=useast8`、`GCP=gcp`、`NO1A=no1a`、`USEAST2B=useast2b`。
- `--cluster` 默认是 `default`。
- `--body` / `--body-file` 是 RPC 方法的 request body，CLI 会原样传给 Panama，不会先解析后重组，避免大整数精度丢失。
- `--assert-json` / `--assert-file` 是 Panama assertion JSON。
- Panama 只返回 log/assertion 结果，不展示 RPC 原始返回值；需要查看返回值时请改用接口测试工具。
- Panama 鉴权复用 bytedcli ByteCloud JWT，请优先用 `auth login` 获取，不要手写请求头。
- 输出 JSON 时，`--json` 是全局参数，放在 `panama` 前面。

## References

- `references/panama.md`
