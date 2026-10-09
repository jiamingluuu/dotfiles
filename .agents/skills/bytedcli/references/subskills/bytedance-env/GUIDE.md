---
name: bytedance-env
description: "Use bytedcli ENV for environment search, 治理服务部署模版/deploy_template, baseline creation, TCE/TCC deployment or deploy-tce dry-run payload previews, PPE TCE upgrades from Git branch/SCM version, persistent branch-push auto-update pipelines/自动更新流水线 (create/delete), devices/tickets, bytefaas/FaaS PPE 泳道部署/挂载/upgrades (upgrade-bytefaas), ByteCopy services/instances/target addresses, and list-scm-deps/SCM 依赖 by PSM."
---

# bytedcli ENV

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

- 查看我收藏的 ENV
- 查看我管理的 ENV
- 按环境标识搜索 ENV
- 按服务（PSM）搜索 ENV
- 列出 ENV 下的服务列表
- 查某 PSM 在某 ENV 部署使用的 SCM 仓库与版本（含主仓 Git 地址）
- 列出创建流程可选基准环境
- 查看基准环境可用机房
- 创建前校验环境名
- 创建 ENV
- 向 ENV 部署 TCE/TCC 服务
- 一次性升级 TCE 服务（可指定集群、Git 分支、SCM 依赖 env_type 或 SCM 版本）
- 创建/删除 ENV service 的持久自动更新流水线：绑定 SCM 仓库分支，分支 push 后触发热更新
- 按 ENV 平台"集群模板"（如 UI 中"上次所选集群" / "online_cn 默认"）一把部署 TCE 多集群
- 列出某 service 的"集群模板"下拉数据源（cluster_param_template）
- 部署 bytefaas（ByteCloud FaaS）服务到 PPE 泳道
- 升级 PPE 泳道里已挂载的 bytefaas 实例到新的 SCM 版本
- 管理 ENV ByteCopy：按名称查看 ByteCopy service、查看 service 下 instance、查看/添加 instance 的目标地址
- 设备管理（新增/续期/解绑/列表）
- 工单查询（列表/详情）
- 需要跨站点（cn/boe/i18n-tt/i18n-bd/us-ttp/eu-ttp）统一查询

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

Commands are grouped under `env site`, `env service`, `env bytecopy`, `env device`, and `env ticket`. Old flat names (e.g. `env list-sites`, `env list-starred-env`, `env deploy-tce-service`) still work as hidden aliases.

