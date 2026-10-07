# 搜索 DevFlow 资源

当用户需要查询 DevFlow 任务，或查询可用于部署/创建DevFlow任务/添加到DevFlow任务的资源时，使用本能力。
当用户表达“先帮我搜索下 xxx，再加到 DevFlow 任务里”这类意图时，也应先调用本能力定位可添加资源。

## 何时调用

- 用户明确说要按 `meego` / `meego_id` 查询 DevFlow 任务或关联信息
- 用户明确说要按 DevFlow 任务创建者查询任务
- 用户明确说要按任务标题关键词搜索 DevFlow 任务
- 用户想搜索可部署资源，并给出关键词或资源类型
- 用户明确说想搜索“可添加到 DevFlow 任务”的资源，例如 TCE / FAAS / TCC / GOOFY / GECKO-UFRA / REPO / GECKO / LEGO / LAMBDA
- 用户明确说“帮我搜索下 xxx 并添加到 DevFlow 任务”“先查能不能加到 DevFlow 的资源”“帮我找能添加进任务流程的资源”
- 用户要确认某个 Meego 需求、缺陷或任务目前关联了哪些 DevFlow 资源

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. CLI 参数默认值

如果同一参数同时在用户对话和默认值中出现，必须优先使用用户对话中的值。

## 目标参数

参考后端接口，请尽量收集这些参数：
- `meego_id`
- `pattern`
- `creator`
- `type_list`
- `order_type`
- `page_index`
- `page_size`

其中：
- `type_list` 决定搜索模式：`8` 表示任务搜索；`2,3,4,5,17,24,29,18,30` 分别表示 `TCE/FAAS/TCC/GOOFY/GECKO-UFRA/REPO/GECKO/LEGO/LAMBDA` 可部署资源搜索
- `meego_id` 是任务搜索的主要查询入口；用户明确提供时应优先传入
- `pattern` 可用于任务标题关键词搜索，也可用于资源标识搜索
- `creator` 适合按 DevFlow 任务创建者过滤，仅任务搜索支持，当前应传 `creator_name`
- `order_type` 仅任务搜索支持
- `page_index`、`page_size` 都是可选参数，用户没提到时可以留空，不必追问

## 执行原则

- 用户明确给了 `meego_id` 时，直接使用，不要改写。如果用户提供了类似 "https://meego.larkoffice.com/governance/story/detail/6999755050" 的 URL，提取出 `6999755050` 作为 `meego_id` 。
- 非必需参数缺失时不要频繁追问用户
- 如果用户只表达“查某个 meego 相关任务”，优先只传 `meego_id`
- 如果用户要搜索任务，默认按 `type_list=8` 处理；未显式给 `type_list` 时不要额外追问
- 如果用户明确提到了“搜索资源”“搜索可部署资源”“搜索可添加到 DevFlow 任务的资源”，必须显式按资源搜索处理，优先传 `type_list=2,3,4,5,17,24,29,18,30`，不要落到默认任务搜索
- 如果用户要搜索可部署资源，也可按用户要求只传其中部分类型
- 如果用户表达的是“搜索后继续添加到 DevFlow 任务”，先执行资源搜索，优先返回可添加的候选资源，再根据后续步骤衔接任务创建/服务部署相关能力
- 不支持同时搜索任务和可部署资源；如果用户同时要求两者，提示拆成两次调用
- 资源搜索不传 `meego_id`、`creator`、`order_type`
- 当任务搜索同时提供 `meego_id`、`creator`、`pattern` 时，按交集过滤处理

## 调用方式

任务搜索场景，优先调用：

```bash
bytedcli devflow resource search --meego_id="<meego_id>" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户还给了任务关键词：

```bash
bytedcli devflow resource search --meego_id="<meego_id>" --pattern="<pattern>" --type_list="8" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户要按任务创建者或标题关键词筛选：

```bash
bytedcli devflow resource search --creator="<creator>" --pattern="<pattern>" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户同时给了 `meego_id`、`creator`、`pattern`：

```bash
bytedcli devflow resource search --meego_id="<meego_id>" --creator="<creator>" --pattern="<pattern>" --type_list="8" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户明确说的是搜索资源或搜索可部署资源：

```bash
bytedcli devflow resource search --pattern="<pattern>" --type_list="2,3,4,5,17,24,29,18,30" --bytedcli-skill-dir="<skill所在目录>"
```

如果用户只想搜某几类可部署资源：

```bash
bytedcli devflow resource search --pattern="<pattern>" --type_list="<type_list>" --bytedcli-skill-dir="<skill所在目录>"
```

如果任务搜索还给了排序和分页参数：

```bash
bytedcli devflow resource search --meego_id="<meego_id>" --type_list="8" --order_type="<order_type>" --page_index="<page_index>" --page_size="<page_size>" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量必要说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/resource/search`
- 当前通过 `type_list` 分流搜索语义：`8` 搜任务，`2,3,4,5,17,24,29,18,30` 搜 `TCE/FAAS/TCC/GOOFY/GECKO-UFRA/REPO/GECKO/LEGO/LAMBDA` 可部署资源
- 不支持同时传任务类型和可部署资源类型
- 当前支持根据 `meego_id`、`creator`、`pattern` 组合查询 DevFlow 相关任务和资源
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
