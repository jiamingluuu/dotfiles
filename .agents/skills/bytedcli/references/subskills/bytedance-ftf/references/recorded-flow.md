# Recorded Flow 管理

用户需要查询或删除尚未进入回放任务的 Recorded Flow 时，使用本流程。先按
[`invocation.md`](invocation.md) 校验准确命令路径；任务内 Flow 仍使用 `ftf task flow`，不要混用。

## 删除边界

`ftf flow delete` 是写操作，但 CLI 没有 dry-run 或预览能力。缺少 `--yes` 时命令直接以
`FTF_CONFIRMATION_REQUIRED` 拒绝执行，既不删除也不返回任何匹配流量；只有用户已经明确授权删除时才追加
`--yes` 真正执行。必须同时提供 `--psm` 和至少一个非空删除条件。空 `--filter-json` 不构成有效条件，
CLI 会拒绝空过滤，禁止通过猜测条件扩大删除范围。

命名 selector（`--id`、`--pid`、`--method`、`--log-id`）先组成过滤器，随后合并
`--filter-json`。JSON 对象中的同名字段覆盖命名 selector，因此同时使用时必须以最终合并后的过滤条件为准人工复核范围。

## 过滤示例

按实际泳道删除：

```bash
bytedcli --site cn ftf flow delete \
  --psm <psm> \
  --filter-json '{"env":"boe_demo"}'
```

按绝对时间区间删除：

```bash
bytedcli --site cn ftf flow delete \
  --psm <psm> \
  --filter-json '{"create_time":{"$gte":"2026-09-01T00:00:00+08:00","$lt":"2026-09-08T00:00:00+08:00"}}'
```

删除截止日期前的流量：

```bash
bytedcli --site cn ftf flow delete \
  --psm <psm> \
  --filter-json '{"create_time":{"$lt":"2026-09-01"}}'
```

用户使用“N 天前”等相对时间时，先按用户明确的时区换算为绝对 RFC3339 时间或日期值，再写入
`--filter-json`。不得把动态 shell 表达式写入命令，也不得隐式猜测时区。执行前展示换算后的绝对边界。

## 执行与核验

1. 删除前只能人工复核构造出的最终 JSON filter；CLI 没有 dry-run 或预览命令，不要声称能预览匹配范围。
2. 缺少 `--yes` 时命令只会返回 `FTF_CONFIRMATION_REQUIRED` 并终止，不会删除，也不会回传任何匹配流量；确认范围后再用完全相同的参数追加 `--yes` 执行。
3. 删除后可用 `ftf flow count` / `ftf flow has` 做近似核验，但它们不接受 `--filter-json`，只能用受支持的 typed flag（如 `--method`、`--env`、以毫秒计的 `--min-create-time`/`--max-create-time`），无法用与删除完全相同的条件精确回读剩余数量；核验结果不确定时不得自动重试删除。
