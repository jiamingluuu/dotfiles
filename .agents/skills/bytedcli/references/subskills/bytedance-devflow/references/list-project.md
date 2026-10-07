# 查询空间项目列表

当用户需要查看某个业务空间下的项目列表时，使用本能力。

## 何时调用

- 用户明确说要查看空间项目列表
- 用户给出 `biz_id`，希望查看该业务下的项目列表
- 用户想先查某个 Biz 下有哪些项目，再继续做资源或任务操作

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户当前对话中明确提供的信息
2. CLI 参数默认值

如果同一参数同时在用户对话和默认值中出现，必须优先使用用户对话中的值。

## 目标参数

当前只需要一个参数：

- `biz_id`：空间 ID，可选参数，默认值为 `0`

## 执行原则

- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

```bash
bytedcli devflow project list --biz_id="<biz_id>" --bytedcli-skill-dir="<skill所在目录>"
```

例如：

```bash
bytedcli devflow project list --biz_id="1001" --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化后端返回
- 只有用户明确要求解释时，再补充说明
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量必要说明

## 备注

- 本能力对应接口：`GET /openapi/mcp/project/list`
- 对应底层 CLI action：`project list`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill
