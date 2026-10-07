# Nario 场景一键刷新

基于 psm+接口下的存量场景流量，重新批量打标、映射模板推荐规则，重新生成推荐场景。对应 Nario 模板详情页的「一键刷新」按钮。

## 何时使用

- 模板初始化：模板刚配好特征与推荐规则，需要基于存量流量产出第一批场景。
- 变更后替换：改了特征或推荐规则，需要用新规则替换掉旧版已过期的场景。
- 接口维度补充：不关注某个具体模板，只想让接口下的存量场景流量重新走一遍打标，增量补充场景。

典型用户输入：「帮我一键刷新模板 {{模板 id/名称}}」「刷新下模板下的场景」「重新打标模板 X」「一键刷新接口（psm+接口）下的场景」。

## 两种刷新范围

| 范围     | 传参                 | 行为                                                     |
| -------- | -------------------- | -------------------------------------------------------- |
| 模板维度 | 传 `--template-id`   | **先清除该模板下的推荐场景**，再基于存量流量重新推荐生成 |
| 接口维度 | 不传 `--template-id` | 仅对接口下场景流量重新打标，增量更新场景，不清除已有场景 |

`--save-manual` 只在模板维度生效，默认 `true`，表示保留手动创建等非推荐类型的场景；传 `false` 会一并清除。

## 命令

```bash
# 模板维度刷新：先 dry-run 查看前置校验与计划请求
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template flush execute \
  --psm example.psm \
  --method GetDemo \
  --template-id 3000001 \
  --dry-run

# 检查 dry-run 报告后执行
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template flush execute \
  --psm example.psm \
  --method GetDemo \
  --template-id 3000001 \
  --yes

# 接口维度刷新：省略 --template-id，仅增量打标
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli nario template flush execute \
  --psm example.psm \
  --method GetDemo \
  --yes

# 查询刷新状态，state 为 idle（未刷新或已完成）或 running（进行中）
NARIO_OPENAPI_AUTHORIZATION_TOKEN=<token> bytedcli --json nario template flush status \
  --psm example.psm \
  --method GetDemo
```

## 异步语义（重要）

后端 flush 是异步任务：接口返回 `开始同步...` 只代表**任务已受理**，不代表刷新完成。命令返回成功后必须用 `nario template flush status` 查询是否结束，不要重复触发 `flush execute`。

状态查询是单次查询，不内置轮询。需要等待终态时，由调用方按需轮询 `flush status` 直到返回 `idle`。

## 刷新锁是接口维度

后端锁的粒度是 `psm + method`，**不是模板**。因此：

- 同一 psm+method 下不同模板的刷新会互相阻塞。
- 锁 TTL 为 24 小时；任务异常中断时，锁最长残留 24 小时。
- 锁被占用时后端直接拒绝，`preflight` 的 `not_flushing` 检查会提前拦住这种情况。

## 前置校验（preflight）

`flush execute` 默认在发起刷新前跑三项校验，把「命令成功但场景不会刷新」的情况提前暴露：

| 检查项              | 判定                                           | 不通过的后果                                                     |
| ------------------- | ---------------------------------------------- | ---------------------------------------------------------------- |
| `scene_flow_exists` | 接口下是否有存量场景流量（FTF `flow_type=2`）  | 无流量则刷新产不出任何场景                                       |
| `template_valid`    | 模板已启用、已开启推荐、配了特征，且归属接口与 `--psm`/`--method` 一致 | 模板未开推荐等情况后端不校验，会静默无效；归属接口不一致时后端按 psm+method+模板 ID 三元组过滤，刷新会静默空转 |
| `not_flushing`      | 接口维度的刷新锁是否空闲                       | 锁被占用时后端会拒绝                                             |

- `template_valid` 仅在传 `--template-id` 时执行。
- `--dry-run` 输出完整校验报告，不阻断，便于先看清问题。
- `--yes` 时若存在 `fail` 项，命令直接拒绝并抛 `NARIO_FLUSH_PREFLIGHT_BLOCKED`，`hint` 给出对应修复动作。
- 校验项状态取值为 `pass` / `fail` / `skipped`；`skipped` 不影响放行结论。
- 模板的 `host_env_config` 三项全 false 表示不限制来源、全环境采集（后端 `CheckFlowTagConfigMatch` 的默认行为），属有效配置，不会阻断刷新；报告里用 `flow_source_restricted` 说明来源是否被显式收窄。
- 校验项自身执行失败（未登录 SSO、FTF 返回 5xx 等）会降级为 `skipped` 并在 message 中说明原因，不会让整条刷新链路不可用。

