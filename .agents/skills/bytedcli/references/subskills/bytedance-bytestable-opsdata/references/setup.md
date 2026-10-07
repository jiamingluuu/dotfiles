# 环境、身份与故障处理

## 前置条件

运行环境需安装包含 `opsdata` 内置命令的 bytedcli，并能访问公司内网。先检查 `bytedcli bytestable opsdata --help`；若命令不存在，升级 bytedcli。无需单独安装 opsdata 插件。Skill 不自带凭证，也不授予数据权限。

身份由 bytedcli 管理。个人会话用 `--as user`，已配置的服务身份用 `--as app`，宿主已授权的委托身份用 `--as ai_auth`。禁止为了成功而回退身份；显式 `--as auto` 不受支持。需要登录时先查看 `bytedcli auth --help`，按宿主认证流程处理，不自行抓取 cookie 或构造 JWT。

共享机器人中，操作者与消息发送者不一定相同。只有宿主已正确绑定当前调用身份时才能查询；不能使用机器上的个人登录冒充任意群成员。应用 Key 授权的是应用可访问的数据集，不证明发消息的人获准访问这些数据。

## 个人首次使用

先运行 `bytedcli --as user --json bytestable opsdata auth status`。该命令只检查当前用户在平台的开通状态与本地凭证是否存在，不会注册，也不代表 MCP 检索已调通。

用户希望开通/使用个人检索时，执行 `bytedcli --as user --json bytestable opsdata auth login`：复用宿主 SSO，幂等开通个人访问并将凭证写入宿主私有目录。重复登录不会覆盖数据集选择，也不会打印 Key。新设备或当前用户缺少本地凭证时可再次 login；已停用/吊销的凭证不能靠重登恢复。

首次开通复制管理员维护的默认数据集列表，之后以用户自行保存的列表为准。管理员调整默认值不影响已有用户。所有已公开发布的数据集可在平台「接入应用 → 个人访问数据集」中选择。列表为空时说明没有启用的数据集，不要求用户去创建应用 Key。Skill 不应擅自修改用户选择或管理员默认配置。

`--api-key-file` 高于 `OPSDATA_API_KEY`，显式应用 Key 高于个人凭证。login 不清除环境变量；status 的 `effective_mode` 和 hint 会提示环境变量覆盖。共享 Agent 不能通过个人 login 绑定机器主人来代表聊天用户。个人访问当前使用 `--as user`；应用或委托身份仍使用显式应用 Key。

默认个人管理 API 为 CN 平台。其他站点/测试部署需由用户或宿主设置对应的 HTTPS `OPSDATA_API_BASE_URL`；凭证按该地址、站点、服务端确认的用户分别保存。MCP 的 `--env` 不会自动改变管理 API 地址，不得混用不同环境的凭证。

## 两层认证

- TAE 网关使用 bytedcli 提供的 ByteCloud JWT，负责调用身份与 MCP 访问许可。
- 平台使用个人 login 托管的凭证，或显式 `OPSDATA_API_KEY` / `--api-key-file PATH` 的应用 Key，决定应用数据集范围；文件应为私有普通文件（如 600）。两者不能互相替代。
- `tools list` 不要求应用 Key；业务命令要求平台应用授权。工具目录成功不证明业务数据已授权。
- 内置客户端按 PSM/region 自动发现 TAE 网关，不要求手工创建长期 Streamable HTTP URL。不要让用户额外提供此 URL，也不要保存网关临时 URL/token。
- 密钥由用户/宿主注入；禁止把值放进 argv、代码、日志、Skill 或聊天。只检查“是否存在”，不读取整个 `.zshrc`、`env` 或认证配置到输出。用户更新 shell 配置后，当前进程可能仍未继承；由可信的本地 shell 加载或启动新会话，而不是要求用户粘贴密钥。

## 分层排障

| 现象                                            | 处理                                                                         |
| ----------------------------------------------- | ---------------------------------------------------------------------------- |
| 未安装/不识别命令                               | 检查 CLI 安装及子命令 help                                                   |
| 本地输入校验错误                                | 按 hint、命令上限和当前 schema 修正；不要重试原参数                          |
| OPSDATA_NOT_REGISTERED / OPSDATA_LOGIN_REQUIRED | 个人用户运行 auth status 后按需 auth login；应用模式检查注入的 Key，不展示值 |
| 网关 401/403                                    | 检查当前身份、站点与 TAE MCP 权限；不要轮换身份碰运气                        |
| 平台应用/数据集拒绝                             | 确认应用授权范围；由 Owner 处理授权，不能用别人的 Key                        |
| 工具未部署                                      | tools list 核对；报告环境/CLI 差异，不编造备用接口                           |
| grep 范围拒绝                                   | 根据 recommendations 用 list 缩小范围；不当成空结果                          |
| GraphQL 契约错误                                | 刷新 dataset get，按示例/必需参数修正；不盲试标准 GraphQL 语法               |
| 超时/暂时性连接错误                             | 保持身份和范围不变，小范围重试一次；持续失败报告层次与脱敏错误               |
| success 但内容空/部分错误                       | 按记录或知识参考检查业务完整性；不宣称检索得到答案                           |

排障反馈保留错误码、操作、数据集、必要的 log_id，省略 token、Key、HTTP 认证头和含凭证的 URL。app、ai_auth 和海外链路尚未实测，不把参数支持说成端到端验证通过。
