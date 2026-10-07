---
name: bytedance-watchdog
description: "Call RPC/DB in US-TTP and EU-TTP compliance regions through Watchdog Diag and assert whether results match expectations. BDEE cannot invoke those RPCs directly. Generate request bodies with api-test gen-request. Distinct from ByteDog profiling (`bytedog`)."
---

# bytedcli Watchdog Diag

BDEE 无法直接调用 US-TTP、EU-TTP 内的 RPC。Watchdog Diag 用来在合规区内执行 RPC/DB，并对结果断言，判断表现是否符合预期。当前 CLI 覆盖 RPC 与 RDS。

Watchdog Diag 与 ByteDog（`bytedog`）是不同产品。

## 前置条件

- 默认控制面是 I18N-TT：先执行 `bytedcli --site i18n-tt auth login`。CLI 按 `--site` / `--region` 自动选择 execute 控制面，不要手写 host。打 US 合规区需要 `bytedcli --site us-ttp auth login`，打 EU 合规区需要 `bytedcli --site eu-ttp auth login`
- `--json` 是全局参数，放在 `watchdog` 前
- `--env` 默认 `prod`。打 PPE 泳道时传 `--env ppe_demo`（与 `api-test rpc-call --env` 同一写法）：CLI 会写入 `Base.TrafficEnv.Open=true`、`Base.TrafficEnv.Env`，并带 `x-tt-env` / `x-use-ppe`
- 请求体不要手写 schema。先走 `bytedance-api-test` skill 的 `api-test gen-request` / `list-apis`，把生成的 JSON 存成 `--body-file`
- 合规区（US-TTP / EU-TTP，含 USEASTRED）Diag **不回业务明文**，只回断言是否命中。`--assert` 应对应明确业务预期；验证接口状态时可断言 `BaseResp.StatusCode`，验证内容时应断言具体业务字段
- ROW（`--site i18n-tt --region sg1` 或 RDS `--region Singapore-Central/alisg`）可以返回 `data`，用来对照写出合规区要用的 `--assert`

## Quick start

```bash
bytedcli watchdog region list

# 0. 请求体：走 api-test skill，不要自己编 schema
bytedcli --json api-test gen-request \
  --psm example.service.api \
  --protocol rpc \
  --function-name DemoMethod \
  --idl-source 2 \
  --idl-version 1.0.0 > /tmp/demo-gen-request.json
# 把返回的 body 存成 ./demo-request.json 再给 watchdog

# 1. ROW 可读回包，用来对照写断言。这一步不要写 --assert
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --body-file ./demo-request.json

# PPE 泳道（TrafficEnv + x-tt-env）
bytedcli --json --site i18n-tt watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region sg1 \
  --env ppe_demo \
  --body-file ./demo-request.json

# 2. 合规区只能断言：把 ROW 里看到的业务字段写成「路径 = 值」
bytedcli --site us-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region useast5 \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.EpisodeNum = 1' \
  --assert 'VideoDetails.demo-id.IsPreview = true' \
  --assert 'VideoDetails.demo-id.Title = demo-title'

bytedcli --site eu-ttp watchdog rpc execute \
  --psm example.service.api \
  --method DemoMethod \
  --region USEASTRED \
  --vdc useast2b \
  --body-file ./demo-request.json \
  --assert 'VideoDetails.demo-id.EpisodeNum = 1' \
  --assert 'VideoDetails.demo-id.IsPreview = true'
```

```bash
# RDS：ROW 可读行，用来对照写断言
bytedcli --json --site i18n-tt watchdog db execute \
  --db-name example_db \
  --region Singapore-Central/alisg \
  --sql 'SELECT id, name, extra FROM demo_table WHERE id=1'

# RDS 合规区只能断言。Region 必须是 Diag 控制台的 vregion/dc
bytedcli --site us-ttp watchdog db execute \
  --db-name example_db \
  --region US-TTP2/useast8 \
  --sql 'SELECT id, name, extra FROM demo_table WHERE id=1' \
  --assert 'id = 1' \
  --assert 'name = demo-name' \
  --assert 'extra.multi_language.contract_language = zh'

bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region US-EastRed/us_east_gcp \
  --sql 'SELECT id, extra FROM demo_table WHERE id=1' \
  --assert 'extra.multi_language.contract_language = zh'

bytedcli --site eu-ttp watchdog db execute \
  --db-name example_db \
  --region EU-TTP2/no1a \
  --sql 'SELECT id FROM demo_table WHERE id=1' \
  --assert 'id = 1'
```

