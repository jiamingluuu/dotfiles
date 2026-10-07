# Nario 案例：调试流量命中

当用户询问流量为何未命中 Nario 模板/场景、覆盖率为何偏低，或某个流量样本能否被打标时，使用本案例。

## 工作流

1. 判断用户拥有完整的流量 JSON，还是只有已存储的流量 PID。
2. 对于完整 JSON，先运行 `nario tagging flow tag --dry-run --need-detail`。
3. 对于已存储流量，如果用户询问命中了哪些模板/场景，使用 PSM 和 PID 运行 `nario tagging flow hit`。除非用户明确知道集合，否则省略集合参数。
4. 对已存储流量做底层调试时，使用 `flow tag`，并传入 PSM、PID 和显式集合。
5. 检查命中模板数、命中场景数和扁平化的 `hits[]` 命中明细。
6. 如果需要聚焦调试某个目标场景，切换到 `nario tagging scene-debug execute`；尚未准备好经过检查的调试 payload 时，先运行 `--dry-run`。

## 命令

```bash
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow tag \
  --payload-file ./flow.json \
  --dry-run \
  --need-detail

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow tag \
  --payload-file ./flow.json \
  --need-detail

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow tag \
  --psm example.psm \
  --pid sample-pid \
  --flow-collection flow_tagged \
  --dry-run

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging flow hit \
  --psm example.psm \
  --pid sample-pid

NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario tagging scene-debug execute \
  --psm example.psm \
  --pid sample-pid \
  --template-id 3000001 \
  --scene-id 2200001 \
  --dry-run
```

## 结果解读

- `summary.isTagged` 表示后端是否认为该流量已被打标。
- `summary.hitTemplateCount` 和 `summary.hitSceneCount` 可快速说明命中范围。
- `flow hit` 返回 `collection`、`attemptedCollections` 和扁平化的 `hits[]` 命中明细，便于转换为面向用户的表格。
- 用户询问命中了哪个模板或场景时，主要检查 `result.data.hit_detail`。
- 诊断时 `summary.isWrite` 应保持为 false，除非用户明确要求执行写入。

## 常见后续步骤

- 如果没有命中模板，检查 PSM/method/protocol 和模板启用状态。
- 如果命中模板但未命中场景，检查场景规则和 `check_value_list` 值。
- 如果流量 payload 缺少规则引用的字段，请用户提供包含这些字段的代表性流量或调试 payload。
- 如果用户希望持久化结果，说明 `--yes` 会启用写入语义，且只能在检查影响后使用。
