# FTF v3 线上 source refresh

## 用途与入口边界

本文件用于排查接入完成后，业务修改 build 或 bootstrap 导致线上 SCM 编译出现 `source_hash_mismatch` 的后台闭环。

`/build/sdk_agent/report` 是 SCM 构建脚本到 Manager 的内部回调，不是 bytedcli 命令，也不由 Agent 主动调用。Agent 只能使用用户提供的回调响应，或日志、SCM 等可观测证据；不得伪造 report、重复触发业务编译或用原接入 session 代替后台 refresh session。

## 与接入期调优的复用和区分

| 场景 | 触发与执行 | Agent 职责 |
| ---- | ---------- | ---------- |
| 接入期验证编译 | Agent 按当前接入 session 提交 attempt、生成 draft，并触发 `v3_online` 与 `legacy_test` 双路径验证 | 审查和受控执行脚本，采集真实 diff/构建证据，按失败原因继续调优 |
| 接入完成后的线上变更 | SCM mismatch 后 fail-open 并上报；Manager 创建独立 refresh session，后台生成 draft、双路径验证并发布 | 不参与后台脚本执行；在取得 refresh session 后查询状态，仅在 blocked/manual recovery 时介入 |

两条链路复用 Manager 的 AI draft、编译验证、失败分类和 verified artifact 发布逻辑。线上链路使用独立 session，不改写已经完成的原接入 session。

## Source hash 模型

- canonical hash 固定由 `build.sh + script/bootstrap.sh` 计算，是新 manifest、匹配、去重和 source refresh 的唯一键。
- `main.go + go.mod` 只随四文件 snapshot 上报，作为 AI 生成与编译诊断上下文，不参与 canonical hash，也不允许成为 draft 修改目标。
- 四文件 hash 只用于兼容未声明 `actual_source_hash_scope` 的历史回调；Manager 校验后立即归一为 canonical hash。新调用不要把它作为第二种正式 hash 方案。

## 观察方式

当 SCM 回调响应或日志证据包含 `source_refresh` 时，记录其中的 `session_id`、`source_hash`、`created`、`reused` 和 `next_action`。这些字段属于 Manager 的 callback 响应契约，不是 bytedcli API 层直接获取的结果。

拿到 `source_refresh.session_id` 后，继续复用创建该 session 的站点。下例固定为 cn；zg 使用
`--site cn --vregion China-Pay`，不得根据裸 session ID 猜测站点：

```bash
bytedcli --json --site cn ftf access status --session-id sample-refresh-session --with-versions
```

按状态判断：

- `artifact_generation` / `validation` / `compile_verifying`：后台仍在推进，继续有限观察，不由 Agent 手工重跑接入期 artifact 流程。
- `published`：新的 canonical hash 已产生 verified artifact；再结合 source manifest 和 SCM 双路径版本确认闭环。
- `blocked` 或明确 manual recovery：读取 block reason、attempt 和 SCM 失败证据，再由 Agent 介入调优。
- 没有 `source_refresh.session_id`：只能确认 report 前半链路，不得宣称后台闭环已创建或完成；把“缺少 refresh session 追踪信息”作为当前观测缺口。

report 的 `accepted=false` 只表示本次线上编译没有注入当前 artifact；是否成功创建后台 refresh，以 `source_refresh` 和后续 session 状态为准。
