---
name: bytedance-codebase
description: "Operate Codebase: repositories, namespaces, branches and branch-creator lookup, merge requests, diffs, files, snippets, check runs, CI analysis, CI variables/schedules, and repository permissions."
---

# Codebase（bytedcli）

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

- 仓库查询、MR 详情/评论
- Codebase namespace 列表与搜索
- 创建仓库（默认 validate_only dry-run）
- Diff 列表/内容、文件查看
- MR 文件个人已查看状态查询、标记与取消标记
- Check Runs 与 CI 失败分析
- CI 变量查询与定时任务（variable list、schedule list/create/delete；variable set 目前为 dry-run）
- Codebase/Bits CI Pipeline 手动触发
- 聚合 MR 状态与跨仓库搜索
- Snippet 查询、导出与创建/更新/删除
- 当前用户 SSH 公钥查询、上传与删除
- 创建分支
- 查询分支创建人、创建时间与初始提交（包括从 BITS 仓库活动页发起的查询）
- 删除分支、cherry-pick 提交、rebase 分支（git 原生操作）
- 保护分支规则（lock/unlock：rule list/create/delete，按数字 rule id 解锁）
- 列出两个 ref 之间的提交区间（commit list --base --target）
- 创建 Merge Request
- 经授权为指定 MR 的当前提交创建 Review Bypass，并在保留 MR 审计记录的前提下完成合入
- MR 关联 Meego 工作项（需求/缺陷）
- 文件 Blame（行级归因查询）
- 仓库成员权限盘点（实名用户、用户组、直接/继承来源与到期统计）
- 仓库自身权限申请，以及依赖权限检查与批量申请

## 前置条件

- 使用通用调用方式：`../../invocation.md`
- 认证优先级：`BYTEDCLI_CODEBASE_AUTH_MODE` 默认为 `auto`，顺序为 user JWT/file > App id/secret env/file > OAuth/PAT > 自动换票；`app` 模式只接受 App id/secret。自动换票（含过期落盘 JWT 刷新、以及本地 JWT/PAT 被服务端拒绝后的那一次重试）在生产网优先 ZTI→个人 ByteCloud JWT，失败再回退 SSO；办公网保持 SSO。明确未登录才继续回退 App/OAuth/PAT。`BYTEDCLI_NETWORK_PROFILE=prod` 下 Codebase/Coco 数据 API 走 `https://code.byted.org/api/v2/`（RoW/Compliance Gateway 可达），办公网仍用 `https://codebase-api.byted.org/v2/`。手动配置使用：`bytedcli codebase auth config-add-pat <pat>`，或 `bytedcli codebase auth config-auth --app-id <app-id> --app-secret <app-secret>`

> 执行前缀见 `../../invocation.md`；下面示例直接写 `bytedcli`。

## Quick start

