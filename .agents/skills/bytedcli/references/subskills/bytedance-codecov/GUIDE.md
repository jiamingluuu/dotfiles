---
name: bytedance-codecov
description: "Operate ByteDance codecov via bytedcli: inspect client BITS MR coverage with a mandatory evidence-based SOP and reusable report template, analyze uncovered lines, produce a separate Case list, generate reports and line-level actions, submit or reset existing client coverage tags, create and rerun incremental report generation, create/update full coverage reports, query reports, print coverage-next links, and manage collection-side tags and upload intervals. Use when tasks mention codecov, 检查客户端 MR 覆盖率, 分析未覆盖行, 补充 Case, 客户端覆盖率, BITS MR 覆盖率, 覆盖率标签, 撤销覆盖率标签, 覆盖率报告, 全量覆盖率, 增量覆盖率, coverage-next."
---

# Codecov (bytedcli)

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

- Create full coverage reports from PSM + branch
- Create incremental coverage reports from PSM + branch
- Query an existing server-side incremental report by report ID or exact PSM + branch (+ commit/MR)
- Rerun generation for an existing incremental report and wait for its update time to advance
- List coverage-next incremental files for an MR
- Mark coverage-next incremental files as ignored / no-coverage-required, or reset an existing mark
- Inspect or review a client BITS MR coverage URL end to end, classify uncovered paths from code and test evidence, and produce a separate Case list
- Generate a Markdown report and line-level action manifest from a client BITS MR coverage URL
- Preview, submit, or reset client coverage actions through the BITS comment API
- Refresh (update) existing coverage reports
- Query a report by rid or by PSM + branch
- List reports for a PSM
- Print the bits coverage-next URL without an HTTP call
- Manage collection-side tags and upload intervals
- Check whether a PSM is integrated into the coverage platform (access status; note that `not_registered` is inferred from an empty response — may also indicate ACL or transient empty)

## 前置条件

- 使用通用调用方式：`../../invocation.md`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## 客户端 MR 覆盖率检查 SOP

当用户要求“检查”“分析”或“审查”客户端 MR 覆盖率时，必须读取并按照 `references/client-coverage-review-template.md` 执行和输出。仅要求拉取报告、预览 action、提交标签或撤销标签时，按细粒度命令完成即可，不自动扩展为完整检查。

1. **拉取远端事实**：使用 `codecov report client get` 获取远端未覆盖列表、原始 Markdown 报告和 action manifest。此阶段只读，不执行评论或标签写入。
2. **补齐变更证据**：根据输出定位 Codebase 仓库和 MR，读取 MR 元数据与 diff，并核对所有存在待处理行的文件。存在本地仓库时，确认本地 HEAD 与目标提交的关系、检查脏工作区，并只使用与 MR 相关的改动作为证据。按可用性继续读取模块文档、已有测试、本次测试改动、MR 描述、评论和检查项。
3. **按业务路径分类**：覆盖率结果只证明行是否命中，不能单独证明分类。结合控制流和证据，将未覆盖路径归为 `miss-test`、`untestable`、`uninstrumentable`、`useless-code` 或“待确认”。同一路径的连续语句合并判断；证据不足时必须保留“待确认”。
4. **单独生成 Case 清单**：只为能稳定复现的 `miss-test` 路径生成 Case，至少包含前置条件、操作或输入、预期结果、建议测试层级、关联文件与行号、优先级。不得把 `untestable` 或 `uninstrumentable` 伪装成普通测试 Case。
5. **可选人工校验**：在任何写入前，向用户展示覆盖概览、文件与行级结论、Case 清单、证据缺口和待确认项，供人工调整分类。
6. **写入必须再次授权**：只有用户明确确认具体分类和范围后，才可使用 `codecov report client execute --yes` 写入标签或评论。预览不等同于授权；未确认时保持只读。
7. **按模板交付**：最终报告使用 `references/client-coverage-review-template.md` 的章节与口径。所有待标注 action 行必须进入某个分类或“待确认”，分类合计必须与 `actionableLines` 一致，每个 `miss-test` 路径必须能映射到独立 Case。已有标记行、其他不可评论或无有效行号的未覆盖行，以及拉取失败项不进入本次逐行分类，但必须单独核算并说明影响。

## 常用命令

