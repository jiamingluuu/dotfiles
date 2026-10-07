# Panama

Panama 只用于必须通过合规机房链路调用 RPC 的场景。它执行 RPC 后返回 Panama 的
log/assertion 结果，不展示 RPC 原始返回值；普通 RPC 接口测试、需要查看 response
payload 或调试业务字段时，不要使用 Panama，请优先使用 `bytedcli api-test rpc-call`
或 bytedcli 中对应的接口测试工具。

```bash
# 执行 Panama RPC 工具
bytedcli --site i18n panama rpc execute \
  --psm "example.service" \
  --method "DemoMethod" \
  --idc TTP \
  --body '{"id":"1234567890123456789"}' \
  --assert-json '{"1":{"value":"1","operator":"="}}'

# 机器可读输出，从文件读取 body/assertion
bytedcli --json --site i18n panama rpc execute \
  --psm "example.service" \
  --method "DemoMethod" \
  --env prod \
  --idc USEAST2B \
  --body-file ./request.json \
  --assert-file ./assert.json
```

## Notes

- `--env` 默认 `prod`；`--cluster` 默认 `default`。
- `--idc` 只接受 `TTP`、`TTP2`、`GCP`、`NO1A`、`USEAST2B`。
- `--idc` 使用 Panama UI 展示的标签；CLI 发给 Panama API 时会映射为后端 IDC：`TTP=useast5`、`TTP2=useast8`、`GCP=gcp`、`NO1A=no1a`、`USEAST2B=useast2b`。
- `--body` / `--body-file` 表示内层 RPC request body，不是 Panama 外层 API payload。
- `--assert-json` / `--assert-file` 表示 Panama assertion JSON。
- Panama 不展示 RPC 原始返回值，只适合合规机房 RPC 执行与断言。
- 正常 RPC 接口测试请使用 `bytedcli api-test rpc-call` 或其他接口测试命令。
- 鉴权复用 ByteCloud JWT，首次使用前执行 `bytedcli --site i18n auth login`。
