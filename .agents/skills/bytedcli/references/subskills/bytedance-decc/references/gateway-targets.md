# Gateway 目标选择与诊断

## 确认注册对象

同一 endpoint ID 可能出现在多个 service entity 或区域注册下。先用 `gateway service list --name` 查服务，结合用户提供的 service 页面 entity 和 endpoint list 的 method/path、assurance paths 确认目标；不能根据历史会话中某个 ID 或相同服务名永久绑定 entity。

```bash
bytedcli --site i18n-tt --json decc gateway service list --name demo.api_service
bytedcli --site i18n-tt --json decc gateway endpoint list --entity-id demo-entity-id --stage draft --path /demo/api
# 精确读取区域版本：caller/callee 必须一起提供；版本由实际列表确定
bytedcli --site i18n-tt --json decc gateway endpoint get --id demo-endpoint-id --entity-id demo-entity-id --stage draft --version 0 --caller-vpc demo-office-net --callee-vpc EU_demo-vpc
```

先检查命令 exit code 和 JSON success，再读取列表。缺少 `--stage` 是调用失败，不能用空数组 fallback 报成“没有 endpoint”。列表有分页时继续按 `has_more` 翻页；approved 与 draft 分别查询。`--entity-id` 是返回对象断言，不是后端 detail 的 entity 查询参数；entity、指定 version 或 caller/callee 不匹配时返回 `DECC_GATEWAY_TARGET_MISMATCH`。

## 修改与提交

- `gateway endpoint update`、`gateway field update` 支持 `--entity-id` 和成对的 `--caller-vpc` / `--callee-vpc`，用于限定读取目标；draft 固定读取 version 0。预览和 live 使用完全相同的参数及 confirmation token。
- `gateway assurance-path create` 支持 `--entity-id` 断言；它的 caller/callee 是**要新增的路径**，不用于选择读取已有草稿。
- `gateway endpoint submit` 支持 `--entity-id`；显式提供完整 caller/callee pair 时，初次读取和提交前复查都带这个 pair。新 review plan 保存返回的 entity，并在 live 自动复用；CLI entity 与 plan 冲突会在提交前拒绝。已有不含 entity 的 plan 继续按原有 snapshot guards 校验。
- entity 参数可选以兼容现有调用。涉及同 ID 多注册时应显式提供；省略时不能据此证明注册对象正确。

```bash
# 先预览，核对 entity、schema diff 和 confirmation token
bytedcli --site i18n-tt --json decc gateway field update --draft-id demo-endpoint-id --entity-id demo-entity-id --caller-vpc demo-office-net --callee-vpc EU_demo-vpc --path req.body.name --description 'Resource name'
# submit 默认只读；使用新建私有目录，复核 plan 后才使用同一个文件加 --yes
demo_plan_dir=$(mktemp -d)
chmod 700 "$demo_plan_dir"
bytedcli --site i18n-tt --json decc gateway endpoint submit --draft-id demo-endpoint-id --entity-id demo-entity-id --caller-vpc demo-office-net --callee-vpc EU_demo-vpc --plan-file "$demo_plan_dir/submit-plan.json"
```

后端 draft update 仅按 ID 写入，不接受 entity/区域 selector。CLI 在 scoped 读取后还会比较不带区域的读取；entity、路由或状态不一致就拒绝 POST。这个检查只能发现已观测到的冲突，不能提供后端 CAS 或保证其他编辑器不会并发修改。保持无其他 CLI/Web 编辑器，并检查写后回读；出现 target mismatch 时核对注册与区域，不要通过删除 selector 绕过。

## 解读诊断

- `DECC_GATEWAY_RESPONSE_PARSE_ERROR.details.reason` 区分 `invalid_selector`（ID/path/method 不安全或缺失）、`unknown_region`（无法识别区域）、`incomplete_candidate_metadata`（区域候选缺少安全读取所需信息）。`unknown_region` 的 `observed_regions` 提供有限条数和长度的原始区域标签及 callee VPC，帮助定位新枚举。不能因此推断 pending ticket，也不要自行把未知枚举映射成 US/EU。
- `summary.deprecated_endpoint_count` 统计读取到的 deprecated endpoint，非零会输出 lifecycle warning。打标覆盖的 `verdict: complete` 仍表示契约字段与标签覆盖，不证明该注册正在运行或可以立即提交。
