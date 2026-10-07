# Argos 告警规则搜索

用于按一个必填 PSM 搜索、过滤和统计 Argos 告警规则。命令调用只读列表接口，不会创建或修改规则。

## 命令

```bash
# 默认第 1 页，每页 20 条；plain 输出适合人读
bytedcli apm argos alarm rule search \
  --filter '{"psm":"example.service.api"}'

# JSON 输出适合 Agent 或脚本；page-size 最大 500
bytedcli --json apm argos alarm rule search \
  --filter '{"psm":"example.service.api","level":["critical"],"status":["normal"]}' \
  --page 2 \
  --page-size 100

# filter 也可从文件读取
bytedcli --json apm argos alarm rule search \
  --filter @alarm-filter.json
```

- `--filter <json|@file>` 必填；必须是 JSON object。
- `psm` 只写在 filter 内，是唯一必填 filter 字段；命令没有独立 `--psm`。
- `--page` 默认 1，必须是正整数。
- `--page-size` 默认 20，范围 1–500。
- 每次只请求指定页，不自动完整分页；`total` 始终是后端对当前 filter 的总数。
- `--site` 和 `--json` 是全局参数，必须放在 `apm` 之前。

## Filter 字段和值域

```json
{
  "psm": "example.service.api",
  "keyword": "demo",
  "check_vregions": ["Example-Region-A"],
  "alarm_modes": ["discrete", "aggregated"],
  "tags": [
    { "namespace": "default", "key": "alarm_team", "val": "demo" },
    { "key": "demo_flag" }
  ],
  "tags_relation": "or",
  "suit_type": ["bosun_raw", "slo"],
  "level": ["critical"],
  "status": ["normal"],
  "traditional_notification": ["enabled"],
  "alarm_methods": ["Lark", "LarkAtUser"]
}
```

| 字段 | 必填 | 枚举或输入说明 |
| --- | :---: | --- |
| `psm` | 是 | 无固定枚举；单个非空 PSM 字符串，不接受数组 |
| `keyword` | 否 | 无固定枚举；任意非空搜索字符串 |
| `check_vregions` | 否 | 无固定枚举；控制面动态提供的监控区域字符串数组 |
| `alarm_modes` | 否 | 固定枚举：`discrete`、`aggregated` |
| `tags` | 否 | 无固定枚举；`{namespace?,key,val?}[]`，key/value 来自规则 |
| `tags_relation` | 否 | 固定枚举：`or`、`and`；只能与非空 `tags` 一起传，传 tags 时默认 `or` |
| `suit_type` | 否 | 当前控制面选项见下节；CLI 不做闭集限制 |
| `level` | 否 | 当前控制面选项：`critical`、`warning`、`notice`；CLI 不做闭集限制 |
| `status` | 否 | 当前控制面选项：`normal`、`pause`；CLI 不做闭集限制 |
| `traditional_notification` | 否 | 固定枚举：`rule_disabled`、`enabled`、`space_disabled` |
| `alarm_methods` | 否 | 当前控制面选项：`Lark`、`LarkUrgent`、`LarkAtUser`、`SMS`、`Phone`；CLI 不做闭集限制 |

`level`、`status`、`suit_type`、`alarm_methods` 的列表来自当前控制面，后端可能新增值。CLI 只校验它们是非空字符串数组，未知值继续交给服务端判断；不要把上表当作客户端永久白名单。

### `suit_type` 当前选项

```text
bosun_raw
slo
ms_methodcalled
ms_calltodownstream
ms_runtime
error_log
critic_log
smartlog
tsap
cloudplatform_tce
infra_tlb
cloudplatform_faas
cloudplatform_cronjob
infra_cache_redis
cloudplatform_bke
python_script
core_dump
machine_system
```

这些是已确认的叶子类型；不要直接传 `micro_service`、`log`、`cloud_products` 等页面父节点。

## Tag 语义

`key` 必填，`namespace` 默认 `default`。必须区分省略 `val` 和显式空字符串：

