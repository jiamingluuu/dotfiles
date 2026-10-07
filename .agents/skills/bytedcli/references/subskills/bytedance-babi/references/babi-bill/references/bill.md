# BABI 账单查询

## 成本与用量

```bash
bytedcli babi bill cost list \
  --begin-date 1780243200000 --end-date 1782835199000 \
  --consumer-type 1 --consumer-ids <consumer_id> \
  --amount-type 0 --group-keys dynamic_date,provider_l2_account_id,unit_price \
  --settlement-type "<resolved-settlement-type>" --time-span 2 \
  --filter '{"key":"unit_price","operator":5,"value":["1.5"]}' \
  --page-size 100
```

- `--consumer-type`：`1` 账号、`2` 团队、`3` 服务树。
- 按业务名输入时先通过 [babi-account 指南](../../babi-account/GUIDE.md) 解析账号；按团队名输入时使用 [babi-finops 指南](../../babi-finops/GUIDE.md) 的 `finops team search`。
- 查询单位成本时，`--group-keys` 包含 `cost_driver_type`；`cost_driver_value` 是指标值，`cost_driver_name` 是展示名称。
- 使用 `--cost-driver-types 1,2` 按 CD 类型筛选；不传则不按 CD 类型筛选。

响应保留 `status_code`、`status_msg`；`data.items` 包含 `bill_amount`、`date`、`area`、`region`、`flavor`、`billing_account_id`（服务树 ID）、`product_id`、`provider_l1_account_id` 至 `provider_l6_account_id`、`customer`、`cost_driver_name`、`cost_driver_value`、`unit_price`、`un_discount_unit_price`、`un_discount_unit_price_interval`、`charge_item`、`measure_function`、`count_unit`、`unit` 和 `count`；分页位于 `data.pagination`。

### 多主体保留主体维度

`consumer_ids` 一次传入多个主体时，后端会按 `group_keys` 聚合。要保留输入主体维度，应在
同一次查询中加入与主体类型对应的业务分组，不要拆成多个单主体请求：

- `consumer_type=1`（BABI 账号）：先用 `account list --account-ids <consumer_id,...> --limit <N>`
  批量补查账号层级，能确认同一层级时加入对应的 `customer_lN_account_id`。输入账号层级混合、
  自定义账号无法稳定映射到单层或层级仍不确定时，同时加入六级消费方账号 ID；不要编造账号名称或层级。
- `consumer_type=3`（服务树）：加入公开分组 key `billing_account_id`；该 key 在成本查询
  后端内部映射到 `service_tree_node_id`。命令参数不要传内部字段名
  `service_tree_node_id`。
- `provider_l1_account_id` 至 `provider_l6_account_id` 表示卖方成本来源，不能用于区分
  输入的消费主体。

账号层级名称不作为账单分组字段猜测。查询返回消费方账号 ID 后，需要名称或层级时使用
`account list --account-ids <account_id,...> --limit <N>` 批量补齐；服务树名称使用已解析的
ByteTree 节点信息。

CLI 现已把消费方 `customer_l1_account_id` 至 `customer_l6_account_id` 作为 cost/income 的
公共分组与过滤 key。若后端返回 `status_code=10201006` / `invalid group_key value`，表示目标
环境尚未部署该分组能力；保留 LogID 并按
[业务排障](business-troubleshooting.md)降级，禁止把未分组的聚合结果描述为逐主体结果。

## 卖方收入

```bash
bytedcli babi bill income list \
  --begin-date 1780243200000 --end-date 1782835199000 \
  --provider-account-ids <provider_account_id> \
  --amount-type 0 --group-keys dynamic_date,customer_l2_account_id \
  --settlement-type "<resolved-settlement-type>" --time-span 2 \
  --filter '{"key":"charge_item","value":["storage"]}'
```

`GetBillIncomeReq` 没有生效的 `provider_type` 字段，因此收入命令只接收 `--provider-account-ids`。响应保留 `status_code`、`status_msg`；`data.items` 包含 `income_amount`、`date`、`area`、`region`、`flavor`、`billing_account_id`（服务树 ID）、`customer_l1_account_id` 至 `customer_l6_account_id`、`unit_price`、`un_discount_unit_price`、`un_discount_unit_price_interval`、`charge_item`、`measure_function`、`count_unit`、`unit` 和 `count`；分页位于 `data.pagination`。

## 公共枚举与复杂参数

CLI 的 `--group-keys` 对应请求字段 `group_keys`（也常被口头称为 groupBy）。选择分组或过滤字段前，必须先查看[分组与过滤字段中文映射](semantics.md)；表中逐项说明了中文业务含义、cost/income 可用范围和能否作为 `filter.key`，不要只根据英文 key 猜测。

- `--amount-type`：`0` 总金额、`1` 纯资源金额、`2` 纯人力金额。
- `--time-span`：`1` 日、`2` 月、`3` 季度。
- `--settlement-type`：`1` 日正式+日预估、`2` 日正式+月正式、`3` 日正式+月组合、`4` 日正式、`5` 月正式。
- `--true-up`：`0` 不包含、`1` 包含；`--currency` 支持 `CNY`、`USD`。
- cost / income 共同支持的 `--group-keys`：`dynamic_date`、`area`、`region`、`flavor`、`billing_account_id`、卖方层级 `provider_l1_account_id` 至 `provider_l6_account_id`、消费方层级 `customer_l1_account_id` 至 `customer_l6_account_id`、`unit_price`、`un_discount_unit_price`、`un_discount_unit_price_interval`、`charge_item`、`measure_function`、`count_unit`、`unit`。卖方与消费方层级现为公共分组维度，cost 与 income 均可用。
- cost 额外支持：`product_id`、`customer`、`cost_driver_type`；income 不接受 CD 分组。
- `--area-region-list` 和 `--product-flavor-list` 接受 JSON 数组；`--billing-account-info` 接受 JSON 对象。具体结构可直接查看命令 `--help`。

