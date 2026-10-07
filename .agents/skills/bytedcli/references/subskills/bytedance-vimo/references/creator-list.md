# 海外 Vimo 创作者列表

本参考适用于 `bytedcli --site i18n vimo creator list`。该命令映射 CapCut 海外 Vimo
“创作者管理 > 创作者列表”，提供全量分页和组合筛选，只读返回创作者资料与近 30 天指标。

## 与相邻页面的区别

不要混用以下三类查询：

| 页面                    | CLI                      | BFF                                                 | 语义                                |
| ----------------------- | ------------------------ | --------------------------------------------------- | ----------------------------------- |
| 创作者管理 > 创作者列表 | `--site i18n vimo creator list` | `POST /user/api/Creator/getCreator`                 | 全部/C 端/B 端/素材创作者及组合筛选 |
| 基础信息 > 用户查询     | `--site i18n vimo user list`    | `POST /user/api/User/getUser`                       | UID、CapCut 号或营销签约状态四选一  |
| 创作者管理 > 签约管理   | 尚未提供                 | `POST /user/api/CreatorContract/getCreatorContract` | 合同号、邀约人、签约类型和状态      |

浏览器抓到 `CreatorContract/getCreatorContract` 只说明打开了签约管理页，不能用它实现创作者列表。

## 鉴权与网络

海外 `/user/**` BFF 优先使用 `i18n-tt` 个人 ByteCloud JWT。JWT 获取失败或服务端返回 HTTP 401
时，读请求才回退到 Vimo Cookie。

验证 JWT-enabled PPE 时带上环境路由头：

```bash
bytedcli --site i18n \
  --http-header "x-use-ppe: 1" \
  --http-header "x-tt-env: sample-ppe-env" \
  --json vimo creator list --page 1 --page-size 1
```

未部署 JWT 鉴权的环境需要 `BYTEDCLI_VIMO_COOKIE` 或 TikTok SSO session。生产网入口由
`BYTEDCLI_NETWORK_PROFILE=prod` 选择，并保护 `x-use-ppe`、`x-tt-env` 和 `x-schedule-vdc`
等路由头不被全局配置覆盖。不要输出 JWT 或 Cookie 原值。

## 参数总览

```bash
bytedcli --site i18n --json vimo creator list [options]
```

| 参数                    | 输入                                | 语义                                           |
| ----------------------- | ----------------------------------- | ---------------------------------------------- |
| `--biz`                 | `capcut`                            | 可选顶层业务；默认 `capcut`，请求使用 bid `106` |
| `--identity`            | `all\|consumer\|business\|material` | 创作者 Tab；默认 `all`                         |
| `--uids`                | 逗号、空格或换行分隔                | CapCut UID 精确匹配，1..19 位数字，最多 100 个 |
| `--ccids`               | 逗号、空格或换行分隔                | CapCut 号精确匹配，最多 100 个                 |
| `--names`               | 逗号或换行分隔                      | CapCut 昵称精确匹配，最多 100 个，不是模糊搜索 |
| `--creator-types`       | 见创作者类型表                      | 一个或多个创作者子类型                         |
| `--permissions`         | 动态权限 key                        | 拥有任一指定功能权限                           |
| `--permission-start`    | 日期、ISO/RFC 3339、Unix 时间       | 权限开通时间起点                               |
| `--permission-end`      | 同上                                | 权限开通时间终点                               |
| `--sources`             | 见来源表                            | 创作者来源                                     |
| `--recommend-channels`  | 动态渠道值                          | 推荐渠道精确匹配                               |
| `--focus-levels`        | `0..8`                              | 重运营地区达人等级                             |
| `--non-focus-levels`    | `0..4`                              | 互通地区达人等级                               |
| `--certification`       | `uncertified\|top-template`         | 创作者认证                                     |
| `--affiliation-biz-ids` | 正整数列表                          | 创作者归属国的 Vimo business ID                |
| `--penalty-statuses`    | `never\|punishing\|ended`           | C 端创作者处罚状态                             |
| `--sort-by`             | 见排序表                            | 白名单排序字段                                 |
| `--sort-order`          | `asc\|desc`                         | 排序方向，必须与 `--sort-by` 同时使用          |
| `--page`                | `1..1000000`                        | 一基页码；默认 `1`                             |
| `--page-size`           | `1..100`                            | 单页数量；默认 `20`                            |

`--uids`、`--ccids`、`--names` 最多使用一种；它们可与创作者类型、权限、来源等其他筛选组合。
没有业务筛选也是合法的，会按当前账号的数据权限分页列出创作者。