```bash
# 查看站点与动态 standard_env 列表
bytedcli env site list

# 查看收藏/管理 ENV（默认查全部站点）
bytedcli env list-starred --page 1 --page-size 10
bytedcli env list-managed --page 1 --page-size 10

# 指定站点（支持重复或逗号）
bytedcli env list-starred --env-site cn --env-site boe
bytedcli env list-managed --env-site i18n-tt,us-ttp

# 按环境标识搜索
bytedcli env search --keyword "ppe_coze" --env-site eu-ttp

# 按服务搜索（先 service suggest，再按 psm 查询）
bytedcli env search-service --service "example.service.api" --env-site cn,boe

# 列出 ENV 下的服务列表
bytedcli env service list --env "ppe_qianchuan2" --standard-env online_cn
bytedcli env service list --env "ppe_qianchuan2" --standard-env online_cn --service-types tce --page 1 --page-size 20
bytedcli env service get --instance-id 123456 --standard-env online_cn

# 创建流程：基准环境 / 机房 / 名称校验 / 创建
bytedcli env site baseline-list
bytedcli env site baseline-zones --standard-env online_cn
bytedcli env check-name --name "ppe_demo" --standard-env online_cn
bytedcli env create --name "ppe_demo" --standard-env online_cn --idc LF --visibility private

# 部署/升级服务
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_i18nbd --psm "example.service.api" --flow-base prod
# 自定义资源租期：UI"添加服务"弹窗里的"租期"输入框对应 --lease-days，--lease-rule-id 透传系统策略 id
bytedcli env service deploy-tce --env "boe_demo" --standard-env boe --psm "demo.sample.svc" --flow-base prod --lease-days 2 --lease-rule-id 145
bytedcli env service deploy-tcc --env "ppe_demo" --standard-env online_i18nbd --psm "demo.sample.svc"
# upgrade-tce 是真实写操作：必须显式传 --dry-run（预览已解析的集群与 SCM 仓库）或 --yes（提交）二选一
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_i18nbd --psm "example.service.api" --cluster-id 12345 --flow-base prod --scm-env-type prod --scm-repo-version "1.0.0.370" --yes
# 预览从指定 Git 分支一次性升级现有 PPE TCE 集群；--dry-run 不触发编译或提交
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --cluster-id 12345 --branch "feat/demo" --dry-run
# --all 先预览该 PSM 当前的全部 cluster_ids 和解析后的 scm_repos；不要自动紧接着执行 --yes
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --all --branch "feat/demo" --dry-run
# 用户确认预览后，把返回的 cluster_ids 原样带入 --expected-cluster-ids；成员变化时提交会被阻止
bytedcli env service upgrade-tce --env "ppe_demo" --standard-env online_cn --psm "demo.sample.service" --all --expected-cluster-ids 111,222 --branch "feat/demo" --yes

# 持久自动更新流水线：绑定 SCM 仓库分支，分支 push 后触发热更新（不同于一次性 deploy/upgrade）
bytedcli env service auto-update create --env "ppe_demo" --standard-env online_cn --env-type ppe --psm "demo.psm.tce" --repo "demo/service/api" --branch "debug/demo"
# 已存在同一 env+psm 的自动更新流水线时，命令返回已有流水线，不重复创建。
# 删除持久自动更新流水线需要 --yes；若已不存在，命令返回 deleted=false。
bytedcli env service auto-update delete --env "ppe_demo" --standard-env online_cn --env-type ppe --psm "demo.psm.tce" --yes

# 按 ENV 平台"集群模板"部署（等价 UI"集群模板"下拉，一次写入多集群分集群配置）
bytedcli env service list-cluster-templates --psm "demo.psm.tce" --standard-env online_cn
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --cluster-template-name "上次所选集群"
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --cluster-template-id 22708

# ENV 治理"服务部署模版"（deploy_template，与上述 cluster_param_template 独立）
bytedcli env service deploy-template list --psm "demo.psm.tce" --standard-env online_cn
bytedcli env service deploy-template list --psm "demo.psm.tce" --standard-env online_cn --page 1 --page-size 20 --include-disabled

# 按 PSM 查该环境部署使用的 SCM 仓库与版本（含主仓 Git 地址；只读）
bytedcli env service list-scm-deps --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce"

# 部署前预览将提交的集群与 DSL payload（只读；与提交共用同一条解析链路）
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --dry-run

# 部署/升级 bytefaas（PPE 泳道）
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas"
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --scm-version "1.0.0.123"
bytedcli env service upgrade-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --scm-version "1.0.0.124"

# 允许远程调试：置 meta.debug=true（默认关闭）
bytedcli env service deploy-tce --env "ppe_demo" --standard-env online_cn --psm "demo.psm.tce" --allow-debug
bytedcli env service deploy-bytefaas --env "ppe_demo_swimlane" --standard-env online_cn --psm "demo.psm.faas" --allow-debug

# ENV ByteCopy（CN/SG/EU/US：--site cn|i18n-tt|eu-ttp|us-ttp）
bytedcli env bytecopy service get --site i18n-tt --service-name "demo.service"
bytedcli env bytecopy instance get --site eu-ttp --service-name "demo.service" --instance-name "demo.instance"
bytedcli env bytecopy target-address list --site i18n-tt --instance-id 67890
bytedcli env bytecopy target-address add --site i18n-tt --instance-id 67890 --target-address 192.0.2.11:8080 --ttl 30

# 设备管理
bytedcli env device list --env "ppe_demo" --standard-env online_i18nbd
bytedcli env device add --env "ppe_demo" --standard-env online_i18nbd --device-id 4252524525 --expire-at "2026-02-19T01:19:40.471Z"
bytedcli env device update --env "ppe_demo" --standard-env online_i18nbd --device-id 4252524525 --expire-at "2026-02-19T09:19:58+08:00"
bytedcli env device unbind --standard-env online_i18nbd --device-id 4252524525

# 工单
bytedcli env ticket list --env "ppe_demo" --standard-env online_i18nbd --page 1 --page-size 10
bytedcli env ticket get --ticket-id 2021755505366867968 --standard-env online_i18nbd
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json env ticket get --ticket-id 2021755505366867968 ...`）
- `--env-site` 支持：`cn|boe|i18n-tt|i18n-bd|us-ttp|eu-ttp`
- ByteCopy 命令使用 `--site cn|i18n-tt|eu-ttp|us-ttp`，对应控制台里的 CN、SG、EU TTP、US TTP；不要用 `--env-site`
- `create` 名称规则：
  - `online_*` 必须 `ppe_` 前缀
  - `boe*` 必须 `boe_` 前缀
