---
name: merlin-devbox
description: 管理 merlin, seed 开发机：查询列表与详情、启动/停止、远程执行脚本、配置线上任务环境、检测当前是否为 Devbox 环境。当用户说"查看开发机/列出开发机/启动开发机/停止开发机/在开发机上执行/配置任务环境/mlx install/检测开发机环境/存储使用情况"时使用。
---

# 开发机管理

管理 Merlin 开发机的查询、生命周期、远程执行和环境配置。

## 工作台 SSH 公钥

工作台「SSH 公钥」管理当前账号的公钥集合，不需要开发机 ID。原生 `get/upload/delete` 直连 v4 REST 接口并复用 bytedcli JWT；ROW 站点使用 `--site i18n-tt`。与其他 Merlin 命令一样，通过全局 `--site` / `--vregion` 选择控制面，不支持 `--vdc`。目前真实读取已在 ROW 验证；其他站点按现有 Merlin 站点映射路由，仍受后端部署和权限限制。

```bash
# 列出完整公钥、SHA256 指纹及 ssh_permission_required
bytedcli --site i18n-tt --json merlin cpu-devbox ssh-keys get

# 上传一条公钥：先预览，再提交；只能传 .pub，不能传私钥
bytedcli --site i18n-tt merlin cpu-devbox ssh-keys upload --key-file ./demo-key.pub
bytedcli --site i18n-tt merlin cpu-devbox ssh-keys upload --key-file ./demo-key.pub --yes

# 删除选中的公钥；同样默认预览
bytedcli --site i18n-tt merlin cpu-devbox ssh-keys delete --key-file ./demo-key.pub
bytedcli --site i18n-tt merlin cpu-devbox ssh-keys delete --fingerprint '<SHA256 fingerprint from get>' --yes

# 显式 --dry-run 即使与 --yes 同时使用也不会写入
bytedcli --site i18n-tt merlin cpu-devbox ssh-keys delete --key-file ./demo-key.pub --yes --dry-run
```

- `--key-file` 与 `--public-key '<algorithm> <base64> [comment]'` 二选一；删除也可选 `--fingerprint`，三种选择器互斥。
- 输入支持普通 RSA、DSA、Ed25519、ECDSA nistp256/384/521 及 OpenSSH sk Ed25519/P-256 公钥，不支持 SSH 证书。校验完整二进制字段格式，不评估密钥强度或数学有效性；拒绝控制字符，允许文件末尾单个 LF/CRLF。无法识别的已有条目仍原样保留，指纹为 `null`；文本显示过滤终端控制字符，JSON 保留原始值。
- 公钥按 SHA256 指纹匹配，不依赖注释。重复上传同一把公钥不写入；删除移除该指纹的所有副本（包括注释不同的副本），其他条目原样保留。删除不存在的公钥返回错误，不提交。
- 默认预览会读取当前列表，返回 `dry_run`、`changed`、`applied`、前后条数、最终 `public_keys` 与完整请求；`get --dry-run` 和 `get --schema` 不访问后端。
- `get` 的 `ssh_permission_required` 始终存在：后端未提供时为 `null`，明确提供时保留 `true` / `false`。
- 上传／删除与当前页面一样通过 `POST .../ssh-keys/get` 读取，再以 `POST .../ssh-keys/set` 替换列表。提交前再次核对当前列表，提交后读回校验。接口没有原子版本条件，仍有读写竞态窗口，执行期间不要从页面或其他客户端同时修改公钥。
- 写请求不自动重试。提交失败返回 `MERLIN_SSH_KEYS_WRITE_OUTCOME_UNKNOWN`，不能据此判断未写入；写入报错或读回失败时，先使用相同 `--site` / `--vregion` 运行 `get` 确认实际状态，再决定是否重试。
- 提交成功后，读回请求失败返回 `MERLIN_SSH_KEYS_READBACK_FAILED`；读到的列表与提交列表不一致（包括顺序不同）返回 `MERLIN_SSH_KEYS_READBACK_MISMATCH`。两者均标记 `write_accepted: true`，不重复提交；删除无匹配项返回 `MERLIN_SSH_KEYS_NOT_FOUND`。
- 已有 generated `ssh-keys add/set` 保持上游 MCP 命令契约；部分控制面可能返回 tool-not-found。工作台单条增删优先使用上述原生 `upload/delete`，不要用 MCP `set` 绕过确认。

