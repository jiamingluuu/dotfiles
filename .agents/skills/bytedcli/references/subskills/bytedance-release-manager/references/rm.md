# Release Manager

ByteCloud Release Manager 是面向稳定性敏感服务的发布编排平台，支持灰度策略（abonly / reversalab / noab 等）、多阶段工作流、自动 / 手动 confirm、灰度比例调整、回滚等。

UI: `https://cloud-ttp-us.bytedance.net/release_manager/pipeline/<pipeline>` 和
`https://cloud-ttp-us.bytedance.net/release_manager/pipeline/<pipeline>/release/<release_id>`

bytedcli 提供查询与发布操作能力。API 走 RM v4 接口：us-ttp 与 i18n-tt 经 ByteCloud 网关挂载（`/api/v1/releasemanager/api/v4/...`），i18n 保持直连控制面（`/api/v4/...`），CLI 层对调用方透明。

## 命令

```bash
bytedcli release-manager release get    --id <release_id>            # 单次 release 详情（含当前可执行 actions）
bytedcli release-manager release list   --pipeline <name> [options]  # release 列表（默认历史）
bytedcli release-manager release create --pipeline <name> [options]  # 发起一次 release（写操作）
bytedcli release-manager release execute --id <release_id> --command <cmd>  # 对 release 执行操作，如 continue / rollback（写操作）
bytedcli release-manager pipeline list  [options]                    # pipeline 列表（默认全部）
bytedcli release-manager pipeline scm-versions --pipeline <name>     # 可选 SCM 版本列表（创建 release 前选版本用）
bytedcli release-manager pipeline queue --pipeline <name>            # 操作队列（同时查 v1/v2 两个视图）
```

`release-manager` / `release-manager release` / `release-manager pipeline` 不带子命令时打印帮助。

## `release-manager release get`

```bash
bytedcli --site us-ttp release-manager release get --id demo-pipeline.efb23b9e-c7d4-404d-914e-0d98b4f44df2
```

| 参数                | 默认 | 说明                           |
| ------------------- | ---- | ------------------------------ |
| `--id <release_id>` | —    | 必填，格式 `<pipeline>.<uuid>` |

文本模式输出：

- 顶部一组 `Release` 元信息（pipeline / state / strategy / creator / startTime / endTime / note / tips / rollback）
- `Repo Versions` 表：repo / branch / `base → target`
- `Workflow` 表：每个阶段的 status + start/end
- `Clusters` 表：每个目标集群的 PSM / cluster / region / status
- `Available Actions` 表：当前阶段可执行的操作（COMMAND / DISPLAY / LEVEL），COMMAND 列的值可直接传给 `release execute --command`

JSON 模式：完整 detail 对象（含 `actions[]`），外加 `raw` 字段保留后端原始 payload。

## `release-manager release list`

```bash
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --running
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --page 3 --page-size 20
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --version 2
```

| 参数                | 默认   | 说明                                                                                                         |
| ------------------- | ------ | ------------------------------------------------------------------------------------------------------------ |
| `--pipeline <name>` | —      | 必填                                                                                                         |
| `--running`         | (omit) | 裸 flag：传则只看进行中的 release；服务端空结果时自动从 pipeline 的 running release ids 恢复；不传则默认历史 |
| `--page <n>`        | `1`    | 1 起步                                                                                                       |
| `--page-size <n>`   | `10`   | 每页返回条数；返回条数严格等于 `page-size`（最后一页可能更少），不会静默超发                                 |
| `--version <pool>`  | `both` | 查询的 release pool：`1`（default pool）/ `2`（version=2 pool）/ `both`（全局合并两个 pool）                 |

文本模式：表格列 `RELEASE_ID / STATE / STRATEGY / CREATOR / STAGE / STARTED`。

JSON 模式：

```json
{
  "pipeline": "demo-pipeline",
  "running": false,
  "source": "release-list",
  "warnings": [],
  "version": "both",
  "note": "Queried both release pools (version=1 and version=2) and returned a single page globally merged by startTime (descending), deduped by release id.",
  "page": 1,
  "page_size": 10,
  "returned": 10,
  "has_more": true,
  "total": 37,
  "releases": [
    {
      "pipeline": "demo-pipeline",
      "releaseId": "demo-pipeline.<uuid>",
      "creator": "...",
      "strategy": "ab",
      "state": "Succeed",
      "startTime": "2026-04-28T...",
      "endTime": "2026-04-28T...",
      "currentStage": "...",
      "baseVersions": ["2.0.0.6430"],
      "targetVersions": ["2.0.0.6458"]
    }
  ]
}
```

