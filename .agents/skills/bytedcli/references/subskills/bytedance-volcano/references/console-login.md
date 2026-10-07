# 控制台登录流程

默认先使用 `scripts/ve_login_babi.sh` 自动批准设备码。本文件描述 Babi 自动批准不可用时的手动 fallback。

## 默认：Babi 自动批准

```bash
bytedcli volcano auth list-accounts
scripts/ve_login_babi.sh --region <region> --profile <babi-name> [--volc-account-id <account-id>]
```

`<babi-name>` 必须来自 `list-accounts` 中所选账号的名称，不能用 account ID 替代。该脚本要求 `ve >= 1.1.5` 且支持 `--no-browser`。它以 `--profile <babi-name>` 启动 ve 轮询进程，从验证 URL 解析 `trace_id`，再调用：

```bash
bytedcli volcano auth approve-device --trace-id <trace-id> [--volc-account-id <account-id>] --yes
```

Cookie 只在 bytedcli 进程内使用，脚本不会读取或打印 Cookie 文件。批准后最多等待 `VE_LOGIN_APPROVAL_TIMEOUT` 秒，默认 60 秒。登录落盘后，脚本显式执行 `ve configure profile --profile <babi-name>`；`ve login --profile` 本身不会完成当前 profile 切换。

## 手动 fallback

**不要直接运行孤立的 `ve login`。必须使用 `scripts/ve_login_remote.sh`。** Agent 的每次工具调用可能使用新 shell，直接运行会让轮询进程被清理，导致设备链接失效。辅助脚本通过独立 session 保持 ve 存活、提取 URL/Code、处理旧 profile 替换提示并验证结果。

地域解析：用户指定值 > `VOLCENGINE_REGION` > `cn-beijing`。Babi 登录必须把账号名称作为 profile，并在 `start`、`verify` 和成功后的 `ve configure profile` 中保持一致。

### 1. 启动

```text
scripts/ve_login_remote.sh start <region> [profile]
```

成功输出固定键值：

```text
URL=https://signin.volcengine.com/authorize/oauth/device?trace_id=<id>
CODE=XXXX-XXXX
LINK=https://signin.volcengine.com/authorize/oauth/device?trace_id=<id>&user_code=XXXX-XXXX
EXPIRES_IN=300
NEXT=...
```

`start` 在部分 Runner 中可能因后台后代进程而看似超时。不能据此判断成功或失败，也不要重试、abort 或改用 nohup；进入下一步检查。

### 2. 读取并检查状态

```bash
scripts/ve_login_remote.sh url [profile]
scripts/ve_login_remote.sh status
```

- `url` exit 0：返回可用 LINK。
- `url` exit 11：URL 尚未输出，短暂等待后再查一次。
- `url` exit 3：进程已经退出，旧链接已失效；abort 后重新 start。
- `status` 输出 PID、URL 是否就绪、运行时长和是否过期。

### 3. 把 LINK 交给用户

优先发送 `LINK`，`URL + CODE` 作为 fallback。设备码当前有效期通常为 300 秒，以 `EXPIRES_IN` 实际输出为准。用户不需要粘贴授权码，只需完成页面批准并告知 Agent。

不得自行拼接或复用旧的 signin URL。

### 4. 验证

```text
scripts/ve_login_remote.sh verify [profile]
```

| Exit code | 含义                                      | 处理                                |
| --------- | ----------------------------------------- | ----------------------------------- |
| 0         | 登录成功且 GetCallerIdentity 验证通过     | 继续任务                            |
| 11        | ve 仍在轮询，用户尚未完成                 | 询问是否已批准，未过期时再次 verify |
| 13        | ve 已保存 Session，但 API endpoint 不可达 | 不要重登，修复网络                  |
| 10        | 设备码过期或被拒绝                        | abort 后重新开始                    |

切换账号时 ve 可能在成功后询问是否替换 profile 的 `login_session`；脚本已通过 FIFO 预先回答，不需要额外输入。

手动 fallback 的 `verify` 返回 0 或 13 后，也要显式切换：

```bash
ve configure profile --profile <babi-name>
```

退出该 Babi 登录态时使用 `bytedcli volcano auth logout --volc-account-id <account-id>`；它会同步执行 `ve logout --profile <babi-name>`。该操作保留 bytedcli 的默认 Babi account ID 和 ve profile，只清理 session 缓存；不要使用 `ve logout --all`。

### 5. 中断或切换地域

```bash
scripts/ve_login_remote.sh abort
```

用户取消、改用 AK/SK、设备码过期或切换地域时先 abort。一个 UID 同时只允许一条 ve 登录流程。

## 不可违反的规则

- 不得让 ve 轮询进程在用户批准前退出。
- 不得把 `start` 超时直接当成失败；先用 `url/status` 判断。
- 不得用 `nohup` 替代辅助脚本。
- 不得发送已退出进程或已过期设备码对应的链接。
- 不得自行构造 signin URL 或追加 user_code。
- 不得省略 `--no-browser`；辅助脚本固定使用它。
- 不得让用户粘贴不存在的 authorization code。
- 不得并行启动多个 ve login。
- `verify` exit 13 不是登录失败，不能重新登录。