- `env create --idc` 使用机房短值（如 `LF`）。若 `site baseline-zones` 的 `idc_list`
  返回 `China-North/LF`，可传 `LF` 或原样传该组合值；CLI 会校验并将创建请求中的
  `env.idc` 及结果中的 `idc` 规范化为 `LF`，不会把区域前缀写入环境机房字段。
  组合值必须与返回列表匹配，不能随意拼接区域；机房列表不可用时不能使用组合值。
- 翻页参数统一是 `--page` + `--page-size`。`--page-num` 是 `--page` 的隐藏别名仍可用；
  **`--size` 不是别名**，传了会直接 `unknown option '--size'`（CLI_PARSE_ERROR）

## Agent 易踩坑

- **`--standard-env` 填错不会报错，会返回空列表。** 例如对 `boe_*` 环境误填 `online_cn` 时，
  `env service list` 返回 `status:"success"`、`data.result.pagination.total` 为 `0`、`items` 为空，
  与「这个环境里确实没有该服务」无法区分，Agent 容易据此得出「服务没部署过」的错误结论。
  只有 `boe*` → `boe` 是唯一确定的；`ppe_*` 只说明它是 online 基线，具体落在
  `online_cn` / `online_i18n` / `online_i18nbd` / `online_usttp` / `online_euttp` 中的哪一个由**站点**决定，
  必须用 `bytedcli env site list` 确认（返回里每个站点各带自己的 `standard_env`）。
- **拿不到某个环境里服务的 `cluster_id` 时，不要在 `env service list` 上找。** 它打的是
  `instance_meta` 接口，返回里没有 cluster 字段；`data.result.items[].id` 是 instance_meta id，不是
  cluster id，误当成 cluster id 传给 `bits env deploy-upgrade --cluster-id` 会把部署发到别处。
  cluster id 有两条路，返回同一个值：`bytedcli env service get --instance-id <instance_meta id>
  --standard-env <standard-env>` 取 `data.result.instances[].id`，或
  `bytedcli --site <site> tce cluster list --psm <psm> --env <env>` 取 `data.clusters[].meta.id`
  （后者漏 `--site` 会报 `TCE_NOT_FOUND`，那不代表服务不存在；另见 `bytedance-tce` skill）。

## PPE TCE 一次性分支升级

用户要求“用 Git 分支更新 PPE PSM”“把现有 PPE TCE 集群升级到某分支”时，使用
`env service upgrade-tce --branch`。先用 `--dry-run` 预览已解析的 cluster IDs 与 SCM repositories；
该模式不会编译或提交。单集群操作在用户明确确认同一计划后，将 `--dry-run` 改为 `--yes`，
ENV/SCM 才会对推断出的主仓触发一次分支编译和升级：

```bash
bytedcli env service upgrade-tce \
  --env ppe_demo \
  --standard-env online_cn \
  --psm demo.sample.service \
  --cluster-id 12345 \
  --branch feat/demo \
  --dry-run
```

- `--cluster-id <id>` 升级单个集群；`--all --dry-run` 会先查当前 ENV 下该 PSM 的 service detail，
  返回所有 TCE `cluster_ids` 和已解析的 `scm_repos`。用户确认后，提交命令必须把这些 ID 作为
  `--expected-cluster-ids <id1,id2>` 传回；若提交时集群成员已变化，命令会阻止写入并要求重新预览。
- `--branch` 与 `--scm-repo-name` / `--scm-repo-version` 互斥；已有明确制品版本时改用
  `--scm-repo-version <version>`。
- 多集群升级推荐 `--all --branch <branch>`，避免对同一 PSM 的每个集群分别触发分支编译。
- 已知平台时序问题：少数情况下 ENV 会在 SCM 版本仍处于 building 时把"SCM 编译"步骤标成
  Succeed 并推进 TCE 升级，随后 TCE 报 `is not a successful version`。遇到此错误时，先在
  工单详情或 SCM 链接里确认生成的版本号并等待构建成功。重试时保留原集群选择器：原操作使用
  `--cluster-id <id>` 就继续使用同一 ID，只有原操作使用 `--all` 时才继续使用 `--all`。先配合
  `--scm-repo-version <version> --dry-run` 复核；单集群获得明确确认后再改为 `--yes`，`--all` 则还要
  把此次 dry-run 返回的 `cluster_ids` 作为 `--expected-cluster-ids <id1,id2>` 带入 `--yes` 提交。
  不要再次用 `--branch` 重复触发新版本。
