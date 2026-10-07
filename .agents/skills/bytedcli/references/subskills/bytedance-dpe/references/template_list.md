# DPE Template List API Snapshot

本文件记录 DPE 环境助手的多服务环境模版列表接口，供后续设计 CLI、排查模版筛选逻辑，或创建 `multi` / 联调环境前定位 `env_template_id` 时参考。

## Endpoint

- Method: `GET`
- Path: `/dpe/env/assitant/jupiter/list_all_template`
- Full URL: `https://bytedpe.bytedance.net/dpe/env/assitant/jupiter/list_all_template`
- Controller: `com.bytedance.adqa.dpeEnvAssitant.controller.JupiterApi#listAllTemplate`
- Service: `com.bytedance.adqa.dpeEnvAssitant.service.jupiterService.JupiterTemplateService#listAllTemplate`

## Authentication

该接口走 `EnvAssistJupiterJwtFilter`：

- URL patterns:
  - `/dpe/env/assitant/jupiter/*`
  - `/dpe/env/assitant/api/*`
- 调用方携带 ByteCloud JWT。
- Filter 从 JWT 解析用户名并注入 `x-tt-username`。
- 调用方不应自行伪造 `x-tt-username`。

## Query parameters

| 参数       | 类型         | 必填 | 说明                                                                                                                                        |
| ---------- | ------------ | ---- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `tpl_name` | String       | 否   | 模版名或模版 ID 的模糊匹配。匹配逻辑为 `templateName.contains(tplName)` 或 `String.valueOf(templateId).contains(tplName)`；空值表示不过滤。 |
| `psm[]`    | List<String> | 否   | PSM 列表。只返回模版内 `tpl_psmlist.psm` 包含全部给定 PSM 的模版；未传表示不过滤。                                                          |

`psm[]` 是 AND 语义，不是 OR。多个 PSM 表示“模版必须同时覆盖这些 PSM”。如果原始 URL 或 shell 示例里出现 `psm%5C%5B%5C%5D`，其中反斜杠通常是文档或 shell 转义噪声，HTTP 参数名仍是 `psm[]`。

## Request examples

不带筛选，返回所有有效模版：

```text
GET /dpe/env/assitant/jupiter/list_all_template
```

按模版名或 ID 模糊搜索：

```text
GET /dpe/env/assitant/jupiter/list_all_template?tpl_name=广告排序
```

按多 PSM 精确匹配，要求模版同时包含两个 PSM：

```text
GET /dpe/env/assitant/jupiter/list_all_template?psm[]=example.dpe.service&psm[]=example.dpe.dependency
```

混用 `tpl_name` 与 `psm[]`：

```text
GET /dpe/env/assitant/jupiter/list_all_template?tpl_name=官方&psm[]=example.dpe.service
```

## Processing notes

1. 计算 `isAdmin`
   - 调用 `dpeAdminInfoService.queryByUserName(username)`。
   - 返回非空即认为当前 JWT 用户是 DPE 管理员。
2. 拉取候选模版
   - 通过 `DpeMultiEnvTemplateInfoService.queryAll(tplInfo)` 查询。
   - 查询条件包含 `template_status = 1`，软删除或未发布模版不会返回。
3. 并行筛选与装配
   - 基础校验：`templateId != null && templateId != -1L`。
   - `tpl_name` 模糊匹配在装配前执行，可减少后续 `loadTemplateById` 次数。
   - 通过 `loadTemplateById(id, false)` 装配前端友好的 `DpeTemplateInfoModel`。
   - `hasDetail=false`，列表接口只解析 `template_psm_config_list_jsonstr` 到 `tpl_psmlist`，并读取 `template_bytediff_case` 到 `tpl_caselist`；不会回填 SCM 信息。
   - `psm[]` 匹配在装配后执行，逻辑为 `tplPsmList.containsAll(psm)`。
4. 排序
   - 官方模版优先。官方判定依赖 `tpl_tags` 包含字面量 `"官方"`。
   - 同类模版按 `Collator.getInstance(Locale.CHINA)` 对 `tpl_name` 做中文排序。

## Success response

