# 计费项、单价与首次出现版本

## 查询计费项与单价

```bash
bytedcli babi product charge-item list --product-id <product_id>
```

按计费项、组合计费单元和版本过滤：

```bash
bytedcli babi product charge-item list \
  --product-id <product_id> \
  --charge-item-code demo-charge-item-code \
  --combine-flavor-code cpu,mem \
  --version-id v1 \
  --limit 20
```

不知道草稿的 `version_id` 时，可以按单个草稿环境自动解析：

```bash
bytedcli babi product charge-item list \
  --product-id <product_id> \
  --draft-env month \
  --charge-item-code demo-charge-item-code
```

`--draft-env` 可选值为 `outer`、`month`、`half_year`、`normal`、`budget`，一次只能指定一个。未传 `--version-id` 时，命令先请求 `POST /v4/product/listProductInfo`，使用 `id=[product_id]`、`env=[draft_env]` 和 `version_status=[100]` 定位草稿，将唯一结果的 `version_id` 注入计费项请求；查不到、返回多个版本或缺少 `version_id` 时停止并提示显式指定版本。若同时传入 `--version-id` 和 `--draft-env`，以 `--version-id` 为准并跳过草稿版本查询。

用户已明确提供 `product_id` 和 `version_id` 时，直接执行一次 `product charge-item list`，不得把 `product get` 商品确认或 `product version list` 版本确认作为前置步骤。只有用户同时要求商品主数据，或这次直接查询明确返回商品/版本无效错误时，才追加对应查询；不要仅为“确认”稳定 ID 而增加请求。

最终计费项查询请求 `POST /v4/charge_item/listChargeItem`。未传 `--draft-env` 时保持原逻辑，直接调用该接口。未传 `--effect-time` 时使用当前毫秒时间；需要可复现查询时显式传入。常用精确过滤包括 `--charge-item-code`、`--combine-flavor-code`、`--flavor`、`--region`、`--period`、`--billing-function`、`--manage-type` 与 `--bill-tag`。

定价商品读取 `items[].price[]`：`price_type/name` 表示总价、纯资源、纯人力等价格口径，`unit_price` 是配置单价，阶梯价格还要同时保留 `unit_price_interval` 与 `measure_interval`。命令还会补充 `manage_type_name`、`billing_function_name` 与 `measure_function_name`。摊销商品读取 `items[].amortize_configuration[]` 的大区和折算比例。分页以 `pagination.total/limit/offset` 为准。

## 查询首次出现版本

```bash
bytedcli babi product charge-item first-appearance get \
  --product-id <product_id> \
  --charge-item-code demo-charge-item-code
```

该命令先查询商品的草稿、失效和生效版本（`100/101/202`），按版本创建时间升序，再用每个 `version_id` 精确查询目标计费项；首次命中即返回 `first_appear_version.version_id`、`updater`、版本时间与计费项快照。

这条链路只使用 BABI API，不执行任意 SQL。无结果表示目标计费项未出现在当前 API 可见的非删除版本中；不要扩大解释为数据库历史上绝对不存在。
