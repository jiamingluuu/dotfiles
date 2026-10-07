# Smart queue 配置查询

使用 `bytedcli pontus smart-queue list` 查询 Pontus smart queue 配置。请求固定查询第 1 页、每页 20 条，region 默认为 `cn`。

## 参数

- `--queue-name <name...>`：按一个或多个队列名过滤。
- `--region <region>`：区域名，默认 `cn`；`cn` 映射为接口值 `1`。

## 示例

```bash
# 默认查询
bytedcli pontus smart-queue list

# 按多个队列名查询
bytedcli pontus smart-queue list --queue-name demo-queue other-queue

# 结构化 JSON 输出；--json 是全局参数，放在 pontus 前
bytedcli --json pontus smart-queue list --region sg
```

文本模式展示队列名、创建者、data team 和 region，并分别标明后端总数（缺失时显示 `unknown`）与当前页条数。JSON 模式通过 `total` 返回后端总数（缺失时为 `null`），通过 `current_count` 返回当前页条数；同时保留接口返回条目的未知字段，并增加规范化的 `queueName`、`creator`、`dataTeam` 和 `region` 字段，便于脚本稳定消费。