### 环境覆盖

`scene_flow_exists` 依赖 FTF，两侧环境对应关系为：

| Nario `--env` | FTF env    | 行为                   |
| ------------- | ---------- | ---------------------- |
| `cn`          | `cn`       | 实查                   |
| `boe`         | `boe`      | 实查                   |
| `row`         | `i18n`     | 实查                   |
| `zg`          | `zg`       | 实查                   |
| `gcp` / `ttp` | 无对应站点 | 标记 `skipped`，不阻断 |

同一映射也用于 `measure report get` / `tagging scene-debug execute` 的 `--ftf-env` 自动推导（见 SKILL.md 的环境路由说明）。`flush` 本身不接受 `--ftf-env`，只按 `--env` 推导。

查询 FTF 时使用的 ByteCloud 凭据按目标 FTF 站点所属分区获取（`i18n` 走 i18n-tt 分区，`cn`/`boe`/`zg` 走 cn/boe），不沿用全局 `--site`。

### 跳过校验

`--skip-preflight` 会跳过全部三项检查直接提交，输出中会标注已跳过。仅在用户明确要求绕过校验时使用。

## JSON 输出结构

以下字段位于 `--json` 输出的 `data` 下（外层还有 `status` / `error` / `context`）。示例取自 `--dry-run`：

```json
{
  "psm": "example.psm",
  "method": "GetDemo",
  "templateId": "3000001",
  "scope": "template",
  "saveManual": true,
  "preflight": {
    "passed": false,
    "skipped": false,
    "checks": [
      {
        "name": "scene_flow_exists",
        "status": "pass",
        "value": true,
        "message": "接口下存在场景流量，可用于重新打标推荐。"
      },
      {
        "name": "template_valid",
        "status": "fail",
        "value": {
          "template_id": "3000001",
          "is_enable": true,
          "should_recommend": false,
          "has_feature": true,
          "flow_source_restricted": true,
          "template_psm": "example.psm",
          "template_method": "GetDemo"
        },
        "message": "模板未开启推荐（should_recommend=false）。"
      },
      {
        "name": "not_flushing",
        "status": "pass",
        "value": 0,
        "message": "当前没有进行中的刷新任务。"
      }
    ]
  },
  "flush": {
    "ok": true,
    "dryRun": true,
    "env": "cn",
    "baseUrl": "https://nario-manager.byted.org",
    "request": {
      "method": "POST",
      "path": "/openapi/v2/scene/psm_scene/flush",
      "body": { "psm": "example.psm", "method": "GetDemo", "scene_meta_id": 3000001, "save_manual": true }
    }
  }
}
```

`scope` 为 `template` 或 `method`，与是否传 `--template-id` 对应。接口维度刷新时 `templateId` 与 `saveManual` 为 `null`（字段恒存在，不会被省略）。非 dry-run 时 `flush` 是后端受理响应，不会是 `null`。

## 后端接口

| 能力     | 方法与路径                                      | 鉴权                                                |
| -------- | ----------------------------------------------- | --------------------------------------------------- |
| 一键刷新 | `POST /openapi/v2/scene/psm_scene/flush`        | `Authorization: <token>`，与其他 Nario OpenAPI 一致 |
| 刷新状态 | `POST /openapi/v2/scene/psm_scene/flush/status` | 同上                                                |

刷新请求体字段：`psm`（必填）、`method`（必填）、`scene_meta_id`（可选，模板维度必传）、`save_manual`（可选，默认 `true`）。状态接口只用 `psm` + `method`，返回 `data` 为裸数字 `0`（未刷新或已完成）/ `1`（进行中）。CLI 只接受这两个取值：`data` 缺失、无法收敛为数字或收敛后不是 0/1 时抛 `NARIO_RESPONSE_SCHEMA_ERROR`，不会静默当成 `idle` 放行后续刷新（`"0"` / `"1"` 这类数字字符串会被收敛后接受）。
