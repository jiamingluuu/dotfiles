# BABI 账号查询

```bash
bytedcli babi account list --fuzzy-name 'demo-business' --limit 100
bytedcli babi account list --account-type goods --status 1 --limit 100
bytedcli babi account list --account-ids <account_id> --account-type goods --limit 100
bytedcli babi account cost-version list \
  --babi-account-id <babi_account_id> \
  --search-begin-time 1767225600000 \
  --search-end-time 1772323200000 \
  --limit 100
bytedcli babi account cost-config list \
  --version-id <version_id> \
  --babi-account-id <babi_account_id> \
  --billing-account-type 1 \
  --limit 100
bytedcli babi account consumer-config list \
  --version-id <version_id> \
  --cost-config-unique-keys cfg-1,cfg-2 \
  --limit 100
bytedcli babi product version list --product-id <product_id>
bytedcli babi account cost-config list \
  --version-id <version_id> \
  --babi-account-id <babi_account_id> \
  --billing-account-type 1 \
  --use-unit-version-id=true \
  --limit 100
```

- `account list` 是分页查询账号信息的接口，请求 `POST /v4/api/account/pageAccountList`，body 使用
  `id_list/fuzzy_name/type_list/status_list/parent_id_list/offset/limit`；输出包含
  `id/name/type/type_name/parent_id/all_parent_ids/entity_id/remark/status/status_name/version_id/is_volcano/belong_second_product_line/source_type/source_type_name/source_code/category/category_name`。
  其中 `type_name` 使用 BABI 账号类型枚举名，`status_name` 使用账号状态枚举名；ID 类字段以字符串
  输出以避免 JSON 数字精度损失。命令只返回候选，不会替用户选择。
- 后端要求显式传 `offset/limit`；CLI 默认发送 `--offset 0` 和 `--limit 100`。
  `--limit` 最大 100，`--offset` 必须大于等于 0。
- `--account-ids` 对应 `id_list`，用于按 BABI 账号 ID 精确筛选，最多 100 个；返回中的
  `entity_id` 是该账号绑定的主体 ID。
- `--fuzzy-name` 对应可选的 `fuzzy_name` 模糊筛选；只按 `--account-ids`、
  `--account-type`、`--status` 或 `--parent-account-ids` 查询时可以不传 `--fuzzy-name`。
- 候选按稳定 ID 排序只用于确定性展示，没有“推荐第一项”的含义。
- `--format json|ndjson|csv|table|pretty` 只改变展示方式，不改变候选集合。

## 成本配置与消费者配置

- `account cost-version list` 请求 `POST /v4/cli_api/account_cost_config/listVersion`，body 使用
  `babi_account_id/search_begin_time/search_end_time/offset/limit`；输出
  `data.version_data_list[].version_id/effect_begin_time/effect_end_time/status`，后端版本数据如果返回
  `origin_version_id`，该字段表示商品版本 ID。当前查询只返回 `status=1` 生效和 `status=-1`
  停用版本；后端版本状态还定义 `0=下线`、`2=草稿`、`3=无效`、`4=草稿废弃`。
- `account cost-config list` 请求 `POST /v4/cli_api/account_cost_config/listConfig`，body 使用
  `version_id/babi_account_id/billing_account_type/billing_account_id/billing_account_name/use_unit_version_id/limit/offset/area_list/bind_type`。
  输出 `data.result[]` 来自后端 `AccountCostConfigForApi`，关键字段包括
  `config_key/babi_account_id/billing_account_type/billing_account_id/bind_type/exclude_billing_account_ids/area_list/bind_rate/share_babi_account_ids/share_babi_account_name_list/share_config_list/share_type/order_option_data/origin_type/origin_babi_account_id/origin_babi_account_name/can_edit/can_delete/cost_type/share_calculation_method`。
- `account consumer-config list` 请求 `POST /v4/cli_api/account_cost_config/listConsumerConfig`，body 使用
  `version_id/billing_account_filters/consumer_account_filters/offset/limit/cost_config_unique_keys`。
  输出 `data.result[]` 来自后端 `ConsumerCostConfig`，关键字段包括
  `version_id/id/cost_config_id/babi_account_id/cost_type/bind_type/external_account_type/external_account_id/external_account_name/area/consumer_account_type/consumer_account_id/consumer_account_name/rate/editor/can_edit/can_delete/create_time/update_time/cost_id/cost_update_time/share_external_account_ids/order_option_data`。