`--biz` 是可选的顶层业务选择器，不传时默认 `capcut`。历史写法 `--biz 106` 为已有脚本
继续保留；新调用应使用 `capcut`。两者都会在请求中转换成数字 bid `106`。它不是地区筛选；
归属国仍使用 `--affiliation-biz-ids`。

不同筛选组之间是 AND；`--creator-types`、`--permissions`、`--sources`、渠道、等级和处罚等
多值列表的内部是 OR。

## 身份与创作者类型

| `--identity` | 页面           | 可用 `--creator-types`               |
| ------------ | -------------- | ------------------------------------ |
| `all`        | 全部           | 下列全部类型                         |
| `consumer`   | C 端模板创作者 | `ugc-video`、`prompt-template`       |
| `business`   | B 端模板创作者 | `marketing-video`、`marketing-image` |
| `material`   | 素材创作者     | `material`                           |

| CLI 类型          | 上游值 | 页面含义          |
| ----------------- | -----: | ----------------- |
| `ugc-video`       |    `1` | UGC 视频创作者    |
| `prompt-template` |    `2` | Prompt 模板创作者 |
| `marketing-video` | `1001` | 营销视频创作者    |
| `marketing-image` | `1002` | 营销图片创作者    |
| `material`        | `2001` | 素材创作者        |

显式身份与不兼容类型会在请求发出前报 `VIMO_INPUT_ERROR`，不会交给上游静默返回空结果。

来源、推荐渠道和归属国只允许 `all` 或 `consumer`。处罚状态只允许
`--identity consumer`，与页面能力保持一致。

## 来源、认证和处罚

| CLI 来源      | 上游值        | 页面含义        |
| ------------- | ------------- | --------------- |
| `agency`      | `agency`      | Agency 拉新     |
| `model`       | `model`       | 模型开权        |
| `operation`   | `operation`   | 运营人工招募    |
| `white-apply` | `white_apply` | 端内申请        |
| `tt-anchor`   | `tt_anchor`   | TikTok 锚点报名 |
| `creativity`  | `creativity`  | 开放创意        |

页面某些旧前端代码还显示 `referral`，但当前 BFF schema 不接受它，因此 CLI 不暴露该值。

认证映射：

- `uncertified` → `0`，未认证；
- `top-template` → `1`，Top template creator。

处罚映射：

- `never` → `0`，无处罚；服务端同时匹配空处罚状态；
- `punishing` → `1`，处罚中；
- `ended` → `2`，处罚已结束。

## 动态值与时间

权限 key、推荐渠道和归属国 business ID 都是动态配置，不应根据中文标签猜测：

- 权限使用 Vimo 页面请求/选项里的原始 key；
- 推荐渠道使用原始 `recommendCode` 值；
- 归属国使用 Vimo country selector 的数字 business ID，不是 ISO 国家码，也不是顶层 the top-level CapCut bid。

归属国会与当前用户拥有的 Kani 地区权限求交。传入无权地区可能得到空结果；CLI 不会绕过
Vimo 的地区数据权限。

`--permission-start` 和 `--permission-end` 必须成对，并且只能搭配恰好一个
`--permissions` 值。上游在多权限配时间时会静默漏掉权限筛选，所以 CLI 会 fail-closed。
`YYYY-MM-DD` 按 UTC 自然日展开，wire 使用 Unix 秒；起止边界为闭区间。

`--focus-levels` 和 `--non-focus-levels` 互斥。重运营等级支持 `0..8`，互通等级支持
`0..4`。

## 排序

`--sort-by` 和 `--sort-order` 必须同时出现。允许值对应页面可排序列：

| CLI               | 上游字段             |
| ----------------- | -------------------- |
| `followers`       | `fans_cnt`           |
| `templates-30d`   | `template_cnt_30d`   |
| `s-templates-30d` | `s_template_cnt_30d` |
| `a-templates-30d` | `a_template_cnt_30d` |
| `income-30d`      | `income_30d`         |

CLI 不允许透传原始排序字段，因为当前上游会将该字段用于 Doris SQL。未指定排序时不发送
`sortOrderObj`，保留 Vimo 默认行为。

## 示例

列出全部创作者：

```bash
bytedcli --site i18n --json vimo creator list --page 1 --page-size 20
```

按 UID 和组合条件筛选 C 端创作者：

```bash
bytedcli --site i18n --json vimo creator list \
  --identity consumer \
  --uids '<capcut-uid-1>,<capcut-uid-2>' \
  --creator-types ugc-video,prompt-template \
  --sources operation \
  --focus-levels 3,4
```

按昵称精确查询：

```bash
bytedcli --site i18n --json vimo creator list --names 'Sample Creator'
```

查询一个动态权限在指定 UTC 日期内开通的创作者：

