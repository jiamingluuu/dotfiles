# BITS 发布单 TCC Draft 与 Deploy Target

执行以下命令前读取本文档：

```text
bits release tcc-config create
bits release tcc-config get
bits release tcc-config update
bits release tcc-config delete
bits release tcc-deploy-target get
bits release tcc-deploy-target update
```

这些命令操作发布单内的 TCC change item：`create` 新建一个没有线上 source 基线的 Draft，其余命令只操作已经存在的 change item。它们不会导入 source config、物化 TCC 版本、执行 `pipeline sync-tcc`、运行流水线、推进 stage 或发布 TCC 配置。

## 对象边界

- `tcc-config` 操作一个 Draft，选择键是发布单 ID、PSM、source control plane、config name、source region、source dir；`create` 是例外——它在该坐标新建一个无线上 source 基线的 Draft。
- `tcc-deploy-target` 操作一个 `regionChangeItem` 的完整 BOE / PPE / PROD 目标快照，选择键不包含 config name。
- `tcc-config delete` 删除整条变更项：该 source 坐标下全部已导入配置、Draft 编辑内容与 deploy target 一起移除；它不发布任何配置，也不是单配置操作。
- deploy target 不是 Draft 正文，也不是流水线执行状态。设置 target 只声明后续发布面向哪里。
- `--control-plane` 与 target spec 中的 `control-plane` 使用语义值：`cn`、`i18n`、`eu-ttp`、`us-ttp`、`i18n-bd`。
- source control plane 始终使用 TCC 语义。Release change-item list 的 EU/US slice 编号不同，CLI 会自动执行 `eu-ttp: TCC 3 -> Release 4`、`us-ttp: TCC 4 -> Release 5` 的内部查询映射；Draft endpoint 和候选身份仍使用 TCC source ID。
- 发布单 ID 按十进制字符串处理，不能先转成 JavaScript number。

## 查询 Draft

默认查询只输出元数据和 `content_sha256`，正文从 text 和 JSON 中完全省略：

```bash
bytedcli --json bits release tcc-config get \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default
```

只有明确需要编辑正文时才使用 `--content-output`。输出文件权限为 `0600`；默认拒绝已有文件和 symlink，显式 `--force` 时以新私有文件替换目标而不跟随 symlink。下面先 fail-closed 地创建系统临时目录，避免把正文落入 Git 工作区；在同一 shell 中继续执行后续 update：

```bash
release_tcc_tmp="$(mktemp -d)" || exit 1
trap 'rm -rf -- "$release_tcc_tmp"' EXIT
chmod 700 "$release_tcc_tmp" || exit 1

bytedcli bits release tcc-config get \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --content-output "$release_tcc_tmp/demo_config.json"
```

## 创建 Draft

`create` 在发布单上新建一个没有线上 source 基线的 Draft，适用于线上还不存在该配置、需要随本次发布一起新增的场景。它要求该 PSM 的 TCC project 已挂载到发布单：新建发布单时用 `bits release create-ticket --tcc-psm <psm>@<plane>` 挂载（可重复；同一 PSM 多控制面写 `<psm>@cn,i18n`，approvers 缺省自动填当前登录的个人账号，服务账号登录时不会自动填、需显式传 `--release-approvers`），或用 `--copy-from-rt-id <同 PSM 的历史发布单>`；未挂载时 create 报 `BITS_TCC_PROJECT_NOT_FOUND`。若线上同坐标已存在同名 source 配置，改用 `tcc-config import` 导入。固定创建 `static` 配置，`--data-type` 支持 `json`、`yaml`、`string`（默认 `json`）；`--encrypted`、`--with-l4-data`、`--cdn-supported` 均默认关闭；`--content-file` 按 UTF-8 最大 4 MiB。命令会实时解析目录 ID 与 storage version，不要从浏览器抓包复制这些内部 ID 作为参数。