- 成本版本查询必填 `--babi-account-id` 和 `--limit`；`--search-begin-time` 和
  `--search-end-time` 必须同时传或同时省略，时间范围不能超过两个月。
- 后端要求这些查询命令都显式传 `limit` 和 `offset`；CLI 要求用户传 `--limit`，并默认发送
  `--offset 0`。`--limit` 范围 1-1000，`--offset` 必须大于等于 0。
- 成本配置查询必填 `--version-id`、`--babi-account-id`、`--billing-account-type`；账号类型
  `1=服务树节点`、`2=火山账号`、`3=BytePlus`、`4=BABI账号`。消费者配置响应中的
  `external_account_type` 也是成本账号类型，和请求侧 `billing_account_type` 含义一致。
- 成本配置查询的 `--billing-account-id`、`--billing-account-name`、`--use-unit-version-id`、
  `--area-list`、`--bind-type` 都是可选过滤条件。`--use-unit-version-id` 表示把
  `--version-id` 当作商品大版本号 ID 使用，只适用于商品账号版本。
- 消费者配置查询必填 `--version-id`；`--cost-config-unique-keys` 是可选过滤条件，最多 1000 个。
- 消费者配置的成本账号筛选用 `--billing-account-type`、`--billing-account-ids`、
  `--billing-account-name` 拍平传入；消费账号筛选用 `--consumer-account-type`、
  `--consumer-account-ids`、`--consumer-account-name` 拍平传入。
- `account consumer-config list` 只用于代持类商品的代持/消费者配置。沿商品链路查询时，
  必须先用 `product get` 确认 `product_type_code=3` 或 `product_type_name=代持`；
  商品不是代持或无法确认商品类型时，不得调用消费者配置查询。
- 消费者配置查询的 `--version-id` 必须是商品版本 ID。若前置步骤拿到的是
  `account cost-version list` 返回的普通成本关联版本 `version_id`，不能直接传给
  `account consumer-config list`，必须改用同一条版本数据中的 `origin_version_id`；若响应没有
  `origin_version_id`，不得继续查询消费者配置。
- 账号筛选三元组中，只有传入任一账号筛选字段时才会组装 filter；组装 filter 时对应的
  `--billing-account-type` 或 `--consumer-account-type` 必须传。每侧账号 ID 列表最多 1000 个。
- 枚举解释：`bind_type` 为 `1=单一关联`、`2=递归关联`；`cost_type` 为
  `0=上游资源及人力`、`1=自投人力`、`2=外采成本`、`3=上游资源及人力（个人资源）`；
  `origin_type` 为 `1=用户主动配置`、`2=分摊创建`、`3=三方账号主动绑定`、`4=BABI平台`、
  `5=原价收入分摊创建`；`share_type=-1` 为固定比例分摊，`share_type=-2` 为原价收入分摊，
  正数为 Cost Driver ID；`share_calculation_method` 为 `1=默认`、`2=分大区`。

### 串联查询

查询某个账号的成本配置及其消费者分摊时：

1. 先用 `account list --account-ids <account_id> --limit 100` 确认账号类型。若账号类型为商品
   （`type=6` 或 `type_name=GOODS`），主链路是取返回的 `entity_id` 作为商品 ID，转到“从商品账号串联”；
   备选链路仍可继续使用后续成本版本查询，并用版本数据里的 `origin_version_id` 查消费者配置。
2. 若用户未提供成本配置版本 ID，先执行 `account cost-version list --babi-account-id <account_id> --limit <N>`；
   需要按时间定位版本时成对传 `--search-begin-time/--search-end-time`。
3. 从返回的 `data.version_data_list[]` 选择覆盖目标时间且经用户确认或唯一匹配的成本关联版本 ID
   `version_id`；如需查询消费者配置，同时保留同一条版本数据的 `origin_version_id`。
4. 执行
   `account cost-config list --version-id <成本关联版本ID> --use-unit-version-id=false --babi-account-id <account_id> --billing-account-type <type> ...`，
   按 `version_id/babi_account_id/billing_account_type` 拉取成本配置。