```bash
# 仓库
bytedcli codebase repo get "example-org/example-repo"
bytedcli codebase namespace list # 只列出可用 namespace；按名称查找用 search
bytedcli codebase namespace search --query "example" # search 必须带 query
bytedcli codebase repo create --namespace example-org --name example-repo --description "Demo repo" --search-bytetree "Example Team"
bytedcli codebase repo create --namespace example-org --name example-repo --groot-node-id 12345
bytedcli codebase repo create --namespace example-org --name example-repo --groot-node-id 12345 --execute --confirm example-org/example-repo

# MR 详情/评论
bytedcli codebase mr get 821 -R "example-org/example-repo"
bytedcli --json codebase mr get 821 -R "example-org/example-repo" --work-items
bytedcli codebase mr comment list 821 -R "example-org/example-repo"

# Diff 文件/内容
bytedcli codebase mr files 821 -R "example-org/example-repo"
bytedcli codebase mr diff 821 -R "example-org/example-repo" --file "path/to/file.ts"
bytedcli codebase mr file-review get --mr 821 -R "example-org/example-repo"
# 先预览完整 payload；用户确认目标与 payload 后，再以相同参数追加 --yes。
bytedcli codebase mr file-review update --mr 821 -R "example-org/example-repo" --state viewed --file path/to/file.ts
bytedcli codebase mr file-review update --mr 821 -R "example-org/example-repo" --state viewed --file path/to/file.ts --yes

# 文件与目录内容
bytedcli codebase repo file "README.md" -R "example-org/example-repo"
bytedcli codebase repo file "https://code.byted.org/example-org/example-repo/blob/main/path/to/file.ts"
bytedcli codebase repo directory list -R "example-org/example-repo" --path src --page-size 20
bytedcli codebase repo directory list --path "https://code.byted.org/example-org/example-repo/tree/main/src"

# Blame（行级归因）
bytedcli codebase repo blame "src/main.ts" -R "example-org/example-repo" -r main
bytedcli codebase repo blame "src/main.ts" -R "example-org/example-repo" -r main --start-line 10 --end-line 20
bytedcli codebase repo blame "https://code.byted.org/example-org/example-repo/blob/main/src/main.ts" --start-line 10

# Snippet
bytedcli codebase snippet get <snippet_id>
bytedcli codebase snippet get <snippet_id> --file index.ts
bytedcli codebase snippet get <snippet_id> --save ./snippet-files
bytedcli codebase snippet list --query "demo-query" --page-size 10
bytedcli codebase snippet create --title "demo snippet" --visibility internal --file ./README.md
bytedcli codebase snippet update --id <snippet_id> --add-file ./new.txt --remove-file old.txt
bytedcli codebase snippet delete --id <snippet_id> --yes

# SSH 公钥
bytedcli codebase ssh-key list
bytedcli codebase ssh-key create --title "codex-mac" --key-file ~/.ssh/id_ed25519.pub
bytedcli codebase ssh-key delete --id <key_id> --yes

# 仓库成员权限 / 分支保护
bytedcli codebase repo member get -R "example-org/example-repo"   # 当前用户 access level + 能否 push
bytedcli codebase repo member list -R "example-org/example-repo" --all   # 全量实名用户 + 直接/继承/到期统计
bytedcli codebase repo member list -R "example-org/example-repo" --identity-type user-group --all   # 单独检查用户组授权
bytedcli codebase repo member create -R "example-org/example-repo" --user demo-user --role reporter --days 30   # 默认只预览
bytedcli codebase repo member update -R "example-org/example-repo" --user demo-user --role developer --days 30   # 默认只预览
bytedcli codebase repo member delete -R "example-org/example-repo" --user demo-user   # 默认只预览
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action reporter   # 默认只预览
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action developer --days 30 --yes   # 仅在用户确认当前预览后执行
bytedcli codebase repo protected-branch list -R "example-org/example-repo"   # 保护分支 + push/merge access

# 管理 Branch
bytedcli codebase repo branch list -R "example-org/example-repo" --query "feat/" --query-mode prefix
bytedcli codebase repo branch get -R "example-org/example-repo" --name main
bytedcli codebase repo branch get -R "example-org/example-repo" --name release/1.2 --with-creation
bytedcli codebase repo branch get -R "example-org/example-repo" --name release/1.2 --with-creation --creation-max-pages 50
bytedcli codebase repo branch create feat/demo -R "example-org/example-repo" --from master
bytedcli codebase repo branch delete -R "example-org/example-repo" --name feat/demo
bytedcli codebase repo branch cherry-pick -R "example-org/example-repo" --target-branch release --commit <sha> --yes
bytedcli codebase repo branch rebase -R "example-org/example-repo" --branch feat/demo --base-branch master --yes

# 保护分支规则（lock/unlock，携带数字 rule id；只读汇总用 protected-branch list）
bytedcli codebase repo protected-branch rule list -R "example-org/example-repo"
bytedcli codebase repo protected-branch rule create -R "example-org/example-repo" --name-pattern master
bytedcli codebase repo protected-branch rule create -R "example-org/example-repo" --name-pattern "release/*"
bytedcli codebase repo protected-branch rule delete -R "example-org/example-repo" --id <rule_id>
bytedcli codebase repo protected-branch rule delete -R "example-org/example-repo" --name-pattern master

# 提交区间：列出 base..target 之间可达的 commit
bytedcli codebase commit list -R "example-org/example-repo" --base v1.0.0 --target v2.0.0

# 管理 Tag
bytedcli codebase repo tag list -R "example-org/example-repo" --query "v1." --query-mode prefix
bytedcli codebase repo tag get -R "example-org/example-repo" --name v1.0.0
bytedcli codebase repo tag create -R "example-org/example-repo" --name v1.0.1 --revision master --message "Release v1.0.1"
bytedcli codebase repo tag delete -R "example-org/example-repo" --name v1.0.1

# TTP 同步工单
# 面向 Devbox / TCE BOE 研发环境；客户端只调用 Codebase 合规工单控制面，不直连 TTP SCM。
bytedcli codebase repo ttp-sync list -R "example-org/example-repo" --execution-env devbox
bytedcli codebase repo ttp-sync get --ticket-id 123456 --execution-env devbox
bytedcli codebase repo ttp-sync trigger -R "example-org/example-repo" --branch feature/foo --execution-env devbox --dry-run
# 在 TCE BOE 实例内运行时自动识别，无需 --execution-env。
bytedcli codebase repo ttp-sync trigger -R "example-org/example-repo" --tag v1.0.0 --sync-dependencies

# 管理 Label（仓库标签，含 id/name/color/description）
bytedcli codebase repo label list -R "example-org/example-repo"
bytedcli codebase repo label create -R "example-org/example-repo" --name type/bug --color "#D73A4A" --description "Defect"
bytedcli codebase repo label update -R "example-org/example-repo" --id 780113308321420 --name type/defect
bytedcli codebase repo label delete -R "example-org/example-repo" --id 780113308321420

# 管理 Webhook（对应仓库设置页的 settings/integrations）
# 只有 list / create 需要 -R；get / update / delete / test / log 用 webhook 自身 id 定位。
bytedcli codebase repo webhook list -R "example-org/example-repo"
bytedcli codebase repo webhook get --id 789674161371057
# create / update / delete 默认只预览 payload，必须显式 --yes 才提交。
bytedcli codebase repo webhook create -R "example-org/example-repo" --url https://example.com/hooks/codebase --events push,merge_request
# 共享密钥只从 --secret-file 读，不接受命令行明文；TLS 证书校验默认开启，需要关闭才传 --no-ssl-verify。
bytedcli codebase repo webhook create -R "example-org/example-repo" --url https://example.com/hooks/codebase --events push --secret-file ./webhook-secret.txt --yes
bytedcli codebase repo webhook update --id 789674161371057 --status disabled --yes   # 暂停投递；--status enabled 恢复
bytedcli codebase repo webhook delete --id 789674161371057 --yes
# test 立即发送一条真实投递，没有 dry-run 预览也没有 --yes 门禁，执行前先跟用户确认。
bytedcli codebase repo webhook test --id 789674161371057
# 投递日志：排查回调没生效时先看这里的响应码与响应体
bytedcli codebase repo webhook log list --webhook-id 789674161371057 --page-size 20
bytedcli --json codebase repo webhook log get --id 789697639818049   # 完整 request/response 只在 JSON 模式返回

# 管理 Release
bytedcli codebase release list -R "example-org/example-repo" --query "v1." --query-mode prefix
bytedcli codebase release get -R "example-org/example-repo" --tag v1.0.0
bytedcli codebase release create -R "example-org/example-repo" --tag v1.0.1 --description "Release v1.0.1" --revision master --tag-message "Release v1.0.1"
bytedcli codebase release update -R "example-org/example-repo" --tag v1.0.1 --description "Updated release notes"

# 创建 MR（含本地分支准备与创建前推送）
bytedcli codebase mr branch create --branch feature/demo --base master --remote origin
bytedcli codebase mr branch create --branch feature/demo --worktree
bytedcli codebase mr branch create --branch feature/demo --worktree ../demo-task
bytedcli codebase mr branch create --branch feature/demo --no-worktree
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo"
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --push
bytedcli codebase mr create -R "example-org/example-repo" --head feature/demo --title "feat: demo" --push --remote origin
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --push --force-with-lease   # 改写过历史（如 amend）后重推
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --meego 123456
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --link "Codebase Managed Agents=https://example.com/session/123"   # 挂结构化外部链接（Text=URL，可重复）

# 更新 MR：关联工作项 / 切 target branch / 修改合入方式 / 增删外部链接 / 改 label
bytedcli codebase mr update 821 -R "example-org/example-repo" --meego 123456
bytedcli codebase mr update 821 -R "example-org/example-repo" --base develop
bytedcli codebase mr update 821 -R "example-org/example-repo" --merge-method rebase_merge
bytedcli codebase mr update 821 -R "example-org/example-repo" --merge-method rebase_merge --yes
bytedcli codebase mr update 821 -R "example-org/example-repo" --link "Codebase Managed Agents=https://example.com/session/123"   # 增量追加，不影响描述
bytedcli codebase mr update 821 -R "example-org/example-repo" --remove-link "https://example.com/session/123"
# label 用 id，不是名字；先用 repo label list 查 id
bytedcli codebase repo label list -R "example-org/example-repo"
bytedcli codebase mr update 821 -R "example-org/example-repo" --add-labels <label_id>
bytedcli codebase mr update 821 -R "example-org/example-repo" --remove-labels <label_id>
bytedcli codebase mr update 821 -R "example-org/example-repo" --set-labels <label_id>   # 整体替换，不能与 add/remove 同用

# 上传附件并嵌入评论或描述（截图证据）
bytedcli codebase upload --path ./screenshot.png
bytedcli codebase mr comment create 821 -R "example-org/example-repo" --body "视觉证据：" --attach ./before.png --attach ./after.png
bytedcli codebase mr update 821 -R "example-org/example-repo" --attach ./screenshot.png   # 追加到现有描述末尾，不覆盖

# 安全门禁：先展示不带 --yes 的预览；仅在用户明确确认同一 repo、MR 和 merge method 后执行 --yes。
# 任一字段变化都必须重新预览并再次确认。
# Check Runs / CI
bytedcli codebase checks mr 821 -R "example-org/example-repo"
bytedcli codebase checks list -R "example-org/example-repo"
bytedcli codebase checks list -R "example-org/example-repo" --commit <sha> --mr 821
# 同一套 check 命令也挂在 mr 下，便于从 MR 出发排查
bytedcli codebase mr checks list --mr 821 -R "example-org/example-repo"
bytedcli codebase checks mr --commit <sha> -R "example-org/example-repo"
bytedcli codebase checks get -R "example-org/example-repo" --id c1
bytedcli codebase checks log 1234567890 unit_test_and_coverage --run-seq 126 --step-id 3456789012
bytedcli codebase checks log 2345678901 build_lint-step_4 --run-seq 1 --no-limit
bytedcli codebase checks log -R "example-org/example-repo" --check-run-id 4567890123
bytedcli codebase checks log -R "example-org/example-repo" --check-run-id 4567890123 > /tmp/check.log
bytedcli codebase mr artifacts list 821 -R "example-org/example-repo" --artifact example-artifact-filename
bytedcli codebase mr artifacts download 821 -R "example-org/example-repo" --artifact example-artifact-filename --all --output-dir ./ci-artifacts
grep -n 'error\\|fail' /tmp/check.log
bytedcli codebase mr status 821 -R "example-org/example-repo"

# Codebase/Bits Pipeline
bytedcli codebase pipeline list -R "example-org/example-repo" --branch main
bytedcli codebase pipeline status -R "example-org/example-repo" --branch main --pipeline CI
bytedcli codebase pipeline run -R "example-org/example-repo" --branch main --pipeline CI
bytedcli codebase pipeline run -R "example-org/example-repo" --branch main --pipeline CI --inputs '{"target":"demo"}'
bytedcli codebase pipeline runs list -R "example-org/example-repo" --branch main --pipeline CI
bytedcli codebase pipeline runs list -R "example-org/example-repo" --pipeline CI --status succeeded --since "7d ago"
bytedcli codebase pipeline runs get -R "example-org/example-repo" --branch main --pipeline CI --run-seq 6

# Issue
# 清空负责人；不传 --assignee-ids 则保留原负责人
bytedcli codebase issue update 24 -R "example-org/example-repo" --assignee-ids ""
bytedcli codebase issue comment 24 -R "example-org/example-repo" --body "ack"
# UTF-8 文件适合长正文；-F - 从 stdin 读取，内容不裁剪、不解释字面量转义
bytedcli codebase issue create -R "example-org/example-repo" --title "Demo issue" -F ./body.md
bytedcli codebase issue update 24 -R "example-org/example-repo" -F ./body.md
bytedcli codebase mr update 821 -R "example-org/example-repo" -F ./body.md
cat ./body.md | bytedcli codebase issue comment 24 -R "example-org/example-repo" -F -
bytedcli codebase issue comment update -R "example-org/example-repo" --issue-number 24 --id <comment_id> -F ./reply.md
bytedcli codebase comment update -R "example-org/example-repo" --id <comment_id> -F ./reply.md
# Issue 标签接受名称或 ID；set 与 add/remove 互斥，空 set 清空全部标签
bytedcli codebase issue update 24 -R "example-org/example-repo" --add-labels demo-label
bytedcli codebase issue update 24 -R "example-org/example-repo" --remove-labels demo-label
bytedcli codebase issue update 24 -R "example-org/example-repo" --set-labels ""
# 视图由仓库共享；写操作默认预览，--yes 提交并读回核对
bytedcli codebase issue saved-view list -R "example-org/example-repo"
bytedcli codebase issue saved-view create -R "example-org/example-repo" --name "Demo triage" --filter-label demo-label --filter-status todo --sort-by UpdatedAt --sort-order Desc
bytedcli codebase issue saved-view create -R "example-org/example-repo" --name "Demo triage" --filter-label demo-label --yes
bytedcli codebase issue saved-view update -R "example-org/example-repo" --id <view_id> --name "Demo renamed" --yes
bytedcli codebase issue saved-view update -R "example-org/example-repo" --id <view_id> --filter-json '{}' --yes
bytedcli codebase issue saved-view delete -R "example-org/example-repo" --id <view_id> --yes
bytedcli codebase issue comment list 24 -R "example-org/example-repo"
bytedcli codebase issue comment list https://code.byted.org/example-org/example-repo/issues/24
bytedcli codebase issue comment list 24 -R "example-org/example-repo" --author alice --status open
bytedcli codebase issue comment reply 24 -R "example-org/example-repo" --thread-id <thread_id> --body "fixed"
bytedcli codebase issue comment resolve -R "example-org/example-repo" --id <thread_id> --resolve-reason fixed
bytedcli codebase issue comment unresolve -R "example-org/example-repo" --id <thread_id>
bytedcli codebase issue delete 24 -R "example-org/example-repo"
bytedcli codebase search issue --assignee @me --status todo --page-size 5

# 仓库与依赖权限
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action reporter
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action developer --days 30 --yes   # 仅在用户确认当前预览后执行
bytedcli codebase permission repository apply -R "example-org/example-repo" --action reporter
bytedcli codebase permission repository apply -R "example-org/example-repo" --action developer --reason "implement integration" --yes
bytedcli codebase permission check -R "example-org/example-repo"
bytedcli codebase permission check -R "example-org/example-repo" --revision main
bytedcli codebase permission apply -R "example-org/example-repo" --action reporter --reason "need read access" --repos "dep-org/dep-repo" --dry-run
bytedcli codebase permission apply -R "example-org/example-repo" --action reporter --reason "need read access" --repos "dep-org/dep-repo" --yes   # 仅在用户确认当前预览后执行

# MR 列表 / 生命周期
bytedcli codebase mr list -R "example-org/example-repo" --state open -L 20
bytedcli codebase mr list -R "example-org/example-repo" --label bug,urgent --milestone-id m-1 --attention @me --updated-since 2026-07-01T00:00:00Z
bytedcli codebase mr count -R "example-org/example-repo"
bytedcli codebase mr count -R "example-org/example-repo" --milestone-id m-1 --commit abc123
bytedcli codebase mr close 821 -R "example-org/example-repo"
bytedcli codebase mr status 821 -R "example-org/example-repo"

# review scope
# approve、request-changes、withdraw 会立即写入远端 review 状态；执行前必须先向用户确认 repo、MR 和具体 action
bytedcli codebase mr review 821 -R "example-org/example-repo" --approve --body "LGTM"
bytedcli codebase mr review 821 -R "example-org/example-repo" --withdraw
bytedcli codebase mr reviewer list 821 -R "example-org/example-repo"
bytedcli codebase mr reviewer update 821 -R "example-org/example-repo" --set 123456 --set 234567
bytedcli codebase mr reviewer update 821 -R "example-org/example-repo" --set alice --add bob   # 支持 username

# Review Bypass：保留 MR，只豁免当前 source commit 的人工 Review 门禁。
# 必须先获得用户对同一 repo、MR、source commit 和合入方式的明确授权；CI/Checks 仍需通过。
bytedcli --json codebase mr status 821 -R "example-org/example-repo"   # 取 source_commit_id、ReviewRules[].Name，并确认 checks/mergeability
bytedcli codebase mr bypass list 821 -R "example-org/example-repo" --commit-id <source_commit>
bytedcli --json codebase mr bypass create 821 -R "example-org/example-repo" --commit-id <source_commit> --inputs-json '[{"TargetType":"review","Target":{"ReviewTarget":{"RuleId":"<review_rule_id>"}},"Reason":"no_need_for_review"}]'
bytedcli --json codebase mr bypass list 821 -R "example-org/example-repo" --commit-id <source_commit>   # 回读审计记录
bytedcli --json codebase mr status 821 -R "example-org/example-repo"                                  # 再确认 Review 已豁免且其他门禁通过
bytedcli --json codebase mr merge 821 -R "example-org/example-repo" --merge-method merge_commit
bytedcli --json codebase mr get 821 -R "example-org/example-repo"                                     # 确认 Status=merged 和 MergeCommitId

# merge_queue scope
bytedcli codebase mr queue status -R "example-org/example-repo"
bytedcli codebase mr queue list -R "example-org/example-repo" -L 20
bytedcli codebase mr queue enqueue 821 -R "example-org/example-repo" --merge-method rebase_merge
bytedcli codebase search mr --author @me --status open --page-size 5

# check_run scope
bytedcli codebase checks get -R "example-org/example-repo" --id c1
bytedcli codebase checks create -R "example-org/example-repo" --payload-json '{"Name":"ci/test","CommitId":"<sha>"}'
bytedcli codebase checks update -R "example-org/example-repo" --payload-json '{"Id":"c1","Status":"completed","Conclusion":"success"}'
bytedcli codebase checks operate -R "example-org/example-repo" --payload-json '{"CheckRunId":"c1","OperationId":"<operation_id_from_operations>"}'
bytedcli codebase checks operate -R "example-org/example-repo" --mr 821 --check-name SyncMrToCommon --operation-label 确定合入

# ci variable / schedule scope（Bits git pipeline 后端，复用 Bits SSO 登录）
bytedcli codebase ci variable list -R "example-org/example-repo"
printf %s "$SECRET" | bytedcli codebase ci variable set -R "example-org/example-repo" --key MY_TOKEN   # dry-run only：读 stdin 但不写
bytedcli codebase ci schedule list -R "example-org/example-repo" --branch main
bytedcli codebase ci schedule create -R "example-org/example-repo" --yaml release.yaml --branch main --name daily --cron "0 2 * * *"
bytedcli codebase ci schedule delete --id <triggerId>
bytedcli codebase ci schedule delete --id <id1> --id <id2>   # 批量按 id 删除

# Bits Analysis (Merge Check) — 拉每条规则级 issue 的详情（codebase checks get 只给汇总）
bytedcli codebase analysis project list -R "example-org/example-repo"
bytedcli codebase analysis issue list -R "example-org/example-repo" --severities warning,error
bytedcli codebase analysis issue list -R "example-org/example-repo" --mr 100
bytedcli codebase analysis issue list -R "example-org/example-repo" --project-id 1001 --scenario-id 2001
bytedcli codebase analysis issue list -R "example-org/example-repo" --actions open,false,wont_fix   # action 过滤：open|closed|fixed|false|resolved|wont_fix|path_removed|rule_removed|delay_fix
bytedcli --json codebase analysis issue list -R "example-org/example-repo"

# Bits Analysis issue 处理 — 等价 issue 页面上的 误报/延迟修复/暂不解决 按钮；默认 dry-run，先预览确认无误再追加 --yes 提交
bytedcli codebase analysis issue update -R "example-org/example-repo" --issue-id 6100001 --action false-positive                  # 先 dry-run 预览 payload（不写入）
bytedcli codebase analysis issue update -R "example-org/example-repo" --issue-id 6100001 --action false-positive --yes            # 确认后追加 --yes 标误报
bytedcli codebase analysis issue update -R "example-org/example-repo" --issue-id 6100001,6100002 --action delay-fix --yes         # 批量延迟修复
bytedcli codebase analysis issue update -R "example-org/example-repo" --issue-id 6100001 --action wont-fix --reason code-generated --yes   # 暂不解决必须带 --reason: code-generated|fix-cost-high|useless-worthless
bytedcli codebase analysis issue update -R "example-org/example-repo" --issue-id 6100001 --action reopen --yes                    # 撤销标记，恢复为未解决

# MR 检查页 annotation 级按钮（[Bits Analysis] Merge Check 推荐问题）也可通过 checks operate 按下
bytedcli codebase checks operate -R "example-org/example-repo" --check-run-id <id> --annotation-id <annotationId> --operation-label 误报
```