- `version` 回显实际查询的 pool（`1` / `2` / `both`），`note` 用自然语言说明是否跨 pool 合并，`has_more` 标识本页之后是否还有更多结果——三者一起满足「列表命令不得静默截断/合并」的要求。
- `total` 在正常列表路径下：单 pool（`--version 1|2`）为该 pool 的 `pageInfo.total`（精确），`both` 为 default + `version=2` 两个 pool 各自 `pageInfo.total` 之和（上界，跨 pool 的同一 release 可能被重复计数；仅在后端返回时出现）；running fallback 路径表示 pipeline metadata 快照中的 `runningReleaseIds` 候选总数。当前页详情加载期间已失效或转为非活跃状态的条目会被跳过并产生 warning，因此当前页返回条数可能少于 page size。
- **双 pool 与 `--version`**：后端把 release 分散在 default（无 `version` 参数，即 `version=1`）与 `version=2` 两个 pool，`release create` 会随机落到其中一个。默认 `--version both` 做**全局合并**：对两个 pool 各拉取第 `1..page` 页，按 `releaseId` 去重、按 `startTime` 降序排序后切出请求的那一页，因此翻页在全局有序流上是精确的（不会因另一个 pool 的数量把边界行挤到别的页），代价是 `2 × page` 次请求。`--version 1` / `--version 2` 只查单个 pool，走服务端精确分页（单次请求，更快）。无论哪种模式，返回条数都严格等于 `page-size`。
- `baseVersions` / `targetVersions` 已归一化为版本号字符串数组；后端原始形态是 `{repoName, version}` 对象数组，repo 与版本的完整对应关系可在 `raw` 中查看。

## `release-manager release create`（写操作）

发起一次真实发布。创建前先用 `pipeline scm-versions` 查可选版本。

```bash
# 单 repo（最常见）
bytedcli --site us-ttp release-manager release create \
  --pipeline demo-pipeline --strategy ab \
  --repo example/repo --base-version 1.0.0.1 --target-versions 1.0.0.2

# 多 repo / 多版本用 --repos-json
bytedcli --site us-ttp release-manager release create \
  --pipeline demo-pipeline --strategy ab \
  --repos-json '[{"name":"example/repo","baseVersion":"1.0.0.1","targetVersions":["1.0.0.2"]}]' \
  --enqueue --auto-start
```

| 参数                        | 默认   | 说明                                                                                            |
| --------------------------- | ------ | ----------------------------------------------------------------------------------------------- |
| `--pipeline <name>`         | —      | 必填                                                                                            |
| `--strategy <strategy>`     | —      | 必填，发布策略（如 `ab`、`reversalab`，以 pipeline 配置为准）                                   |
| `--repo <name>`             | —      | 单 repo 模式：repo 名                                                                           |
| `--base-version <version>`  | —      | 单 repo 模式：基线版本                                                                          |
| `--target-versions <v1,v2>` | —      | 单 repo 模式：目标版本，逗号分隔；多个值即多版本发布                                            |
| `--repos-json <json>`       | —      | 多 repo 模式，JSON 数组 `[{"name","baseVersion","targetVersions":[...]}]`；与单 repo 三参数互斥 |
| `--tests-json <json>`       | —      | AB 实验参数，JSON 数组 `[{"name","baseParam","abtestParams":[...]}]`                            |
| `--using-config <name>`     | 主配置 | 指定 pipeline 配置副本                                                                          |
| `--enqueue`                 | (omit) | 无法立即执行时进入等待队列                                                                      |
| `--auto-start`              | (omit) | 队列排到后自动执行                                                                              |
| `--note <text>`             | —      | Release 工单备注                                                                                |

JSON 模式输出 `data.release_id`（格式 `<pipeline>.<uuid>`）；文本模式输出 release id 与跟踪命令提示。

## `release-manager release execute`（写操作）

对已存在的 release 执行操作。**可用操作随当前阶段动态变化**：先 `release get --id <id>` 看 `actions[]`（文本模式的 `Available Actions` 表），再把 COMMAND 原样传给 `--command`。

**默认安全**：不传 `--yes` 时只打印待提交操作的 dry-run 预览（不改动任何状态），确认后再加 `--yes` 真正执行。`--dry-run` 与 `--yes` 不能同时使用。

