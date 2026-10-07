# Tesla (RM)

Tesla RM（Repository Mode）是 ByteDance 内部的自动化测试执行平台，支持按测试计划触发任务、查询执行结果和失败归因分析。

## 认证

所有命令需要 Tesla RM token，优先级：`--token TCE_xxx` > `BYTEDCLI_TESLA_TOKEN` 环境变量 > 配置文件 token（项目级覆盖用户级）。

Base URL 优先级：`--base <url>` > `BYTEDCLI_TESLA_BASE_URL` 环境变量 > 配置文件中的 `base` 字段（项目级覆盖用户级）> 全局 `--site` 映射的海外 plane > 默认值 `http://tesla.bytedance.net/rm`。

海外站点：默认走国内。查海外 Tesla RM 任务（如 TikTok ROW 的 `cloud.tiktok-row.net/tesla_repo` 链接）时带全局 `--site i18n-tt`（`--site` 是全局参数，须写在子命令前：`bytedcli --site i18n-tt tesla task get --id <id> --token TCE_xxx`），会路由到 `tesla-maliva.tiktok-row.net`。auth header 与国内一致（`tesla-rm-token`），token 用对应海外 RM 的即可。尚未登记映射的 control plane（US online / TTP / GCP 等）用 `--base <url>` 显式指定。

配置分两层，两层都可放 token（项目级优先）：

- 用户级 `~/.local/share/bytedcli/data/tesla.yaml`：个人默认 token / base / 计划等。
- 项目级 `.tesla/config.yaml`（仅读取当前目录，不向上查找）：按仓库覆盖 token / `base` / `default_rm` / `default_plan_id`。`.tesla/` 已被 gitignore，token 不会进版本库。

```bash
# 推荐：直接传 token
bytedcli tesla plan list-task --id 507863 --token TCE_xxx

# 或设置环境变量
export BYTEDCLI_TESLA_TOKEN=TCE_xxx
bytedcli tesla plan list-task --id 507863

# 或在用户级存储 ~/.local/share/bytedcli/data/tesla.yaml 写入 token
# 单 RM 写法：
#   token: TCE_xxx
#   default_plan_id: 507863
#
# 多 RM 写法：
#   default_rm: 3878
#   rms:
#     "3878":
#       token: TCE_xxx
#       default_plan_id: 507863
#
# 自定义 base URL（如指向 staging 环境）：
#   base: http://tesla-staging.example.com/rm
#
# 项目级 .tesla/config.yaml（仅当前目录，已 gitignore）可按仓库覆盖 token 与默认值：
#   token: TCE_xxx
#   default_plan_id: 507863
#   base: http://tesla-staging.example.com/rm
```

## 任务管理

```bash
# 触发新任务（动词跟着输入资源 plan 走，返回 task_id）
bytedcli tesla plan start-task --id 507863 --token TCE_xxx

# 触发并等待完成（start → 轮询 → 摘要报告）
bytedcli tesla plan run-task --id 507863 --token TCE_xxx --env-label ppe

# 查看完整任务元数据（自动合并失败用例明细 / Plan Name / Duration / Web URL）
bytedcli tesla task get --id 289935400 --token TCE_xxx
# 同时拉失败归因，合并到 get 结果（并发请求；归因接口失败时降级为只返回 detail）
bytedcli tesla task get --id 289935400 --with-analysis --token TCE_xxx

# 列出任务（支持时间/状态/计划过滤）
bytedcli tesla plan list-task --id 507863 --token TCE_xxx
bytedcli tesla plan list-task --id 507863 --since '7d ago' --token TCE_xxx

# 取消任务
bytedcli tesla task cancel --id 289935400 --token TCE_xxx
```

## 测试计划管理

```bash
# 查看计划详情（自动合并近 30 天的执行 stats；--since / --until / --trigger-type 可调时间窗与过滤）
bytedcli tesla plan get --id 507863 --token TCE_xxx
bytedcli tesla plan get --id 507863 --since '7d ago' --token TCE_xxx
bytedcli tesla plan get --id 507863 --since '7d ago' --trigger-type cron --token TCE_xxx

# 在指定 repo 下列出 plans（动词跟 repo 走，--id 即 repo_id，可从 --rm 兜底）
bytedcli tesla repo list-plan --id 3878 --token TCE_xxx
bytedcli tesla repo list-plan --rm 3878 --token TCE_xxx   # --id 从 --rm 兜底

# 在指定 repo 下创建新计划
bytedcli tesla repo create-plan --id 3878 --name demo-plan --token TCE_xxx
bytedcli tesla repo create-plan --id 3878 --body @plan.json --token TCE_xxx

# 更新计划（部分更新，仅修改传入的字段；后端要求每次更新带 git_branch，否则返回 code:500 "invalid git branch"）
bytedcli tesla plan update --id 507863 --name new-name --git-branch main --token TCE_xxx
# 修改没有专用 flag 的字段（trigger / config 等）：先 get 出来编辑再回填
bytedcli tesla plan get --id 507863 --token TCE_xxx --json > plan.json
bytedcli tesla plan update --id 507863 --body @plan.json --token TCE_xxx

# 删除计划
bytedcli tesla plan delete --id 507863 --token TCE_xxx
```

## JSON 输出

```bash
# 所有命令支持 JSON 输出
bytedcli --json tesla plan list-task --id 507863 --token TCE_xxx
bytedcli --json tesla plan get --id 507863 --since '7d ago' --token TCE_xxx
```
