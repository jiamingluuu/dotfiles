---
name: bytedance-obric-jenkins
description: 使用 bytedcli 查询 Obric Jenkins 单次构建的状态、参数、变更、产物和控制台日志尾部。
---

# bytedcli obric jenkins

用于读取 `obric-build-jenkins.bytedance.net` 上的 Jenkins 构建。命令复用
`bytedcli auth login --session` 保存的 ByteDance SSO 浏览器会话，并自动完成 Jenkins CAS 登录。

## Build details

```bash
bytedcli obric jenkins build get \
  --url 'https://obric-build-jenkins.bytedance.net/job/demo-job/54/'

bytedcli --json obric jenkins build get \
  --job demo-folder/demo-job \
  --build 54
```

结果包含构建状态、时间、触发原因、参数、提交变更和产物链接。凭据类参数名对应的值会被脱敏。
使用 `--url`，或同时使用 `--job` 和 `--build`；两种定位方式不能混用。嵌套 job 使用
`--job folder/job-name`。

## Console log

```bash
bytedcli obric jenkins log get \
  --url 'https://obric-build-jenkins.bytedance.net/job/demo-job/54/' \
  --tail 200

bytedcli --json obric jenkins log get \
  --job demo-job \
  --build 54 \
  --tail 50
```

- `--tail` 默认为 `200`，范围为 `1-5000`。
- 命令先读取 Jenkins 的日志字节位置，再只下载有界尾部窗口，不会默认拉取完整大日志。
- 文本模式直接输出日志行；JSON 模式同时返回 `startOffset`、`nextOffset`、`totalBytes`、
  `moreData` 和 `truncated`。

## Authentication

认证失效时执行：

```bash
bytedcli auth login --begin --session
```

当前能力只读，不提供触发、重建、停止、删除或修改 Jenkins 配置的命令。