## Notes

### TTP 合规同步边界

- `ttp-sync` 只允许固定的 Codebase HTTPS 控制面，且拒绝 HTTP 重定向；不要添加 SCM/TTP 直连域名或 endpoint override。
- 工单及其 `sync_tasks` 的 `status_name` 统一为 `pending|running|succeed|failed|canceled`；排障和轮询优先判断该字段，同时保留原始数字 `state`。
- Devbox 通过 `--execution-env devbox`（或 `BYTEDCLI_TTP_SYNC_EXECUTION_ENV=devbox`）声明支持场景；该声明不是网络身份认证。TCE BOE 使用平台注入的 `TCE_HOST_ENV=boe` 自动识别。
- 已知 ByteFaaS、TCE online 与 TCE PPE 运行时会在仓库解析、PAT 交换和 HTTP 请求之前失败。

### 仓库与分支推断

- 在 `code.byted.org` / `code-tx.byted.org` 的 Git 目录内，`-R/--repo` 和 `--branch`/`--commit` 可省略，CLI 自动从 `origin` 推断
- MR selector 支持 `<number> | <url> | <branch>`，未传时回落到当前 Git 分支
- `mr branch create` 将远端 base 拉取到单次调用独占的临时 ref，再创建本地分支，避免并发会话通过共享 `FETCH_HEAD` 串扰；`mr create --push` 推送 `--head` 或当前分支。`--remote` 必须是已配置、指向 Codebase host 且与 `-R/--repo` 为同一仓库的 remote 名称。默认推送不带 force，改写过历史（如 amend 后重推）才加 `--force-with-lease`：远端分支多出你尚未整合的 commit 时它会拒绝（CLI 同时带上 `--force-if-includes`，所以**光 `git fetch` 不足以放行**，必须 `git rebase <remote>/<branch>` 真正整合进来），这正是为了保住平台代打的空 commit（CI 的 `ci: preserve mr squash message`）；已进入 merge queue 的 MR 不要 force push，会被移出队列。
- TRAE 会话执行 `mr branch create` 时默认创建独立 worktree；其他宿主可设置 `BYTEDCLI_WORKSPACE_KEY` 启用同样策略。工作区 key 只以短哈希进入自动路径，不输出原值。需要原地 checkout 时显式传 `--no-worktree`。
- 自动 worktree 位于当前仓库同级目录；显式 path 必须位于所有现有 worktree 和其他 Git 仓库之外。后续命令必须从输出的 `worktree_path` 目录执行。
- 这些命令调用的 git 子进程都有时间上限：网络操作（`fetch`/`push`）默认 300 秒，本地操作默认 30 秒，超时返回 `CODEBASE_GIT_ERROR` 且 `details.git_timed_out=true`。超时不代表分支名非法或 lease 被拒--看到 `git_timed_out` 先查网络与仓库状态（如残留的 `index.lock`）。仓库确实需要更久时用 `BYTEDCLI_CODEBASE_GIT_NETWORK_TIMEOUT_MS` / `BYTEDCLI_CODEBASE_GIT_LOCAL_TIMEOUT_MS` 调整，只接受正整数毫秒，非法值静默回落到默认。git 子进程一律带 `GIT_TERMINAL_PROMPT=0`，凭据 helper 不会在这里索要输入。

