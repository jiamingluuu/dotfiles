# 商品折扣与溢价

```bash
bytedcli babi product discount-premium list --product-id <product_id>
```

按时间、类型和目标筛选：

```bash
bytedcli babi product discount-premium list \
  --product-id <product_id> \
  --search-begin-time 1704038400000 \
  --search-end-time 1715788800000 \
  --discount-type 1,2 \
  --dimension charge_item \
  --target-type service_tree
```

命令请求 `POST /v4/product/listProductDiscountTicketDetails`。`discount_type` 为 `1=折扣`、`2=溢价`；`dimension` 为 `product`、`charge_item` 或 `region`；目标类型为 `babi_account` 或 `service_tree`。输出额外补充对应的 `*_name`，包括原价计价方式与折溢价方式，原始编码仍保留。

用户指定生效日、时间点或时间范围时，必须把时间条件下推到后端：同时传入 `--search-begin-time` 和 `--search-end-time`，不得省略后先查全量再只在本地按返回记录筛选。自然日按用户指定时区取 `00:00:00.000` 至 `23:59:59.999`；未指定时区时使用 `Asia/Shanghai` 并向用户说明。例如 `2026-02-15` 对应 `1771084800000` 至 `1771171199999`。最终只回答用户需要的时间字段；若主动换算返回记录的 `begin_time`、`end_time` 或 `offline_time`，必须沿用同一时区并确保日期准确，不确定时保留原始毫秒值。

单据追踪使用服务端返回的 `ticket_id`、`process_instance_id`、`operator`、`ticket_status` 与时间字段。当前接口没有承诺直接返回文档链接，因此不要根据 ID 拼接 URL，也不要复用旧 Skill 中未实现的占位接口。