```bash
# Report management (new coverage-report gateway)
bytedcli codecov report create-incr --psm example.service.api --branch feat/demo
bytedcli codecov report incr get --psm example.service.api --branch feat/demo --commit 0000000aaaa --region i18n
bytedcli --json --site boe codecov report incr rerun --report-id 10000001 --region i18n
bytedcli --json --site boe codecov report incr rerun --psm example.service.api --branch feat/demo --region i18n
bytedcli codecov report create --psm example.service.api --branch master
bytedcli codecov report update --rid 10000001
bytedcli codecov report update --psm example.service.api --branch master --no-wait
bytedcli codecov report get --rid 10000001
bytedcli codecov report get --psm example.service.api --branch master
bytedcli codecov report list --psm example.service.api --limit 10
bytedcli codecov report incr list-files --coverage-project-id 100001 --mr-id TE-XXX-demo --psm example.service.api
bytedcli codecov report incr source --report-id 100001 --file src/demo/service.go --source-mode changed-uncovered
bytedcli codecov report incr source --psm example.service.api --branch feat/demo --file src/demo/service.go --package-name src/demo --tag nightly
bytedcli codecov report incr update --coverage-project-id 100001 --mr-id TE-XXX-demo --file service/activity/demo.go --comment-tag no-coverage-required --dry-run
BITS_COVERAGE_URL='<client-bits-coverage-url>'
bytedcli codecov report client get --url "$BITS_COVERAGE_URL" --report-output ./coverage-report.md --actions-output ./coverage-actions.json
bytedcli codecov report client execute --actions-file ./coverage-actions.json --comment-tag miss-test
# 仅在明确确认写入后提交
bytedcli codecov report client execute --actions-file ./coverage-actions.json --comment-tag miss-test --yes
# 已有 comment_id 且 comment_tag=null 的 action 可用 reset 预览/提交撤销
bytedcli codecov report client execute --actions-file ./coverage-reset-actions.json --comment-tag reset
bytedcli codecov report client execute --actions-file ./coverage-reset-actions.json --comment-tag reset --yes
bytedcli codecov report link --rid 10000001

# Access status (new gateway)
bytedcli codecov access-status --psm example.service.api
bytedcli -j codecov access-status --psm example.service.api

# Collection-side (collection gateway, unchanged)
bytedcli codecov create-tag --tag demo-tag --service example.service.api:prod --expire 10
bytedcli codecov delete-tag --psm example.service.api --env prod --tag demo-tag
bytedcli codecov set-interval --interval 60 --service example.service.api:prod --expire 30

# Legacy (deprecated wrapper; forwards to `codecov report create`)
bytedcli codecov create-report --psm example.service.api --branch-name master --base-commit 0000000 --os-type server
```

## 报告链接

所有 `report create/update/get/list` 命令都会在响应里附加 `link` 字段，格式为：

```
https://bits.bytedance.net/quality/measure/coverage-next/full?language=1&rId={rid}&region=cn&viewId=1
```

## Notes

