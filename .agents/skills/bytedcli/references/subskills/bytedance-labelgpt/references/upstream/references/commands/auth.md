# bytedcli labelgpt auth

认证命令用于登录、查看当前登录状态和退出登录。本 skill 中统一使用 `auth login` 登录。
执行登录前先运行 `auth status --format raw` 检查状态；如果 `logged_in=true`，复用现有
登录态，不要重复执行 `auth login`。只有 `logged_in=false`、登录态无效或业务命令提示未登录时，
才执行 `auth login`。

自动化环境可以设置公开环境变量 `LABELGPT_SERVER_TOKEN`。该值会去除首尾空白，trim 后为空
等同未设置；它只从环境变量读取，不写入配置文件，也不会在输出中回显，只用于换取个人 token。
换票请求中的 `TenantId` 固定为协议占位字符串 `"1"`，不表示业务 Space；Server Token 换票不发送
业务 `x-space-id`。登录态、个人 sync-token cache 和 session Cookie 均不与业务 Space 绑定；后续
业务命令独立解析目标 Space 并发送 `x-space-id`。

## auth login

登录并刷新 LabelGPT 登录态。默认写入全局 auth store；需要隔离当前工作区时传 `--local`，
登录状态会保存在当前工作目录下的 `./.labelgpt-cli/`。如果在 IDE / Agent 沙箱环境中默认
全局登录被文件系统拦截、权限不足或无法写入 `~/.labelgpt-cli/`，降级使用
`auth login --local`。

`LABELGPT_SERVER_TOKEN` trim 后非空时优先于所有 JWT 与 SSO 来源。命令会跳过二维码/浏览器
交互，并强制执行一次换票，即使当前 site 已有 fresh cache 也不直接复用；失败立即返回，
不回退 JWT、SDK 登录态或交互登录。

未设置 Server Token 且进入交互流程时，`auth login` 是同步阻塞命令：输出登录挑战后会持续
等待用户完成授权，登录成功或失败前不会返回。Agent 执行该命令时必须持续读取输出；首次拿到
挑战信息后，要在命令仍运行时立即把二维码信息和完整授权链接展示给用户，然后继续等待同一个
命令完成。终端二维码无法完整转述时，至少展示 `qr_image_path` 或说明二维码已在终端输出。
不要等待命令退出后才汇总这些信息。

未设置 `LABELGPT_SERVER_TOKEN` 时，如果 `AIME_USER_CLOUD_JWT` trim 后非空，所有 resolved
site 都先尝试用它跳过二维码/浏览器交互，直接换取个人凭据并写入对应 auth store；换票失败时
继续 site-aware 登录。resolved site
为 `cn`（包括 CN、BOE 和 unknown region 的现有归一结果）时只读取
`MIRA_TOKEN_BYTED_JWT_CN`；resolved site 为 `tt`、`nontt` 或其他非 `cn` 值时只读取
`MIRA_TOKEN_BYTED_JWT`。两个 MIRA 变量之间不做跨 site fallback；本 site 对应变量为空白
时进入交互登录。非交互路径不会输出 `qr_image_ready` 事件。

### 用法

```bash
bytedcli labelgpt auth login [选项]
```

### 示例

```bash
LABELGPT_SERVER_TOKEN=<SERVER_TOKEN> bytedcli labelgpt auth login --format raw
bytedcli labelgpt auth login
bytedcli labelgpt auth login --local
bytedcli labelgpt auth login --custom-region SG
bytedcli labelgpt auth login --no-terminal-qr
bytedcli labelgpt auth login --qr-image /tmp/labelgpt-cli-qr.png
bytedcli labelgpt auth login --format raw
```

### 参数说明

- `--no-terminal-qr`：不在终端打印二维码。
- `--qr-image <path>`：把二维码保存为 PNG 图片。
- `--local`：写入当前工作目录的 workspace-local auth store；不传时写入全局 auth store。
- `--custom-region <region>`：全局参数，指定登录区域。
- `--format <pretty|raw|json>`：输出格式。
- `-o <DIR>`：写入登录结果 JSON。

### 输出

`raw/json` 输出字段：

- `event`：登录事件名，成功时为 `login_success`。
- `site`：认证站点。
- `store`：凭据存储范围，`global` 或 `local`。默认 `global`，传 `--local` 时为 `local`。
- `qr_image_path`：`raw/json` 交互登录过程中可能先输出的 `qr_image_ready` 事件字段，表示临时二维码图片路径。
- `auth_url`：`raw/json` 交互登录过程中可能先输出的 `qr_image_ready` 事件字段，表示授权 URL。

`raw/json` 交互登录时，stdout 可能先输出一条 `qr_image_ready` JSON 事件，最终再输出 `login_success` JSON 事件；交互进度文本输出到 stderr。

### 输出文件

