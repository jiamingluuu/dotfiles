# BABI companion 排障

## 命令或参数不存在

先用当前运行时 help 核对命令树：

```bash
bytedcli babi --help
bytedcli babi <namespace> --help
```

运行时 help 中的 standalone 网关参数受[宿主调用规则](babi-invocation.md)约束：禁用 `--base-url`，网关区域使用 `babi` 前的 `--vregion`；商品业务筛选 `--region` 保留。
若返回 `BYTECLOUD_BABI_CLI_OPTION_DUPLICATED`，删除重复的 `--site`，仅保留一个目标站点后重试。

## Companion 安装或校验失败

首次失败先原样重试一次；
若持续出现 `BYTECLOUD_BABI_CLI_VALIDATION_FAILED` 或版本配置错误，重新安装当前 bytedcli 版本，
不要单独把 companion 改成 `latest`。本地开发时检查 `BYTEDCLI_BABI_CLI_PATH` 是否指向可执行文件。

## 认证失败

只有错误明确为 `AUTH_REQUIRED` 时运行 `bytedcli auth login`。跨站点调用使用
`bytedcli --site <site> babi ...`，确保登录站点与业务站点一致。权限不足不是登录问题。
不得读取或回显注入到 companion 子进程的 JWT。

领域接口、参数和业务限制继续读取对应领域目录中的 troubleshooting 或 reference 文件。

## Oncall 缺少 bytedcli

发起 BABI Oncall 需要 bytedcli。提示 `bytedcli: command not found` 时，先安装 CLI，
安装成功后回到[问题反馈的 Oncall 流程](feedback.md#oncall直接使用-bytedcli-子-skill)加载依赖 Skill。

获取[bytedcli 最新安装说明](https://bytedcli.gf-preview.bytedance.net)：

```bash
curl -fsSL https://bytedcli.gf-preview.bytedance.net
```

该地址返回 Markdown 文档，用于读取安装说明，不要将其直接管道传给 shell 执行。
有 npm 时，从组织内部 registry 查询并记录精确版本，再全局安装：

```bash
BYTEDCLI_VERSION="$(npm view @bytedance-dev/bytedcli dist-tags.latest --registry https://bnpm.byted.org)"
npm install -g "@bytedance-dev/bytedcli@${BYTEDCLI_VERSION:?未取得版本}" --registry https://bnpm.byted.org
```

没有 Node.js/npm 时，先按组织安装规范准备运行环境；本指南不提供下载脚本后直接交给 shell
执行的降级安装路径。安装后检查 `bytedcli --version` 和 `bytedcli --help`；命令仍找不到时，
按安装输出检查 PATH，必要时新开终端或 Agent 会话。安装失败时说明实际错误，不进入 Oncall 创建流程。
用户仅询问安装方法或明确要求不执行时，只提供命令。安装成功不表示已创建工单或发起 Oncall。
