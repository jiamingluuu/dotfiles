# TEA 看板有数据，但独立事件分析页参数为空或日期不一致

TEA 同时保存可执行的 `content` / `periods` 和恢复前端编辑器的 `show_option`；只有前者不代表报表可完整编辑。

- `tea report create` / `tea report update` 会为没有 `show_option` 的普通事件分析 DSL 生成 UI 配置，保持核心查询不变。支持原始事件 PV/UV、PCT（例如 P90）、基础属性过滤、相同属性分组、四则公式、UTC+8 相对天数和固定时间戳窗口。不支持的最小 DSL 会在写入前报错，要求使用 UI 模板，而不是静默丢弃配置。
- CLI 生成的 `show_option` 带 `__bytedcli_generated: 1`；再次提交时按核心 DSL 重建指标、筛选、分组和日期，保留其他展示字段。已有 UI 创建的完整元数据原样保留；修改这种模板时仍须同步两层配置，不能只改 `content`。
- “7 天前到今天”对应 `7 day -> 0 day`、`shortcut: custom`、结束端 `amount: 0, tab: 4`。`past_7_day` 快捷项或 `tab: 3` 可能使 UI 排除今天。不要只根据 `timestamp` 判断相对日期语义。
- 升级 CLI 不会自动改写历史报表。对以前的最小 DSL，显式执行 `report get --dsl-only` 后用 `report update` 回填；高级分析用同项目、结构相近的 UI 报表模板，并保留其完整 `show_option`。
- 验收应打开 `/event-analysis/<report-id>`。`/event-analysis/result/<snapshot-id>` 是不可变查询快照，刷新旧快照不能验证报表更新。分别核对看板、独立页参数、日期和重新查询结果。
- 工具集合、task、成功率分母等业务口径仍由调用方明确配置；CLI 不会自动添加业务工具或修改统计口径。
