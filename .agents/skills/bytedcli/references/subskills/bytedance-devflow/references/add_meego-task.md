# 绑定 Meego 到 DevFlow 任务

当用户需要把某个 Meego issue 绑定到 DevFlow task 时，使用本能力。

## 何时调用

- 用户明确说要把某个 Meego 需求、缺陷或任务关联到 DevFlow task
- 用户要求给某个 DevFlow task 添加 `meego_id`
- 用户希望把当前仓库或当前分支对应的 DevFlow task 与某个 Meego issue 建立关联

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. CLI 内部自动推断得到的任务上下文

如果同一参数同时在用户对话和自动推断结果中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请尽量收集这些参数：

- `meego_id`
- `task_id`
- `repo_name`
- `branch`

其中：

- `meego_id` 是当前 action 的必填参数，用户明确提供时应优先传入
- `task_id`、`repo_name`、`branch` 三者用于定位目标任务；优先使用 `task_id`
- 如果用户没有提供 `task_id`，但已经明确给出 `repo_name` 和 `branch`，可以直接透传
- 如果用户没有提供 `task_id`、`repo_name`、`branch`，由 `bytedcli devflow`基于当前环境自动推断任务

## 执行原则

- 用户明确给了 `meego_id` 时，直接使用，不要改写
- 如果用户提供了类似 "https://meego.larkoffice.com/governance/story/detail/6999755050" 的 URL，提取出 `6999755050` 作为 `meego_id`
- `meego_id` 的获取方式与 `references/search-resource.md` 保持一致
- 只要 `meego_id` 已明确，就不要为了补齐 `task_id`、`repo_name`、`branch` 频繁追问用户
- 如果用户同时给了 `task_id` 和 `repo_name`/`branch`，允许一起透传；若只给了一部分任务定位参数，也允许省略，由底层 CLI 补全
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

用户明确提供 `task_id` 时：

```bash
bytedcli devflow task add_meego --task_id="<task_id>" --meego_id="<meego_id>" --bytedcli-skill-dir="<skill所在目录>"
```

用户明确提供 `repo_name` 和 `branch` 时：

```bash
bytedcli devflow task add_meego --repo_name="<repo_name>" --branch="<branch>" --meego_id="<meego_id>" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户只给了 `meego_id`，也可以直接调用：

```bash
bytedcli devflow task add_meego --meego_id="<meego_id>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量必要说明

## 备注

- 本能力对应接口：`POST /openapi/mcp/task/add_meego`
- 对应底层 CLI action：`task add_meego`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
