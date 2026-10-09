---
name: bytedance-aeolus
description: "Use exact bytedcli Aeolus commands/flags/region/auth for BI reports, charts, dashboards and datasets; fields/models, computed fields, XLSX field import/export, SQL/visual queries, chart styles/filters, Query Editor files/folders/templates/temp tables/tasks, Shuttle compliance queries, and 看板/数据集移动归类. Existing dashboard edits (live sheet re-anchor, smallest change, page validation, 字段加到表格, TopN, 筛选项/联动) require references/dashboard-development.md first."
---

# bytedcli Aeolus (Data Analytics Platform)

精确命令入口。改已有看板时先读 [references/dashboard-development.md](references/dashboard-development.md)，再按当前步骤读取所需命令 reference。纯查询/命令任务只读对应命令分支。

## 如何调用

先全局安装，之后直接调用 `bytedcli`。不要把 `npx -y @bytedance-dev/bytedcli@latest` 写进日常命令。

```bash
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

通用前缀、`--json` 位置和网络 profile 见 [../../invocation.md](../../invocation.md)。下面示例直接写 `bytedcli`。

## 何时加载

修改已有看板中的组件、筛选联动、布局或验证其页面时，先读 dashboard-development，再按当前步骤读取命令分支。独立 report / chart 任务直接读取对应命令分支。

示例 URL 写成 `$AEOLUS_REPORT_URL` / `$AEOLUS_DASHBOARD_URL`。`$AEOLUS_DATASET_ID` 取自目标数据集。不要编造 host，不要把真实资源 ID 写进文档。

## 按分支读取

先判断任务分支。改已有看板时读 dashboard-development，再按当前步骤读取所需命令 reference。纯命令任务只读对应命令分支。不要预加载全部文件，不要再打开已拆走的长文。

| 任务 | 读取 |
|---|---|
| 改已有看板：回锚线上对象、最小改动、页面验收 | [references/dashboard-development.md](references/dashboard-development.md)，再按下表命令分支 |
| report / chart / style / dimMet / 单图 query | [references/report-chart.md](references/report-chart.md) |
| dashboard 查询、筛选、diff、下载、folder/move、sheet 更新 | [references/dashboard.md](references/dashboard.md) |
| dataset 字段、模型、Join、同步/回刷、SQL、viz-query | [references/dataset.md](references/dataset.md) |
| Query Editor 文件/模板/临时表/任务 | [references/query-editor.md](references/query-editor.md) |
| Shuttle / TTP / DECC 合规取数 | [references/shuttle.md](references/shuttle.md) |
| 调用前缀、`--json`、prod 网络 | [../../invocation.md](../../invocation.md) |
| 版本过期、常见错误、排障 | [../../troubleshooting.md](../../troubleshooting.md) |

`chart get` 已提供所需 dimMet 或样式时，不要再 `report resolve`。字段发现、查询构造或验证需要补充信息时，按需读取 dataset 字段/模型或筛选元数据；已有结果足够时跳过重复调用。

命令索引（细节在对应 reference，不在本文件展开）：

- Report/Chart：`resolve-report`、`report resolve|query|download|create|style`、`chart get|query`、`report filters`、`filter options`
- Dashboard：`list-authorized`、`resource recent|search`、`dashboard query|filters|diff|download|update|folder|move`
- Dataset：`dataset-fields`、`dataset-dim-met-map`、`dataset-fields-download|upload`、`dataset-model-info`、`dataset-create`、`dataset-update-sql|fields`、`dataset-add-source-table|fields`、`dataset-remove-fields`、`dataset-draft get|publish`、`dataset-sync`、`dataset-delete|restore`、`dataset-folder`、`dataset-move`、`query`、`viz-query`
- Query Editor：`query-editor folder|file|template|tmp-table|query|task|login|whoami|queues|datasources`
- Shuttle：`shuttle project|template|queue|task`

## 安全规则

1. 默认串行调用 `bytedcli aeolus`。不要用并行 tool call、后台 shell 或 batch runner 同时打共享远端状态。查询、Query Editor、任务提交和 dataset/report/dashboard 写入尤其如此。
2. Dataset / report API 必须带 `-r/--region`。Query Editor 默认 `cn`，跨区显式传 `-r`。
3. 写操作先 dry-run / 预览，用户确认同一 payload 后再 `--yes`。响应不明确时先回读，禁止盲目重试。
4. Dataset / report / dashboard / chart 在生产网且存在 `SEC_TOKEN_STRING` / `SEC_TOKEN_PATH` 时，先按 region 映射的 ByteCloud site 做 ZTI→个人 JWT，再换 Titan Passport。ZTI 交换本身不可用（`AUTH_REQUIRED`）时回退 `bytedcli auth login`；已经换到 ZTI JWT 后被 Titan/Aeolus 拒绝，不再回退 SSO。办公网仍只走 SSO。Dataset API 可选用 `~/.bytedcli/.aeolus.env` 或 `./.aeolus.env` 的 ClientID/ClientSecret。`dataset-dim-met-map` 只用环境变量 `BYTEDCLI_AEOLUS_OPEN_API_TOKEN`，不要把 token 写进 argv。Query Editor 不继承这条 ZTI 链路，也不走 ClientID；`euttp` / `euttp2` / `usttpusts` / `eupipo` 的登录表在 query-editor 分支。
5. 逻辑数据集名或 dataset ID 当表名常失败。`SELECT * LIMIT 1` 只返回 `dummy` 不代表不可用。先读 dataset 分支再查物理表。
6. `--json` 放在 domain 之前。不确定参数时先 `--help`，不要猜。
7. 排障先读 [../../troubleshooting.md](../../troubleshooting.md)。调用失败只证明本次失败，不等于平台不支持。

## 选命令，不要叠调用

- 已有图的展示或样式：`chart get` → `report style`。`chart get` 已含 dimMet/轴/图例时不要 `report resolve`。
- 只用已有字段改查询：先读 `chart get`；字段或语义不完整时，按 dataset 分支读取字段与模型，再用 `report query` 验证。
- 数据集字段/模型查询，以及计算字段、Join、同步或回刷：读 dataset 分支。`viz-query` 走 Dataset API cookie，不是 Query Editor session。
- 临时 SQL 且不依赖 Shuttle project/template/DECC：Query Editor。`hrbimycis` 只用 `viz-query`。
- 需要 Shuttle project、模板、YARN 队列、TTP/DECC 或多日 BATCH：先读 shuttle 分支。`-r va` 只表示 Shuttle 控制面，不表示任务数据在 VA。
- Query Editor CH 默认由平台自动选集群；`--cluster-name automatically` 是同义入口。自动模式省略请求体 `cluster_name` 和未显式指定的 `region`，`--ch-region` 显式值仍保留。EU GCP 使用 `-r euttp`，不跨站点回退；`query-editor queues` 是 Hive YARN 队列，不是 CH 集群列表。失败或状态不明时先读已有任务状态，不重复提交 SQL（仅明确 401 保留一次同站点认证重试）。

## 鉴权摘要

| 面 | 默认 | 例外 |
|---|---|---|
| Dataset / report / dashboard / chart | 生产网有 ZTI 时先换个人 JWT；仅交换不可用时回退 `bytedcli auth login` | 可选 ClientID/ClientSecret；`dataset-dim-met-map` 用 Open API token |
| Query Editor | `bytedcli auth login` | 不继承普通 API 的 ZTI opt-in；不支持 ClientID；合规站点见 query-editor |
| Shuttle 控制面 | `--site` + `-r va` | 任务数据区域来自 template `infos`，不是 `-r` |

环境变量名、issuer 和失败码只写在对应 reference，不要在本文件复制。

## Regions

Dataset / report API 默认域名与 `src/api/aeolus/site.ts` 一致。控制台入口可能因租户不同而异。

| Region | Description | Default API host |
|---|---|---|
| `cn` | China | `https://data.bytedance.net` |
| `sg` | Singapore (TikTok row) | `https://aeolus-sg.tiktok-row.net` |
| `va` | US East (TikTok row) | `https://aeolus-va.tiktok-row.net` |
| `euttp` | EU-TTP / EU Compliance (GCP) | `https://aeolus-eu-ttp.tiktok-eu.net` (office); `https://aeolus-eu-ttp.bytedance.net` (prod). Override: `BYTEDCLI_AEOLUS_EUTTP_ORIGIN` |
| `euttp2` | EU-TTP2 / NO1A (`eu-ttp2` / `no1a`) | `https://aeolus-no.tiktok-eu.net`. Override: `BYTEDCLI_AEOLUS_EUTTP2_ORIGIN` |
| `eupipo` | EU PIPO / IE2 | `https://aeolus-clover-pipo.tiktok-eu.net` |
| `mycis` | MYCIS | `https://aeolus-mycis.byteintl.net` |
| `jplark` | Japan Lark | `https://aeolus-jp-lark.bytedance.net` |
| `hrbimycis` | HRBI MYCIS (`hrbi_mycis` / `hrbi-mycis`) | `https://people-aeolus.byteintl.net` |
| `mybd` | MYBD | `https://aeolus-mybd.sinf.net` |
| `sglark` | Singapore Lark | `https://aeolus-sglark.bytedance.net` |
| `uspipo` | US PIPO | `https://aeolus-uspipo.byteintl.net` |
| `usttpusts` | US TTP USTS | `https://aeolus-tx.tiktok-usts.net` |
| `usbd` | US ByteDance | `https://aeolus-usbd.byteintl.net` |