> 说明：本指南覆盖 CPU 开发机，命令族为 `bytedcli merlin cpu-devbox instances …`。GPU 开发机是并列的 `bytedcli merlin gpu-devbox instances …` 命令面，但子命令与参数**并不一致**：gpu-devbox 没有 `exec`、没有 `instance-usages`，其 get/start/stop 用 `--instance-sid`（不是 `--sid`），也没有 `--is-force`。

## 前置条件

- 拥有目标开发机的访问权限
- `bytedcli merlin` 可用

### 环境检测

判断当前是否在 Merlin Devbox 中：

```bash
if [ -n "$ARNOLD_WORKSPACE_ID" ]; then
    echo "当前在开发机中，资源 ID: $ARNOLD_WORKSPACE_ID"
fi
```

完整检测（两个条件都满足才是 Devbox）：

```bash
env | grep -E "^(HOSTNAME=mlxlab|MERLIN_)" | head -20
```

| HOSTNAME 以 `mlxlab` 开头 | MERLIN_* 变量存在 | 结果 |
|--------------------------|-----------------|------|
| 是 | 是 | **Merlin Devbox** |
| 否 | 任意 | 非 Devbox |
| 是 | 否 | 非 Devbox |

### bytedcli merlin 安装检查

```bash
bytedcli merlin --help &>/dev/null || \
  NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest merlin --help
```

如果出现认证错误（401/403），运行 `bytedcli auth login`。

---

## 1. 查询开发机

### 列出所有开发机

```bash
bytedcli merlin cpu-devbox instances list
```

### 获取特定开发机详情

```bash
bytedcli merlin cpu-devbox instances get --sid 12345
```

查询开发机详情；如需等待运行状态，重复执行该命令轮询：

```bash
bytedcli merlin cpu-devbox instances get --sid 12345
```

输出包含：基本信息（ID、名称、状态、所有者）、访问信息（VSCode URL、SSH 命令、WebShell URL）、资源配置（CPU、内存、GPU）等。

开发机状态：`running`（运行中）、`stopped`（已停止）、`starting`（启动中）、`stopping`（停止中）。

---

## 2. 生命周期管理

### 启动开发机

```bash
bytedcli merlin cpu-devbox instances start --sid 12345
```

### 停止开发机

```bash
bytedcli merlin cpu-devbox instances stop --sid 12345
```

强制停止（包括所有 remote worker）：

```bash
bytedcli merlin cpu-devbox instances stop --sid 12345 --is-force
```

### 查询存储使用情况

```bash
bytedcli merlin cpu-devbox instance-usages get --instance-sid 12345
```

输出包含系统盘、bytedrive、bytenas 的使用情况。

**注意**：停止开发机前确保没有重要任务在运行；如果有 remote worker 运行，需加 `--is-force`。

---

## 3. 远程执行脚本

在指定开发机中远程执行命令，60 秒超时限制。

```bash
bytedcli merlin cpu-devbox instances exec --sid 12345 --command nvidia-smi
```

```bash
bytedcli merlin cpu-devbox instances exec --sid 12345 --command 'pip install numpy && python -c "import numpy; print(numpy.__version__)"'
```

在开发机环境中可直接执行命令，无需通过 bytedcli merlin。

**注意**：确保开发机处于 `running` 状态；敏感操作（如删除文件）请谨慎执行。

---

## 4. 配置线上任务环境

在开发机中配置与线上任务或任务模板一致的运行环境，用于复现和调试。

### 从任务链接安装

URL 包含 `development/instance/jobs`，提取 `job_run_id`：

```bash
bytedcli merlin cpu-devbox instances exec --sid '<id>' --command 'mlx install --job_run <job_run_id>'
```

### 从任务模板安装

URL 包含 `development/template/jobs`，提取 `job_def_name`：

```bash
bytedcli merlin cpu-devbox instances exec --sid '<id>' --command 'mlx install --job_def <job_def_name>'
```

### 强制覆盖安装

当底层镜像不同时，需用户确认后追加 `--force`：

```bash
bytedcli merlin cpu-devbox instances exec --sid '<id>' --command 'mlx install --job_run <job_run_id> --force'
```

**注意**：强制覆盖可能导致现有环境配置丢失，操作前必须得到用户确认。

---

## 关联技能

- `merlin-devbox-troubleshoot`：排查连接、启动和性能问题
- `merlin-devbox-worker`：启动和管理 MLX GPU Worker
