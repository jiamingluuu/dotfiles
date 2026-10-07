# 预算预实 Dashboard 模板

此目录存放 `babi-finops` 预实分析 HTML 报告的固定模板资产，版本为 `2026-09-03-cd-empty-v8`。
真源是 babi-cli 仓库中的 `skills/babi-finops/templates/budget-dashboard/`，随完整 FinOps
Skill 或宿主指南发布。使用者通过更新对应 Skill 或宿主指南获取模板，
不要从历史部署取回模板或单独覆盖生成副本。

ECharts、CSS 和 JavaScript 已内联；页面通过 HTTP 加载相对路径 `data/*.json`，没有包外 CDN
依赖。HTML 默认本地文件交付，本地预览仅使用绑定 `127.0.0.1` 的静态服务；额外提供
办公网查看链接时遵循[页面部署](../../references/budget-variance-report.md#页面部署)。没有链接不影响本地报告完成。

- `index.html`：交互式单页 dashboard 模板。单预算单元报告支持通过 `?data=<file_stem>` 或 `?data=<file_name>.json` 加载 `data/` 目录下的数据文件；多预算单元报告通过顶部预算单元筛选框加载各单元数据，支持单选切换和多选聚合。页面筛选区固定包含子预算单元、1级供给方、供给方商品、组合计费单元、售卖区域等多选筛选项，其中 1级供给方 默认“全部”，并从 `productRows.providerLevel1` 真实去重生成候选。
- `data/demo_mock_prototype.json`：仅用于说明模板数据结构和本地样式预览，正式预实分析报告禁止使用该文件作为交付数据。

执行预实分析时，Agent 必须把本目录复制到本次报告输出子目录，并在复制后的 `data/` 目录为每个预算单元写入 `{budget_source_id}_{timestamp}_{user_tag}.json` 真实数据文件。

- 单预算单元：本地预览或可选办公网查看 URL 使用 `?data=` 指向唯一真实数据文件；文件交付仍保留完整目录。
- 多预算单元：同一次任务只生成一个 `index.html`，在模板预算单元元数据中登记全部稳定 ID、名称和唯一数据文件；本地预览或可选办公网查看使用不带 `?data=` 的统一页面 URL，顶部筛选框必须支持在这些单元间切换和多选聚合。除非用户明确要求分别生成，否则禁止按预算单元拆成多个 HTML。
