---
name: bytedance-byterec
description: "Operate the complete Byterec platform through bytedcli. Always use this skill whenever a task mentions Byterec、Candidate DB / CandsDB / 候选库、candidate_db URLs、Byterec Index Service / 正排索引服务、Byterec product/config/cluster/operation、Byterec model list、Viking service config / flags / ByteKV deploy / Viking DB / recall / DSL、Byterec Elements / 特征工程、Darwin feature group、抽前 raw feature、抽后 extracted feature、feature_space、zion_name、Rosetta OP、bfs_app、Byterec feature branch/pack/source/retriever、feature models、FID or sequence features. It is the single skill entry for every Byterec component; choose the relevant reference inside this skill instead of looking for component-specific Byterec skills."
---

# bytedcli Byterec

这是 Byterec 平台的唯一 Skill 入口。所有组件仍使用现有 `bytedcli byterec ...` 命令树；本 Skill 只统一 Agent 的触发、路由与操作约束，不改变任何组件命令或后端语义。

## 组件路由

先按用户目标读取对应 reference；一个任务跨多个组件时，读取所有相关 reference，再分别执行各自命令。

| 用户目标或线索 | 命令入口 | 必读 reference |
| --- | --- | --- |
| Candidate DB、CandsDB、候选库、`candidate_db/detail` URL、候选记录、抽样、监控、关联模型、候选库生命周期 | `byterec candidate-db ...` | [Candidate DB](references/candidate-db.md) |
| Elements、Darwin、特征工程、抽前/抽后特征、`feature_space`、`zion_name`、Rosetta OP、bfs_app、branch、pack、retriever、FID | `byterec elements ...` / `byterec darwin ...` | [Elements / Darwin](references/elements.md) |
| Index Service product/config/cluster/operation、模型配置、Viking service config/flags、ByteKV、Viking DB、recall、DSL | `byterec indexservice ...` / `byterec model ...` / `byterec viking ...` | [Index Service / Model / Viking](references/indexservice-viking.md) |

需要确认安装方式、全局参数、站点、JSON 输出时读 [通用调用方式](../../invocation.md)；命令报错或认证失败时读 [常见问题](../../troubleshooting.md)。

## 统一执行流程

1. 从组件名、页面 URL、资源字段和目标动作识别组件，不根据共享的 `byterec` 代码 domain 猜资源语义。
2. 读取对应组件 reference，确认资源选择器、分页、输出和写入边界。
3. 默认使用用户指定的 `--site`；用户未指定时使用 `i18n-tt`。Byterec 控制面路由为 `i18n*` -> VA/SG、`us-ttp` / `us-ttp-bdee` -> US BDEE、`eu-ttp` -> EU、`cn` -> CN；切换站点前先确认对应登录态。
4. `--json` 是全局参数，必须放在 `byterec` 之前；脚本或 Agent 后续还要消费结果时优先使用 JSON。
5. 查询操作可直接执行。写操作先运行不带 `--yes` 的 dry-run，核对目标和完整 payload；只有用户明确要求提交时才追加 `--yes`。
6. 提交后按组件 reference 指定的读接口回查，不把请求成功等同于最终状态正确。

## Authentication

Byterec 复用控制面返回的 BDSSO CAS realm 登录态。鉴权失败时优先执行错误中的 `auth_command`，不要自行猜测 SSO realm。常用登录与状态检查：

```bash
bytedcli --site i18n-tt --auth-site bytedance auth login --session
bytedcli --site us-ttp auth login --session
bytedcli --site us-ttp-bdee --auth-site bytedance auth login --session
bytedcli --site eu-ttp auth login --session
bytedcli --site cn auth login --session
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli auth status
```

`us-ttp-bdee` 的 Byterec 控制面当前返回 ByteDance CAS，因此其浏览器 session 必须存入
`bytedance` realm；Byterec 不使用 USTS，也不携带 `is_ttp=1`。运行时仍以控制面实际返回的
CAS redirect 为准。

## 不可混淆的资源边界

- Candidate DB 与 Viking DB 是不同资源和接口；不要因为都在 `byterec` 命令树下而互换 ID、path 或查询方式。
- Darwin production feature group 与 Elements `bfs_app` feature group 不是同一资源；前者用 `byterec darwin feature-group get`，后者用 `byterec elements feature-group ...`。
- Index Service 配置与 Viking service config 使用不同 `ns_tag`；Viking flags 与 ByteKV deploy 必须走 `byterec viking service-config ...`。
- Elements raw feature（抽前）与 extracted feature（抽后）是不同对象；依赖、主键和写入参数以 Elements reference 为准。

## 写操作安全

- Candidate DB、Elements、Viking DB 与 Viking service config 的写命令默认 dry-run；不要跳过预览直接提交。
- Elements 写命令必须显式传 `--branch`，避免误写 `master`。
- `byterec indexservice` 仅提供 GET 查询，不触发 TCE 状态刷新、配置修改、部署、告警注入或 Kafka 工单写入。
- 写请求结果不确定时不要重复提交；先用对应 get/list 命令回读。

## 快速发现命令

```bash
bytedcli byterec --help
bytedcli byterec candidate-db --help
bytedcli byterec elements --help
bytedcli byterec darwin --help
bytedcli byterec indexservice --help
bytedcli byterec model --help
bytedcli byterec viking --help
```

## References

- [Candidate DB](references/candidate-db.md)
- [Elements / Darwin](references/elements.md)
- [Index Service / Model / Viking](references/indexservice-viking.md)
- [通用调用方式](../../invocation.md)
- [常见问题](../../troubleshooting.md)
