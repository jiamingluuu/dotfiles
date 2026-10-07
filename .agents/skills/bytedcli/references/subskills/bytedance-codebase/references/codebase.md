# Codebase (bytedcli)

```bash
# 在 code.byted.org 或 code-tx.byted.org 的 Git 仓库目录内，支持仓库选择器的命令可省略 -R/--repo 或 --repo-name

# Auth
bytedcli codebase auth config-add-pat <pat>
bytedcli codebase auth config-auth --jwt-token <token>
bytedcli codebase auth config-auth --app-id <app-id> --app-secret <app-secret>

# Repo
bytedcli codebase repo get "example-org/example-repo"
bytedcli codebase repo list --query "demo-query"
bytedcli codebase namespace list # 只列出可用 namespace；按名称查找用 search
bytedcli codebase namespace search --query "example" # search 必须带 query
bytedcli codebase repo create --namespace example-org --name example-repo --description "Demo repo" --search-bytetree "Example Team"
bytedcli codebase repo create --namespace example-org --name example-repo --groot-node-id 12345
bytedcli codebase repo create --namespace example-org --name example-repo --groot-node-id 12345 --execute --confirm example-org/example-repo
bytedcli codebase repo branch list -R "example-org/example-repo" --query "feat/" --query-mode prefix
bytedcli codebase repo branch get -R "example-org/example-repo" --name main
bytedcli codebase repo branch get -R "example-org/example-repo" --name release/1.2 --with-creation
bytedcli codebase repo branch get -R "example-org/example-repo" --name release/1.2 --with-creation --creation-max-pages 50
bytedcli codebase repo branch create feat/demo -R "example-org/example-repo" --from master
bytedcli codebase repo branch delete -R "example-org/example-repo" --name feat/demo
bytedcli codebase repo branch cherry-pick -R "example-org/example-repo" --target-branch release --commit <sha> --yes
bytedcli codebase repo branch rebase -R "example-org/example-repo" --branch feat/demo --base-branch master --yes
bytedcli codebase repo file "README.md" -R "example-org/example-repo"
bytedcli codebase repo file "https://code.byted.org/example-org/example-repo/blob/main/path/to/file.ts"
bytedcli codebase repo directory list -R "example-org/example-repo" --path src --page-size 20
bytedcli codebase repo directory list --path "https://code.byted.org/example-org/example-repo/tree/main/src"
bytedcli codebase repo blame "src/main.ts" -R "example-org/example-repo" -r main
bytedcli codebase repo blame "src/main.ts" -R "example-org/example-repo" -r main --start-line 10 --end-line 20
bytedcli codebase repo blame "https://code.byted.org/example-org/example-repo/blob/main/src/main.ts" --start-line 10
bytedcli codebase repo member get -R "example-org/example-repo"
bytedcli codebase repo member list -R "example-org/example-repo" --all
bytedcli codebase repo member list -R "example-org/example-repo" --identity-type user-group --all
bytedcli codebase repo member create -R "example-org/example-repo" --user demo-user --role reporter --days 30
bytedcli codebase repo member update -R "example-org/example-repo" --user demo-user --role developer --days 30
bytedcli codebase repo member delete -R "example-org/example-repo" --user demo-user
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action reporter
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action developer --days 30 --yes   # 仅在用户确认当前预览后执行
bytedcli codebase repo protected-branch list -R "example-org/example-repo"
bytedcli codebase repo protected-branch rule list -R "example-org/example-repo"
bytedcli codebase repo protected-branch rule create -R "example-org/example-repo" --name-pattern master
bytedcli codebase repo protected-branch rule delete -R "example-org/example-repo" --id <rule_id>
bytedcli codebase repo webhook list -R "example-org/example-repo"
bytedcli codebase repo webhook get --id <webhook_id>
bytedcli codebase repo webhook create -R "example-org/example-repo" --url https://example.com/hooks/codebase --events push,merge_request --yes
bytedcli codebase repo webhook create -R "example-org/example-repo" --url https://example.com/hooks/codebase --events push --secret-file ./webhook-secret.txt --yes
bytedcli codebase repo webhook update --id <webhook_id> --status disabled --yes
bytedcli codebase repo webhook delete --id <webhook_id> --yes
bytedcli codebase repo webhook test --id <webhook_id>
bytedcli codebase repo webhook log list --webhook-id <webhook_id> --page-size 20
bytedcli --json codebase repo webhook log get --id <log_id>
bytedcli codebase commit list -R "example-org/example-repo" --revision master
bytedcli codebase commit list -R "example-org/example-repo" --base v1.0.0 --target v2.0.0
bytedcli codebase commit get -R "example-org/example-repo" --revision <sha>

# Snippet
bytedcli codebase snippet get <snippet_id>
bytedcli codebase snippet get <snippet_id> --file index.ts
bytedcli codebase snippet get <snippet_id> --save ./snippet-files
bytedcli codebase snippet list --query "demo-query" --page-size 10
bytedcli codebase snippet create --title "demo snippet" --visibility internal --file ./README.md
bytedcli codebase snippet update --id <snippet_id> --add-file ./new.txt --remove-file old.txt
bytedcli codebase snippet delete --id <snippet_id> --yes

# SSH Public Key
bytedcli codebase ssh-key list
bytedcli codebase ssh-key create --title "codex-mac" --key-file ~/.ssh/id_ed25519.pub
bytedcli codebase ssh-key delete --id <key_id> --yes

# Issue
bytedcli codebase issue list -R "example-org/example-repo" # 默认只看 open
bytedcli codebase issue list -R "example-org/example-repo" --status todo --limit 20
bytedcli codebase issue get 52 -R "example-org/example-repo"
bytedcli codebase issue activity 24 -R "example-org/example-repo"               # 读：动态时间线（评论、状态变更、关联 MR，按时间倒序）
bytedcli codebase issue comment 24 -R "example-org/example-repo" --body "ack"          # 写：发一条评论
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
bytedcli codebase issue comment list 24 -R "example-org/example-repo"                  # 读：列出某 issue 的所有评论
bytedcli codebase issue comment list https://code.byted.org/example-org/example-repo/issues/24
bytedcli codebase issue comment list 24 -R "example-org/example-repo" --author alice --status open
bytedcli codebase issue comment reply 24 -R "example-org/example-repo" --thread-id <thread_id> --body "fixed"
bytedcli codebase issue comment resolve -R "example-org/example-repo" --id <thread_id> --resolve-reason fixed
bytedcli codebase issue comment unresolve -R "example-org/example-repo" --id <thread_id>
bytedcli codebase issue delete 24 -R "example-org/example-repo"

# MR 基础查询
bytedcli codebase mr get 821 -R "example-org/example-repo"   # JSON 模式的 data.merge_request.Links 为机器可读外部链接列表
bytedcli --json codebase mr get 821 -R "example-org/example-repo" --work-items
bytedcli codebase mr get
bytedcli codebase mr get 821 -R "example-org/example-repo"
bytedcli codebase mr activity 821 -R "example-org/example-repo"                 # 读：动态时间线（评审、推送、合入队列、合入，按时间倒序）
bytedcli codebase mr comment list 821 -R "example-org/example-repo"
bytedcli codebase mr files 821 -R "example-org/example-repo"
bytedcli codebase mr diff 821 -R "example-org/example-repo" --file "path/to/file.ts"
bytedcli codebase mr file-review get --mr 821 -R "example-org/example-repo"
# 先预览完整 payload；用户确认目标与 payload 后，再以相同参数追加 --yes。
bytedcli codebase mr file-review update --mr 821 -R "example-org/example-repo" --state viewed --file "path/to/file.ts"
bytedcli codebase mr file-review update --mr 821 -R "example-org/example-repo" --state viewed --file "path/to/file.ts" --yes
bytedcli codebase repo tag list -R "example-org/example-repo" --query "v1." --query-mode prefix
bytedcli codebase repo tag create -R "example-org/example-repo" --name v1.0.1 --revision master --message "Release v1.0.1"
bytedcli codebase repo label list -R "example-org/example-repo"
bytedcli codebase repo label create -R "example-org/example-repo" --name type/bug --color "#D73A4A" --description "Defect"
bytedcli codebase repo label update -R "example-org/example-repo" --id 780113308321420 --name type/defect
bytedcli codebase repo label delete -R "example-org/example-repo" --id 780113308321420
bytedcli codebase release list -R "example-org/example-repo" --query "v1." --query-mode prefix
bytedcli codebase release get -R "example-org/example-repo" --tag v1.0.0
bytedcli codebase release create -R "example-org/example-repo" --tag v1.0.1 --description "Release v1.0.1" --revision master --tag-message "Release v1.0.1"
bytedcli codebase release update -R "example-org/example-repo" --tag v1.0.1 --description "Updated release notes"

# CI / Check Runs
bytedcli codebase checks mr 821 -R "example-org/example-repo"
bytedcli codebase checks list -R "example-org/example-repo"
bytedcli codebase checks list -R "example-org/example-repo" --commit <sha> --mr 821
bytedcli codebase checks mr --commit <sha> -R "example-org/example-repo"
bytedcli codebase mr checks list --mr 821 -R "example-org/example-repo"   # 同一套 check 命令也挂在 mr 下
bytedcli codebase checks get -R "example-org/example-repo" --id <check_run_id>
bytedcli codebase checks log 1234567890 unit_test_and_coverage --run-seq 126 --step-id 3456789012
bytedcli codebase checks log 2345678901 build_lint-step_4 --run-seq 1 --no-limit
bytedcli codebase checks log -R "example-org/example-repo" --check-run-id 4567890123
bytedcli codebase mr artifacts list 821 -R "example-org/example-repo" --artifact example-artifact-filename
bytedcli codebase mr artifacts download 821 -R "example-org/example-repo" --artifact example-artifact-filename --all --output-dir ./ci-artifacts
# Logs can be large; prefer redirecting to a file and searching locally.
bytedcli codebase checks log -R "example-org/example-repo" --check-run-id 4567890123 > /tmp/check.log
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

# Comment
bytedcli codebase mr comment create 821 -R "example-org/example-repo" --body "global comment"
bytedcli codebase mr comment create 821 -R "example-org/example-repo" --body "inline comment" --path src/foo.ts --start-line 42
bytedcli codebase mr comment create 821 -R "example-org/example-repo" --body "range comment" --path src/foo.ts --start-line 42 --end-line 43 --start-column 1 --end-column 20
bytedcli codebase mr comment draft 821 -R "example-org/example-repo" --body "draft comment"
bytedcli codebase mr comment publish 821 -R "example-org/example-repo" --body "LGTM"
bytedcli codebase mr comment reply 821 -R "example-org/example-repo" --thread-id <thread_id> --body "fixed"
bytedcli codebase mr comment resolve -R "example-org/example-repo" --id <thread_id> --resolve-reason fixed
bytedcli codebase mr comment unresolve -R "example-org/example-repo" --id <thread_id>

# 创建 / 更新 PR
bytedcli codebase mr create -R "example-org/example-repo" \
  --title "feat: demo"
bytedcli codebase mr create -R "example-org/example-repo" \
  --title "feat: demo" --meego 123456
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --link "Codebase Managed Agents=https://example.com/session/123"   # 挂结构化外部链接（Text=URL 均必填，可重复；按第一个 = 拆分）
bytedcli codebase mr update 821 -R "example-org/example-repo" --body "first line\nsecond line"
bytedcli codebase mr update 821 -R "example-org/example-repo" --meego 123456
bytedcli codebase mr update 821 -R "example-org/example-repo" --base develop   # 切 MR 的 target branch 到另一条 release/集成分支
bytedcli codebase mr update 821 -R "example-org/example-repo" --merge-method rebase_merge        # 默认只预览旧值和新值
bytedcli codebase mr update 821 -R "example-org/example-repo" --merge-method rebase_merge --yes  # 写入后回读校验
bytedcli codebase mr update 821 -R "example-org/example-repo" --link "Codebase Managed Agents=https://example.com/session/123"   # AddLinks 增量追加，与描述解耦，mr update --body 不会覆盖
bytedcli codebase mr update 821 -R "example-org/example-repo" --remove-link "https://example.com/session/123"   # 按 URL 移除
bytedcli codebase repo label list -R "example-org/example-repo"   # label 写入用 id，先查 id
bytedcli codebase mr update 821 -R "example-org/example-repo" --add-labels <label_id>     # 增量加，可重复或逗号分隔
bytedcli codebase mr update 821 -R "example-org/example-repo" --remove-labels <label_id>  # 增量删
bytedcli codebase mr update 821 -R "example-org/example-repo" --set-labels <label_id>     # 整体替换，不能与 add/remove 同用

# 附件：上传后拿 markdown，或用 --attach 一步上传并嵌入
bytedcli codebase upload --path ./screenshot.png                # 返回 file_id / file_url / markdown
bytedcli --json codebase upload --path ./report.tar.gz          # JSON 始终含 markdown 字段
bytedcli codebase mr comment create 821 -R "example-org/example-repo" --body "视觉证据：" --attach ./before.png --attach ./after.png
bytedcli codebase mr create -R "example-org/example-repo" --title "feat: demo" --attach ./screenshot.png
bytedcli codebase mr update 821 -R "example-org/example-repo" --attach ./screenshot.png   # 不传 --body 时追加到现有描述末尾

# 安全门禁：先展示不带 --yes 的预览；仅在用户明确确认同一 repo、MR 和 merge method 后执行 --yes。
# 任一字段变化都必须重新预览并再次确认。
# 搜索 Meego 工作项（获取 work_item_id 后填入 MR）
bytedcli --json meego workitem list --project-key <project_key> \
  --mql "SELECT \`work_item_id\`, \`name\` FROM \`<project_key>\`.\`story\` WHERE \`name\` LIKE '%关键字%' LIMIT 10"

# PR 列表 / 生命周期
bytedcli codebase mr list -R "example-org/example-repo" # 默认只看 open
bytedcli codebase mr list -R "example-org/example-repo" --state open -H feature/foo -B master -L 20
bytedcli codebase mr list -R "example-org/example-repo" --label bug,urgent --milestone-id m-1 --attention @me --updated-since 2026-07-01T00:00:00Z
bytedcli codebase search mr --author @me --status open --page-size 5
bytedcli codebase mr count -R "example-org/example-repo"
bytedcli codebase mr count -R "example-org/example-repo" --milestone-id m-1 --commit abc123
bytedcli codebase mr close 821 -R "example-org/example-repo"
bytedcli codebase mr reopen 821 -R "example-org/example-repo"
bytedcli codebase mr merge 821 -R "example-org/example-repo" --merge-method rebase_merge

# PR Review / Queue
bytedcli codebase mr review 821 -R "example-org/example-repo" --approve --body "LGTM" # 自动附带当前 MR 最新 source commit
bytedcli codebase mr review --comment --body-file ./review.txt
bytedcli codebase mr reviewer list 821 -R "example-org/example-repo"
bytedcli codebase mr reviewer update 821 -R "example-org/example-repo" --add 123456 --add 234567
bytedcli codebase mr reviewer update 821 -R "example-org/example-repo" --add alice --remove bob   # 支持 username

# Review Bypass：保留 MR，只豁免当前 source commit 的人工 Review 门禁。
# 必须先获得用户对同一 repo、MR、source commit 和合入方式的明确授权；CI/Checks 仍需通过。
bytedcli --json codebase mr status 821 -R "example-org/example-repo"   # 取 source_commit_id、ReviewRules[].Name，并确认 checks/mergeability
bytedcli codebase mr bypass list 821 -R "example-org/example-repo" --commit-id <source_commit>
bytedcli --json codebase mr bypass create 821 -R "example-org/example-repo" --commit-id <source_commit> --inputs-json '[{"TargetType":"review","Target":{"ReviewTarget":{"RuleId":"<review_rule_id>"}},"Reason":"no_need_for_review"}]'
bytedcli --json codebase mr bypass list 821 -R "example-org/example-repo" --commit-id <source_commit>   # 回读审计记录
bytedcli --json codebase mr status 821 -R "example-org/example-repo"                                  # 再确认 Review 已豁免且其他门禁通过
bytedcli --json codebase mr merge 821 -R "example-org/example-repo" --merge-method merge_commit
bytedcli --json codebase mr get 821 -R "example-org/example-repo"                                     # 确认 Status=merged 和 MergeCommitId
bytedcli codebase mr queue status -R "example-org/example-repo"
bytedcli codebase mr queue list -R "example-org/example-repo" -L 20
bytedcli codebase mr queue entries 821 -R "example-org/example-repo"
bytedcli codebase mr queue enqueue 821 -R "example-org/example-repo" --merge-method rebase_merge
bytedcli codebase mr queue dequeue 821 -R "example-org/example-repo"

# Check Run 读写
bytedcli codebase checks get -R "example-org/example-repo" --id c1
bytedcli codebase checks create -R "example-org/example-repo" --payload-json '{"Name":"ci/test","CommitId":"<sha>"}'
bytedcli codebase checks update -R "example-org/example-repo" --payload-json '{"Id":"c1","Status":"completed","Conclusion":"success"}'
bytedcli codebase checks operate -R "example-org/example-repo" --payload-json '{"CheckRunId":"c1","OperationId":"<operation_id_from_operations>"}'
bytedcli codebase checks operate -R "example-org/example-repo" --mr 821 --check-name SyncMrToCommon --operation-label 确定合入
bytedcli codebase search issue --assignee @me --status todo --page-size 5

# 跨仓库代码内容搜索（code.byted.org grep），搜索词放在最前面，过滤器随后
bytedcli codebase search code --query "fmt.Println" --lang go --limit 10
bytedcli codebase search code --query "handleCodebase" --repo-filter "^example-org/example-repo$"
bytedcli --json codebase search code --query "TODO" --pattern-type regexp --file "\.go$"

# Permission（Owner 直接授权、仓库自身申请与依赖权限）
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action reporter
bytedcli codebase permission repository create -R "example-org/example-repo" --user demo-user --action master --days 30 --yes   # 仅在用户确认当前预览后执行
bytedcli codebase permission repository apply -R "example-org/example-repo" --action reporter
bytedcli codebase permission repository apply -R "example-org/example-repo" --action developer --reason "implement integration" --yes
bytedcli codebase permission check -R "example-org/example-repo"
bytedcli codebase permission check -R "example-org/example-repo" --revision main
bytedcli --json codebase permission check -R "example-org/example-repo"
bytedcli codebase permission apply -R "example-org/example-repo" --action reporter --reason "need read access" --repos "dep-org/dep-repo" --dry-run
bytedcli codebase permission apply -R "example-org/example-repo" --action reporter --reason "need read access" --repos "dep-org/dep-repo" --yes   # 仅在用户确认当前预览后执行
bytedcli codebase permission apply -R "example-org/example-repo" --action developer --reason "need write access" --repos "dep-org/repo1,dep-org/repo2" --yes
```

