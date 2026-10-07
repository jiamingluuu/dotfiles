# 查询 Meego 列表候选

当用户需要查看自己的 meego/需求 列表，或根据 meego 链接、meego id、meego 名称/描述查询 meego 候选列表时，使用本能力。

## 何时调用

- 用户明确说“查看一下我的 meego/需求 列表”
- 用户说“帮我查询 xxx meego/需求”“查一下某个 meego/需求”
- 用户给出 meego 链接，希望查询对应 meego
- 用户给出 meego id，希望查询对应 meego
- 用户给出 meego 名称、标题片段或需求描述，希望查询相关 meego

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. CLI 参数默认值

如果同一参数同时在用户对话和默认值中出现，必须优先使用用户对话中的值。

## 目标参数

当前对外支持这些参数：

- `biz_id` ：空间 ID
- `project_key` ：项目键
- `source` ：任务来源
- `work_item_name` ：任务名称

其中：

- 当用户没有提供任何筛选条件，只是说“查看一下我的 meego 列表”时，允许不传 `work_item_name`
- 当用户提供了 meego 链接、meego id、meego 名称或描述时，都统一透传到 `work_item_name`
- `source` 支持传数字枚举值或枚举名；如果用户没传，默认按 `2` 处理，如果用户希望查询最近最近创建/最近有估分的 meego/需求，应传 `4` 处理
- `project_key` 是可选筛选条件，用户没提到时不传，如果用户要求查看全部空间下的meego项目，应传 `project_key=""`
- 如果用户指定了项目空间，但当前上下文无法直接推断出对应的 `project_key`，应先阅读参考 `references/list-project.md` 的方法拉取全部项目空间，再用返回结果中的 `name -> key` 做映射
- 只有当本次完全未传 `project_key` 参数时，CLI 才会尝试读取本地缓存里的 `work_item_project`
- 如果用户显式传了 `--project_key=""`，CLI 会视为“已传空字符串”将查询所有空间下的meego项目，不会回退到本地缓存

## 执行原则

- 用户提供 meego 链接时，原样作为 `work_item_name` 传入
- 用户提供纯数字 meego id 时，原样作为 `work_item_name` 传入
- 用户提供 meego 名称、标题片段或自然语言描述时，原样作为 `work_item_name` 传入
- 用户没有提供筛选条件时，不要追问，直接发起无参查询
- 后端返回 `project_key` 和 `project_name` 时，CLI 会按 `project_key:::project_name` 写入本地缓存，供下次未传 `project_key` 时复用
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

查看自己的 meego 列表：

```bash
bytedcli devflow work_item list --bytedcli-skill-dir="<skill所在目录>"
```

按 meego 链接、meego id 或 meego 描述查询：

```bash
bytedcli devflow work_item list --work_item_name="<work_item_name>" --bytedcli-skill-dir="<skill所在目录>"
```

例如：

```bash
bytedcli devflow work_item list --work_item_name="7322229145" --bytedcli-skill-dir="<skill所在目录>"
```

```bash
bytedcli devflow work_item list --work_item_name="支付链路重试" --bytedcli-skill-dir="<skill所在目录>"
```

按项目或来源筛选：

```bash
bytedcli devflow work_item list --biz_id="1001" --project_key="DEVFLOW" --source="2" --bytedcli-skill-dir="<skill所在目录>"
```

当用户只提供项目空间名称，且无法直接确定 `project_key` 时，先拉取全部项目空间再映射：

```bash
bytedcli devflow project list --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量必要说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/task/work_item`
- 对应底层 CLI action：`work_item list`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