| 写法 | 匹配语义 |
| --- | --- |
| `{"key":"demo_flag"}` | key 存在，不限制 val；可匹配只有 key 的 tag |
| `{"key":"demo_flag","val":""}` | 精确匹配空值 |
| `{"key":"alarm_team","val":"demo"}` | 精确匹配 key + val |

多个 tag 默认 OR；传 `"tags_relation":"and"` 才要求全部条件命中。`tags_relation` 不能脱离非空 `tags` 单独使用。不同顶层 filter 字段之间使用 AND；普通数组内多个值使用 OR。V1 不支持 NOT、正则、范围比较或嵌套布尔表达式。

## 语义字段到接口字段

- `psm` 单字符串转换为单元素数组。
- `alarm_modes`: `discrete=false`、`aggregated=true`，进入 `check_aggregation`。
- `alarm_methods` 进入 `alarm_methods_list`。
- `traditional_notification` 转成固定三位 boolean array，顺序为：
  1. `rule_disabled`：通过规则关停
  2. `enabled`：开启
  3. `space_disabled`：通过空间配置关停

例如 `traditional_notification:["enabled","space_disabled"]` 转为 `[false,true,true]`。未传该字段时不发送 raw boolean array。

## 输出和 Agent 解析

plain 输出包含 PSM、site、当前页条数、`total`、分页表格，以及存在下一页时的可复制提示；请求页超过最后一页时会明确提示可重试的最后页页码。JSON 的稳定分页字段为：

```json
{
  "status": "success",
  "data": {
    "psm": "example.service.api",
    "site": "cn",
    "filter": { "psm": "example.service.api" },
    "page": 1,
    "page_size": 20,
    "current_count": 20,
    "total": 123,
    "has_more": true,
    "rules": []
  }
}
```

每条 `rules[]` 保留接口返回的完整规则结构，最多 500 条时输出很大。Agent 分析多条规则时，先落临时 JSON 文件，再用 `jq` 读取需要的部分：

```bash
bytedcli --json apm argos alarm rule search \
  --filter '{"psm":"example.service.api"}' \
  --page-size 500 > /tmp/argos-alarm-rules.json

jq '.data.total' /tmp/argos-alarm-rules.json
jq '.data.rules[] | {id,uid,name,status,level,suit_type,check_vregions}' \
  /tmp/argos-alarm-rules.json
```

不要把 `current_count` 当成总数。成功响应当前页为空但 `total > 0` 表示请求页超出当前结果范围，不表示该 PSM 没有规则；plain 模式会提示最后一个有效页，JSON 模式保留原始分页事实供调用方判断。

## 规则详情页 URL

`alarm rule get/search` 会使用实际请求对应的 Argos 告警控制面解析详情页，并在 plain 表格后逐行展示完整链接、在 JSON 中返回 `detail_url`。直接消费命令结果，不要在 skill、提示词或脚本里维护控制面域名表，也不要根据 `site`、API host 或 JWT host 自行拼接。若后端规则缺少可用 `id`，JSON 明确返回 `detail_url:null`，plain 不输出该条链接。

单条规则：

```bash
bytedcli --site <site> --json apm argos alarm rule get --id "demo-rule-id" \
  | jq -r '.data.detail_url'
```

搜索结果：

```bash
bytedcli --site <site> --json apm argos alarm rule search \
  --filter '{"psm":"example.service.api"}' \
  | jq -r '.data.rules[] | [.id, .detail_url] | @tsv'
```

即使使用 `--uid` 查询，链接也应读取响应中的 `detail_url`；CLI 会基于后端返回的规则 `id` 生成正确链接。若字段缺失，先执行只读的 `bytedcli self update --check`；若检查结果提示可升级，向用户说明影响并获得授权后，再执行 `bytedcli self update` 并重试。未获授权时只报告当前版本可能过旧，不要回退到手工域名映射。

## 明确不支持的 filter 字段

V1 不公开 `cluster`、`executor`、`create_source`，也不允许把 `page`、`page_size` 或 `site` 放进 filter。未知字段会返回 `APM_INPUT_ERROR`，不会静默忽略。
