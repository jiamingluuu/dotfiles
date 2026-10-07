# Region 与控制面 (Partition) 映射

Region 是 Argos 中数据查询的物理分区标识。每个 region 属于一个**控制面 (Partition)**，控制面决定了使用哪个 `--site` 参数来查询。

**核心规则**：`--site` 参数必须与 region 所属的控制面对应，否则查不到数据。`argos tool` 与 `argos ai-agent-session get` 支持 `cn`、`boe`、`i18n`、`i18n-tt`、`i18n-bd`、`us-ttp`、`eu-ttp`；其中 `i18n` 与 `i18n-tt` 路由到同一海外控制面。`argos run`、`argos session list/get` 暂不接受 `i18n` 别名，应使用 `i18n-tt`。

| 控制面          | bytedcli `--site` | 说明                  |
| --------------- | ----------------- | --------------------- |
| cn              | `cn`（默认）      | 国内站                |
| boe             | `boe`             | 测试环境              |
| i18n            | `i18n`            | 海外站通用别名        |
| i18n            | `i18n-tt`         | 海外站（TikTok 等）   |
| i18n-bd         | `i18n-bd`         | 海外 BD 站（Lark 等） |
| eu-ttp          | `eu-ttp`          | 欧洲 TTP 合规         |
| us-ttp / tx-ttp | `us-ttp`          | 美国 TTP              |

---

## cn (国内站) — `--site cn`

| Region            | Alias            |
| ----------------- | ---------------- |
| China-North       | cn               |
| China-East        | China-East       |
| China-Aggregation | cn_ag            |
| China-Pay         | China-Pay        |
| China-Pay2        | China-Pay2       |
| China-HKPay       | China-HKPay      |
| China-Fintech     | China-Fintech    |
| China-Enterprise  | China-Enterprise |
| China-North3      | China-North3     |
| China-North5      | China-North5     |
| China-North6      | China-North6     |
| ChinaSinf-East    | ChinaSinf-East   |
| ChinaSinf-North   | ChinaSinf-North  |
| Aliyun_NC2        | Aliyun_NC2       |
| China-PPE         | ppe              |
| China-East-PPE    | China-East-PPE   |

## boe (测试环境) — `--site boe`

| Region        | Alias         |
| ------------- | ------------- |
| China-BOE     | boe           |
| China-BOE2    | China-BOE2    |
| US-BOE        | boei18n       |
| ChinaSinf-BOE | ChinaSinf-BOE |

## i18n (海外站) — `--site i18n` 或 `--site i18n-tt`

| Region               | Alias               |
| -------------------- | ------------------- |
| Singapore-Central    | sg                  |
| US-East              | US-East             |
| US-West              | US-West             |
| US-SouthWest         | US-SouthWest        |
| Europe-Central       | Europe-Central      |
| EasternEuro-TT       | EasternEuro-TT      |
| Asia-SouthEast       | Asia-SouthEast      |
| Australia-SouthEast  | Australia-SouthEast |
| ID-Compliance        | ID-Compliance       |
| MY-Compliance        | MY-Compliance       |
| Singapore-Compliance | compliance-sg       |
| Singapore-PPE        | ppe-sig             |
| US-PPE               | ppe-va              |

## i18n-bd (海外 BD 站 / Lark) — `--site i18n-bd`

| Region                | Alias                 |
| --------------------- | --------------------- |
| Singapore-Common      | Singapore-Common      |
| Singapore-SaaS        | Singapore-SaaS        |
| US-EE                 | va                    |
| US-Central            | US-Central            |
| US-WestBD             | US-WestBD             |
| US-EastBD             | US-EastBD             |
| US-TTP3               | US-TTP3               |
| US-TTP4               | US-TTP4               |
| US-Compliance         | US-Compliance         |
| Europe-WestBD         | Europe-WestBD         |
| Asia-South            | Asia-South            |
| Asia-SaaS             | Asia-SaaS             |
| Asia-NorthEast        | Asia-NorthEast        |
| Asia-Enterprise       | Asia-Enterprise       |
| Australia-SouthEastBD | Australia-SouthEastBD |
| SouthAmerica-East     | SouthAmerica-East     |
| MiddleEast-South      | MiddleEast-South      |
| Africa-South          | Africa-South          |

## eu-ttp (欧洲 TTP 合规) — `--site eu-ttp`

包括 `EU-Compliance`、`EU-Compliance2`、`EU-TTP`、`EU-TTP2`、`US-EastRed` 等 region。

`eu-ttp-limited` 与 `eu-ttp-full` 在 Argos 路由中归一化到同一 `eu-ttp` 控制面。不要使用 `--site i18n-tt` 代查；该操作会连接错误控制面。

## us-ttp / tx-ttp (美国 TTP) — `--site us-ttp`

包括 `US-TTP`、`US-TTP2` 等 region。

Argos 的已验证入口是 `--site us-ttp`。`us-ttp-bdee` 与 `us-ttp-usts` 只是 bytedcli 全局 site 的兼容归一化输入，不是独立 Argos 控制面；尤其 `us-ttp-usts` 尚未完成 Argos 可用性验证。它们共享 `BYTEDCLI_SERVICE_ACCOUNT_JWT_US_TTP` 仅表示 credential partition 相同，不表示入口可用或分别绑定某个 region。不要使用 `--site i18n-tt` 代查；该操作会连接错误控制面。