## 迁移说明

- 认证兜底换票：生产网存在 ZTI 时优先 ZTI→个人 ByteCloud JWT 再换 Codebase JWT，ZTI 交换失败才回退 SSO；办公网保持 SSO。`BYTEDCLI_NETWORK_PROFILE=prod` 下 Codebase/Coco 数据 API 使用 `https://code.byted.org/api/v2/`（避开 RoW Compliance Gateway 对 `codebase-api.byted.org` 的拦截），办公网仍用 `https://codebase-api.byted.org/v2/`。
- 公开命令树已切换为 `codebase auth|repo|commit|mr|issue|checks|search` 的资源分组形式；MR 评论统一走 `codebase mr comment`，reviewer/bypass/queue 相关操作分别走 `codebase mr reviewer|bypass|queue`，跨仓库搜索走 `codebase search mr|issue`，master 上已有的平铺命令仍保留为兼容入口。
- `codebase search code` 走 code.byted.org 的流式代码搜索（`/.api/v1/tasks`，Sourcegraph 风格 SSE），做的是跨仓库代码内容 grep，返回文件路径 + 匹配行。`--query` 是搜索词本身，`--repo-filter`（正则，如 `^example-org/example-repo$`）/`--lang`/`--file`（正则）/`--case-sensitive` 是过滤器，`--pattern-type literal|regexp` 控制匹配模式，`--limit` 映射为后端 `count:`，控制返回的匹配总数（命中数，非文件数）、`--timeout-ms` 控制后端匹配超时。搜索词始终拼在查询最前、过滤器随后（后端对 filter 在前的查询超时敏感，可能静默返回 0 匹配）。默认跨全站搜索；如需限定某个仓库，显式传 `--repo-filter`（正则）。
- Snippet 入口为 `codebase snippet list|get|create|update|delete`；`get --save <dir>` 默认不覆盖本地已有文件，增量更新 `--add-file/--remove-file` 会拒绝复用内容缺失或被截断的远端文件。
- SSH 公钥入口为 `codebase ssh-key list|create|delete`；上传只接受单个 OpenSSH 公钥文件并拒绝私钥，删除必须显式传 `--yes`。
- 当前 Git 仓库 `origin` 可用于自动推断仓库；如果推断失败，CLI 会说明是非 Git 仓库、缺少 `origin`、host 不支持，还是 remote 无法解析。
- 主仓库选择器统一推荐 `-R, --repo`；PR / issue 编号默认使用位置参数；正文统一用 `--body`，PR 创建改用 `--head/--base`。
- `codebase commit list|get` 使用 `--revision` 指定 branch/tag/commit SHA；未显式传入时会优先使用当前 Git 分支，失败后回落到仓库默认分支。
- `codebase repo directory list` 按目录路径分页返回完整文件元信息；根目录使用 `--path .`，继续翻页时把 JSON 输出的 `next_page_token` 传给 `--page-token`。也可直接把 Codebase tree URL 传给 `--path`。
- `codebase release list|get|create|update` 用于查询和维护挂在 tag 上的 release 描述；`release list` 会按 tag 扫描并解析 release，tag 很多时会更慢。
- `codebase checks list` 会保留 branch / commit 级 check runs，并在能解析出对应 MR 或显式传入 `--mr` / `--mr-id` 时，额外分组展示 `MR Check Runs`。
- `codebase pipeline list` 支持用 `-R + --branch/--git-tag` 列出 git-backed pipeline，可配 `--search` 过滤；不知道 pipeline 名称时先用它确认 name 与 YAML file。
- `codebase pipeline run` 支持用 `-R + --branch/--git-tag + --pipeline` 触发 git-backed pipeline，也可用 pipeline detail URL 或 `--file` 定位；manual inputs 用 `--inputs` 或 `--inputs-file` 传入。
- `codebase pipeline status` 支持用同一组 `-R + --branch/--git-tag + --pipeline` 选择器查询最新 run 状态，并自动拉取该 run 的详情：failReason、失败 job/step 以及逐 step 的成功/失败状态。
- `codebase pipeline runs list` 用 `-R + --branch/--git-tag + --pipeline` 列出该 pipeline 的 run 历史（runSeq / 状态 / 触发人 / 提交），支持 `--page/--page-size`，用于判断「连续挂了几晚」。省略 `--branch`/`--git-tag` 时返回跨所有分支的 run 历史（每条 run 带自己的 branch），结果按时间倒序；可用 `--status <succeeded|failed|...>`（服务端过滤）与 `--since <2026-06-01|"7d ago">` 缩小范围。`--since` 按触发时间过滤后再分页（先 filter 再 page），run 倒序只扫描到满足当前页所需即停。
- `codebase pipeline runs get` 给出某次 run 的失败诊断，需用 `--run-seq <n>`（来自 runs list）或 `--run-id <id>` 指定 run（最新 run 直接用 status）：失败 step、failReason、逐 step 状态，以及指向完整日志的 Run URL（git pipeline 的 atom 日志在 Orca，step_logs 接口对 git pipeline 返回空）。
- `codebase mr artifacts list|download` 会解析 MR check run 正文里的 BITS artifact 链接；下载多个匹配项时需要 `--all`，文件默认按 check run id 分目录保存。
- `codebase mr file-review get` 会把当前 MR 版本的变更文件与当前用户的 viewed paths 对齐，返回 total / viewed / unviewed 汇总和文件列表；`update --state viewed|unviewed` 只修改个人查看状态。文件范围使用可重复的 `--file` 或 `--all`，二者不能混用；`--mr` 也接受 BITS Code detail URL。`update` 默认 dry-run 并输出完整 payload；Agent 必须先展示预览，只有用户确认同一组目标、状态和 payload 后，才用相同参数追加 `--yes` 提交。任一字段变化都要重新预览并确认。
- **Review Bypass 的含义与边界**：它不会跳过 MR、不会直接推主分支，也不会自动豁免 CI/Checks；它只为指定 MR 的当前 `source_commit_id` 创建人工 Review 门禁豁免，并保留创建人、时间、原因和 commit 的服务端审计记录。仅当仓库规则允许、当前用户具有 bypass 权限，并且用户明确授权同一 repo、MR、source commit 与合入方式时执行；“帮我发 MR”“直接发布”等泛化表述不视为 bypass 授权。
- **Review Bypass 的固定流程**：先用 `bytedcli --json codebase mr status` 读取 `data.merge_request.source_commit_id`、`data.review.review_rule_groups[].ReviewRules[].Name` 和 checks/mergeability；确认非 Review 门禁均已满足后，用服务端字段 `TargetType` / `Target` / `Reason` 创建 review bypass；随后用 `mr bypass list --commit-id <source_commit>` 和 `mr status` 回读，最后才执行 `mr merge`，并用 `mr get` 验证 `Status=merged` 与 `MergeCommitId`。不要用 `--review` 快捷参数或小写 `kind` / `target` / `reason` 示例，已知会被部分服务端规则拒绝。
- **Commit 变更后必须重新确认**：Review Bypass 绑定创建时的 `source_commit_id`。源分支新增或改写 commit 后，旧 bypass 不适用于新提交；必须重新读取 status，并再次获得用户对新 commit 的明确授权，不能静默续用旧授权。
- `codebase repo member get` 读当前登录用户在该仓库的 access level，并派生 `Can Push`（developer/maintainer/master/owner 可推）；走 code.byted.org 前端 REST `/_/api/v1/repos/{path}/members/self`。
- `codebase repo member list` 走 Codebase `ListRepoMembers` + `GetRepoMemberStatistics`，返回角色、直接/继承来源、到期时间，以及直接/间接/即将到期的统计。默认查实名用户并分页；`--all` 自动翻页并按 identity id 去重；用户组是独立授权主体，必须另用 `--identity-type user-group` 查询，实名用户数不能当成实际访问人数上限。`--expiring-within-days` 默认 30。
- `codebase repo member create/update/delete` 管理用户的直接仓库授权：新增/改角色走 Codebase `UpsertRepoMember`，删除走 `RemoveRepoMember`；GitLab v4 `/api/v4/projects/:id/members` 已 phased out，在当前 Codebase 返回 503，不能作为实现后端。三条命令默认 dry-run，显式 `--yes` 才写；`create` 拒绝覆盖已有直接成员，`update/delete` 拒绝继承权限，写后会用 `ListRepoMembers` 回读。用户组写操作暂不支持。
- `codebase permission repository create` 由仓库 Owner 直接新增或更新用户的直接授权，username 和数字 user id 均可。支持 `--action reporter|developer|master|owner`；默认 dry-run，显式传 `--yes` 才调用 Codebase `UpsertRepoMember`。Reporter/Developer 默认 365 天，Master 默认 180 天，三者可用 `--days 1..365` 覆盖；Owner 永不过期且不能传 `--days`。这与 Kani 权限申请是两条不同链路。
- **直接授权写入确认（强制）**：Agent 必须先不带 `--yes` 运行并核对该命令真实输出的完整目标。`repo member create/update` 核对 repo、user、operation、new role、expiration、permissions、endpoint；`repo member delete` 核对 repo、user、current direct role、current expiration、endpoint；旧入口 `permission repository create` 核对 repo、user、role、expiration、permissions、endpoint。只有用户明确确认这一次具体写入后，才可用相同参数追加 `--yes`。任一目标字段或 operation 变化都必须重新预览并再次确认。
- `codebase permission repository apply` 直接为当前 Codebase 用户申请 `-R/--repo` 的仓库权限。命令会按仓库路径精确读取 CN Codebase 的 Kani 申请页资源，不依赖仓库读取权限或资源搜索结果，支持 `reporter`、`developer`、`master`；默认由 Kani 校验并预览，显式传 `--yes` 才创建审批。返回的 `manual_apply_url` 来自已校验的资源；精确读取失败时保留 Kani 错误，不能据此判断仓库不存在。可用 `--days` 指定授权天数，省略 `--reason` 时会自动生成仓库相关理由。
- `codebase permission apply --repos` 保持依赖仓库批量申请语义，但必须显式选择执行档：`--dry-run` 读取当前依赖权限状态并打印将提交的 payload，`--yes` 才逐个依赖仓创建审批工单；两者都不传时命令报错而不是提交（后端 `batch_apply` 请求体没有 dry-run 字段，该档位由 CLI 侧强制）。
- **依赖权限批量申请确认（强制）**：Agent 必须先用 `--dry-run` 展示 repo 列表、当前权限、将提交的 action 与 reason；只有用户明确确认这一批具体申请后，才可用相同参数追加 `--yes`。任一目标字段变化都必须重新预览并再次确认。预览里 `known_dependency: false` 的仓不是该主仓的依赖：整批都不是时 `--yes` 直接报错，部分不是时照常提交并在 `unknown_dependencies` 里列出。`state_unavailable: true` 表示依赖状态没读到，此时只能核对 payload、无法核对仓名；提交结果里同样带 `state_unavailable`/`state_error`，为 true 时 `unknown_dependencies: []` 只说明没核对过，不说明核对通过。
- `codebase repo protected-branch list` 列保护分支及其 push/merge access level；走 GitLab v4 `/api/v4/projects/{id}/protected_branches`（仓库的 Codebase 数字 Id 即 GitLab project id），空列表表示没有保护分支。
- `codebase repo protected-branch rule list/create/delete` 走 Codebase gateway（`?Action=ListProtectedBranches/CreateProtectedBranch/DeleteProtectedBranch`），比 v4 `protected-branch list` 多返回数字 rule id：`rule create --name-pattern` 用分支名或 glob（如 `release/*`）锁分支；`rule delete` 用 `--id`（精确 rule id，来自 `rule list`）或 `--name-pattern`（bytedcli 会先翻页在 rule list 里解析出 id，规则数超单页也不会漏）解锁。lock 状态的 source of truth 是 `rule list`，不是 v4 `protected-branch list`。
- `codebase repo branch get --with-creation` 在普通分支详情之外查询最新的同名 `git_branch_created` 活动，返回创建人、创建时间和初始 commit。活动按每页 100 条扫描，默认最多 20 页；老分支可用 `--creation-max-pages <1..100>` 扩大范围。JSON 的 `CreationScan.Truncated=true` 表示达到扫描上限但仍有后续页，不能据此断言没有创建活动；完整扫描仍未命中时也只表示活动记录未找到。省略 `--with-creation` 时保持原有分支详情输出。
- `codebase repo branch delete/cherry-pick/rebase` 是 git 原生写操作：`branch delete --name` 删分支；`branch cherry-pick --target-branch --commit` 把某 commit 应用到目标分支（冲突时 Codebase 返回 conflict 错误、不产生新 commit）；`branch rebase --branch --base-branch` 把分支 rebase 到 base 上。cherry-pick / rebase 默认 dry-run 只预览，必须加 `--yes` 才真正执行。
- `codebase commit list --base <ref> --target <ref>` 列出 base..target 之间可达的 commit（区间模式下 `--revision` 被忽略）；单 ref 历史仍用 `--revision`。
- 旧的扁平命令如 `get-merge-request`、`create-mr`、`create-branch`、`list-check-runs` 仍保留为隐藏兼容别名，建议新流程切到新命令树。

