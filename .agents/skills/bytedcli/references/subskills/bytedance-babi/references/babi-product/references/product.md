# 商品主数据、类目与定价方式

## 查询商品基础信息

按名称和商品状态搜索商品：

```bash
bytedcli babi product get --fuzzy-product-name 'Data' --product-status 1 --limit 20
```

按稳定 ID 查询商品类目和定价方式：

```bash
bytedcli babi product get --product-id <product_id>
```

`product get` 只请求 `POST /v4/product/listProductBaseInfo`，不会通过 `getProduct` 补查。`--product-id` 对应 IDL 的 `product_id`，`--product-code` 对应 `product`，两者不能同时传递。该命令不接受 `--version-status` 或 `--version-id`。查询当前生效版本的商品信息时，本命令成功返回后即停止；即使结果包含 `version_id` 或 `version_status`，也不得再调用 `product version list` 进行确认或补查。

用户只提供商品 ID 并泛问商品信息时，若没有明确指定草稿版本、失效版本、过去生效版本、未来生效版本或某个日期/时间点的版本，默认解释为查询当前生效版本，并直接使用 `product get`。不要因为用户没有说“当前生效”就额外调用 `product version list`。

`--action` 是“我的商品”权限过滤条件：只有用户明确要求查询“我的商品”时才传 `--action product_info_read`；其他商品查询不传 `--action`，等价于请求中的 `action=""`。不要仅因为用户说“我的”某个版本或提供了商品 ID 就自动添加该参数，必须有“我的商品”这一查询范围。

返回按 `ProductInfoDTO` 规范化为 `items[]`、`product_info_map` 和 `missing_product_ids`。读取 `items[].product_category_code/name` 与 `items[].product_type_code/name`：

- 类目：`0=默认类别`、`1=系统部`、`2=基础架构`、`3=中台数据`、`4=中台（原业务中台）`、`5=外采商品`、`6=业务商品`、`7=人力商品`、`8=火山引擎`、`9=BytePlus`、`10=小基架 on 火山引擎`
- 定价方式：`1=定价`、`2=摊销`、`3=代持`

常用筛选：

- 标识：`--product-id`、`--product-code`、`--fuzzy-product-name`
- 类型：`--product-type`、`--product-category`、`--product-definition`、`--finance-category`、`--manage-type`
- 层级：`--product-line-id`、`--second-product-line-id`、`--parent-product-id`、`--sub-product-id`
- 状态：`--product-status`、`--is-external`、`--sale-scope`
- 权限与精简：`--action`、`--ignore-parent-info`、`--ignore-member`、`--ignore-introduction`
- 站点与分页：`--site-en-name`、`--site-id`、`--offset`、`--limit`、`--order-by field:asc|desc`

商品状态为 `0=已下架`、`1=已上架`、`2=新建`、`3=下架中`、`4=待上架`、`999=软删除`。未传 `--product-status` 时，CLI 请求体不包含 `product_status`；服务端收到空状态后按 `0/1/2/3/4` 查询，排除软删除和错误态。`--is-external` 使用 `0=未定义`、`1=非外采`、`2=外采`。

站点 ID 为 `BABI=560086`、`VOLCANO=660086`、`BytePlus=660065`。未指定 `--site-id` 时，CLI 会默认发送 `site_id=[560086,660086,660065]`，在这三个站点下查询；用户显式指定 `--site-id` 时以命令行值为准。

按名称或其他宽条件查询时，根据 `pagination.total/limit/offset` 拉取全部分页。多个候选必须展示站点、商品 ID、商品 code 和名称并等待用户确认，不能默认选择第一项。成功空结果只证明当前站点范围和筛选条件下没有匹配商品，不证明其他站点没有该商品，也不代表账单成本为零。

## 查询商品版本记录

仅当用户明确查询商品版本记录、版本元数据，或查询草稿、失效、过去生效、未来生效、指定日期或时间点版本关联的商品信息时，才使用 `product version list`。查询当前生效版本的商品名称、类目、定价方式等商品信息时仍只使用 `product get`；未指定版本范围的泛化商品信息请求也按当前生效版本处理。

查询指定商品的生效版本记录：

```bash
bytedcli babi product version list --product-id <product_id>
```

`product version list` 请求 `POST /v4/product/listProductInfo`，一次只接受一个正整数 `--product-id`。普通 flag 模式下的版本状态规则：

- 未传 `--version-status` 和 `--env`：默认发送 `version_status=[202]`，查询生效版本
- 显式传 `--version-status`：使用命令行值，可选 `100=草稿`、`101=失效`、`202=生效`、`999=软删除`
- 传入 `--env`：自动将 `version_status` 覆盖为 `[100]`，即使同时传入其他 `--version-status` 也以草稿状态为准

草稿类型为 `normal=日常变更`、`month=月度调价`、`half_year=半年调价`、`outer=外采新增计费项`、`budget=预算专用`。例如查询月度草稿：

```bash
bytedcli babi product version list --product-id <product_id> --env month
```

`--only-basic-info` 默认 `true`，可显式传 `--only-basic-info=false`；还可使用 `--valid-time-lower-bound`、`--valid-time-upper-bound`、`--offset` 和 `--limit`。使用 `--data` 原始请求模式时，不会自动补充 `version_status=[202]`、根据 `env` 派生 `[100]`，也不会自动补充 `only_basic_info=true`，需要在 JSON 请求体中明确提供所需字段。

返回的 `items[]` 包含商品基础信息、`version_id`、`version_status/version_status_name`、`env/env_name`、生效时间、创建/修改人与时间以及服务端返回的 `extra`。