- `jplark` 用 CN ByteCloud session（host 在 `bytedance.net` 下）；Coral/Hive/Manta 的 `jplark` 用 DataLeap `i18n-bd` session（`dataleap-jp.byteintl.net`）。
- `mycis` / `jplark` / `uspipo` 即使换到 Titan Passport 也可能还需要 Aeolus 产品侧 cookie bootstrap：`mycis` / `uspipo` 跑 `bytedcli --site i18n-bd auth login --session --auto --yes`，`jplark` 跑 `bytedcli --site cn auth login --session --auto --yes`。
- `eupipo` 用 `--site eu-ttp` + Clover/PIPO host + host 专属 `do-pipo.tiktok-eu.net` Titan issuer；缺产品登录时跑一次 `bytedcli --site eu-ttp auth login --session --auto --yes`。

VA / 生产开发机上，调 i18n-tt / i18n-bd / sg 前先 `export BYTEDCLI_NETWORK_PROFILE=prod`。办公网跳过。

## 最短例子

```bash
bytedcli aeolus list-authorized -r va --limit 20
bytedcli aeolus chart get --url "$AEOLUS_REPORT_URL"
bytedcli aeolus dashboard query --url "$AEOLUS_DASHBOARD_URL"
bytedcli aeolus dataset-fields -r va "$AEOLUS_DATASET_ID"

# Query Editor 即席查数（支持 --output <file> 或 --feishu）
bytedcli aeolus query-editor query one -r cn --sql "SELECT 1" --queue root.default
```

