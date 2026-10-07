# veFaaS 服务说明

veFaaS 已收录的 Action 全部使用 `ve vefaas`，不切换到同名 bytedcli 资源命令。先通过帮助确认当前版本的 Action 和参数：

```bash
ve vefaas
ve vefaas ListFunctions --help --detail --lang ZH
ve vefaas GetFunction --help --detail --lang ZH
ve vefaas GetReleaseStatus --help --detail --lang ZH
ve vefaas ListSandboxes --help --detail --lang ZH
```

最低版本统一为 `ve >= 1.1.5`。

## 依赖接口需要 FunctionId

`ListSandboxes` 需要 `FunctionId`。`CreateTimer`、`CreateKafkaTrigger`、`CreateSandbox` 也依赖已存在的函数 ID，创建依赖资源前必须先验证函数创建成功。

临时资源删除顺序：

```text
DeleteKafkaTrigger / DeleteTimer -> 必要时 KillSandbox -> DeleteFunction
```

除非任务明确验证对应集成，否则保持 `EnableVpc`、TOS/NAS 挂载和 TLS 日志投递关闭，避免扩大权限、依赖和费用范围。

`UpdateFunction --Envs` 是数组全量覆盖，不是单键 merge。修改一个环境变量前先用 `GetFunction` 读取完整环境变量列表，修改目标项后把全量数组回填，避免清空其他变量。
