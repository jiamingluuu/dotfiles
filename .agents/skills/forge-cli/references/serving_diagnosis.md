# serving_diagnosis.md — Serving diagnosis guide

Use this reference for **why** questions, not basic deployment lookup.
Use [serving.md](serving.md) first to identify one concrete `model_name + psm`, then apply the diagnosis rules below.
MaaS job lifecycle state/progress before a PSM exists stays in
[serving.md](serving.md); this guide starts only when diagnosing an existing
PSM's deployment or instance health.

- 为什么这个 `model_name + psm` 没有成功部署 / 为什么 serving instances are not up
- 为什么 list 里的 `status` 和 detail 里的 `deployment_status` 不一样
- Can this deployment be used to judge whether distribution can proceed?
- Do shared weights / OnlinePS / `train_mode` change the serving-side interpretation?

---

## Non-goals and routing guard

Do **not** use this reference for basic inspection questions:

- “这个 model 有没有 serving / 有哪些 PSM” → use [serving.md](serving.md)
- “是不是 MaaS” as a pure lookup question → use [serving.md](serving.md)
- “MaaS job 当前是 `offline/start/online/stop` 的哪一步 / 上线进度如何” → use
  `forge serving deployment get` through [serving.md](serving.md), even when
  `psm=null`
- list-mode-only output without one concrete `psm` → explain the coarse status only; do **not** do full diagnosis

Do **not** diagnose from list mode alone.

---

## Minimal evidence pack

Collect these fields before giving a diagnosis conclusion:

- `model_name`
- concrete `psm`
- list `status` when available
- `detail.deployment.deployment_status`
- `detail.instance_list.total_instance_count`
- `detail.instance_list.error_instance_count`
- `detail.deployment.from_maas` and `from_maas.maas_job_status` when present
- `model_info.train_mode`
- `model_info.is_shared_weights_model` / `share_weights_from`
- `model_info.is_online_ps_released`
- `model_info.job_status`

---

## Diagnosis entry rules

1. Diagnose only after one concrete `model_name + psm` is identified.
2. Read `detail.deployment.deployment_status` as the default deployment health signal.
3. Read raw `status` only as lower-level reported state.
4. Read `detail.instance_list.total_instance_count` and `error_instance_count` together with `deployment_status`.

---

## Quick decision table

| Question | What to check first | Interpretation |
|---|---|---|
| “为什么 list 状态和 detail 状态不一样？” | list raw `status` vs detail `deployment_status` | Expected: list is a raw summary; detail is calibrated from instance checks |
| “这个 deployment 健康吗？” | `deployment_status`, `total_instance_count`, `error_instance_count` | Prefer calibrated detail status, then explain instance counts |
| “已有 MaaS PSM 的 serving 状态为什么和 MaaS job 状态不同？” | `from_maas.maas_job_status` vs `deployment_status` and instance counts | MaaS job lifecycle and deployment instance health are different views; preserve both |
| “为什么看起来已启动但又不健康？” | raw `status` + instance counts | Raw distribution state may already be `started` while calibrated deployment health is `partial_ready` |
| “为什么没实例？” | `total_instance_count == 0` plus raw/detail status | Zero instances alone does not prove failure; report the zero-instance fact separately |
| “能不能判断现在是否可以继续分发 / 放量？” | `model_info` prerequisites first, then detail deployment health | Do not answer from serving state alone |

---

## Status semantics you must preserve

- `status` = raw status reported by lower-level distribution / serving components.
- `deployment_status` = platform-calibrated status derived from per-instance inspection.
- `deployment_status` exists **only in detail mode**.
- In list mode, `status` is a coarse summary signal only; do **not** present it as calibrated health.

Calibration rule:

- Only raw statuses in `{started, todo, healthy, partial_ready}` are recalibrated.
- Calibration happens only when there is at least one instance.
- `error_instance_count == 0` → `healthy`
- `error_instance_count > 0` → `partial_ready`

---

## How to judge whether distribution can proceed

For “为什么这个 deployment 没成功拉起 / 现在能不能继续分发 / 现在能不能放量 / 首发是否 ready” questions, check in this order:

1. `model_info.train_mode`
2. `model_info.is_shared_weights_model` / `share_weights_from`
3. `model_info.is_online_ps_released`
4. `model_info.job_status`
5. `detail.deployment.deployment_status` and instance counts

Interpretation rule:

- `model_info` carries model-side prerequisites.
- `detail.deployment` and `detail.instance_list` carry serving-side health.
- Do **not** collapse prerequisite failures into serving-state wording.

---

## Stop / do-not-conclude rules

- Without one concrete `psm` and detail output, do **not** conclude whether distribution can proceed.
- Without `model_info` prerequisites, do **not** say distribution can proceed only from serving health.
- `from_maas != nil` means MaaS-backed only; do **not** treat it as health or a signal that distribution can proceed by itself.
- `total_instance_count == 0` is a fact about the normalized response; do **not** automatically turn it into success or failure.
- If the deployment relation is not found, stop at not-found; do **not** continue inferring deeper causes.

---

## Train-mode and shared-weights heuristics

- `train_mode=streaming`: usually the most direct online path; if OnlinePS is released and detail health is good, that is practical evidence that downstream distribution can proceed, but not a substitute for the prerequisite check order above.
- Batch model: do **not** look only at serving deployment existence; `job_status` and OnlinePS release may still block downstream distribution.
- `is_shared_weights_model=true`: treat it differently from ordinary batch models.
- Shared-weights models reuse the parent model's OnlinePS; `share_weights_from` identifies that parent dependency.
- When a shared-weights child looks “not ready”, prefer saying the key prerequisite may be on the parent-model side, not only on this child deployment.
- Current output shows the parent relationship, but does **not** fetch the parent model's state.

---

## MaaS and zero-instance rules

- Interpret a MaaS job's own `offline/start/online/stop`, precheck, and progress
  through `serving deployment get`; do not require `from_maas` or a PSM for
  that lifecycle view.
- Determine MaaS only by `from_maas != nil`.
- Keep `from_maas.maas_job_status` as the MaaS raw status; do **not** remap it into deployment health wording.
- The CLI flattens instances across IDC `prod_list + seed_list + canary_list`.
- `total_instance_count == 0` means “currently no instances in the normalized response”, not automatically “deployment failed”.

---

## Preferred answer patterns

- Status discrepancy: **“list 里的 `status` 是原始分发状态；detail 里的 `deployment_status` 是结合实例检查后的平台健康态，两者口径不同，不能直接等同。”**
- Distribution issue: **“先区分 model 侧前置条件和 serving 侧实例健康；当前更像是 <前置条件问题 / serving 健康问题 / 两者都需要看>。”**
- Not found: **“未找到该 `model_name + psm` 对应的 serving 部署关系。”**
