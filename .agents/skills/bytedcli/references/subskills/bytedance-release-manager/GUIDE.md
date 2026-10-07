---
name: bytedance-release-manager
description: "Query and operate ByteCloud Release Manager pipelines and releases via bytedcli. Invoke when tasks mention release manager, RM 发布, release pipeline, 发布流水线, 单次 release 详情, 进行中的 release / 发布历史, 发起发布 / 创建 release, 继续发布 / 回滚 release, or surface release state / strategy / rollback info / repo versions / cluster status."
---

# bytedcli Release Manager

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 查询 ByteCloud Release Manager 单条 release 的详情（state / strategy / 工作流阶段 / 集群状态 / 回滚信息 / repo 版本对照 / 当前可执行 actions）
- 列出某个 pipeline 的发布历史（默认）或当前进行中的发布（`--running`）
- 列出可见 pipelines（默认全部，`--following` 限定为关注的），支持按 owner / 关键字 / 状态过滤
- 在 pipeline 上发起一次 release（`release create`），或对进行中的 release 执行继续 / 回滚等操作（`release execute`）
- 创建 release 前查询 repo 可选版本与推荐基线版本（`pipeline scm-versions`）
- 查看 pipeline 操作队列与锁持有者（`pipeline queue`，同时查 v1/v2 两个视图）
- 对应 UI：`https://cloud-ttp-us.bytedance.net/release_manager/pipeline/<pipeline>/release/<release_id>`

## Quick start

```bash
# 单次 release 详情（id 形如 <pipeline>.<uuid>；含 Available Actions 表）
bytedcli --site us-ttp release-manager release get \
  --id demo-pipeline.efb23b9e-c7d4-404d-914e-0d98b4f44df2

# 发布历史（默认 page=1, page_size=10）
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline

# 当前进行中的 release
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --running

# 翻页 / 自定义页大小
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --page 2 --page-size 20

# 只查单个 release pool（更快，服务端精确分页）
bytedcli --site us-ttp release-manager release list --pipeline demo-pipeline --version 2

# JSON 模式（agent / 脚本消费）
bytedcli --site us-ttp --json release-manager release get --id <release_id>
bytedcli --site us-ttp --json release-manager release list --pipeline <pipeline>

# 列出 pipelines（默认全部）
bytedcli --site us-ttp release-manager pipeline list

# 只看自己关注的 pipelines
bytedcli --site us-ttp release-manager pipeline list --following

# 按 owner / 关键字 / 状态过滤
bytedcli --site us-ttp release-manager pipeline list --owner alice
bytedcli --site us-ttp release-manager pipeline list --search demo --page-size 20

# 创建 release 前先查可选版本（每个 repo 带推荐 defaultBaseVersion）
bytedcli --site us-ttp release-manager pipeline scm-versions --pipeline demo-pipeline

# 查看操作队列（v2 是 Web UI 使用的现行队列；遇到 -3 队列冲突时先看这里）
bytedcli --site us-ttp release-manager pipeline queue --pipeline demo-pipeline

# 发起一次 release（写操作；返回新 release id）
bytedcli --site us-ttp release-manager release create \
  --pipeline demo-pipeline --strategy ab \
  --repo example/repo --base-version 1.0.0.1 --target-versions 1.0.0.2

# 对 release 执行操作（写操作；先 release get 看 actions[] 再选 command）
# 默认 dry-run 预览，加 --yes 才真正提交
bytedcli --site us-ttp release-manager release execute --id <release_id> --command continue
bytedcli --site us-ttp release-manager release execute --id <release_id> --command continue --yes
bytedcli --site us-ttp release-manager release execute --id <release_id> --command rollback --note 'error rate spike' --yes
```

## Notes