先 dry-run 预览计划。text / JSON 输出都不回显正文与 payload，只包含 `content_sha256`：

```bash
bytedcli --json bits release tcc-config create \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --description "Demo config" \
  --content-file ./demo_config.json \
  --dry-run
```

检查发布单、PSM、控制面、config、region、目录与目录 ID、`storage_psm_version`、`content_sha256` 与 `plan_sha256`。向用户展示计划并取得该创建操作的明确授权后，使用完全相同的选择器与正文，回传计划 hash 执行 live：

```bash
create_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli --json bits release tcc-config create \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --description "Demo config" \
  --content-file ./demo_config.json \
  --expected-plan-sha256 "$create_plan_sha256" \
  --yes
```

`plan_sha256` 覆盖 workflow、source 坐标、config 名称、描述、数据类型、三个能力开关、正文 hash，以及 preflight 解析出的 storage version 与目录 ID。live 提交前会立即重跑 preflight 并重算计划：project 未挂载（`BITS_TCC_PROJECT_NOT_FOUND`）、同坐标 Draft 已存在（`BITS_TCC_DRAFT_ALREADY_EXISTS`）、线上出现同名 source 配置（`BITS_TCC_SOURCE_CONFIG_ALREADY_EXISTS`）、目录无法唯一定位或任何字段漂移，都会在首次写入前以对应错误或 `BITS_TCC_DRAFT_PLAN_CONFLICT` 失败。创建接口成功时可能返回空对象；CLI 以 change-item detail 回读 `region + dir + config-name`，恰好一条匹配才确认成功（`confirmed=true`，返回 `change_item_id` 与 `draft_config_id`）。请求提交后发生网络错误、HTTP 408/5xx 或成功响应结构异常时报告 outcome unknown；回读失败或多条匹配报告 partial success——这两类结果都先重新 `get` 检查当前状态，禁止盲目重试。

## 更新 Draft

更新使用完整正文替换，不是 patch。必须先查询并记录 `content_sha256`，再用同一精确选择器 dry-run：

```bash
content_sha256='paste-the-latest-64-character-content-sha256-here'
bytedcli --json bits release tcc-config update \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --content-file "$release_tcc_tmp/demo_config.json" \
  --expected-content-sha256 "$content_sha256" \
  --dry-run
```

检查发布单、change item、config、Draft/source/baseline/version identity、旧/新 SHA-256、`plan_sha256` 和变更字段。向用户展示计划并取得该 Draft 写入的明确授权后，使用完全相同的选择器、正文与 metadata，回传计划 hash 执行 live：

```bash
draft_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli --json bits release tcc-config update \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --config-name demo_config \
  --region US-East \
  --dir /default \
  --content-file "$release_tcc_tmp/demo_config.json" \
  --expected-content-sha256 "$content_sha256" \
  --expected-plan-sha256 "$draft_plan_sha256" \
  --yes
```

命令会在生成计划后、PUT 紧邻之前再次读取完整 Draft snapshot，检查内容 hash、计划 hash 和导入身份，保留未显式替换的 metadata，写入后再完整回读。计划 hash 还锁定 change item、Draft/source config ID、baseline/draft/storage version、directory ID、正文 hash 和下一版 metadata；同坐标 Draft 被重新导入但正文相同也会被拒绝。

update 的 text / JSON 输出（包括 dry-run）只包含 hash 与变更摘要，不包含 `--content-file` 中的新正文，也不回显包含正文的 PUT payload。

完成所需的 dry-run/live update 后立即清理，不要等待长期交互式 shell 退出：

```bash
if rm -rf -- "$release_tcc_tmp"; then
  trap - EXIT
  unset release_tcc_tmp
else
  echo "failed to remove sensitive TCC temporary directory" >&2
fi
```

`content_sha256` 与 `plan_sha256` 是 CLI 侧漂移门禁，不代表后端提供原子 CAS。请求提交后发生网络错误、HTTP 408/5xx 或成功响应结构异常时，结果会标记为 outcome unknown；先重新查询，不要盲目重试。