```bash
bytedcli --site us-ttp release-manager release execute --id <release_id> --command continue                          # dry-run 预览
bytedcli --site us-ttp release-manager release execute --id <release_id> --command continue --yes                    # 真正执行
bytedcli --site us-ttp release-manager release execute --id <release_id> --command rollback --note 'error rate spike' --yes
```

| 参数                         | 默认    | 说明                                                                                                                                      |
| ---------------------------- | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `--id <release_id>`          | —       | 必填                                                                                                                                      |
| `--command <command>`        | —       | 必填，文档化的有 `continue`（继续/确认）、`rollback`（回滚）；后端可能通过 `actions[]` 暴露更多（如 `confirmClose` 关实验），CLI 原样透传 |
| `--note <text>`              | —       | 操作理由（如回滚原因）                                                                                                                    |
| `--deploy-version-index <n>` | —       | 多版本发布时选择上线版本下标                                                                                                              |
| `--enqueue` / `--auto-start` | (omit)  | 同 `release create`                                                                                                                       |
| `--dry-run` / `-y, --yes`    | dry-run | 不传 `--yes` 默认只预览（`data.dry_run: true`）；`--yes` 才真正提交；两者互斥                                                             |

## `release-manager pipeline scm-versions`

创建 release 前查询 repo 可选版本；每个 repo 带服务端推荐的 `defaultBaseVersion`。

```bash
bytedcli --site us-ttp release-manager pipeline scm-versions --pipeline demo-pipeline
bytedcli --site us-ttp --json release-manager pipeline scm-versions --pipeline demo-pipeline
```

| 参数                | 默认 | 说明                                                    |
| ------------------- | ---- | ------------------------------------------------------- |
| `--pipeline <name>` | —    | 必填                                                    |
| `--limit <n>`       | `10` | 仅限制文本表格每个 repo 显示的版本数；JSON 始终返回全部 |

文本模式：每个 repo 一张表（VERSION / BRANCH / SELECTABLE / COMMIT / COMMIT_INFO），超出 `--limit` 时打印明确截断提示。

**重要**：`disabled: true`（文本表 SELECTABLE=N）的版本不能用于发起 release——通常是分支不在 pipeline 允许范围内（limitBranch 约束）；给 `release create` 选版本时必须挑 SELECTABLE=Y 的条目。JSON 中每个版本含 `version` / `branch` / `commit` / `commitInfo` / `type` / `disabled`。

## `release-manager pipeline queue`

查看 pipeline 操作队列。**后端同时存在 v1（旧）和 v2（现行，Web UI 使用）两个队列视图，且 v1 可能为空而 v2 有真实条目（已线上验证）**，所以命令同时查询两个视图都展示。

```bash
bytedcli --site us-ttp release-manager pipeline queue --pipeline demo-pipeline
bytedcli --site us-ttp --json release-manager pipeline queue --pipeline demo-pipeline
```

| 参数                | 默认 | 说明 |
| ------------------- | ---- | ---- |
| `--pipeline <name>` | —    | 必填 |

JSON 输出 `data.v1` / `data.v2`，各含 `lockerOwner`（当前持有 pipeline 锁的 release 与所在 stage）与 `entries[]`（action / user / releaseId / autoStart / enqueueTime / note）。排队中的 `createRelease` 条目的 `releaseId` 是预分配 id——release 要等队列执行到该操作才落库（落库前 `release get` 会报 not-found 类错误）。

## `release-manager pipeline list`

```bash
bytedcli --site us-ttp release-manager pipeline list                                     # 全部
bytedcli --site us-ttp release-manager pipeline list --following                    # 仅订阅
bytedcli --site us-ttp release-manager pipeline list --owner alice
bytedcli --site us-ttp release-manager pipeline list --search demo --page-size 20
```

| 参数                 | 默认   | 说明                                                                           |
| -------------------- | ------ | ------------------------------------------------------------------------------ |
| `--following`        | (omit) | 裸 flag：传则只看自己订阅的（服务端 `only_subscription=true`）；不传则默认全部 |
| `--owner <username>` | —      | 按 owner 用户名过滤（服务端）                                                  |
| `--search <keyword>` | —      | 按 pipeline 名称搜索（服务端）                                                 |
| `--status <status>`  | —      | 状态过滤（服务端）                                                             |
| `--page <n>`         | `1`    |                                                                                |
| `--page-size <n>`    | `10`   |                                                                                |