## 扩展过滤树

`--filter` 接受一个 JSON 对象，字段名固定使用蛇形小写：`relation`、`key`、`operator`、`value`、`children`。叶子节点填写 `key/operator/value`，分组节点填写 `relation/children`；`relation=1` 表示 AND，`relation=2` 表示 OR。

`filter.key` 的逐项中文含义、cost/income 白名单和 `operator=1..24` 的中文含义见[分组与过滤字段中文映射及过滤操作符中文映射](semantics.md)。

- cost / income 共同的过滤 key：卖方层级 `provider_l1_account_id` 至 `provider_l6_account_id`、消费方层级 `customer_l1_account_id` 至 `customer_l6_account_id`，以及 `unit_price`、`un_discount_unit_price`、`un_discount_unit_price_interval`、`charge_item`、`measure_function`、`count_unit`、`unit`。卖方与消费方层级现为公共过滤 key，cost 与 income 均可用。
- `operator` 省略时后端按 `IN(8)` 处理；支持 `1=EQ`、`2=NE`、`3=GT`、`4=LT`、`5=GE`、`6=LE`、`7=GT_OR_LT`、`8=IN`、`9=NOT_IN`、`10=IS_NULL`、`11=IS_NOT_NULL`、`12=LIKE`、`13=LEFT_LIKE`、`14=RIGHT_LIKE`、`15=NOT_LIKE`、`16=RECURSIVE_LIKE`、`17=APPLY`、`18=MAP`、`19=CURRENT_NODE_ONLY`、`20=CHILD_NODES_ONLY`、`21=ABS_LE`、`22=ABS_GE`、`23=ABS_LT`、`24=ABS_GT`。`IS_NULL` / `IS_NOT_NULL` 可省略 `value`，其他 operator 必须传字符串数组。

嵌套示例：

```bash
bytedcli babi bill cost list <其他必填 flags> \
  --filter '{"relation":2,"children":[{"key":"provider_l3_account_id","value":["<provider_l3_account_id>"]},{"key":"unit_price","operator":5,"value":["1.5"]}]}'
```

两个请求的 `--begin-date`、`--end-date` 都是毫秒时间戳字符串，账期边界必须按
`Asia/Shanghai` 换算：自然月从首日 `00:00:00` 到末日 `23:59:59`。真实请求前先核对换算后的
本地日期与目标账期一致；禁止先用 UTC 零点试查、再根据跨月结果重复请求。ID 和聚合维度支持
逗号分隔。旧脚本仍可使用 `--data` 传完整 JSON；同时传显式 flags 时，flags 覆盖 `--data` 中的
同名字段。BFF headers 与 Thrift `Base` 由宿主 Runtime 管理，不开放为业务 flag。

### 用户未指定结算类型

成本和收入使用同一套封账判断，CLI 的 `--settlement-type` 仍是必填参数，由 Agent 在发起账单请求前解析：

1. 在 `Asia/Shanghai` 下取 `--end-date` 所在月，作为查询范围覆盖的最后一个账期月。
2. 计算该账期月的下一个自然月，传该月任意一天的毫秒时间戳执行：

   ```bash
   bytedcli babi bill calendar workday check \
     --month "<next-month-millis>" --nth 5 --format json
   ```

3. 这条命令必须与后续账单查询分开执行。先检查其完整输出，再以字面量 `--settlement-type 1|2` 构造账单命令；不得用一条复合 shell 命令完成检查、解析和查询。
4. `check` 返回扁平 JSON，`is_after_nth_workday` 位于顶层，不在 `data` 下。例如：

   ```json
   {
     "boundary": 1784131199999,
     "is_after_nth_workday": true,
     "month": 1782835200000,
     "nth": 5,
     "nth_workday": 1784044800000,
     "timezone": "Asia/Shanghai",
     "workday_count": 5
   }
   ```

5. `is_after_nth_workday=true`（即顶层字段明确为 JSON boolean `true`）时，最后账期月才视为已封账，使用 `--settlement-type 2`；`is_after_nth_workday=false` 时使用 `--settlement-type 1`。第 5 个工作日当天尚未越过当天 `23:59:59.999` 边界，因此仍是 `false`。
6. 字段缺失、值不是 JSON boolean 或响应无法解析时，属于封账检查失败而不是 `false`。立即终止，不执行成本或收入查询，并向用户说明无法确认封账状态；不得猜测金额或根据“月份已经结束”推断“已经结算完成”。

例如查询 2026 年 7 月账期时，应检查 2026 年 8 月的第 5 个工作日。即使已经进入 8 月，只要仍处于第 5 个工作日当天，就不能声称“2026 年 7 月已经结算完成”。

成本和收入请求使用固定 `domain: BABI_BILL;v1`，由 Command 注入；JWT 由宿主 Runtime 注入，不要写入参数或请求体。查询无结果时区分后端空数据与参数/权限错误，并保留输出中的 `logId` / `RequestId`。

## 工作日日历

```bash
bytedcli babi bill calendar workday list --month 1782864000000
bytedcli babi bill calendar workday check --month 1782864000000 --nth 5
```

`--month` 是目标月份任意一天的毫秒时间戳。`check` 默认判断当前时刻，也可传 `--now`；第 N 个工作日的结束边界固定为 `Asia/Shanghai` 当天 23:59:59.999。机器读取时必须使用 `--format json`，并按上文的顶层布尔字段契约处理。