### 常用约定

- 结构化输出：`bytedcli --json codebase ...`（`--json` 放子命令之前）
- `codebase repo branch get --with-creation` 在普通分支详情之外查询最新的同名 `git_branch_created` 活动，返回创建人、创建时间和初始 commit。活动按每页 100 条扫描，默认最多 20 页；老分支可用 `--creation-max-pages <1..100>` 扩大范围。JSON 的 `CreationScan.Truncated=true` 表示达到扫描上限但仍有后续页，不能据此断言没有创建活动；完整扫描仍未命中时也只表示活动记录未找到。省略 `--with-creation` 时保持原有分支详情输出。
- `codebase mr get --work-items` 会额外调用一次关联工作项接口，JSON 在 `data.work_items` 返回最多 100 条关联项，并用 `total_count` / `truncated` 明示是否还有更多结果；默认不传时不会发起这次附加请求。
- `mr list` 默认 open；`issue list` 默认未完成态
- MR 外部链接（Links）：`mr create/update --link "Text=URL"` 挂结构化链接（按第一个 `=` 拆分，Text 与 URL 均必填，缺任一报 `CODEBASE_INPUT_ERROR`；URL 可含 `=`/逗号；多条重复传 `--link`），`mr update --remove-link <url>` 按 URL 移除（URL 需与现有 link 完全一致，不存在时报错并列出现有 URL）。Links 走增量语义，与描述解耦，`mr update --body` 整份覆盖描述不会碰掉 Links，适合存放机器可读的归属元数据（如任务来源 + 会话 URL）。注意：当前 Codebase Web UI 不渲染 Links，读取只能走 `bytedcli --json codebase mr get`（`data.merge_request.Links`）或文本输出的 Links 行；给人看的信息仍要写进 MR 描述
- `mr file-review get` 汇总当前 MR 版本的 viewed / unviewed 文件；`update --state viewed|unviewed` 只修改当前用户的个人查看状态，不影响代码、评论或审批。选择文件时重复传 `--file`，或使用 `--all` 处理当前版本全部变更文件。`update` 默认 dry-run 并输出完整 payload；Agent 必须先展示预览，只有用户确认同一组目标、状态和 payload 后，才用相同参数追加 `--yes` 提交。任一字段变化都要重新预览并确认。
- `mr file-review` 的 `--mr` 支持 MR number、Codebase MR URL、BITS Code detail URL 或 source branch；省略时从当前 Git 分支推断。
- MR selector 每个 `mr` 子命令都同时接受位置参数与 `--mr <selector>`（`mr get 821` 与 `mr get --mr 821` 等价），不用记哪个命令用哪种写法。两种写法同时给会报错而非静默择一。别名映射：`--mr` = 位置参数 selector；`mr comment resolve` / `unresolve` 的 `--thread-id` = `--id`（与 `comment reply --thread-id` 同名同义）。两个别名都在 `--help` 里以 `alias:` 标注，不引入任何新参数。
- MR label：`mr update --add-labels / --remove-labels / --set-labels` 收的是 **label id**（不是名字），先用 `repo label list -R <repo>` 查 id；`--set-labels` 整体替换，不能与 add/remove 同用。label 写入走独立接口，`mr get` 会回读并在输出里带上 Labels，可直接自证是否生效。
- 附件：`codebase upload --path <file>` 上传后返回 `file_id` / `file_url` / `markdown`；更常用的是 `--attach <path>`（可重复，`mr comment create` / `mr create` / `mr update` 均支持），一步完成上传并把 markdown 追加到正文末尾。`mr update --attach` 不传 `--body` 时是**追加**到现有描述，不会覆盖。markdown 形态由服务端按文件内容嗅探出的 MIME 决定（图片 `![]()`、视频 `![video]()`、其余 `[]()`），客户端无法指定。上传只支持用户身份，App Identity 会被拒绝。
- 想要在 MR 描述或评论里贴截图，必须先真的上传；不要写「截图见评论区」之类指向不存在内容的说明。
- `check_runs` 相关 JSON 同时提供 PascalCase 与 camelCase 两套键（`Id` / `id`、`ExternalId` / `externalId`），新代码建议读 camelCase；嵌套对象仍保持原大小写。
- `mr status` 的 `data.mergeability` 分两层：`mergeable` / `reason` / `reason_detail` 是聚合结论，`checks[]` 是逐项合入门禁（`name` / `passed` / `reason`，如 `checkNoConflict`、`checkReviewPassed`、`checkWIP`），`failed_checks[]` 是其中未通过的门禁名。判断「MR 为什么不能合」要读 `checks[]`，`reason` 只给单一主因。注意合入门禁（`checks[]`）与 CI 检查（`check_runs`）是两套东西，前者是平台合入闸门，后者是流水线跑出来的检查。
- 缺少必填参数时，错误行与帮助都写到 **stderr**，且错误会在帮助之后再重复一次，所以 `2>&1 | head` 和 `| tail` 都能看到原因；不要用 `2>/dev/null` 丢掉 stderr
- 连接失败（`Network error: ... fetch failed`）会额外输出 `Host:` 行；若配了代理且该 host 不在 `NO_PROXY` 内，还会提示把该 host 加进 `NO_PROXY` 后重试（只报 host，不输出可直接执行的命令）。注意 `mr artifacts download` 跨两个 host：数据 API 在 office 为 `codebase-api.byted.org`、prod 为 `code.byted.org`，产物在 `bits.bytedance.net`。按报错里的 `Host:` 处理，不要写死 office API host
- **Review Bypass 的含义与边界**：它不会跳过 MR、不会直接推主分支，也不会自动豁免 CI/Checks；它只为指定 MR 的当前 `source_commit_id` 创建人工 Review 门禁豁免，并保留创建人、时间、原因和 commit 的服务端审计记录。仅当仓库规则允许、当前用户具有 bypass 权限，并且用户明确授权同一 repo、MR、source commit 与合入方式时执行；“帮我发 MR”“直接发布”等泛化表述不视为 bypass 授权。
- **Review Bypass 的固定流程**：先用 `bytedcli --json codebase mr status` 读取 `data.merge_request.source_commit_id`、`data.review.review_rule_groups[].ReviewRules[].Name` 和 checks/mergeability；确认非 Review 门禁均已满足后，用服务端字段 `TargetType` / `Target` / `Reason` 创建 review bypass；随后用 `mr bypass list --commit-id <source_commit>` 和 `mr status` 回读，最后才执行 `mr merge`，并用 `mr get` 验证 `Status=merged` 与 `MergeCommitId`。不要用 `--review` 快捷参数或小写 `kind` / `target` / `reason` 示例，已知会被部分服务端规则拒绝。
- **Commit 变更后必须重新确认**：Review Bypass 绑定创建时的 `source_commit_id`。源分支新增或改写 commit 后，旧 bypass 不适用于新提交；必须重新读取 status，并再次获得用户对新 commit 的明确授权，不能静默续用旧授权。
- `codebase snippet get --save <dir>` 默认不覆盖本地已有文件；需要覆盖时显式加 `--force`
- `codebase snippet update --add-file/--remove-file` 会先读取现有文件并整组更新；若现有文件内容缺失或被服务端截断，会拒绝执行，避免写空远端文件
- `codebase ssh-key create` 只接受包含单个 OpenSSH 公钥的文件；检测到私钥或多个非空行会拒绝上传。删除公钥必须显式传 `--yes`
- `codebase repo directory list` 按目录路径分页返回完整文件元信息；根目录使用 `--path .`，继续翻页时把 JSON 输出的 `next_page_token` 传给 `--page-token`
- Issue 评论：`bytedcli codebase issue comment <n> --body "..."` 是**写**一条；`bytedcli codebase issue comment list <n>` 是**读**评论列表（与 `mr comment list` 同款 sub-resource 模式，selector 支持 number 或 console URL，过滤参数 `--status open|resolved|closed`（thread 状态，非法值会直接报错；非 issue 自身 lifecycle status）/ `--author <name>`（按评论作者 Username 或 Email 做大小写不敏感的子串匹配））；`reply <n> --thread-id <id> --body "..."` 回复已有 thread；`resolve --id <id> [--resolve-reason <fixed|false_positive|deferred|wont_fix>]` / `unresolve --id <id>` 更新 thread 状态，`--resolve-reason` 会作为 `ResolveReason` 发送；mr/issue 评论均支持 `comment reaction create/delete --comment-id <id> --name THUMBSUP`（写立即生效、`--name` 大小写敏感、非法名由服务端报错透出），issue 侧另有 `comment reaction list --comment-id <id>`（可重复传多个 id，逗号分隔亦可）

