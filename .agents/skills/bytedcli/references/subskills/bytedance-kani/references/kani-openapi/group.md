# Kani OpenAPI: Group

在以下场景读取本文件：

- 你需要读取单个 group
- 你在为 group 申请或成员排障收集上下文
- 你已经从 namespace 维度缩小范围，准备进一步查 group 对象

## `group get`

用途：读取单个 group。

参数说明：

- `--region <region>`：可选
- `--namespace <namespace>`：必填
- `--group-key <key>`：必填
- `--metadata`、`--jwt-token`、`--auth-token`：同总览

示例：

```bash
bytedcli kani openapi group get --namespace kani_demo --group-key demo-group
```