- `upgrade-tce --branch` 只执行一次升级。需要分支后续每次 push 都自动更新时，使用
  `env service auto-update create --branch` 创建持久流水线。
- 目标必须是现有 TCE 服务；不用 `--all` 时，`--cluster-id` 从 `env service get` 的实例详情获取。
- Bytefaas PPE 仍只支持 SCM 制品，不要把本节 `--branch` 用到 `upgrade-bytefaas`。

## ENV ByteCopy

### 触发场景

- 用户给出 ENV ByteCopy 控制台 URL，或提到 ByteCopy service / instance。
- 用户要按 service name 或 instance name 查看 ByteCopy service / instance。
- 用户要创建、启动或停止 instance，或在具体 instance 上添加"目标地址"。

在 ByteDance 生产网络环境中调用 `env bytecopy --site i18n-tt` 时，设置 `BYTEDCLI_NETWORK_PROFILE=prod`；bytedcli 会自动把 i18n-tt 路由到生产网可达域名。

### 命令示例

```bash
# 查 ByteCopy service
bytedcli env bytecopy service get --site i18n-tt --service-name demo.service

# 查看某个 service 下的 instance
bytedcli env bytecopy instance get --site eu-ttp \
  --service-name demo.service --instance-name demo.instance

# 创建不会自动启动；所有业务值均需调用方显式提供
bytedcli env bytecopy instance create --site i18n-tt \
  --service-name example.service.api --instance-name demo.instance \
  --source-env MESH --source-type PSM --protocol THRIFT --dc sg1 \
  --required-function forward --env prod --cluster default \
  --sd-name dev.example.sg1.demo --online-data-percent 100 \
  --force-mode false --context-json '{}' --yes

# 也可将完整后端 InstanceReq JSON 原样提交；不能与上述字段参数混用
bytedcli env bytecopy instance create --site i18n-tt   --service-name example.service.api   --request-json '{"InstanceName":"demo.instance","SourceEnv":"MESH"}' --yes

# 启动与停止是独立命令；start-storage 必须显式选择
bytedcli env bytecopy instance start --site i18n-tt \
  --instance-id 67890 --start-storage false --yes
bytedcli env bytecopy instance stop --site i18n-tt --instance-id 67890 --yes

# 查看 / 添加 instance 目标地址
bytedcli env bytecopy target-address list --site i18n-tt --instance-id 67890
bytedcli env bytecopy target-address add --site i18n-tt \
  --instance-id 67890 --target-address 192.0.2.11:8080 --ttl 30
```

### 关键参数

- `--site` 支持 `cn`（CN）、`i18n-tt`（SG）、`eu-ttp`（EU TTP）、`us-ttp`（US TTP）。
- `--service-name` 是 ByteCopy service 名称。
- `--instance-name` 是 ByteCopy instance 名称。
- `--instance-id` 来自 `env bytecopy instance get` 或控制台 instance URL。
- `instance create` 忠实映射创建接口，不提供 instance、env、cluster、dc、sdName 等业务默认值，也不会隐式启动；不传 `--yes` 时只预览请求。
- `--request-json` 可原样提交完整后端 `InstanceReq`，并与其他创建字段参数互斥。
- `--source-env`、`--source-type`、`--protocol`、`--dc`、`--required-function`、`--force-mode` 和过滤参数按后端组合规则显式提供；MESH forward 需要 `--env`/`--cluster`，NON-MESH 不接收这两个过滤字段；`--thrift-transport` 仅用于 NON-MESH THRIFT；完整参数以 `instance create --help` 为准。
- `instance start` 必须显式传 `--start-storage true|false`；start/stop 都必须传 `--yes`，且 create、start、stop 彼此不隐式串联。
- `--target-address` 使用 `ip:port`；IPv6 用 `[2001:db8::1]:8080`。
- `target-address add` 的 `--ttl` 单位是分钟，默认 `30`。

## PPE bytefaas 部署

### 触发场景