### CI 排查

- **优先用 `codebase checks log --check-run-id <id>` 看远端日志**，不要本地跑全量测试
- 日志重定向到文件后用 `grep “not ok\|fail\|error”` 定位失败点
- 排查顺序：`checks list --mr` → 找失败 check-run-id → `checks log --check-run-id` → grep
- 不知道 pipeline 名称时，先用 `codebase pipeline list -R <repo> --branch <branch>` 列出可用 pipeline name 与 YAML file。
- 触发 Codebase/Bits pipeline 前先用 `codebase pipeline status -R <repo> --branch <branch> --pipeline <name>` 查询最新状态；确认目标后用 `codebase pipeline run -R <repo> --branch <branch> --pipeline <name>` 创建真实 run。
- 需要给 manual pipeline 传输入时使用 `--inputs '<json>'` 或 `--inputs-file ./inputs.json`
- **排查 git-backed pipeline（含定时发版）失败时不用开浏览器**：`codebase pipeline status` 会拉取最新 run 详情，给出 failReason、失败 job/step 以及逐 step 的成功/失败状态；完整日志在输出的 Run URL（git pipeline 的 atom 日志在 Orca，不在 step_logs 接口）。
- 想看「连续挂了几晚」用 `codebase pipeline runs list -R <repo> --branch <branch> --pipeline <name>` 列出 run 历史（runSeq + 状态 + 触发人），再用 `codebase pipeline runs get --run-seq <n>`（或 `--run-id <id>`）定位某一次（含历史）失败原因。
- 不预先知道分支时，`runs list` 可省略 `--branch`/`--git-tag`，返回该 pipeline 跨所有分支的 run 历史（每条 run 带自己的 branch），结果按时间倒序；可用 `--status <succeeded|failed|...>`（服务端过滤）与 `--since <2026-06-01|"7d ago">` 缩小范围。`--since` 按触发时间过滤后再分页（先 filter 再 page）；run 按时间倒序，只扫描到满足当前页所需即停。
- 详见 `../../troubleshooting.md`