- `-o <DIR>`：写入 `auth_login_<site>.json`。

### 注意事项

- 交互式终端可直接扫码登录。
- 执行 `auth login` 前先用 `auth status --format raw` 检查登录态；`logged_in=true` 时不要重复登录。
- `LABELGPT_SERVER_TOKEN` 存在时 `auth login` 为非交互强制刷新，不会输出
  `qr_image_ready`；换票失败不 fallback。
- 命令会同步阻塞等待授权；挑战信息出现后应立即提供二维码信息和完整登录链接，再继续等待命令完成。
- 不要只提示“扫码登录”，也不要等到命令退出后才展示挑战信息。
- 默认 `auth login` 使用全局 auth store；在 Trae-CN 等 IDE / Agent 沙箱中如遇到全局目录写入被拦截，改用 `auth login --local` 写入当前目录的 `./.labelgpt-cli/`。
- `AIME_USER_CLOUD_JWT` trim 后非空时，`auth login` 在所有 site 都先尝试直接换取
  个人凭据；换票失败时继续目标 site 对应的 MIRA 或交互登录。`cn` 只读取
  `MIRA_TOKEN_BYTED_JWT_CN`，非 `cn` 只读取
  `MIRA_TOKEN_BYTED_JWT`。两个 MIRA 变量不互相 fallback，本 site 来源为空白时进入交互
  登录。
- 业务命令读取登录态时会先读 workspace-local auth store，再回退到 global auth store。
- Agent/脚本模式如果无法扫码，可通过全局参数 `--byted-jwt-token` 或环境变量 `LABELGPT_CLI_BYTED_JWT_TOKEN` 提供 JWT。
- 普通 LabelGPT 命令先按当前 site 复用 fresh cache；只有 cache stale 或 miss 时才换票。此时
  Server Token 优先；没有 Server Token 才使用显式 JWT 或 SDK 登录态。

## auth status

查看当前认证状态。

### 用法

```bash
bytedcli labelgpt auth status [选项]
```

### 示例

```bash
bytedcli labelgpt auth status
bytedcli labelgpt auth status --format raw
```

### 输出

`raw/json` 输出字段：

- `logged_in`：是否已有有效凭据。
- `site`：当前站点。
- `store`：登录态命中的存储范围，登录成功时为 `local` 或 `global`；未登录时省略。
- `user_info`：cache 命中时只包含可用的 `email`、`user_id`、`open_id`；SDK fallback 保持既有
  用户信息结构。未登录时省略。

### 输出文件

- `-o <DIR>`：写入 `auth_status_<site>.json`。

### 注意事项

- 机器调用建议使用 `--format raw`。
- `auth status` 没有 `--local`；它先按当前 site 从 workspace-local -> global 查找
  fresh cache，并在 `store` 中返回实际命中范围。
- fresh matching cache 未命中时，`auth status` 再检查 ByteCloud SDK 登录态；它不会用
  `LABELGPT_SERVER_TOKEN`、显式 JWT 或 SDK JWT 换取新的 LabelGPT token。
- 仅临时设置 `LABELGPT_SERVER_TOKEN` 或 `LABELGPT_CLI_BYTED_JWT_TOKEN` 不会让 status 自动
  显示 `logged_in=true`；Server Token 首次使用时执行 `auth login`，或让普通业务命令按需换票。
- `logged_in=true` 时，复用当前登录态，不要重复执行 `auth login`。
- `logged_in=false` 时，应先执行 `bytedcli labelgpt auth login`；如果只是一次性调用业务命令，也可以把 JWT 环境变量直接加在业务命令前。

## auth logout

退出登录。

### 用法

```bash
bytedcli labelgpt auth logout [选项]
```

### 示例

```bash
bytedcli labelgpt auth logout
bytedcli labelgpt auth logout --local
bytedcli labelgpt auth logout --format raw
```

### 输出

`raw/json` 输出字段：

- `logged_out`：是否完成清理。

### 输出文件

- `-o <DIR>`：写入 `auth_logout_result_<timestamp>.json`。

### 注意事项

- 该命令默认清理 workspace-local 和 global 两处登录状态。
- 传 `--local` 时只清理当前工作目录的登录状态。
- 清理范围包括 CLI token/Cookie cache 与对应 ByteCloud SDK 状态。
- 命令不能修改父进程环境，因此不会 unset `LABELGPT_SERVER_TOKEN`、
  `LABELGPT_CLI_BYTED_JWT_TOKEN` 或其他环境变量。若 Server Token 仍存在，后续普通命令仍可
  按需重新换票；如需彻底停用它，调用方必须自行 unset。

## Schema 查询索引

```bash
bytedcli labelgpt schema auth login --format raw
bytedcli labelgpt schema auth status --format raw
bytedcli labelgpt schema auth logout --format raw
```