## CI 排障顺序

1. 先用 `codebase checks mr <mr>` 看 MR 级 checks，总结失败项和运行中项。
2. 再用 `codebase checks get --id <check_run_id>` 看失败 job、step 和 step 链接。
3. 默认用 `codebase checks log --check-run-id <id>` 批量展开整条 check run 的日志。
4. 若 check run 暴露 artifacts，用 `codebase mr artifacts list` 先确认可下载项，再用 `download --artifact <name>` 拉取完整包。
5. 需要手动触发仓库内 pipeline 时，先用 `codebase pipeline list -R <repo> --branch <branch>` 找到 pipeline name，再用 `codebase pipeline status -R <repo> --branch <branch> --pipeline <name>` 看最新状态，随后用 `codebase pipeline run -R <repo> --branch <branch> --pipeline <name>` 创建真实 run。
6. 排查 git-backed pipeline（含定时发版）失败：`codebase pipeline runs list ... --pipeline <name>` 看连续失败的 run 历史，再 `codebase pipeline runs get ... --pipeline <name> --run-seq <n>` 拿到失败 step + failReason；这条链路不依赖 `checks` 接口（git pipeline 原生 run 不进 `codebase checks`）。
7. 日志优先重定向到文件，再用 `rg` / `grep` / `less` 搜索，不要直接把全文贴进上下文。
8. 看到失败后，先判断是业务代码失败、CLI 自己回归，还是外部平台问题，再决定修复方向。
