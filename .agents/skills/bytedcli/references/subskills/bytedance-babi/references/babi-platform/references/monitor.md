# BABI Platform 监控命令

## 查询监控任务列表

```bash
bytedcli babi platform monitor list \
  --entity-ids <entity_id> \
  --entity-types product \
  --monitor-item-keys report_measure_failed \
  --status 1 \
  --page-size 100 \
  --current-page 1 \
  --format json
```

- 该命令查询监控任务配置，响应读取 `data.monitor_jobs[]` 和 `data.pagination`；不要与 `platform monitor alarm list` 的报警记录混淆。
- 可用 `--keyword`、`--ids`、`--job-types`、`--alarm-methods`、`--receivers`、`--entity-types`、`--entity-ids`、`--monitor-item-keys` 和 `--status` 组合过滤。
- `current-page` 默认 1，`page-size` 默认 10、范围 1–1000。需要完整任务清单时持续翻页，直到覆盖 `data.pagination.total`。

## 开启或关闭监控任务

```bash
# 先预览请求；不要在预览阶段执行写入
bytedcli babi platform monitor status \
  --id <resource_id> \
  --disable true \
  --confirm-write \
  --dry-run

# 关闭任务：取得本次具体写入授权后执行
bytedcli babi platform monitor status \
  --id <resource_id> \
  --disable true \
  --confirm-write \
  --format json
```

- `--disable true` 关闭监控任务，`--disable false` 开启监控任务。
- 请求调用 `/v4/platform/monitor/job/status`，body 为 `{ "disable": <boolean>, "id": <number> }`，并携带 `domain: babi;v1`。
- 这是受控写命令，必须使用 `--confirm-write`；该 flag 不能替代用户对本次具体操作的授权。

## 查询报警列表

```bash
bytedcli babi platform monitor alarm list \
  --entity-ids <entity_id> \
  --entity-types product \
  --monitor-item-keys report_measure_failed,report_measure_delay,report_measure_number \
  --start-bill-time 1780588800000 \
  --end-bill-time 1780934400000 \
  --page 1 \
  --size 1000 \
  --format json
```

- `entity_ids` 是稳定监控对象 ID；商品场景使用 Product ID。
- `entity_types` 常用 `product`。
- 对“本月”等自然语言时间，先确认时区和完整自然月/月初至今口径，再转换为毫秒级时间；`start_bill_time` 为闭区间，`end_bill_time` 为开区间。
- “推量失败”的直接证据是 `report_measure_failed`；`report_measure_delay`、`report_measure_number` 和 `measure` 只是相邻信号，不能单独定性为推量失败。
- `page` 默认 1，`size` 默认 10、范围 1–1000。需要完整证据时持续翻页，直到累计记录覆盖 `data.total`，不要只读取第一页。
- 响应主要读取 `data.alarm_records[]` 和 `data.total/page/size`，并保留报警、任务和实体 ID。自动化处理统一使用 `--format json`。

## 查询报警详情

```bash
bytedcli babi platform monitor alarm get \
  --entity-ids <entity_id> \
  --entity-type product \
  --alarm-id <alarm_id>
```

详情通过 `alarm_id` 和实体范围收敛。不要只凭关键词选择报警：若列表返回多条直接相关记录，应逐个查询其 `alarm_id`；若用户只要某个子集，先按账期、状态或任务 ID 明确收敛条件，不能静默只选最新一条。

## 查询商品计量负责人

```bash
bytedcli babi platform monitor measure_owner get --product-ids <product_id>
```

命令按以下顺序选择存在接收人的监控任务：`report_measure_delay` → `report_measure_failed` → `report_measure_number` → `measure` → `cost_goods_add` → `cost_goods_reduce`；均无接收人时回退到 `income`。输出同时包含选中的监控任务、接收人、优先级和是否 fallback，不要只截取邮箱而丢失来源。

## 证据解释

- 报警命中：可作为数据完整性或计量链路异常证据，但仍要与 Bill/Insight 的时间和商品范围对齐。需要继续判断业务影响时，转交 [babi-finops 指南](../../babi-finops/GUIDE.md) 做完整归因；其账单和 Insight 数据查询再由 [babi-bill 指南](../../babi-bill/GUIDE.md) 承担。
- 报警未命中：只能说明当前查询口径未返回报警，不能证明没有业务异常。
- 负责人：来自监控任务配置，不等于最终业务责任认定；需要时交给 [babi-finops 指南](../../babi-finops/GUIDE.md) 解析 Lark mention 并纳入归因工单。