### 操作 check run（重跑 / 取消等）

- `checks operate` 触发某个 check run 上声明的操作 —— 这些操作由创建该 check 的 App 定义，用来流转它的状态机（重跑、取消、刷新等）
- 可用操作不固定：每个 check run 的 `Operations` 数组列出它**当前**能执行的操作，会随 check 状态变化
- 用法：先 `bytedcli --json codebase checks list` 拿目标 check run 的 `Id` 和 `Operations`（`Operations` 只在 `--json` 输出里，默认文本表格不展示）；每个 operation 有 `Id`/`Label`/`Description`，按 `Label`/`Description` 判断它做什么
- 再调用 `checks operate --payload-json '{"CheckRunId":"<check run Id>","OperationId":"<选中 operation 的 Id>"}'`
- 如果是 MR 页面上的手动按钮，可让 bytedcli 自动按 MR + check 名 + 按钮文案解析：`bytedcli codebase checks operate -R <repo> --mr <mr> --check-name <check_name> --operation-label <button_label>`。例如 `SyncMrToCommon` 的「确定合入」按钮对应 `--check-name SyncMrToCommon --operation-label 确定合入`，也可显式传 `--operation-id syncMrToCommon`。
- 例：重跑选 `Label` 为 `Rerun`/`Re-run` 的项，取消选 `Cancel`（operation 的 `Id` 各 App 命名不统一，按 `Label` 认）

