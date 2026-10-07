# DevFlow 删除服务部署引用文档

本引用文档用于从指定 DevFlow 任务中删除某个服务部署。

## 何时使用

当用户明确表达以下意图时使用本引用文档：
- 删除某个 DevFlow 任务里的服务部署
- 从当前任务中移除指定 `psm` 的部署
- 清理某个任务中的服务部署记录

## 参数获取

参考后端接口 `/openapi/mcp/service/delete`，尽量收集这些参数：
- `task_id`
- `psm`
- `provider`

参数收集优先级如下，后者只用于补全缺失值：
1. 用户当前对话中明确提供的信息
2. 当前会话上下文中已经明确关联的 DevFlow 任务或服务信息
3. 仅在确实影响执行且无法唯一确定时，再与用户补问一次

补充规则如下：
- `task_id` 优先使用用户提供的值；如果当前上下文已经明确关联到唯一任务，也可以直接使用
- `psm` 优先从用户请求中提取
- `provider` 支持 `TCE`、`TCC`；如果用户明确给出就透传，未给出且上下文也无法唯一判断时可以留空，不要擅自猜测
- 如果参数缺失但接口允许为空，不要为了补齐参数频繁追问用户

## 调用方式

统一通过 `bytedcli devflow` 调用：

```bash
bytedcli devflow service delete --task_id="<task_id>" --psm="<psm>" --provider="<provider>" --bytedcli-skill-dir="<skill所在目录>"
```

参数允许为空时，省略对应 flag 即可，不要传占位值。

## 执行原则

- 优先使用用户当前消息里已经明确的 `task_id`、`psm`、`provider`
- 如果当前上下文已能唯一定位任务，可直接带上 `task_id`
- 不要擅自补充或猜测 `provider`
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 输出处理

- 直接返回 `bytedcli devflow` 的原始输出
- 不主动改写、总结或格式化底层返回
- 只有用户明确要求解释时，再补充说明
- 如果命令失败，优先保留并展示原始错误信息，再补充最少量的必要说明
