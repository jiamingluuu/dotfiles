# FundEye 子规则安全样例

以下样例只用于 Skill / 文档演示，全部使用 `demo-*` / `sample-*` 占位值。

- 业务样例统一放在 FundEye Skill 文档里，不再放仓库通用 `examples/` 目录。
- `single get/update` 的 `--sub-rule-id` 对应 `single_ds_check_id`。
- `double get/update` 的 `--sub-rule-id` 对应 `edge_seq`。
- `udf get/update` 的 `--sub-rule-id` 透传 open 接口的 `sub_rule_id`；常见场景下可复用 `payload.udf.udf_id`。

## Single

创建：

```bash
bytedcli --json fundeye rule single create \
  --scene-name demo-single-scene \
  --payload-file /tmp/demo-single.json
```

`/tmp/demo-single.json`：

```json
{
  "single_ds_check_name": "demo-single-check",
  "alarm_receiver": ["demo-owner"],
  "ds_locator": {
    "ds_type": "HTTP",
    "region": "cn",
    "idc": "cn",
    "psm": "sample.demo.psm",
    "api_path": "/openapi/v1/demo/check",
    "api_method": "POST",
    "end_point": 1
  },
  "single_ds_delay_check_configs": [
    {
      "trigger_ds_id": "sample-trigger-ds",
      "delay_check_type": "const",
      "delay_check_seconds": 300,
      "effective_seconds": 0
    }
  ]
}
```

查询：

```bash
bytedcli --json fundeye rule single get \
  --scene-id demo-scene-id \
  --sub-rule-id demo-single-check-id
```

更新：

```bash
bytedcli --json fundeye rule single update \
  --scene-id demo-scene-id \
  --sub-rule-id demo-single-check-id \
  --payload '{"single_ds_check_name":"demo-single-check-updated","ds_id":"sample-api-ds"}'
```

## Double

创建：

```bash
bytedcli --json fundeye rule double create \
  --scene-name demo-double-scene \
  --payload-file /tmp/demo-double.json
```

`/tmp/demo-double.json`：

```json
{
  "edge_table_join": {
    "edge_seq": 1,
    "from_vertex": 1,
    "to_vertex": 2,
    "join_expression": "[{\"upstream\":\"order_id\",\"downstream\":\"order_id\"}]",
    "join_expression_type": "govaluate",
    "check_logic": "[up.amount] == [down.amount]",
    "check_logic_type": "govaluate"
  },
  "vertex_table_list": [
    {
      "vertex_seq": 1,
      "vertex_name": "source_a",
      "ds_locator": {
        "ds_type": "MySQL",
        "db_name": "sample_upstream_db",
        "tb_name": "sample_order_table",
        "region": "cn",
        "idc": "cn"
      }
    },
    {
      "vertex_seq": 2,
      "vertex_name": "source_b",
      "ds_locator": {
        "ds_type": "RocketMQ",
        "cluster": "sample_mq_cluster",
        "topic": "sample_order_topic",
        "data_filter_tag": "*",
        "idc": "cn"
      }
    }
  ]
}
```

查询：

```bash
bytedcli --json fundeye rule double get \
  --scene-id demo-scene-id \
  --sub-rule-id 1
```

更新：

```bash
bytedcli --json fundeye rule double update \
  --scene-id demo-scene-id \
  --sub-rule-id 1 \
  --payload '{"edge_table_join":{"edge_seq":1,"from_vertex":1,"to_vertex":2,"join_expression":"[{\"upstream\":\"order_id\",\"downstream\":\"order_id\"}]","join_expression_type":"govaluate","check_logic":"[up.status] == [down.status]","check_logic_type":"govaluate"}}'
```

## UDF

创建：

```bash
bytedcli --json fundeye rule udf create \
  --scene-name demo-udf-scene \
  --payload-file /tmp/demo-udf.json
```

`/tmp/demo-udf.json`：

```json
{
  "udf": {
    "udf_name": "demo-udf-rule",
    "script_type": "yaegi",
    "script_param_type": "map[string]interface{}",
    "script": "func Verify(sourceA, sourceB []map[string]interface{}) (bool, error) { return len(sourceA) == len(sourceB), nil }",
    "alarm_receiver": ["demo-owner"],
    "delay_time": 300,
    "effective_time": 0,
    "verfication_vertex": [
      { "vertex_seq": 1, "is_trigger": 1 },
      { "vertex_seq": 2, "is_trigger": 1 }
    ]
  },
  "vertex_table_list": [
    {
      "vertex_seq": 1,
      "vertex_name": "source_a",
      "ds_locator": {
        "ds_type": "MySQL",
        "db_name": "sample_left_db",
        "tb_name": "sample_left_table",
        "region": "cn",
        "idc": "cn"
      }
    },
    {
      "vertex_seq": 2,
      "vertex_name": "source_b",
      "ds_locator": {
        "ds_type": "MySQL",
        "db_name": "sample_right_db",
        "tb_name": "sample_right_table",
        "region": "cn",
        "idc": "cn"
      }
    }
  ],
  "edge_table_join_list": [
    {
      "edge_seq": 1,
      "from_vertex": 1,
      "to_vertex": 2,
      "join_expression": "[{\"upstream\":\"record_id\",\"downstream\":\"record_id\"}]",
      "join_expression_type": "govaluate"
    }
  ]
}
```

查询：

```bash
bytedcli --json fundeye rule udf get \
  --scene-id demo-scene-id \
  --sub-rule-id demo-udf-id
```

更新：

```bash
bytedcli --json fundeye rule udf update \
  --scene-id demo-scene-id \
  --sub-rule-id demo-udf-id \
  --payload '{"udf":{"udf_id":"demo-udf-id","udf_name":"demo-udf-rule-updated","script_type":"yaegi","script_param_type":"map[string]interface{}","script":"func Verify(sourceA, sourceB []map[string]interface{}) (bool, error) { return len(sourceA) >= len(sourceB), nil }"}}'
```