上面的字段名只是语法示例。真实路径和值必须来自第 1 步的 `data`，或来自已知业务约定。

## 请求体从哪来（不要自己写 schema）

Watchdog **没有** fetch-schema 命令。Agent 转去 `bytedance-api-test` skill：

1. `api-test list-apis` 确认方法名
2. `api-test gen-request --protocol rpc --function-name DemoMethod` 生成请求示例
3. 把返回的 `body` 存成 `--body-file`（snowflake ID 保持 JSON number）
4. 需要 PPE 时只加 `--env ppe_demo`，不要手改 `Base.TrafficEnv`

IDL 版本怎么选，以 `bytedance-api-test` skill 为准。

## 怎么写 `--assert`（Agent 必读）

目标是验证合规区内已知的业务预期。状态码断言验证指定调用结果；业务字段断言验证响应内容。合规区只返回是否命中。

### 1. 先有预期，再打合规区

1. `--json --site i18n-tt --region sg1`，不带 `--assert`（ROW 可读 `data`）
2. 看 `data`（有值）和 `data_outline`（只有类型树）
3. 选业务 map / list 里的字段，把看到的值写成 `--assert`
4. 同一组 `--assert` 打 `--site us-ttp` / `--site eu-ttp` 合规区
5. 根据已知业务约定选择断言；状态码断言只验证指定的状态结果，不代表响应内容正确

合规区只返回 `assertMatched`，不会回业务包。每个 `--assert` 一次 execute。

### 2. 语法

```text
--assert '<path> <op> <value>'
```

| 写法                                                    | 含义                                                                      |
| ------------------------------------------------------- | ------------------------------------------------------------------------- |
| `VideoDetails.demo-id.EpisodeNum = 1`                   | 数字等值                                                                  |
| `VideoDetails.demo-id.IsPreview = true`                 | 布尔等值                                                                  |
| `VideoDetails.demo-id.Title = demo-title`               | 字符串等值（无空格可裸写）                                                |
| `Collections.demo-id.Status = 5`                        | **map 的 key 是 snowflake id**：CLI 会打成 `Collections."demo-id".Status` |
| `Collections["demo-id"].Status = 5`                     | 同上，显式引用 key                                                        |
| `Collections.demo-id.Videos[0].Status = 5`              | 数组下标                                                                  |
| `VideoDetails.demo-id.MiniDramaInfo = {"EpisodeNum":1}` | JSON 对象等值                                                             |

CLI 会把非标识符 key（纯数字 snowflake、`demo-id`）转成 JMESPath：`VideoDetails."demo-id".EpisodeNum`。Agent 也可以自己写成 `VideoDetails["demo-id"].EpisodeNum`。

snowflake ID 当 **值** 时保持十进制字符串，不要先 `Number()`。

### 3. 值怎么写

- 数字：`1`、`5`、`-1`
- 布尔：`true` / `false`
- 字符串：`demo-title`；含空格时写 `demo title`（`--assert` 里 operator 后面整段都是值）
- JSON 对象 / 数组：`'MiniDramaInfo = {"EpisodeNum":1}'`
- 不要把对象断言成 `exists`

### 4. 运算符

合规区 Diag 支持：`=` `==` `!=` `>` `<` `>=` `<=` `contains` `startsWith` `endsWith` `like` `is` `isNot` `~=`

优先用 `=` 做字段等值。`contains` / `startsWith` 只在字符串前缀、子串检查时用。

按验证目的选择字段：

- `BaseResp.StatusCode = 0`：适用于预期成功状态验证；内容验证仍需具体业务字段
- `Collections exists` / `hasElements`：只能说明有容器，不能说明内容对不对
- RDS 行是扁平列。`--assert 'id = 1'` 是列 where。带点的路径如 `extra.multi_language.contract_language = zh` 表示第一段是 JSON 字符串列（CLI 发 getFirst + getJSON + where），不是 SQL 嵌套列。不要用 `id > 0` 当验证

