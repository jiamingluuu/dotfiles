# Guardian 常见问题与处理

## 工具版本过期

**在排查任何错误之前**，先确保 bytedcli 和已安装的技能是最新版本：

```bash
bytedcli self update
```

升级完成后重试原始命令。很多问题是由 CLI 版本和已安装技能之间的版本偏差引起的。

## 1. Missing command

- 原因：未指定子命令
- 处理：`bytedcli guardian --help`；需要查看某个子命令时使用 `bytedcli guardian <command> --help`

## 2. Missing required option

- 原因：缺少必需选项；Guardian 命令不使用必需位置参数
- 处理：使用对应 Guardian 命令的 `--help` 查看 `--id`、`--tenant-id`、`--biz-id` 等选项

## 3. Not authenticated / 获取字节云 JWT 失败

Guardian 固定使用 CN 当前用户身份。不要探测、切换或复用 `i18n-tt`、`i18n-bd`、EU 或 BOE 登录态；全局 `--site` 和 `BYTEDCLI_CLOUD_SITE` 不会改变 Guardian 的 CN 控制面。

仅当用户明确要求检查身份或连通性时执行：

```bash
bytedcli guardian auth status --probe
```

按返回的 `hint` 和 `auth_command` 处理。若结果要求登录，显式覆盖可能存在的全局站点环境变量并执行 CN 登录：

```bash
BYTEDCLI_CLOUD_SITE=cn bytedcli --site cn auth login
```

随后重新运行原 Guardian 命令。不要手写 MAGW/OpenAPI 请求，也不要复制 JWT、Cookie、Origin 或 Referer。

## 4. 网络/权限问题

- 确认内网访问权限
- 确认已登录且 Token 有效

## 5. GUARDIAN_WRITE_BLOCKED

- 含义：请求在发包前被安全门拒绝，例如权限证据不足、目标不唯一、修改/删除超预算、空数组清空、跨业务线或级联影响。
- 处理：阅读错误 `details`，缩小变更或修正 payload 后重新预演。不要试图绕过 mutation client。

## 6. GUARDIAN_WRITE_CONFIRMATION_MISMATCH / ALREADY_USED / EXPIRED

- 含义：确认令牌已使用、已过期，或当前参数/远端快照已与预演不一致。
- 处理：重新运行完全相同的命令但不带 `--yes`，审核新计划后再确认。

## 7. GUARDIAN_WRITE_OUTCOME_UNKNOWN

- 含义：写请求已经尝试，但接口报错、超时或写后读回不能证明最终状态。CLI 已保存包含 before/after 和错误摘要的本地回执。
- 处理：禁止自动重试。先用读命令核对远端，再运行 `guardian restore get --receipt-id <id>` 查看恢复数据；确需修复时创建一份新的写计划。