## 查询 Deploy Target

先用 source 坐标唯一定位 change item，并记录 `snapshot_sha256`：

```bash
bytedcli --json bits release tcc-deploy-target get \
  --ticket-id 123456789 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default
```

结果同时返回完整 BOE / PPE / PROD target arrays。`snapshot_sha256` 覆盖 change item ID、storage PSM version 和三个完整数组；对象字段顺序不影响 hash，数组顺序保留。

## 更新 Deploy Target

每个环境都是“完整替换该环境目标集合”的语义。重复传不同 target 可以保留多个目标；同一目标分别使用 region code 与 region name 表达时会在 metadata 解析后按规范坐标去重。显式 clear flag 用于清空一个环境：

```bash
snapshot_sha256='paste-the-latest-64-character-snapshot-sha256-here'
bytedcli --json bits release tcc-deploy-target update \
  --ticket-id 123456789 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default \
  --prod-target control-plane=i18n,region=US-East,dir=/default \
  --prod-target control-plane=eu-ttp,region=EU-West,dir=/default \
  --expected-snapshot-sha256 "$snapshot_sha256" \
  --dry-run
```

可用参数：

- `--boe-target` / `--ppe-target` / `--prod-target`：重复传入，格式为 `control-plane=<plane>,region=<region>,dir=<dir>`。
- `--clear-boe` / `--clear-ppe` / `--clear-prod`：清空对应环境，不能和同环境 target 同时传。
- 六个 target / clear 参数至少传一个；每个环境的 target 集合与 clear flag 最多选择一类。
- 未点名的环境数组会原样保留，包括当前 CLI 不认识的字段。

dry-run 返回 `previous_snapshot_sha256`、计划后的 `snapshot_sha256`、`plan_sha256`、
`changed_environments` 和完整 PUT payload。确认 source 坐标、三个环境数组和 storage version 后，
取得该 deploy-target 写入的明确授权，再把 `--dry-run` 替换为 `--yes`，同时回传计划 hash：

```bash
target_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli --json bits release tcc-deploy-target update \
  --ticket-id 123456789 \
  --psm example.service.api \
  --source-control-plane i18n \
  --source-region US-East \
  --source-dir /default \
  --prod-target control-plane=i18n,region=US-East,dir=/default \
  --prod-target control-plane=eu-ttp,region=EU-West,dir=/default \
  --expected-snapshot-sha256 "$snapshot_sha256" \
  --expected-plan-sha256 "$target_plan_sha256" \
  --yes
```

live 命令会重新读取并校验 snapshot 与 plan 两个 expected hash，从实时 TCC region list 补齐新目标
metadata，然后 PUT 完整四字段快照：`boeTargetItems`、`ppeTargetItems`、`prodTargetItems`、
`storagePsmVersion`。`plan_sha256` 覆盖 workflow/source 坐标、旧 snapshot、变更环境和完整 PUT
payload；即使旧 snapshot 相同，目标参数发生变化也不能复用授权。回读会验证 change item ID 与每个
环境规范化后的 target 坐标集合；后端可以递增 storage version、重排数组或规范化 metadata，所以
这不是对象逐字比较。hash 是 CLI 侧门禁，不是服务端原子 CAS；outcome unknown 或 partial success
时先重新 get，不要盲目重试。

## 删除变更项

`delete` 按变更来源整条删除：source 坐标（control plane + region + dir）下的全部已导入配置、Draft 编辑内容和 deploy target 一起移除。选择器与 `tcc-deploy-target` 相同，不含 config name。误导入的变更项用它移除；不要用 BITS Web 的「删除配置」处理误导入——那会把配置标记为发布后从线上彻底删除，属于发布内容，不是移除条目。

先 dry-run 查看将删除的配置清单：