- **站点支持 `--site cn`、`--site us-ttp`、`--site i18n` 和 `--site i18n-tt`**：cn 走 ByteCloud 网关（API host `cloud.bytedance.net`，前缀 `/api/v1/releasemanager`，JWT 走 `cloud.bytedance.net`）；us-ttp 走 ByteCloud 网关（API host `cloud.tiktok-us.net`，JWT 走 `cloud-ttp-us.bytedance.net`）；i18n 保持直连 RM 控制面（`release-manager-i18n.byted.org`）；i18n-tt 走 TikTok ROW SG 网关（`bc-sg-gw.tiktok-row.net`，前缀 `/api/v1/releasemanager`，JWT 走 `cloud.tiktok-row.net`）。其他 site 调用会报 `RM_SITE_UNSUPPORTED`，附带提示去补 `src/api/release_manager/site.ts`。
- **release id 格式**：`<pipeline>.<uuid>`，例如 `demo-pipeline.0002ea2d-698c-4dea-b244-bda30244b27a`。`get` 必须传完整 id；用 `release list --pipeline <name>` 可以发现 id。
- **写操作须知**：`release create` 与 `release execute` 会真实触发 / 变更线上发布。创建前先用 `pipeline scm-versions` 选版本；操作前先 `release get` 确认 `actions[]` 中允许该 command（文档化的有 `continue`、`rollback`，后端可能暴露更多，CLI 原样透传）。后端错误码 `-2` 表示集群锁被其他 release 占有，`-3` 表示等待队列不为空（可加 `--enqueue` 排队，配合 `--auto-start` 排到后自动执行；用 `pipeline queue` 查看队列与锁持有者）。enqueue 创建返回预分配 release id，release 要等队列执行到该操作才落库，落库前 `release get` 会报 not-found 类错误。
- **`--running` 是裸 flag**：传则只看进行中的 release；CLI 先使用后端 running filter，空结果时自动从 pipeline 的 `runningReleaseIds` 恢复并逐条获取详情。不传则默认是历史，与后端 `running=false` 行为一致。
- **`--following` 是裸 flag**：传则只看自己订阅的 pipeline；不传则默认是全部，与后端 `only_subscription=false` 行为一致。
- **分页**：`--page` 1 起步，`--page-size` 默认 10；历史列表由服务端分页，running fallback 会对 pipeline 元数据应用相同的分页窗口。返回条数严格等于请求的 `page-size`（最后一页可能更少），不会静默超发。
- **`--version <1|2|both>`**：后端有 default（version=1）与 `version=2` 两个 release pool。默认 `both` 会做**全局合并**——对两个 pool 各拉取第 `1..page` 页，按 releaseId 去重、按 `startTime` 降序排序后切出请求的那一页，因此翻页在全局有序流上是精确的（不会漏掉边界行），代价是 `2 × page` 次请求；`--version 1` 或 `--version 2` 只查单个 pool，走服务端精确分页（单次请求，更快）。`data.version` 回显实际查询的 pool，`data.note` 用自然语言说明是否合并，`data.has_more` 标识本页之后是否还有更多结果。`both` 模式下 `data.total` 是两 pool total 之和（上界，跨 pool 的同一 release 可能被重复计数）。
- **认证**：标准 ByteCloud JWT（`x-jwt-token` header），首次使用前确认已登录对应凭证分区：`BYTEDCLI_CLOUD_SITE=us-ttp bytedcli auth status`（i18n RM 使用 i18n-tt JWT，检查命令为 `BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth status`），否则会报 `获取字节云 JWT 失败: 401`。
- **JSON 输出结构**：
  - `release-manager release get` → `data` 为完整 detail（pipeline / state / strategy / workflow[] / clusters[] / abTestInfos[] / repoVersions[] / rollbackInfo / actions[] / raw）
  - `release-manager release list` → `data.releases[]` 为分页列表，每条包含 releaseId / state / strategy / creator / currentStage / startTime / baseVersions[] / targetVersions[]（版本号字符串，已从后端 `{repoName, version}` 对象归一化）；`data.releases[]` 条数严格等于请求的 `page_size`（最后一页可能更少）；`data.version` 回显查询的 pool（`1`/`2`/`both`），`data.note` 说明是否跨 pool 合并，`data.has_more` 标识本页之后是否还有更多；`both` 模式下 `data.total` 为两 pool total 之和（上界）；`data.source` 标识 `release-list` 或 `pipeline-running-releases`，`data.warnings[]` 说明是否触发 fallback
  - `release-manager release create` → `data.release_id` 为新 release id，另含 pipeline / strategy / enqueue / auto_start
  - `release-manager release execute` → 默认（不带 `--yes`）返回 `data.dry_run: true` 与 `data.request`（待提交操作预览）；加 `--yes` 后 `data.command` / `data.release_id` 回显已提交操作，`data.raw` 为后端原始返回（通常为 null）
  - `release-manager pipeline list` → `data.pipelines[]` 每条包含 name / desc / owners[] / subscribed / runningReleaseCount / runningReleaseIds[] / lastUpdate；`data.total` 为服务端总数（后端返回 pageInfo 时出现）
- **running 空结果自动恢复**：部分控制面的 `release list --running` 会返回空列表，即使 pipeline 确有进行中的 release。CLI 会自动精确匹配 pipeline、读取 `runningReleaseIds` 并逐条 `release get`；触发时文本模式显示 Warning，JSON 模式通过 `source` 和 `warnings[]` 标识。
  - `release-manager pipeline scm-versions` → `data.repos[]` 每条包含 name / defaultBaseVersion / versions[]（version / branch / commit / commitInfo / type / disabled），JSON 始终返回全部版本；`disabled: true` 的版本不能用于 `release create`，选版本时必须挑 `disabled: false` 的条目
  - `release-manager pipeline queue` → `data.v1` / `data.v2` 两个队列视图（v2 为现行，v1 可能为空），各含 lockerOwner 与 entries[]（action / user / releaseId / autoStart / enqueueTime / note）；排队中 createRelease 的 releaseId 是预分配 id，落库前 `release get` 会报 not-found

## References

- [rm.md](./references/rm.md)
