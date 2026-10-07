# BAM 元数据管理

```bash
# PSM 列表（三视图，--recent / --starred 互斥；缺省走 BAM 服务端聚合的平台动态视图）
bytedcli bam psm list --cluster default                # 默认：BAM 服务端聚合的平台动态视图（与登录用户无强绑定）
bytedcli bam psm list --recent --cluster default       # 推荐：查询本人最近访问过的 PSM（bytedcli 本机历史，按 cloud site 隔离，上限 20；只读，不刷新 visited_at；缺省字段并发调用 service/info 回填，--no-enrich 关闭）
bytedcli bam psm list --recent --no-enrich              # 关闭 lazy enrich，仅渲染本地缓存中已存在的字段
bytedcli bam psm list --starred                         # 收藏列表（与控制台「我的收藏」一致；只读，不写本地访问历史）
bytedcli bam psm list --starred --count 10 --offset 40  # 分页（与默认视图一致，不会自动拉全）
bytedcli bam psm search "example.service.api" --cluster default

# 方法列表 / 详情（支持 --cluster 指定集群，--version 指定版本）
bytedcli bam method list --psm "example.service.api"
bytedcli bam method list --psm "example.service.api" --cluster i18n
bytedcli bam method list --psm "example.service.api" --cluster i18n --version 1.0.155
bytedcli bam method get --endpoint-id 123456 --version 1.2.3
bytedcli bam method get --psm "example.service.api" --method "DemoMethod"
bytedcli bam method get --psm "example.service.api" --method "DemoMethod" --ep-type rpc
bytedcli bam method get --psm "example.service.api" --method "DemoMethod" --cluster i18n
bytedcli bam method gencode --endpoint-id 123456
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod"
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod" --ep-type rpc
bytedcli bam method gencode --psm "example.service.api" --method "DemoMethod" --schema-type response

# 代码生成规则与生成任务
bytedcli bam codegen rule list --psm "example.service.api" --cluster default
bytedcli bam method list --psm "example.service.api" --cluster default
bytedcli bam codegen rule create --psm "example.service.api" --name "robot_demo_rule" --app-id 1234 --package "com.example.demo.model" --methods "GetDemoInfo"
bytedcli bam codegen rule update --rule-id 123456 --psm "example.service.api" --name "robot_demo_rule" --app-id 1234 --package "com.example.demo.model" --generate selected --methods "GetDemoInfo"
bytedcli bam codegen generate --rule-id 123456 --branch master
bytedcli bam codegen generate --rule-id 123456 --branch master --create-permission-ticket --permission-reason "need codegen access"
bytedcli bam codegen component build --component-repo "example-org/example-component" --idl-branch master
bytedcli bam codegen component build --component-repo "example-org/example-component" --idl-branch feature/idl --output-branch feature/generated

# 版本历史
bytedcli bam version list "example.service.api" --cluster default

# 按 git_branch 找 master/main 的最新版本（版本号是全服务自增的，列表第一条未必来自 master；
# 版本列表可能上千条，--json 落盘后用 jq 过滤，不要人工浏览全量输出；无输出 = 该分支没有 BAM 版本）
bytedcli --json bam version list "example.service.api" --cluster default > /tmp/bam-versions.json
jq -r '[.data.versions[] | select(.git_branch=="master" or .git_branch=="main")] | max_by(.ctime) | .version // empty' /tmp/bam-versions.json

# 找指定开发分支的最新版本（同名分支可能对应多个版本，取最新；无输出 = 该分支没有 BAM 版本）
jq -r '[.data.versions[] | select(.git_branch=="feature/demo-branch")] | max_by(.ctime) | .version // empty' /tmp/bam-versions.json

# 创建/更新 IDL 版本（--next-version 自动 patch +1；或 --version 指定版本号）
bytedcli bam idl update --psm "example.service.api" --branch master --next-version
bytedcli bam idl update --psm "example.service.api" --branch "codex/fix-idl" --version "1.2.4" --commit-id "abc1234" --commit-msg "update idl"

# 引用 schema 查询（拉取 struct、enum、const，支持按类型和名称过滤）
bytedcli bam idl schema --psm "example.service.api" --version 1.0.155 --cluster default
bytedcli bam idl schema --psm "example.service.api" --version 1.0.155 --type enum --search EntityType
```

## 代码生成规则说明

- `rule create` 和 `rule update` 是两个独立命令；创建不接受 `--rule-id`，更新必须传 `--rule-id`。
- `--generate selected|all|unselected` 默认是 `selected`；`selected` 和 `unselected` 都要求传 `--methods`。
- `--scaffold` 支持 `android`=30、`flutter`=31、`ios`=32、`ferry`=33、`harmony`=34、`kotlinmulti`=35，也可以直接传数字 id。
- `--methods` 使用 BAM 方法名，推荐先执行 `bam method list`，取返回里的 `endpoint.rpc_method || endpoint.name`。
- `codegen generate --rule-id` 会在响应包含 `has_permission=false` 或 `escape_params` 时自动执行 IAM 权限检查；只有显式加 `--create-permission-ticket` 才会创建权限工单，默认权限角色为 `bam.developer.cn`。
- `codegen component build --component-repo` 接受 BAM 组件产物仓库的 Codebase URL 或 `namespace/repository`，按组件配置的 `cmpt_git_repo` 精确匹配后触发打包；IDL 来源仓库由该组件的 BAM 规则管理，不通过命令参数指定。
- `--idl-branch` 指定 BAM 规则读取 IDL 的分支；`--output-branch` 指定组件产物仓库的发布分支，省略时与 `--idl-branch` 相同。
- `codegen component build` 会立即触发组件打包；仅在用户明确要求并确认组件仓库、IDL 分支、产物分支后执行，否则只说明命令，不要触发。
- `pipeline_id` 和 `run_seq` 从 `task_url` 尽力解析，无法解析时为 `null`；非空时可用 `bytedcli bits pipeline <pipeline_id> --run-seq <run_seq>` 查询，命令不会等待打包完成，并保留 `task_url`、`record_id`。
- RPC 方法按 PSM + 方法名查询或生成代码时，给 `method get` / `method gencode` 加 `--ep-type rpc`。
- `method get --schema ref` 输出会保留 HTTP `query_param` / `header_param` / `body_param` 与 RPC `rpc_param`。
- `idl schema` 拉取指定服务版本的全部引用 schema（struct、enum、const），支持 `--search <keyword>` 按名称过滤和 `--type enum|struct|const|string_enum` 按类型过滤。
- `--app-id`、`--package`、`--psm`、`--name` 不提供业务默认值，需要按当前业务显式传入。