- `bytedcli codecov` 命令保持为可组合的细粒度能力；完整检查 SOP 由本 Skill 编排，不改变命令自身行为
- `codecov report *` 走新的覆盖率报告网关，与 bits 覆盖率平台新页面 `coverage-next` 对齐
- `codecov report create-incr` 走增量报告创建接口，当前 `--os-type` 仅支持服务端族：`server/server-cpp/server-java/server-nodejs/python`
- `codecov report incr get` 只走 `/api/v2/increase/server/search`、`/api/v2/increase/get_sub_reports` 和增量文件接口；不得用全量 `report get/list/update` 判断增量报告是否存在
- `codecov report incr rerun` 先按 `incr get` 的 current-state 逻辑解析报告，再调用 coverage data region 对应的 `POST /api/v2/increase/data/mrproduce`；它不会调用 `/api/v2/full/report/*`
- rerun 请求的 `app_id` 必须取已解析报告的 `project_id` / `AppId`，请求的 `project_id` 必须取 `coverage_project_id` / `ProjectID`；二者不得互换，wire payload 均保持 string，也不要求用户手工填写
- rerun 的 `os_type`、`mr_id`、`tag` 取已解析报告；`user` 默认取当前登录用户，可用 `--user-name` 覆盖
- rerun 默认等待 `update_time` 晚于刷新前；`--no-wait` 返回 `refresh_status=accepted`，等待超时返回 `refresh_status=timeout`，只有时间前进才返回 `completed`，覆盖行数不要求变化
- `report incr source` 在 `report incr get` 的坐标解析之上拉单文件的行级覆盖；默认只输出 `changed-uncovered` 行（要修的行），`--source-mode changed|all` 加宽。`--file` 按最后一个 `/` 拆成 package 与文件名（coverage-next 契约，根路径文件报错）；`--tag` 未显式传时继承 report 的 tag。若无匹配文件，报错列 available files
- `report incr get` 返回的是 increase API 当前状态，并显式标记 `report_state=current`。当前 API 未暴露可验证的不可变历史快照；若指定 report ID 存在但 commit/branch/MR 已变化，返回 `CODECOV_INCR_SNAPSHOT_MISMATCH`，不得误报未接入或无报告
- 输出 `project_id` 对应 increase 的 `AppId`；`coverage_project_id` 对应内部 `ProjectID`，供 `incr list-files/update --coverage-project-id` 使用，二者不得混用
- `incr list-files/update` 推荐使用语义明确的 `--coverage-project-id`；已发布的 `--project-id` 仍作为隐藏兼容别名可用
- `codecov report incr list-files` 读取 coverage-next 增量文件树；`--psm` 会按子报告查询，并自动带 `is_sub_report=true`
- `codecov report incr update` 对齐 coverage-next 页面批量标记能力，默认 `operation_type=1`；`--reset` 会改为取消标记（`operation_type=2`）
- `codecov report client get --url` 接收客户端 BITS MR 的“覆盖率详情”页面完整浏览器地址，不接收 Codebase MR 链接、BITS MR 详情链接或接口地址；示例见 `references/codecov.md`
- `codecov report client get` 只读取客户端 BITS MR 覆盖率，过滤已覆盖、非变更、非有效、不可评论和已有标注行；输出固定结构的 Markdown 报告与逐行 action manifest，不调用写接口
- `codecov report client execute` 默认仅预览；未分类 action 必须通过 `--comment-tag` 或 manifest 逐项确认标签，只有显式 `--yes` 才调用 `comment_create/comment_add`
- 客户端撤销标记使用 `comment_add` 更新已有评论：保留已有 `comment_id` 与完整 `comment_lines`，将 `comment_tag` 设为 `0`；可用 `--comment-tag reset` 表达。撤销只清空标签，不删除评论记录；缺少 `comment_id` 时 CLI 会拒绝执行
- 客户端评论写接口可能以 HTTP `204 No Content` 表示成功；bytedcli 会把该状态按成功处理，不会因空响应体误报 JSON 解析失败
- 客户端 `comment_create` action 按项目、MR、平台、文件、完整行号集合和标签去重；`comment_add` 按已有 `comment_id` 区分，同一评论的标签或完整行号集合冲突时会在写入前拒绝执行
- 常用 `--comment-tag`：`no-coverage-required`、`untestable`、`useless-code`、`uninstrumentable`、`miss-test`、`add-case`、`private-code`
- `codecov create-tag/delete-tag/set-interval` 仍走采集网关
- `--os-type` 默认 `server`；其它取值：`android/ios/javascript/server-cpp/python`
- `--if-send-robot` 会在 CLI 内部映射为后端字段 `if_send_rebot`
- `codecov report update` 默认轮询等待最多 30s；用 `--no-wait` 立即返回
- `codecov report get/list/update` 是全量报告能力；增量报告重新生成必须使用独立的 `codecov report incr rerun`，原 `incr update` 仍然只做文件归因标记
- 增量命令的 `--region` 是覆盖率数据区域，仅支持 `cn`（默认）与 `i18n`；它不改变 bytedcli 全局 `--site`，也不是 BOE lane/env。报告中的 `coverage_env` 是第三个独立概念
- `report incr get` 的主/子报告汇总一旦解析成功即返回 `availability=available`；文件树失败仅令 `file_detail.status=blocked`，已确认的覆盖行、增量行和比例仍有效
- `codecov access-status` 仅用于辅助诊断，不是增量报告查询或刷新的硬门禁；成功查到已有增量报告时，不得因其空结果或 false 状态阻止刷新
- 查询服务端增量覆盖率不要求 BITS task URL，也不会发送 BOE/PPE 业务请求
- 无鉴权时 `bytedcli auth login` 后再试

## References

- `references/codecov.md`
- `references/client-coverage-review-template.md`
- `../../invocation.md`
- `../../troubleshooting.md`
