# 商品版本

```bash
bytedcli babi product version list --product-id <product_id>
```

按生效时间范围查询：

```bash
bytedcli babi product version list \
  --product-id <product_id> \
  --valid-time-lower-bound 1777564800000 \
  --valid-time-upper-bound 1780243199999 \
  --offset 0 \
  --limit 20
```

命令向 `POST /v4/product/listProductInfo` 传 `id=[product_id]` 和 `only_basic_info=true`。未传 `--version-status` 时默认使用 `version_status=[202]` 查询生效版本；显式传入时以命令行参数为准。`202` 是 BABI v2 的生效状态；不要改成旧价格版本状态 `5`。

查询指定类型的草稿时只需传入 `--env`，命令会自动把 `version_status` 设为 `100`。例如查询月度草稿：

```bash
bytedcli babi product version list \
  --product-id <product_id> \
  --env month
```

可查询的版本状态为 `100=草稿`、`101=失效`、`202=生效`、`999=软删除`；内部异常初始态 `0` 不作为命令行筛选值。草稿类型为 `normal=日常变更`、`month=月度调价`、`half_year=半年调价`、`outer=外采新增计费项`、`budget=预算专用`。`--version-status` 和 `--env` 都支持逗号分隔的多值输入；即使同时传入其他 `--version-status`，`--env` 也会将实际请求状态覆盖为 `100`。

`--only-basic-info` 默认是 `true`，保持原来的轻量查询行为；如需让服务端返回额外业务信息，显式传入 `--only-basic-info=false`。

结果按 IDL 的 `ProductInfoDTO` 解析，读取 `items[].version_id`、`version_status/version_status_name`、`env/env_name`、`effect_begin_time`、`effect_end_time`、`version_creator`、`version_modifier`，并保留商品基础信息和服务端返回的 `extra`。当 `pagination.total` 大于已取条数时继续翻页，不要把第一页当成完整版本历史。

需要继续查成本关联配置时，转交 [babi-account 指南](../../babi-account/GUIDE.md)：把这里得到的 `version_id` 作为商品大版本号 ID，
调用 `account cost-config list --version-id <商品版本ID> --use-unit-version-id=true ...`。只有
`product get` 已确认该商品 `product_type_code=3` 或 `product_type_name=代持` 时，才用返回的
`config_key` 调用
`account consumer-config list --version-id <商品版本ID> --cost-config-unique-keys <config_key,...> ...`
查询代持/消费者配置；这里的 `--version-id` 复用 `product version list` 返回的商品大版本号 ID。
非代持商品不得调用消费者配置查询。

如果入口是商品类型账号，先由 `account list` 读取账号 `entity_id`，再把该 `entity_id`
作为商品 ID 查询本页商品版本，这是主要链路。备选方案也可以用商品账号调用
`account cost-version list`，但消费者配置必须使用返回版本数据中的 `origin_version_id` 查询，不能使用普通成本关联
`version_id`。
如果成本配置查询返回 `use_unit_version_id conflicts with account type`，暂时回到商品版本口径：
使用商品版本 ID 作为 `account cost-config list --version-id`，并传 `--use-unit-version-id=true`。