- 用户说"把 bytefaas/FaaS 发到 PPE 泳道"、"PPE 挂载 FaaS"、"测试环境部署 FaaS"。
- 用户在 PPE/泳道场景下要升级一个已挂载的 bytefaas 实例到新的 SCM 版本。

### 关键区分：PPE 部署 vs 生产发布

- `bytedcli env service deploy-bytefaas` / `upgrade-bytefaas`：走 **ENV 平台**，把 bytefaas 实例挂到 **PPE 泳道**，用于测试与联调。
- `bytedcli faas release create`（`bytedance-faas` skill）：走 **FaaS 平台**，做生产 cluster 的正式发布。

如果用户要做生产发布，改走 `bytedance-faas` skill；PPE/泳道场景走本节命令。

### 命令示例

```bash
# 首次把 bytefaas 服务挂到 PPE 泳道(自动取 prod 基线最新 SCM 版本)
bytedcli env service deploy-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas

# 显式指定 SCM 版本号
bytedcli env service deploy-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas --scm-version 1.0.0.123

# 升级已挂载实例到新的 SCM 版本
bytedcli env service upgrade-bytefaas \
  --env ppe_demo_swimlane --standard-env online_cn \
  --psm demo.psm.faas --scm-version 1.0.0.124
```

### 关键参数

- `--env` / `--standard-env` / `--psm` 必填。
- `--standard-env` 是基线（`online_cn` / `boe` / `i18n` 等），不是泳道类型；PPE 类型由命令本身定位，必要时用 `--env-type` 覆盖。
- `--scm-version` 省略时自动从 ENV 取 prod 基线最新版。
- `--region` / `--cluster` 默认 `cn-north` / `faas-cn-north`。
- `--code-revision` 省略时使用最新 code revision。
- PPE bytefaas 实例默认 14 天短回收，CLI 暂不支持自定义租期。
- **没有** `--branch`：部署制品是 SCM 包，不是 git 分支。
- **没有** `--lease-days`：PPE bytefaas 实例固定为默认 14 天短回收，CLI 不暴露租期参数。

### Agent 易踩坑

- 把 `--standard-env` 当成"泳道类型"：`online_cn` 是基线，`ppe` 才是 env type；两者不要互换。
- 试图传 git 分支或 ICM 镜像标签：目前只支持 SCM 制品，镜像/分支不会被识别。
- 想做生产发布却调用 `deploy-bytefaas`：这条命令只会挂到 PPE 泳道，生产发布请走 `bytedance-faas`。

## 服务部署模版（Deploy Template）

ENV 治理页面中的“服务部署模版”对应独立的 `deploy_template` 资源。使用
`deploy-template list` 查询启用中的模版；需要同时查看停用模版时增加
`--include-disabled`。命令保留后端总数并提供标准 `--page` / `--page-size`
分页，默认每页 20 条、最多 100 条；后端每次最多返回 10 条时会自动聚合多页。

```bash
bytedcli env service deploy-template list \
  --psm demo.psm.tce --standard-env online_cn
```

该资源与部署弹窗“集群模板”下拉使用的 `cluster_param_template` 不同；
`deploy-template list` 只负责查询治理模版，不改变
`deploy-tce --cluster-template-id` / `deploy-tce --cluster-template-name` 的解析与部署行为。

## 集群模板（Cluster Param Template）

UI 中"集群配置 → 集群模板"下拉对应 ENV 平台的 `cluster_param_template` 资源。
模板返回的 `clusters[]` 已是部署所需的全量字段（`name / zone / virtual_cluster /
dc_infos / cpu / mem / count / base_cluster_id`），CLI 会直接拿来作为 `pre_check`
和 `dsl/env/{env}` 的 `clusters` 数组，**无需再调 create_suggest**。

```bash
# 列出该 service 的所有可选模板（含"上次所选集群"、"<standard_env> 默认"等）
bytedcli env service list-cluster-templates --psm demo.psm.tce --standard-env online_cn

# 等价 UI："集群模板 = 上次所选集群"，一把按多集群分集群配置部署
bytedcli env service deploy-tce --env ppe_demo --standard-env online_cn \
  --psm demo.psm.tce --cluster-template-name "上次所选集群"

# 也可以按 id（从 list 拿到）
bytedcli env service deploy-tce --env ppe_demo --standard-env online_cn \
  --psm demo.psm.tce --cluster-template-id 22708
```

集群配置参数优先级（高 → 低）：
`--cluster-template-id` / `--cluster-template-name` > `--cluster-spec-file`