```bash
bytedcli --json bits release tcc-config delete \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --region US-East \
  --dir /default \
  --dry-run
```

检查 `change_item_id`、`storage_psm_version`、`configs[]`（每条的 config id / name、source config id、baseline version）、`deploy_target_snapshot_sha256` 与 `plan_sha256`。向用户展示清单并取得该删除操作的明确授权后，回传计划 hash 执行：

```bash
delete_plan_sha256='paste-the-latest-64-character-plan-sha256-here'
bytedcli --json bits release tcc-config delete \
  --ticket-id 123456789 \
  --psm example.service.api \
  --control-plane i18n \
  --region US-East \
  --dir /default \
  --expected-plan-sha256 "$delete_plan_sha256" \
  --yes
```

`plan_sha256` 覆盖 workflow、source 坐标、change item ID、storage version、全部配置身份与 deploy-target 快照 hash；live 提交前会立即重读并重算计划，任一项漂移都以 `BITS_TCC_CHANGE_ITEM_DELETE_PLAN_CONFLICT` 失败。成功以删除后的 change-item 回读为准（`readback_verified=true`）。网络错误、HTTP 408/5xx 或无法分类的成功响应报告 outcome unknown；回读失败或变更项仍在时报 partial success——这两类结果都先重新查询，禁止直接重试。

## Agent 写操作授权

- `tcc-config create`、`tcc-config update`、`tcc-config delete` 与 `tcc-deploy-target update` 是四个独立写操作，授权不能互相替代。
- 每次 live 写入前必须先用完全相同的目标和变更参数 dry-run，展示发布单、选择坐标、旧/新 hash 及计划摘要，并等待明确授权。
- 参数、正文、目标数组或服务端快照变化后，必须重新 dry-run 并重新取得授权。
- Draft/target 写入授权不包含 `pipeline sync-tcc`、`pipeline run`、stage 推进或 TCC 发布。


### TCC 控制面与写后确认

- 发布目标的 `--source-control-plane` / target spec `control-plane`，以及 release TCC 命令的 `--control-plane` 使用 `cn`、`i18n`、`eu-ttp`、`us-ttp`、`i18n-bd`。`develop tcc-config create --control-plane` 使用对应数字 `1`、`2`、`3`、`4`、`6`；例如 `I18N_BD` 使用 `6`，语义名称为 `i18n-bd`。不要套用其他 Bits 资源的数字枚举。
- `--source-control-plane` 定位已导入配置的来源；`--boe-target` / `--ppe-target` / `--prod-target` 中的 `control-plane` 指定部署目标，两者可以不同。Draft 的 `--control-plane`（支持该参数的命令）也是来源控制面。全局 `--site` 不选择 TCC 来源或目标。
- 非默认目录的 change item 若返回 `dirId=0`，CLI 按 namespace、来源控制面、region、directory 唯一查目录，并核对源配置与草稿的真实 ID 和路径。目录歧义、缺少源配置或 ID/路径冲突会阻止继续；部署参数使用核验后的真实 ID。
- 草稿或部署目标 PUT 返回不明确的响应时，CLI 不重试写入，而是只读回查。草稿必须版本递增、内容和 metadata 一致；部署目标必须 storage version 递增、各环境目标一致，才确认成功。无法确认时返回 `*_OUTCOME_UNKNOWN`，先用对应 `get` 检查当前状态，禁止盲目重试。

- deploy-target 仅 `--boe-target` 中的 `control-plane` 额外支持 `boe`（兼容目标 ID `5`），`--ppe-target` / `--prod-target` 保持上述五种控制面，如 `--boe-target 'control-plane=boe,region=China-BOE,dir=/default'`；不改变 source 或 release workflow slice 的枚举（release slice `5` 仍为 US）。省略 PPE/PROD 参数会保留这两类完整目标。回读允许 `dirId`、`dirName` 规范化以及等价的 `dir`/`dirs` 表示，但控制面、region、路径和重复数量必须一致。