文本模式：表格列 `NAME / FOLLOWING / RUNNING / OWNERS / LAST_UPDATE`（OWNERS 只显示前 3 个，超出用 `+N` 表示）。

JSON 模式：

```json
{
  "following": false,
  "owner": "",
  "search": "",
  "status": "",
  "page": 1,
  "page_size": 10,
  "returned": 5,
  "pipelines": [
    {
      "name": "demo-pipeline",
      "desc": "...",
      "owners": ["..."],
      "subscribed": true,
      "runningReleaseCount": 6,
      "runningReleaseIds": ["demo-pipeline.<uuid>"],
      "lastUpdate": "2026-..."
    }
  ]
}
```

`runningReleaseIds` 是进行中 release 的 id 列表（无进行中 release 时省略）。**i18n 已验证**：`release list` 对部分 pipeline 不返回进行中的 release（控制面原始接口同样行为）；此时用 `runningReleaseIds` 拿 id 再 `release get`。

## 站点支持

| site      | API host                                                           | 形态               | JWT host                             |
| --------- | ------------------------------------------------------------------ | ------------------ | ------------------------------------ |
| `cn`      | `https://cloud.bytedance.net`（前缀 `/api/v1/releasemanager`）     | ByteCloud OG 网关  | `https://cloud.bytedance.net`        |
| `us-ttp`  | `https://cloud.tiktok-us.net`（前缀 `/api/v1/releasemanager`）     | ByteCloud OG 网关  | `https://cloud-ttp-us.bytedance.net` |
| `i18n`    | `https://release-manager-i18n.byted.org`                           | 直连控制面         | `https://cloud.tiktok-row.net`       |
| `i18n-tt` | `https://bc-sg-gw.tiktok-row.net`（前缀 `/api/v1/releasemanager`） | TikTok ROW SG 网关 | `https://cloud.tiktok-row.net`       |

i18n 的 JWT host 用 `cloud.tiktok-row.net`（i18n-tt 分区）而非 `cloud.byteintl.net`：i18n 直连控制面只接受 i18n(-tt) 分区 JWT，i18n-bd 分区 JWT 会被拒为 `invalid jwt token`。

要扩展其他站点（boe / eu / tx 等），只需要：

1. 从对应站点 RM 网页抓一份请求，或参考 RM 官方 API 文档的控制面域名表
2. 在 `src/api/release_manager/site.ts` 的 `SITES` 里加上 `apiBaseUrl` / `apiPathPrefix` / `jwtHost` / `webOrigin` / `ogPathMode`，并在 `ReleaseManagerSite` 类型加上对应 site 字面量
3. 补一条 `test/api/release_manager/release_manager.test.ts` 用例覆盖新 site 的 URL 拼接与 header

## 认证

走标准 ByteCloud JWT。首次在 TTP-US 站点使用前确认登录态：

```bash
BYTEDCLI_CLOUD_SITE=us-ttp bytedcli auth status
# 必要时
BYTEDCLI_CLOUD_SITE=us-ttp bytedcli auth login
```

否则会报 `获取字节云 JWT 失败: 401`。

## 常见错误

- `RM_SITE_UNSUPPORTED` → 当前支持 `--site cn`、`--site us-ttp`、`--site i18n` 和 `--site i18n-tt`，其他 site 没接通；按 「站点支持」 一节扩展
- `RM_API_ERROR ... permission denied` / 403 → 该 pipeline 你没权限，去 RM Web 申请
- `RM_API_ERROR`，`statusCode: -2` → 集群锁被其他 release 占有，等它结束或与 owner 协调
- `RM_API_ERROR`，`statusCode: -3` → 等待队列不为空，无法直接执行；可加 `--enqueue` 排队
- 写操作被拒还可能是 pipeline 配置了禁发时段（forbiddenRules），换时间窗重试
- `RM_INPUT_ERROR` → CLI 入参问题，错误自带 `hint` 给出可复制的修复示例
- `RM_PARSE_ERROR` → 后端返回的 payload 不是 `{code, message, data}` 标准信封；附带 `details` 看原始响应
- `获取字节云 JWT 失败: 401` → 没登录对应凭证分区，先 `BYTEDCLI_CLOUD_SITE=us-ttp bytedcli auth login`（i18n RM 使用 `BYTEDCLI_CLOUD_SITE=i18n-tt`）
