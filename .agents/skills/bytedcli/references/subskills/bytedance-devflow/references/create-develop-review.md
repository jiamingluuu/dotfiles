# DevFlow 发起任务代码评审引用文档

本引用文档用于为某个 DevFlow task 或当前仓库分支发起代码评审。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 为某个 DevFlow task 发起代码评审
- 为当前仓库分支对应任务发起代码评审
- 查看默认 reviewer 后确认提交代码评审
- 补 reviewer 后重新发起代码评审

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. 当前工作目录和本地仓库上下文
3. 无法自动补齐时，再与用户交互确认必要参数

如果同一参数同时在用户对话和本地上下文中出现，必须优先使用用户对话中的值。

## 目标参数

参考当前 CLI 和后端接口，请收集这些参数：
- `task_id`
- `review_plan_file`

其中：
- `task_id` 不是必填；如果用户未提供，可允许 `bytedcli devflow --bytedcli-skill-dir="<skill所在目录>"` 基于当前仓库上下文自动推断 `repo_name/branch`
- `review_plan_file` 仅在第二次最终提交时需要；第一次仅准备时不需要
- `review_plan_file` 文件内容必须由 skill 按下述模板生成；不要依赖服务端在首次返回里内嵌 JSON 模板
- `review_plan_file` 必须写入 `/tmp` 下的临时文件，例如通过 `mktemp /tmp/devflow-review-plan.XXXXXX.json` 生成；不要写入项目目录、`.trae` 目录或其他工作区路径
- 用户补 reviewer 时，优先收集邮箱前缀；如果用户直接给完整邮箱也可接受，OpenAPI 会自动补全缺失的 `@bytedance.com`

生成 `review_plan_file` 时使用这个模板：

```json
{
  "title": "feat: xxx",
  "repos": [
    {
      "repo_name": "iesarch/devflow_admin",
      "reviewers": [
          "a",
          "b"
      ],
      "description": "optional"
    },
    {
      "repo_name": "iesarch/devflow_mono",
      "reviewers": [
          "c"
      ],
      "description": "train_id=1002"
    }
  ]
}
```

约束：
- `review_plan.repos` 必须覆盖最新准备结果中的全部可评审仓库，仓库名称集合必须完全一致；不得省略其中任何仓库，也不得加入准备结果之外的仓库，仓库顺序不影响集合一致性
- `repos[].reviewers` 必须是该 repo 的最终 reviewer 全量集合
- 准备结果列出的每个可评审仓库都必须填写完整 reviewer 集合；准备阶段已按既有规则排除的仓库不写入 `repos[]`
- 不支持增量参数，例如“只追加一个 reviewer”
- 非火车 repo 的 `description` 可选
- 火车 repo 必须在 `description` 中明确填写选中的车次，格式为 `train_id=<车次ID>`；也兼容 `train_name=<车次名称>`，但推荐优先使用 `train_id`
- 第一次返回的默认 reviewer 展示给用户时，应按邮箱前缀理解和确认，例如 `alice` 而不是 `alice@bytedance.com`

## 执行原则

- 第一次调用只做准备，不真正提交
- 如果接口返回 `pending`，必须把返回文案原样展示给用户
- 不要自己重写、摘要或删减返回里的待确认信息
- 如果准备结果中存在火车仓库，必须先让用户从返回的“可选车次”中明确选择要绑定的车次，再执行第二次最终提交
- 用户只确认 reviewer 还不够；火车场景还需要确认每个火车 repo 绑定哪一趟车，并将该选择写入对应 repo 的 `description`
- 如果用户需要补 reviewer，应让用户给出每个 repo 的最终 reviewer 全量列表，再在 `/tmp` 下生成 `review_plan_file`
- 生成 `review_plan_file` 时，必须按最新准备结果逐一写入全部可评审仓库，不允许用户或 Agent 选择其中一部分仓库
- 第二次最终提交前，必须核对 `repos[]` 的仓库数量与准备结果中的可评审仓库数量相同，并逐一核对 `repo_name` 名称集合完全一致
- 服务端会拒绝只包含部分可评审仓库的真子集方案并返回 `pending`；收到该结果后必须按最新准备结果补齐全部仓库，不能继续尝试部分评审
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

统一通过 `bytedcli devflow --bytedcli-skill-dir="<skill所在目录>"` 调用。

第一次仅准备，不会真正提交：

```bash
bytedcli devflow develop-review create --task_id="<task_id>" --bytedcli-skill-dir="<skill所在目录>"
```

如果没有 `task_id`，且当前目录就是目标 git 仓库，也可以直接让底层 CLI 自动推断：

```bash
bytedcli devflow develop-review create --bytedcli-skill-dir="<skill所在目录>"
```

第二次提交最终方案：

```bash
bytedcli devflow develop-review create --task_id="<task_id>" --review-plan-file="<path>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 对 `pending` 响应，必须原样展示
- 提交成功后，直接展示接口返回的成功文案
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明