```bash
bytedcli --site i18n --json vimo creator list \
  --permissions 'sample_permission' \
  --permission-start 2026-08-01 \
  --permission-end 2026-08-07
```

查询 B 端营销图片创作者并按粉丝数降序：

```bash
bytedcli --site i18n --json vimo creator list \
  --identity business \
  --creator-types marketing-image \
  --sort-by followers \
  --sort-order desc
```

查询无处罚且未认证的 C 端创作者：

```bash
bytedcli --site i18n --json vimo creator list \
  --identity consumer \
  --penalty-statuses never \
  --certification uncertified
```

## JSON 输出

成功响应外层稳定为：

```json
{
  "status": "success",
  "data": {
    "bid": "<capcut-bid>",
    "biz": "capcut",
    "site": "i18n",
    "identity": "consumer",
    "page": 1,
    "page_size": 20,
    "total": 1,
    "creators": [
      {
        "UID": "<capcut-uid>",
        "Name": "Sample Creator",
        "UniqueIDInfo": { "UniqueID": "sample-capcut-id" },
        "followerCount": "<count>",
        "CapcutCreatorInfo": {
          "CreatorTypeList": [1],
          "AffiliationBizID": 123,
          "CapcutLevelV2": "3",
          "CapcutLevelV3": "2"
        },
        "template_cnt_30d": "0",
        "income_30d": 0
      }
    ]
  },
  "error": null,
  "context": {}
}
```

`creators` 保留 BFF 返回的完整原始创作者记录和未知字段，包括用户资料、权限、推荐、处罚、
归属国、达人等级和 Doris 近 30 天指标。UID、CapCut 号、创建时间、粉丝数和模板计数等潜在
64 位字段必须保持字符串。`income_30d` 的上游单位为分；文本列明确标记为 cents。

继续下一页的条件为 `data.page * data.page_size < data.total`。

## BFF 字段映射

命令调用 `POST /user/api/Creator/getCreator`。公共 Vimo 请求体还带鉴权上下文
`scene: ""` 和 `bid: "106"`。

| CLI                     | BFF 字段                         |
| ----------------------- | -------------------------------- |
| `--uids`                | `uids`                           |
| `--ccids`               | `ccids`                          |
| `--names`               | `names`                          |
| `--identity`            | `creatorIdentity`；`all` 时省略  |
| `--creator-types`       | `creatorTypeList`                |
| `--permissions`         | `permissionList`                 |
| `--permission-start`    | `permissionStartTime`（Unix 秒） |
| `--permission-end`      | `permissionEndTime`（Unix 秒）   |
| `--sources`             | `creatorSourceList`              |
| `--recommend-channels`  | `recommendChannelList`           |
| `--focus-levels`        | `focusOprCountryLevelList`       |
| `--non-focus-levels`    | `nonFocusOprCountryLevelList`    |
| `--certification`       | `certificationType`              |
| `--affiliation-biz-ids` | `affiliationBizIdList`           |
| `--penalty-statuses`    | `penaltyStatus`                  |
| 排序参数                | `sortOrderObj`                   |
| `--page`                | `page`                           |
| `--page-size`           | `pageSize`                       |

Referer 会随身份使用创作者列表的 `all`、`cTemplate`、`bTemplate` 或 `material` 页面路径。

## 错误与安全

| 错误码                   | 含义                                         | 处理                                |
| ------------------------ | -------------------------------------------- | ----------------------------------- |
| `VIMO_INPUT_ERROR`       | 空值、枚举、组合、时间、分页或危险字符不合法 | 按 `error.hint` 修正参数            |
| `VIMO_AUTH_REQUIRED`     | Cookie 缺失、过期或被拒绝                    | 注入当前 Cookie，或刷新办公网 SSO   |
| `VIMO_PERMISSION_DENIED` | 缺少创作者列表读权限                         | 申请对应的 C/B/素材创作者列表读权限 |
| `VIMO_API_ERROR`         | 其他 Vimo 业务错误                           | 检查脱敏信息和筛选条件              |
| `VIMO_PARSE_ERROR`       | 响应列表或总数不符合契约                     | 重试并报告脱敏元数据                |

- 不打印 Cookie、`X-Bytedance-User`、JWT 或环境变量原值。
- 不持久化浏览器 Cookie，不把它发送到非海外 Vimo 域名。
- 动态文本最终会进入上游 Doris 查询；CLI 拒绝引号、反斜杠、控制字符和超长值。
- UID 仅接受十进制字符串；排序字段只能来自白名单。
- 不根据页面按钮推断写能力；只使用
  [`creator-mutations.md`](creator-mutations.md) 明确列出的权限/资料/审核/签约/处罚命令。
