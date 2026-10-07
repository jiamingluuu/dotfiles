---
name: bytedance-mindai
description: 通过 MindAI 远程服务生成、调整、监听和下载图表 SVG，并支持搜索和执行官网图表模板，适用于架构图、流程图、ER 图、泳道图、时序图、甘特图、漏斗图、里程碑、思维导图等图示需求。
---

# MindAI 图表生成

## 概览

使用本技能调用 MindAI 远程图表生成服务。本地侧只负责鉴权、创建或续接任务、监听事件并保存 SVG，不在本地实现图生成逻辑。

公开入口：

```bash
bytedcli mindai chart
```

支持的能力：

| 用户意图 | 命令 | 默认交付 |
|---|---|---|
| 普通生图、画图、生成图表或图示 | `execute --prompt <text>` | 本地 SVG、MindAI 会话链接 |
| 只创建任务、不等待产物 | `create --prompt <text>` | MindAI 任务 ID、会话链接 |
| 基于已有任务调整结果 | `update --task-id <id> --prompt <text>` | 更新请求结果、同一任务 ID |
| 继续监听已有任务 | `watch --task-id <id>` | 本地 SVG、MindAI 会话链接 |
| 下载已有会话或任务的 SVG | `svg download --chat-url <url>` 或 `--task-id <id>` | 本地 SVG、MindAI 会话链接 |
| 搜索官网图表模板 | `template search` | 模板列表；`--expand` 时包含参数定义 |
| 查看模板详情 | `template get --template-id <id>` | 模板内容和参数定义 |
| 使用模板生图 | `template execute` | 本地 SVG、MindAI 会话链接 |

MindAI Skill 的交付边界是 SVG。飞书文档、飞书画板、Canvas、文档插图和服务端飞书导出不属于本技能；用户提出这些后续需求时，应在 SVG 生成完成后交给对应的 Lark/whiteboard 能力处理，不要拼接已移除的 MindAI 参数或调用技能目录中的 Python 实现。

## 必需流程

普通生图直接执行：

```bash
bytedcli --json mindai chart execute --prompt "画一个订单履约链路图，包含下单、支付、出库、配送、签收和退款分支"
```

`execute`、`watch` 和模板执行默认监听到 `svg_ready`。SSE 静默期不表示任务失败；客户端会按 `--waiting-interval-ms` 输出本地等待事件。

如果用户基于已有结果继续调整：

```bash
bytedcli --json mindai chart update \
  --task-id <task_id> \
  --prompt "把支付节点拆成预授权、扣款和退款三个步骤"

bytedcli --json mindai chart watch --task-id <task_id>
```

`update` 支持重复传入本地参考图片：

```bash
bytedcli --json mindai chart update \
  --task-id <task_id> \
  --prompt "按照标注调整布局" \
  --attachment /absolute/path/annotation.png
```

附件只通过 MindAI `uploadAttachment` 接口上传，不代表飞书文档或画板操作。

## 组织生图 Prompt

Agent 应把用户意图整理成信息充分、可执行的图表需求，优先说明：

- 业务目标和受众。
- 关键角色、模块、实体、节点或状态。
- 节点之间的调用、数据流或状态流转。
- 条件分支、异常路径和范围边界。
- 必须呈现的字段、指标口径或结论。

不要只提交“画一个架构图”这类薄描述。除非用户明确要求，不要自行编造配色、布局或装饰约束。

用户明确指定视觉风格时，可用 `--image-style-name <name>`。允许值以命令 `--help` 为准，不要推断默认风格。

## 下载已有 SVG

```bash
bytedcli --json mindai chart svg download --chat-url <mindai_chat_url>
bytedcli --json mindai chart svg download --task-id <task_id>
```

客户端优先使用本地任务缓存；没有可访问的 SVG 文件时，才继续监听远端事件。

## 官网模板

搜索并展开候选模板：

```bash
bytedcli --json mindai chart template search \
  --keyword "漏斗" \
  --page 1 \
  --page-size 5 \
  --expand
```

查看已知模板：

```bash
bytedcli --json mindai chart template get --template-id sop:sample-template
```

执行模板时，`--template-id` 与 `--template-title` 必须且只能提供一个：

```bash
bytedcli --json mindai chart template execute \
  --template-id sop:sample-template \
  --param '图片名称=电商转化漏斗' \
  --param '图片内容=曝光 -> 点击 -> 下单 -> 支付'
```

标题只允许唯一精确匹配。遇到模糊或重复标题时，展示候选并让用户明确模板 ID，不要自动选择。

## 鉴权与事件

正常业务命令会自行处理鉴权，不要额外运行状态检查。只有用户明确要求或命令返回鉴权错误时，读取：

- [references/auth.md](references/auth.md)：bytedcli JWT、MindAI 初始化和授权排障。
- [references/event_contract.md](references/event_contract.md)：SSE、JSONL、恢复监听和本地状态。

全局 `--json` 必须放在 `mindai` 之前：

```bash
bytedcli --json mindai chart watch --task-id <task_id>
```

默认不要使用 `--include-svg`，避免把完整 SVG 写入上下文；交付 `svg_path` 即可。

## 最终交付

任务成功后向用户提供：

- 本地 SVG：`<absolute_svg_path>`
- MindAI 会话：`<mindai_chat_url>`
- 任务 ID：仅在后续调整或恢复监听需要时提供

不要声称已创建或更新飞书文档、画板或 Canvas。