> `--cluster-names` > 自动 suggest（`--specify-dcs/--zone/--virtual-cluster`）。

模板与 `--cluster-spec-file` / `--specify-dcs` / `--zone` / `--virtual-cluster`
互斥，混用会直接报 ENV_INPUT_ERROR。

## 按 PSM 查 SCM 依赖（list-scm-deps）

回答"这个服务在这个环境部署用的是哪些仓库、什么版本、主仓在哪"。数据与
`deploy-tce` / `upgrade-tce` 内部解析的是同一份接口结果，但**列出了全部基线 bundle**
（prod / boe_base / …）加 current，而部署只会按 `--flow-base`（默认 `prod`）选其中一个
bundle：默认场景看 `Env Type=prod` 的行；`--flow-base boe` 看对应 boe 行；显式传
`--branch` / `--scm-repo-version` 时以 override 为准。

```bash
bytedcli env service list-scm-deps --env ppe_demo --standard-env online_cn --psm demo.psm.tce
# bytefaas 服务加 --psm-type bytefaas
bytedcli env service list-scm-deps --env boe_demo --standard-env boe --psm demo.faas.svc --psm-type bytefaas
```

输出：

- **依赖表**：`Env Type`（基线 bundle 的 env_type/env 标签，或 `current`=当前部署中）
  × `Repo` × `Version` × `Branch` × `Is Main`。
- **主仓 Git 信息**：主仓（`main_repo=true`）的 `repo_id` / `git_url` / `desc`。该查询是 **best-effort**：SCM 侧查不到（重名/不存在）时依赖表照常输出，
  `main_repository` 为 null 并给出 `main_repository_error`。
- 分支 → 最新构建版本**不在本命令**：用 `bytedcli scm repo version list <repo> --branch <branch>`
  （已有命令，无需新入口）。

JSON 字段：`dependencies[]`（`env_type/name/version/branch/main_repo/path/remote_id/version_type`）、
`main_repository`、`main_repository_error`。

## 部署预览与确认（deploy-tce --dry-run / --yes）

`deploy-tce` 是真实写操作：必须显式传 `--dry-run`（预览）或 `--yes`（提交）二选一，与
`upgrade-tce` 一致。

`--dry-run` 与提交**共用同一条解析链路**（SCM 依赖 → 集群解析 → pre-check → DSL payload
构造），只是不调部署接口。因此：

- 预览里的 `deployment_slice` / `clusters` 就是同参数提交会发送的内容，不存在第二套
  "预览逻辑"可以与之漂移。
- pre-check 也会执行，预览即能发现部署是否会被拦下。

```bash
bytedcli env service deploy-tce --env ppe_demo --standard-env online_cn \
  --psm demo.psm.tce --dry-run
```

**输出**：`env / standard_env / env_type / psm / action / flow_base / branch / allow_debug /
scm_repos / clusters / cluster_spec / pre_check / deployment_slice`。

### 固定落点：cluster_spec 回传

`create_suggest` 非确定性：多个 zone 标 `is_suggested` 且每次返回顺序不同，选择逻辑取
第一个，因此**不传集群模板 / `--cluster-spec-file` / `--cluster-names` 时，连续两次解析
可能选中不同 zone**（`deploy-tce` 提交同样如此）。要把"确认过的预览"原样提交：

```bash
# 1) 预览并把解析出的单集群存成 spec 文件
bytedcli -j env service deploy-tce --env ppe_demo --standard-env online_cn \
  --psm demo.psm.tce --dry-run | jq '.data.cluster_spec' > cluster.json

# 2) 用显式 spec 提交（不再采样；注意去掉 --specify-dcs/--zone/--virtual-cluster，
#    它们与 --cluster-spec-file 互斥）
bytedcli env service deploy-tce --env ppe_demo --standard-env online_cn \
  --psm demo.psm.tce --cluster-spec-file cluster.json --yes
```

`cluster_spec` 仅在解析结果恰为**一个**集群时给出（自动推荐路径即是）；多集群的模板 /
基线名称路径无法用单对象 spec 固定，重新执行可能重新采样。

### selector 语义（重要）

`--specify-dcs` / `--zone` / `--virtual-cluster` 是**门禁**而不是**筛选**：`deploy-tce`
只要求至少一个候选匹配 selector，通过后会把**整批**候选都提交。dry-run 输出的
`clusters` 就是整批，不要以为只部署匹配上的那个。

## References

- `references/env.md`
