# DevFlow 本地工作区清理

用于扫描 `ws build` 创建的本地任务工作区，并在用户明确确认后清理可回收的构建产物。

## 安全边界

- `ws cleanup` 只清理开发任务状态为已完成或全部变更已合入的工作区。
- 清理内容限于代码 worktree、`.agents`、生成的 skill 软链接、`AGENTS.md`、目标为 `AGENTS.md` 的 `CLAUDE.md` 软链和 `.devflow-workspace.json`。
- 用户自有的 `CLAUDE.md` 普通文件或其他软链不会被删除。
- 任务根目录、用户生成的 spec、技术文档及其他资料不会被删除。
- 共享 clone `shared_workdirs/src` 不会被删除。
- 仓库存在未提交内容或工作区正在使用时，默认不可清理。
- `--user-confirm` 是实际执行开关；没有该参数时命令只预览。

## 参数

- `--task_ids`：可选。省略表示扫描全部本地任务工作区；传入后只处理指定任务。
- `--user-confirm`：可选。只有用户明确确认后才能传入。
- `--force`：默认禁止。仅当用户明确要求丢弃未提交内容，或强制清理由 Git 元数据损坏造成的 worktree 残留，并再次确认风险时才允许传入。

## 强制执行步骤

1. 首次调用不得携带 `--user-confirm`。
2. 读取预览结果，向用户展示可清理任务 ID、状态、仓库和预计释放空间；不可清理项展示原因。
3. 请求用户明确确认要清理的任务 ID。
4. 用户未确认时停止，不得执行任何清理。
5. 用户确认后，将确认的精确 ID 固化到 `--task_ids`，追加 `--user-confirm` 再次调用。
6. 原样展示逐任务清理结果；失败项不得自动追加 `--force` 重试。

即使用户确认“清理全部”，第二次调用也要传首次预览中可清理的精确任务 ID，避免两次调用之间新出现的工作区被纳入。

## 扫描全部工作区

```bash
bytedcli devflow ws cleanup --bytedcli-skill-dir="<skill所在目录>"
```

## 扫描指定工作区

```bash
bytedcli devflow ws cleanup --task_ids="471876,474473" --bytedcli-skill-dir="<skill所在目录>"
```

## 用户确认后清理

```bash
bytedcli devflow ws cleanup --task_ids="471876,474473" --user-confirm --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- `mode=preview`：只展示结果并请求确认，不代表已经清理。
- `mode=cleanup`：展示 `cleaned`、`skipped`、`failed` 结果和实际释放空间。
- API、git 或文件操作失败时保留原始错误，不能把失败项描述为已清理。