5. 从返回的 `data.result[]` 保留稳定配置唯一键 `config_key`。
6. 若需要消费者配置，将这些 key 去重后传给
   `account consumer-config list --version-id <origin_version_id> --cost-config-unique-keys <key,...>`，
   查询消费者配置；这里的 `--version-id` 使用第 3 步版本数据中的 `origin_version_id`，不是
   `version_id`。如果第 3 步响应没有 `origin_version_id`，不得继续调用消费者配置查询。
7. 若成本版本、成本配置或消费者配置分页未取完，先继续翻页；不得只用第一页推断完整分摊关系。

### 从商品账号串联

如果账号候选的 `type=6` 或 `type_name=GOODS`，该账号是商品类型账号；优先使用商品版本链路：

1. 用账号返回的 `entity_id` 作为商品 ID，先调用 `product get --product-id <entity_id>` 确认商品信息和定价方式。
2. 调用 `product version list --product-id <entity_id>` 查询商品版本，选择目标商品版本 `version_id`。
3. 调用
   `account cost-config list --version-id <商品版本ID> --use-unit-version-id=true --babi-account-id <商品账号ID> --billing-account-type <type> ...`。
4. 若商品已确认是代持类，从成本配置结果取 `config_key`，再调用
   `account consumer-config list --version-id <商品版本ID> --cost-config-unique-keys <config_key,...> ...`。
5. 商品不是代持类时，只返回成本配置结果，不调用 `account consumer-config list`。

备选方案：也可以用该商品账号调用 `account cost-version list` 查询成本关联版本。此时成本配置查询使用
普通成本关联 `version_id`，消费者配置查询必须使用同条版本数据的 `origin_version_id`。
如果成本配置查询返回 `use_unit_version_id conflicts with account type`，暂时切回商品版本口径：
用 `origin_version_id` 或重新查询 `product version list` 得到的商品版本 ID 作为 `--version-id`，
并传 `--use-unit-version-id=true` 重试 `account cost-config list`。

### 从商品版本串联

如果先调用 `product version list` 得到商品 `version_id`，该值是商品大版本号 ID。继续查询成本关联时：

1. 先用 `product get --product-id <product_id>` 确认商品定价方式。只有
   `product_type_code=3` 或 `product_type_name=代持` 时，才允许继续查消费者配置。
2. 调用 `account cost-config list --version-id <商品版本ID> --use-unit-version-id=true ...`。
3. 若商品已确认是代持类，从成本配置结果取 `config_key`，再调用
   `account consumer-config list --version-id <商品版本ID> --cost-config-unique-keys <config_key,...> ...`。
4. 商品不是代持类时，只返回成本配置结果，不调用 `account consumer-config list`。
5. 这条链路中 `account cost-config list` 必须传 `--use-unit-version-id=true`；否则后端会把
   `--version-id` 当作普通成本配置版本 ID。

### 从成本版本串联

如果先调用 `account cost-version list` 得到成本关联 `version_id`，该值已经是普通成本配置版本 ID。
继续查询成本关联时：

1. 调用 `account cost-config list --version-id <version_id> --use-unit-version-id=false ...`。
2. 从成本配置结果取 `config_key`，再调用
   `account consumer-config list --version-id <origin_version_id> --cost-config-unique-keys <config_key,...> ...`。
   这里的 `origin_version_id` 必须来自同一条成本版本数据，不能用普通成本关联 `version_id` 代替。
3. 若第 1 步返回 `use_unit_version_id conflicts with account type`，暂时使用商品版本 ID
   作为 `--version-id` 并传 `--use-unit-version-id=true` 重试成本配置查询。
4. 常规情况下为避免和商品大版本链路混淆，成本版本链路显式传 `--use-unit-version-id=false`。

## 账号详情边界

本指南当前只覆盖账号候选列表、按 account_id 过滤列表、成本配置和消费者配置查询，不覆盖
独立账号详情命令。

- 用户只提供 `account_id` 时，调用 `account list --account-ids <id> --limit 100` 查询账号候选和
  `entity_id`；不要编造账号名称、层级、绑定主体或商品映射。
- 成本账单中的 `provider_l5_account_id` 不能直接当作 `product_id`；先用
  `account list --account-ids <provider_l5_account_id> --account-type goods --limit 100`
  查询对应账号，再用返回的 `entity_id` 作为后续稳定映射证据。
- 需要商品详情时，必须使用用户提供或 `account list` 等已验证来源给出的稳定 ID 调用
  [babi-product 指南](../../babi-product/GUIDE.md)。