### CI 变量与定时任务

- `variable list` 返回的是**变量组模型**：解析 `group.varDefinitions[].name`（+ `kind` 区分加密/明文），不是扁平 key/value
- `variable set` 目前是 **dry-run / experimental**：仍从 stdin 或 `--value-file` 读值（绝不走命令行参数、不回显值），但**不会**发起任何写请求。原因是真实写入是对整个变量组的覆盖（含 `version`），其 body 尚未抓包确认，盲发可能清掉已有变量；需要写变量请暂时用 Bits/Codebase UI。`--confirm-write` 也被显式拦截
- `schedule list` 走 `GET /pipelines/git/triggers`（复数），**必须带分支**：未传 `--branch` 时回落到当前 git 分支，支持 `--page-num/--page-size`
- `schedule create` 会先用后端纯函数 `next_schedules` 校验 cron（非法 cron 直接报错，不发起写请求），并给出下次执行时间；`triggeredBy` 默认取当前登录用户，可用 `--triggered-by` 覆盖
- `schedule delete` 是**按 id 批量删**：`DELETE /pipelines/triggers`（注意没有 `git` 段），body `{"triggerIds":[...]}`；命令行可重复 `--id` 或逗号分隔
- `variable` 端点按数字 repoId 寻址（owner/repo 自动解析为 repoId）；`schedule` 端点按 owner/repo 路径寻址，因此 `schedule` 必须能拿到 `-R/--repo`

### MR 关联 Meego 工作项

1. 搜索：`bytedcli --json meego workitem list --project-key <key> --mql “SELECT \`work_item_id\`, \`name\` FROM \`<key>\`.\`story\` WHERE \`name\` LIKE '%关键字%' LIMIT 10”`
2. 呈现 ID + 名称列表让用户选择
3. 执行：`bytedcli codebase mr create/update --meego <work_item_id>`

### 仓库与依赖权限

```bash
bytedcli codebase repo member list -R "example-org/example-repo" --all
bytedcli codebase repo member list -R "example-org/example-repo" --identity-type user-group --all
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action reporter   # Owner 直接授权，默认只预览
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action developer --days 30 --yes   # 仅在用户确认当前预览后执行
bytedcli codebase permission repository apply -R "example-org/example-repo" --action reporter   # 默认只预览
bytedcli codebase permission repository apply -R "example-org/example-repo" --action developer --reason "<reason>" --yes
bytedcli codebase permission check -R <repo>              # 查缺少权限的依赖
bytedcli codebase permission apply -R <repo> --action reporter --reason “...” --repos “dep/repo” --dry-run   # 默认无档位会报错
bytedcli codebase permission apply -R <repo> --action reporter --reason “...” --repos “dep/repo” --yes
```