更多参数、鉴权变体和失败签名只在对应 reference。需要 Shuttle 时先读 shuttle 分支，再决定要不要读 dataset/query-editor。

展示改图的命令参数（例如双轴的柱状总量、折线成功率）见 [references/report-chart.md](references/report-chart.md)。

预期远程调用链：

1. `chart get` 读现有轴、图例和已有字段。
2. `report style` dry-run 看双轴 payload。
3. 同一 payload 加 `--yes` 写一次。
4. 回读样式并检查对应图表页面；图表属于已有看板时，按 [references/dashboard-development.md](references/dashboard-development.md) 验证对应组件。

不要叠 `report resolve`、`dataset-model-info`、Hive/Dorado 或全量 `dashboard filters`。

Markdown 多行参数必须用 `$'...'` 写换行，不要写成 `"...\n..."`：bash/zsh 双引号不会解释 `\n`。

## 文档维护与同步

- 已有看板的对象定位、最小改动和页面验收在 [references/dashboard-development.md](references/dashboard-development.md)。命令 flag 在对应命令分支。
- 总路由 `bytedcli` skill 的 Aeolus 入口仍指向本 skill。改本文件后必须跑 `npm run build:assets`，不要手改 `skills/bytedcli/references/subskills/bytedance-aeolus/GUIDE.md`。
- 安装副本在 `bytedcli self skill update -g` 或 npm 发版同步后才会替换 `~/.agents/skills/bytedance-aeolus/`。

## Notes

- Use `--json` for structured JSON output (global option before subcommand)
- **Region (`-r`) is required** for Dataset API commands
- Dataset ID / App ID 来自 `list-authorized`；分区字段标在 `dataset-fields`
- `dataset-fields`、`dataset-model-info` 和 `query` 只用于 `data_set`，不能打 dashboard
- Query Editor 默认 `cn`；`hrbimycis` 只用 `viz-query`，不要走 Query Editor
- `dashboard create|build|update` 和 `report create|update` 的 payload 字段在 dashboard / report-chart 分支，不要从本文件猜

## References

- [references/dashboard-development.md](references/dashboard-development.md)
- [references/report-chart.md](references/report-chart.md)
- [references/dashboard.md](references/dashboard.md)
- [references/dataset.md](references/dataset.md)
- [references/query-editor.md](references/query-editor.md)
- [references/shuttle.md](references/shuttle.md)
- [../../invocation.md](../../invocation.md)
- [../../troubleshooting.md](../../troubleshooting.md)
- [references/aeolus.md](references/aeolus.md)（薄索引，指向以上分支；不要当作命令正文）