```json
{
  "code": 200,
  "message": "获取成功",
  "isAdmin": true,
  "data": [
    {
      "tpl_id": 123,
      "tpl_name": "官方-广告排序联调环境",
      "tpl_description": "...",
      "tpl_owner": "userA,userB",
      "tpl_tags": ["官方", "广告"],
      "tpl_custom_tags": ["排序", "engine"],
      "tpl_psmlist": [
        {
          "id": 1001,
          "zone": "China-North",
          "psm": "example.dpe.service",
          "cluster": "default",
          "source_cluster_id": -1,
          "source_cluster_name": "",
          "scm_id": null,
          "scm_name": null,
          "git_name": null,
          "instance_cnt": 1,
          "env_params": "",
          "resource_params": "",
          "sidecar_params": "",
          "service_mesh": null,
          "advance_config": null
        }
      ],
      "tpl_caselist": [
        {
          "id": 5001,
          "psm": "example.dpe.service",
          "cluster": "default",
          "scene": 1,
          "case_name": "example_case",
          "case_url": "https://example.invalid/case",
          "method": "GET",
          "diff_type": 0,
          "ab_param": ""
        }
      ],
      "tpl_dsl_str": "{\"example\":\"dsl json\"}"
    }
  ]
}
```

## Response field notes

| 字段                     | 类型         | 含义                                                                                                                         |
| ------------------------ | ------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| `code`                   | Integer      | 业务状态码，`200` 表示成功，`500` 表示异常。                                                                                 |
| `message`                | String       | 业务消息。                                                                                                                   |
| `isAdmin`                | Boolean      | 当前 JWT 用户是否为 DPE 管理员。                                                                                             |
| `data[].tpl_id`          | Long         | 模版 ID，可作为 `dpe env create --template-id` 的来源。                                                                      |
| `data[].tpl_name`        | String       | 模版名，也是中文排序键。                                                                                                     |
| `data[].tpl_description` | String       | 模版描述。                                                                                                                   |
| `data[].tpl_owner`       | String       | 模版 owner，可能是逗号拼接用户列表。                                                                                         |
| `data[].tpl_tags`        | List<String> | 系统标签；包含 `"官方"` 时视为官方模版。                                                                                     |
| `data[].tpl_custom_tags` | List<String> | 自定义标签。                                                                                                                 |
| `data[].tpl_psmlist[]`   | List<Object> | 模版包含的 PSM、集群、资源配置列表。本接口 `hasDetail=false`，`scm_id` / `scm_name` / `git_name` 不回填。                    |
| `data[].tpl_caselist[]`  | List<Object> | 模版预设 ByteDiff case 列表，包含 `psm`、`cluster`、`scene`、`case_name`、`case_url`、`method`、`diff_type`、`ab_param` 等。 |
| `data[].tpl_dsl_str`     | String       | 模版 DSL JSON 字符串，供后端创建 multi 环境时消费。                                                                          |

## Failure response

异常会兜底为 `code=500` 且 `data=[]`：

```json
{
  "code": 500,
  "message": "获取失败，出现异常",
  "data": []
}
```

调用方需要区分“成功但筛选不到”与“服务异常”：

- `code=200 && data=[]`：筛选条件下无可用模版。
- `code=500 && data=[]`：服务异常。

## Important caveats

- `psm[]` 是 AND 语义。若需要 OR 语义，需要业务侧拆成多次调用后合并。
- 列表接口不含 SCM 详情。需要 `scm_id`、`scm_name`、`git_name` 时，调用详情接口 `/load_template/{tpl_id}`，该接口通过 `loadTemplateById(id, true)` 回填 SCM 信息。
- 只返回 `template_status = 1` 的有效模版。
- 官方模版判定完全依赖 `tpl_tags` 是否包含 `"官方"`，该标签会影响排序权重和官方模版环境数量上限。
- 性能上，`parallelStream` 会逐条 `loadTemplateById`。`tpl_name` 在装配前过滤，能减少 DB 压力；`psm[]` 在装配后过滤，只减少最终返回条数。

## CLI relationship

当前 `bytedcli dpe template list` 已接入该接口，用于在创建 multi / 联调环境前定位可用模版：

```bash
bytedcli dpe template list --tpl-name <name> --psm <psm> --psm <psm> --json
```

`--tpl-name` 和 `--psm` 都是可选参数；不传筛选条件时返回当前用户可见的有效模版。多个 `--psm` 保留 `psm[]` 的 AND 语义，不是 OR。返回结果里的 `tpl_id` 可作为 `bytedcli dpe env create --template-id <id>` 的来源。
