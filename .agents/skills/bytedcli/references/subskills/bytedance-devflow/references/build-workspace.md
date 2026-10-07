# DevFlow 本地工作区构建引用文档

本引用文档用于通过 DevFlow task_id 或 group_id 构建本地或云端工作区。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 根据 DevFlow task_id 构建本地工作区
- 初始化本地工作区
- 拉取某个 DevFlow 任务的本地工作区
- 重新构建某个 DevFlow 任务对应的本地工作区
- 通过 task_id 构建云端工作区
- group 尚未创建 DevFlow task 时，通过 group_id 构建本地工作区
- 通过 group_id 构建当前已关联 task 的本地工作区
- 通过 group_id 加载云端工作区资产，无论 group 是否已关联 task

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的 `task_id` 或 `group_id`
2. 当前工作区 `AGENTS.md` 或上下文中的 DevFlow TaskID

如果无法获得 `task_id` 或 `group_id`，应先请用户提供其中一个。

## 目标参数

- `task_id` / `group_id`：二选一。分别表示 DevFlow 任务 ID 和 DevGroup ID。
- `is_cloud`：必填布尔值。构建云端工作区资产时传 `true`，构建本地工作区资产时传 `false`；与使用 task_id 还是 group_id 无关。

## 执行原则

- 不需要执行 git 命令来获取参数。
- 不要手动创建工作区目录或 clone 仓库；这些动作由底层 `ws build` 统一完成。
- 如果用户已经明确给出 `task_id`，直接调用命令，不需要额外确认。
- 如果用户已经明确给出 `group_id` 且要求本地构建，直接调用命令，不需要先查询或创建 task。
- 不根据 task_id、当前目录或其他间接信息推断 `is_cloud`。用户明确要求云端工作区时传 `true`，否则传 `false`。
- `--is_cloud` 必须写成 `--is_cloud=true` 或 `--is_cloud=false`，禁止使用不带值的裸参数。
- 如果命令返回 pending，必须优先原样展示 pending 文案，再根据提示补参或让用户重试。

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow ws build --task_id="<task_id>" --is_cloud=false --bytedcli-skill-dir="<skill所在目录>"
```

用户明确要求构建云端工作区时：

```bash
bytedcli devflow ws build --task_id="<task_id>" --is_cloud=true --bytedcli-skill-dir="<skill所在目录>"
```

示例：

```bash
bytedcli devflow ws build --task_id="471876" --is_cloud=false --bytedcli-skill-dir="<skill所在目录>"
```

通过 group_id 构建：

```bash
bytedcli devflow ws build --group_id="998877" --is_cloud=false --bytedcli-skill-dir="<skill所在目录>"
bytedcli devflow ws build --group_id="998877" --is_cloud=true --bytedcli-skill-dir="<skill所在目录>"
```

服务端会自动判断 group 是否已有 active task：有 task 时构建 task workspace，无 task 时构建 `group_workspace/<group_id>`；`is_cloud` 只影响资产配置加载。

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出。
- 不主动对输出做总结、概要、改写、提炼或格式化。
- 只有用户明确要求解释时，才补充说明。
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明。
