# 海外 Vimo 征稿任务

## 目录

- [功能边界](#功能边界)
- [鉴权与网络](#鉴权与网络)
- [标准执行流程](#标准执行流程)
- [筛选参数](#筛选参数)
- [征稿类型](#征稿类型)
- [任务状态](#任务状态)
- [任务来源联动](#任务来源联动)
- [常用示例](#常用示例)
- [请求字段映射](#请求字段映射)
- [JSON 输出与分页](#json-输出与分页)
- [错误与安全](#错误与安全)

## 功能边界

使用以下只读命令查询 CapCut 海外 Vimo 中的“征稿任务”：

```bash
bytedcli --site i18n vimo creator task list [options]
```

该命令固定支持 CapCut 海外业务 `capcut`，可以按任务 ID、创建人、任务标题、
特效/资源 ID、消费国家、任务需求国、征稿类型、任务状态、任务来源和发奖异常状态组合筛选。
该 `list` leaf 不会写入；正式任务、投稿和奖励写命令见
[`creator-task-mutations.md`](creator-task-mutations.md)。

## 任务详情、投稿和获奖名单

查看详情按页面的三个页签选择命令：

```bash
bytedcli --site i18n --json vimo creator task get --task-id '<task-id>'
bytedcli --site i18n --json vimo creator task-submission list --task-id '<task-id>'
bytedcli --site i18n --json vimo creator task-reward list --task-id '<task-id>' --rule-id '<rule-id>'
```

- `task get` 返回 `data.task`：任务说明、可见/生效时间、下发配置、统计和奖励规则。
  从 `task.task_rule_config.task_rules[].rule_id` 选择获奖名单规则；需要全部规则时分别查询。
  标题可能是未翻译的 Starling key；缺失统计不等于零，GMV 单位为美元分。
- `task-submission list` 返回 `data.submissions`，包含模板、作者和投稿指标。
  作者筛选 `--uids/--ccids/--names` 最多选一个；可组合 `--template-ids`、
  `--hashtag-ids`、`--affiliation-biz-ids` 和 `--paid/--ai/--non-low-quality/--valid/--pure-colour true|false`。
  更多条件有 `--fragments min,max`、`--duration min,max`、
  `--high-paid-content/--meets-paid-standard true|false`、`--ecosystem-tags`、
  `--gameplay-names`、`--music-ids`、`--material-ids`、
  `--correlation uncalculated|related|unrelated`、`--quality S,A,B,C,D`、
  `--complexity minimal,low,novice,primary,mid,high`。多值用逗号分隔。
- `task-reward list` 返回 `data.rewards`，支持模板和用户两种获奖对象，并保留奖励类型、
  金额/积分和发放状态。出现在名单中不代表奖励已到账。
- 两个列表都用 `--cursor`（默认 `0`）和 `--page-size`（投稿默认 15，获奖默认 50，
  CLI 范围 1..100）。仅在 `has_more=true` 时原样传入 `next_cursor`，保留 task/rule/筛选条件。
  `current_count` 是本页条数，没有总数；不要用任务列表的 `--page` 翻页。
- 三个入口均只读，鉴权复用 [i18n.md](i18n.md)，写操作继续使用
  [creator-task-mutations.md](creator-task-mutations.md)。

## 鉴权与网络

复用 [i18n.md](i18n.md) 的海外鉴权和网络说明。任务接口支持个人 ByteCloud JWT，
也沿用现有 Cookie/session 链路；不在本参考重复登录步骤。
本地显式测试 TikTok 侧个人 JWT 时，可使用全局 `--site i18n-tt --bytecloud-user-jwt-file -`
从非交互 stdin 注入。JWT 不放入命令参数、输出或仓库文件。

## 标准执行流程

1. 确认版本和命令参数：

   ```bash
   bytedcli --version
   bytedcli --site i18n vimo creator task list --help
   ```

2. 复用海外公共鉴权；托管 Agent 使用运行时注入的请求级凭证。
3. 若要把线索来源进一步限定到某个主类型，先执行
   `bytedcli --site i18n --json vimo creator clue-type list`，取得实时主类型 ID。
4. 使用 canonical 参数组合用户要求的筛选。全局 `--json` 必须放在 `vimo` 前面。
5. 检查顶层 `status`。成功时读取 `data.tasks`；不要把原始嵌套任务记录压平成固定结构。
6. 根据 `data.page`、`data.page_size` 和 `data.total` 判断是否继续下一页。

## 筛选参数

```bash
bytedcli --site i18n --json vimo creator task list [options]
```

| 参数                              | 默认值 | 筛选语义                                          |
| --------------------------------- | ------ | ------------------------------------------------- |
| `--task-ids <ids>`                | 无     | 任务 ID；多分隔符正整数列表，单次最多 100 个      |
| `--creator <username>`            | 无     | 创建人用户名                                      |
| `--title <text>`                  | 无     | 任务标题模糊匹配                                  |
| `--resource-id <id>`              | 无     | 特效/资源 ID；正整数                              |
| `--consumer-biz-ids <ids>`        | 无     | “消费国家”选择器返回的地区业务 ID 多值            |
| `--demand-biz-ids <ids>`          | 无     | “任务需求国”选择器返回的地区业务 ID 多值          |
| `--item-types <types>`            | 无     | 征稿类型语义值多选，允许值见[征稿类型](#征稿类型) |
| `--statuses <statuses>`           | 无     | 任务状态语义值多选，允许值见[任务状态](#任务状态) |
| `--source <manualOrClue>`         | 无     | 任务来源，只接受 `manual` 或 `clue`               |
| `--source-clue-type <mainTypeId>` | 无     | 动态线索主类型 ID；传入后自动限定为线索来源       |
| `--reward-abnormal <boolean>`     | 无     | `true`=仅发奖异常；`false`=排除发奖异常           |
| `--page <n>`                      | `1`    | 页码，范围 `1..1000000`                           |
| `--page-size <n>`                 | `20`   | 单页数量，范围 `1..200`                           |

参数约束：

- `--task-ids` 是 canonical 批量参数，接受逗号、中文逗号、空格或换行分隔，单次最多 100
  个，并会自动去重。旧 `--task-id` 不再兼容；新提示词、脚本和文档必须使用复数参数。
  使用空格或换行分隔时必须给整个参数值加引号，避免 Shell 把它拆成多个参数。
- 其他多值参数会去除空白、去重，并接受英文逗号或中文逗号。显式传入空列表会返回
  `VIMO_INPUT_ERROR`，防止意外扩大查询范围。
- 任务 ID 和资源 ID 始终按十进制字符串处理，以保留 64 位 ID 精度。调用方不要把它们转换
  为 JavaScript `number`。
- `--consumer-biz-ids` 和 `--demand-biz-ids` 接受 Vimo 国家选择器返回的安全正整数 ID。
  不要传 `KR` 等国家码，也不要把 CapCut 顶层 `the top-level CapCut bid` 当作国家 ID。
- 当前命令没有国家目录查询能力；国家 ID 需要从 Vimo 对应选择器或浏览器请求中取得。
- `--reward-abnormal` 只接受严格的 `true` 或 `false`。
- `--reward-abnormal false` 表示排除“发奖失败”，不表示所有命中任务的奖励都已经下发完成。
- 所有筛选可以组合；未传入的可选筛选不会进入请求体。

## 征稿类型

`--item-types` 只接受以下语义值：

| 值                | 含义     |
| ----------------- | -------- |
| `common-template` | 常规模板 |
| `paid-template`   | 付费模板 |
| `ai-template`     | AI 模板  |

支持多选，例如 `--item-types common-template,ai-template`。不要在命令中使用后端数字枚举。

## 任务状态

`--statuses` 只接受以下语义值：

| 值                   | 含义           |
| -------------------- | -------------- |
| `pending-issuance`   | 待下发         |
| `pending-submission` | 待投稿         |
| `in-progress`        | 任务中         |
| `completed`          | 已结束         |
| `reward-generated`   | 奖励已生成     |
| `reward-acked`       | 奖励已确认     |
| `reward-distributed` | 奖励已全部下发 |
| `terminated`         | 已终止         |

支持多选，例如 `--statuses pending-submission,in-progress`。不要使用后端数字状态，也不要推断
未公开的删除状态。

## 任务来源联动

任务来源的两个参数按以下规则联动：

- `--source manual` 查询手动配置任务，不能同时传 `--source-clue-type`。
- `--source clue` 查询全部线索下发任务；可以不指定主类型。
- 在 `--source clue` 基础上增加 `--source-clue-type <dynamic-main-id>`，只查询该主类型的
  线索下发任务。
- 单独传 `--source-clue-type <dynamic-main-id>` 也会自动限定为线索来源，不要求重复传
  `--source clue`。
- `--source-clue-type` 是线索的动态主类型 ID，不是征稿类型、子类型或任务 ID。
- 只传 `--site i18n vimo creator clue-type list` 当前返回的正整数主类型 ID。不要把旧版废弃枚举的
  `0` 当成当前动态类型；上游可能把它解释为未筛选，CLI 会拒绝以避免扩大查询范围。
- 不要硬编码主类型名称、数量或 ID。先运行 `--site i18n vimo creator clue-type list`，再选取返回的
  `data.types[].main_type`。

来源参数组合冲突时，CLI 会返回 `VIMO_INPUT_ERROR`，不会忽略冲突后扩大查询范围。

## 常用示例

```bash
# 查询第一页
bytedcli --site i18n --json vimo creator task list --page 1 --page-size 20

# 批量按任务 ID 查询；始终使用 canonical --task-ids
bytedcli --site i18n --json vimo creator task list \
  --task-ids <task-id-1>,<task-id-2>

# 按创建人、模糊标题和特效/资源 ID 组合筛选
bytedcli --site i18n --json vimo creator task list \
  --creator sample-creator \
  --title 'sample-task-title' \
  --resource-id <resource-id>

# 按消费国家和任务需求国筛选
bytedcli --site i18n --json vimo creator task list \
  --consumer-biz-ids <consumer-biz-id-1>,<consumer-biz-id-2> \
  --demand-biz-ids <demand-biz-id-1>,<demand-biz-id-2>

# 按征稿类型、任务状态和发奖异常筛选
bytedcli --site i18n --json vimo creator task list \
  --item-types common-template,ai-template \
  --statuses pending-submission,in-progress \
  --reward-abnormal true

# 查询全部线索下发任务
bytedcli --site i18n --json vimo creator task list --source clue

# 先查动态线索类型，再查询某类线索下发的任务
bytedcli --site i18n --json vimo creator clue-type list
bytedcli --site i18n --json vimo creator task list \
  --source clue \
  --source-clue-type <dynamic-main-type-id>

# 查询手动配置任务
bytedcli --site i18n --json vimo creator task list --source manual

# 继续下一页
bytedcli --site i18n --json vimo creator task list \
  --page <next-page> \
  --page-size 20
```

## 请求字段映射

CLI 固定使用 CapCut `the top-level CapCut bid`。公开参数会映射为以下 BFF 字段：

| CLI 参数             | BFF 字段                             |
| -------------------- | ------------------------------------ |
| `--task-ids`         | `task_id[]`                          |
| `--creator`          | `creator`                            |
| `--title`            | `task_title`                         |
| `--resource-id`      | `resource_id`                        |
| `--consumer-biz-ids` | `access_biz_id[]`                    |
| `--demand-biz-ids`   | `supplied_biz_ids[]`                 |
| `--item-types`       | `task_item_type[]`                   |
| `--statuses`         | `status[]`                           |
| `--source manual`    | `sourceType=Operator`；`taskFrom=-1` |
| `--source clue`      | `sourceType=Clue`                    |
| `--source-clue-type` | `sourceType=Clue`；`taskFrom`        |
| `--reward-abnormal`  | `is_reward_status_abnormal`          |
| `--page`             | `page`                               |
| `--page-size`        | `pageSize`                           |

语义征稿类型和任务状态由 CLI 映射为内部枚举；使用者不需要依赖数字编码。

## JSON 输出与分页

成功输出示例：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "page": 1,
    "page_size": 20,
    "tasks": [
      {
        "id": "<task-id>",
        "title": "sample-task-title",
        "text": "sample-task-subtitle",
        "task_status": 3,
        "task_item_type": 3,
        "source": {
          "source_type": 2,
          "clue_type": "<dynamic-main-type-id>"
        },
        "supplied_biz_ids": [123],
        "create_by": "sample-creator",
        "create_time": "<unix-seconds>"
      }
    ],
    "total": 42
  },
  "error": null,
  "context": {}
}
```

字段语义：

- `tasks`：BFF 返回的原始嵌套任务记录。不同任务类型可能包含不同字段；自动化应读取所需
  字段并容忍额外字段。
- `total`：匹配当前筛选条件的任务总数。
- `page` 和 `page_size`：当前请求的页码与页大小。
- 本页数量使用 `tasks.length`，不要把 `total` 当成本页长度。

当 `page * page_size < total` 时，可以把 `page + 1` 作为下一次 `--page`；否则停止。不要把
征稿任务分页与 Creator 线索使用的 cursor 分页混用。

文本模式只提供便于人工阅读的任务摘要，长字段可能截断。需要完整嵌套数据、精确 64 位
ID 或稳定机器处理时使用 `--json`。

## 错误与安全

| 错误码                   | 典型原因                                                        | 处理方式                                       |
| ------------------------ | --------------------------------------------------------------- | ---------------------------------------------- |
| `VIMO_INPUT_ERROR`       | 空/非法 ID、未知类型或状态、来源联动冲突、非法页码或页大小      | 按参数表修正；动态来源先查询线索类型目录       |
| `VIMO_AUTH_REQUIRED`     | 生产网未注入 Cookie、Cookie 已失效，或办公网 SSO/CAS 登录态失效 | 获取当前 Cookie；办公网也可重新登录 TikTok SSO |
| `VIMO_PERMISSION_DENIED` | 当前用户没有 CapCut 海外 Vimo 征稿任务读取权限                  | 申请对应业务权限后重试                         |
| `VIMO_API_ERROR`         | Vimo 返回其他业务错误                                           | 检查筛选值与业务权限后重试                     |
| `VIMO_PARSE_ERROR`       | 响应结构或 `total` 不符合预期                                   | 重试；持续出现时保留脱敏日志反馈服务端         |

安全要求：

- Cookie 值不得超过 64 KiB，不能包含换行、其他控制字符或非法 Cookie 名。
- 不打印、不记录、不写文件、不提交 Cookie、JWT 或完整 HTTP 鉴权头。
- Cookie 模式下，凭证仅绑定当前 CLI 进程；不要通过参数、命令输出或临时文件转交。
- 生产网不携带 PPE 路由头；不要尝试用 PPE 参数绕过生产网 fail-closed。
- 该 leaf 是只读列表查询。写请求只使用
  [`creator-task-mutations.md`](creator-task-mutations.md) 明确列出的语义命令，不从页面或
  原始接口推断其它能力。