### 5. 禁止

- 不要照抄本文示例字段（`VideoDetails.demo-id.*` 不是真实 schema）
- 不要把真实 VideoID / CollectionId / PlayUrl / UserIP / 用户名写进回复、skill 或测试
- 请求体用 `--body-file`，保留 JSON number 形态的 i64
- 不要尝试在 US-TTP / EU-TTP 上 `fetchRaw` 或指望返回业务明文

## Agent Guidance

- BDEE 不能直连 US-TTP / EU-TTP 的 RPC/DB；合规区验证走 Watchdog Diag 断言，RPC 不走 `api-test rpc-call`
- RPC `--region` 同时接受 Region 名和 VDC：`sg1`/`alisg`/`my`、`id1a`、`USTTP`/`useast5`、`USTTP2`/`useast8`、`USEASTRED`/`useast2b`、`EUTTP2`/`no1a`、`EUTTP`/`EU-TTP`/`ie`、`EU-Compliance2`/`ie2`、`EU-Compliance`/`de`
- EU RPC 的 ie2、ie、de 自动发送对应 VDC；`--use-direct-rpc` 默认不启用，后端提示 watchman 权限问题时可按提示尝试。地区说明、实例缺失排查与示例见 [EU RPC 地区与调用方式](references/watchdog.md#eu-rpc-地区与调用方式)。
- RDS `--region` 是 Diag 控制台的 `vregion/dc`，只允许：`Singapore-Central/alisg`；`US-BOE/boei18n`、`US-Compliance/useast11a`、`US-East/awsvagm`、`US-East/maliva`、`US-East/maliva_sensitive`、`US-East/useastdt`、`US-EastRed/us_east_gcp`、`US-TTP/ova`、`US-TTP2/useast8`；`EU-TTP/ie`、`EU-TTP/iedt`、`EU-TTP2/no1a`。不要传 `US`/`EU`，也不要把 RPC 的 `useast5`/`useast2b` 用在 RDS 上
- `USEASTRED` RPC 必须显式传 `--vdc useast2b`。只写 `--region USEASTRED` 会报错。`--region useast2b` 本身已指定 VDC。别名 `us_east_gcp` 在 RPC 会按 `useast2b` 发送，在 RDS 则按 DC `us_east_gcp` 发送。`useast2a` 已下线
- `--env` 默认 `prod`。PPE 泳道传 `--env ppe_demo`（与 api-test 相同）；CLI 写入 `Base.TrafficEnv` 和 `x-tt-env` / `x-use-ppe`
- 请求 schema 用 `bytedance-api-test` 的 `gen-request` / `list-apis`，不要手写，也不要在 Watchdog 里 fetch schema
- ROW 的明文只在 `--json` 的 `data` 里；合规区只能看 `passed` / 每条 assertion 的 `passed`
- 断言未命中时命令以 `WATCHDOG_ASSERT_FAILED` 非零退出；JSON `status` 为 `error`，`data.assertions` 仍有明细
- `watchdog db execute` 命中 bytedcli DB SQL 禁入清单时以 `DB_SQL_BLOCKED` 拒绝，不要尝试绕过
- `watchdog db execute` 只允许单条 SELECT / SHOW TABLES / SHOW CREATE TABLE / EXPLAIN SELECT；DML/DDL 以 `RDS_SQL_NOT_READ_ONLY` 拒绝
- RPC `--vdc` 只接受该 region 的 VDC 令牌（如 `useast2b` / `us_east_gcp`），不要把 region 名传给 `--vdc`。`--region us_east_gcp --vdc USEASTRED` 会报错

## References

- 完整参数和区域别名见 `references/watchdog.md`
- 生成 RPC 请求体见 `bytedance-api-test` skill（`api-test gen-request`）
- 不确定 bytedcli 安装方式或 `--site` / `--json` 时，读取 `../../invocation.md`
- 认证失败或命令找不到时，读取 `../../troubleshooting.md`