- `repo member list` 走 Codebase `ListRepoMembers` + `GetRepoMemberStatistics`，返回角色、直接/继承来源、到期时间，以及直接/间接/即将到期的统计。默认查实名用户并分页；`--all` 自动翻页并按 identity id 去重；用户组是独立授权主体，必须另用 `--identity-type user-group` 查询，实名用户数不能当成实际访问人数上限。`--expiring-within-days` 默认 30。
- `repo member create/update/delete` 对应 Codebase 当前成员控制面：新增和改角色走 `UpsertRepoMember`，删除直接成员走 `RemoveRepoMember`；不要改接 `/api/v4/projects/:id/members`，该 GitLab v4 路径在 Codebase 已 phased out 并返回 503。三条命令默认 dry-run，`create` 拒绝覆盖已有直接成员，`update/delete` 拒绝操作继承权限，真实写入后用 `ListRepoMembers` 回读校验。当前只管理用户；用户组仍在成员页操作。
- `permission repository create` 由仓库 Owner 直接新增或更新用户的仓库角色，支持 username 或数字 user id，以及 `--action reporter|developer|master|owner`。默认只解析仓库和用户并预览；显式传 `--yes` 才调用 `UpsertRepoMember` 生效。Reporter/Developer 默认 365 天，Master 默认 180 天，均可用 `--days 1..365` 覆盖；Owner 永不过期且不能传 `--days`。
- **直接授权写入确认（强制）**：Agent 必须先不带 `--yes` 运行并展示该命令真实输出的完整目标。`repo member create/update` 核对 repo、user、operation、new role、expiration、permissions、endpoint；`repo member delete` 核对 repo、user、current direct role、current expiration、endpoint；旧入口 `permission repository create` 核对 repo、user、role、expiration、permissions、endpoint。只有用户明确确认这一次具体写入后，才可用相同参数追加 `--yes` 重跑。仅询问、解释、准备命令或泛化授权不算写入确认；任一目标字段或 operation 变化都必须重新预览并再次确认。
- `permission repository apply` 申请目标仓库自身权限，支持 `reporter`、`developer`、`master`。按仓库路径精确读取 CN Codebase 的 Kani 申请页资源，不依赖仓库读取权限或资源搜索结果。默认通过 Kani 校验并预览，返回 `manual_apply_url`，不创建审批；显式传 `--yes` 才提交。精确读取失败会保留 Kani 错误，不能据此判定仓库不存在。省略 `--reason` 时会按仓库和权限生成理由。
- `permission apply --repos` 申请依赖仓库权限，必须显式选择执行档：`--dry-run` 读当前依赖权限状态并打印将提交的 payload，`--yes` 才逐个依赖仓创建审批工单；两者都不传时命令报错而不是提交。
- **依赖权限批量申请确认（强制）**：Agent 必须先用 `--dry-run` 展示 repo 列表、当前权限与将提交的 action/reason；只有用户明确确认这一批具体申请后，才可用相同参数追加 `--yes` 重跑。预览里 `known_dependency: false` 的仓不是该主仓的依赖（仓名写错、依赖已移除，或它只存在于另一个 revision）：**整批都不是依赖时 `--yes` 直接报错**，只有部分不是时才照常提交并在 `unknown_dependencies` 里列出，提交前要先确认这些行。若 `state_unavailable: true`，说明依赖状态没读到，`known_dependency` 全为 `null`，此时预览只能核对 payload、无法核对仓名。提交结果里也带 `state_unavailable`/`state_error`：为 true 时那批仓**没有**经过依赖核对就提交了，`unknown_dependencies: []` 不代表核对通过。

- 成员列表 JSON 的 `members[].identity` 保留 `username`、`email`、`status`；上游返回账号类型和多邮箱资料时，还包含 `userType` 和 `emails`。`type` 表示成员主体（`user` / `user_group`），`userType` 对应用户账号的 `Type`。资料来自同一次列表请求，不另行查询用户。

## 正文、标签与视图

- Issue create/update/comment/reply、MR create/update、comment update 支持互斥的 `--body` 与 `-F/--body-file <path>`；`-` 显式读取 stdin。文件/stdin 按 UTF-8 原样传递，保留空白、换行和字面量 `\n`；空描述文件可清空描述，评论内容必须非空。Windows 长正文优先用文件，避免命令行长度与 shim 换行限制。
- `issue get/list` 和 `search issue` 的 JSON 保留 `Labels`、`ParentIssue`、`SubIssues`；文本展示标签名。Issue 标签更新接受名称或 ID（可重复参数或逗号分隔），先解析并校验，再调用独立标签接口并读回；`--set-labels ""` 清空，set 与 add/remove 互斥，同一标签不能同时 add/remove。字段与标签是两次写入，不具备事务性；报错后先读取当前 Issue 再重试。
- `issue comment update`使用 `--issue-number` 与 `--id`，校验评论所属 Issue。`codebase comment get/update/delete` 可直接按评论 ID 操作。
- `issue saved-view` 管理共享视图；list 返回视图集合，不分页，JSON 的 `current_count` 表示本次返回数量；`issue view` 仍是查询 Issue 的别名。create/update/delete 默认预览 payload，`--yes` 写入并读回。update 省略的字段保留；简单过滤选项合并到现有 Filter，status 与 label 取 AND，label 使用名称。`--filter-json` 替换整个 Filter，`{}` 清空，不与简单过滤选项混用。复杂过滤器只传已验证的服务端编码。

- 空值语义：Issue 的 `Labels: []` 和视图的 `filter: {}` 表示已知为空；对应字段为 `null` 表示接口未返回数据，写后校验不会将缺失信息当作清空成功。
- 视图 Filter 可能由服务端自动补入当前仓库的 `RepoId`；create/update 无需手工填写该字段，清空业务筛选后仍可能保留它。写后校验只接受额外补入且匹配当前仓库的 `RepoId`，其他筛选内容仍完整比较；若回读失败，先按错误中的视图 ID 查询现状再决定是否重试创建，避免重复视图。

## Markdown 多行换行（必读）

bash/zsh 内联正文使用 ANSI-C 引号，例如 `--body $'第一行\n第二行'`；`--body "第一行\n第二行"` 不会由 shell 转为真实换行。推荐将 Markdown 保存为 UTF-8 文件并使用 `--body-file ./body.md`，避免依赖 shell 转义或历史内联文本兼容行为。

## References

- `references/codebase.md`
- `../../troubleshooting.md`
