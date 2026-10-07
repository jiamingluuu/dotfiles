# 常见错误处理

当响应包含 `ResponseMetadata.Error`，尤其涉及账号状态、实名认证、购买限制、产品开通或权限时，完整阅读本文件。

## 实名认证

不要先把认证类错误归因于参数格式。可查询账号认证状态：

```bash
ve account_verify GetVerifyInfo \
  --version 2018-01-01 \
  --endpoint open.volcengineapi.com \
  --method POST \
  --force \
  --query 'Result.{IsVerified:IsVerified,IdentityType:IdentityType}'
```

`IsVerified=false` 表示未实名；已实名时 `IdentityType` 通常是 `individual` 或 `enterprise`。控制台认证页面：

```text
https://console.volcengine.com/user/authentication/detail/
```

共享排障材料不得记录真实账号 ID、RequestId、TRN、姓名、证件号、手机号或资源 ID。

## 错误分类

| 错误                                                                                                 | 分类               | 处理                                 |
| ---------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------ |
| `AccountNotVerified`                                                                                 | 明确的实名认证阻断 | 完成控制台认证后重试                 |
| `ErrNotVerifiedAccount`                                                                              | 明确的实名认证阻断 | 完成控制台认证后重试                 |
| `OperationDenied.InvalidAccount` 且消息包含 `Account not verified yet or may not exist`              | 账号不存在或未实名 | 先用 `GetVerifyInfo` 核实            |
| `Forbidden.PurchaseLimited`                                                                          | 购买资格或风控     | 不得在无证据时归类为实名问题         |
| `AccountPrivilegeInsufficient`                                                                       | 账号权限不足       | 检查产品与账号权限                   |
| `AccountNoPermission`                                                                                | 产品授权不足       | 检查产品 entitlement/权限            |
| `ProductUnsubscribed`、`ServiceNotActivated`、`KMS_ServiceNotOpen`、`OperationDenied.ServiceStopped` | 产品未开通或已停用 | 按账号产品状态处理，不要改参数碰运气 |

## Babi 自动批准失败

`scripts/ve_login_babi.sh` 的失败阶段决定恢复方式：

| 阶段         | 典型现象                                    | 处理                                                                                                                                                 |
| ------------ | ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| 版本检查     | ve 低于 1.1.5 或无 `--no-browser`           | 升级 `@volcengine/cli`                                                                                                                               |
| Babi Session | bytedcli 登录失败、账号未配置、Session 无效 | 先 `bytedcli auth login`；退出单账号时执行 `bytedcli volcano auth logout --volc-account-id <account-id>`，明确清理全部 Babi 缓存时才用 `--all`，再执行 `list-accounts/config` 后重试 |
| TraceId      | ve URL 没有合法 `trace_id`                  | 停止旧进程，升级 ve 后重试；不要猜 TraceId                                                                                                           |
| 确认接口     | 非 2xx 或业务错误                           | 保留非敏感 RequestId/错误码，停止流程；不得输出 Cookie                                                                                               |
| ve 轮询      | 批准后 60 秒内未完成                        | `abort` 清理，再使用手动设备码 fallback                                                                                                              |

## 手动设备码进程退出

以下错误表示 `scripts/ve_login_remote.sh` 启动的 `ve login` 已不在运行：

```text
ERROR: no running ve login subprocess. Any previously recorded URL is dead
```

设备码只存在于对应 ve 进程中；进程退出后，旧 URL、用户码和 LINK 都失效，不能继续交给用户。

| 原因                | 信号                                       | 恢复                                     |
| ------------------- | ------------------------------------------ | ---------------------------------------- |
| 设备码过期          | `verify` exit 10，日志含 timed out/expired | `abort` 后重新 `start`                   |
| 用户拒绝            | `verify` exit 10，日志含 denied            | 重新开始并说明需要批准，或换认证方式     |
| Runner 清理后台进程 | 之前 ALIVE，未批准就变 DEAD                | 只重试一次；仍失败则换 AK/SK、STS 或 SSO |
| 从未启动或已 abort  | 没有 pid 状态文件                          | 重新 `start`                             |

恢复顺序：

```bash
scripts/ve_login_remote.sh abort
scripts/ve_login_remote.sh start <region> [profile]
scripts/ve_login_remote.sh url
scripts/ve_login_remote.sh status
```

把新 `LINK` 交给用户，用户完成后运行 `verify [profile]`。不得使用已退出进程留下的链接，也不要用 `nohup` 替代脚本的 `setsid`。

## 登录成功但 API 返回 EOF

`verify` exit 13 且输出 `LOGGED_IN_UNVERIFIED` 表示 ve 已成功写入 Session，但主机无法连接 `open.volcengineapi.com`。常见原因是代理或 `NO_PROXY` 只放行 `.volcengine.com`，没有放行 `.volcengineapi.com`。

不要重新登录或更换凭证；修复网络、代理或防火墙后复用已有 Session。可以用只读请求验证连通性：

```bash
curl -sS https://open.volcengineapi.com/
```
