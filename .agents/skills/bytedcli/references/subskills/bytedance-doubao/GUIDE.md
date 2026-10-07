---
name: bytedance-doubao
description: "Use bytedcli doubao for experimental local Doubao desktop status, personal/work edition and login checks, rendered conversations/messages, and confirmed text sends using the desktop user's identity."
---

# bytedance-doubao

控制本机已经开启 CDP 的豆包桌面端。不是豆包模型 API，也不是企业 SSO；不调用未公开的发送 HTTP 接口。

## 先检查身份

```bash
bytedcli --json doubao status --cdp-port 19222
bytedcli --json doubao conversation list --cdp-port 19222 --page 1 --page-size 20
bytedcli --json doubao message list --cdp-port 19222 --page 1 --page-size 20
```

`edition` 表示当前页面是 `personal`、`work` 或 `unknown`，不是根据账号猜测套餐。未登录页面显示个人版，不代表登录后不会进入豆包工作。

| 账号状态 | 行为 |
| --- | --- |
| `logged_in` | 页面内账号探活成功、非游客身份且与当前 Profile 的用户标识一致；允许继续检查发送条件 |
| `logged_out` | 不发送，提示在当前豆包 Profile 手动登录；不以匿名发送代替用户身份 |
| `unknown` | 不发送，提示完成登录/切换、检查页面后重新探活；不会简单认定为未登录 |

个人版的普通对话和豆包工作的电脑任务不是同一种操作。电脑任务必须显式添加 `--allow-work-task`；本地电脑接受“始终询问”和“按需确认”，拒绝“全部允许”和未知权限模式。此命令不批准权限弹窗，也不改变权限、模型、思考强度、项目、技能或连接器。

## 最小发送路径

先在豆包中打开目标会话；新消息使用已经打开的空白新会话。`--new` 只是断言页面为空，不会自动创建、导航或覆盖草稿。

```bash
# 个人版普通对话：默认只预览，不发送
bytedcli --json doubao message send --cdp-port 19222 --new --text "请回复测试成功"
# 豆包工作：先明确接受当前电脑任务上下文，再预览
bytedcli --json doubao message send --cdp-port 19222 --new --allow-work-task --text-file ./message.txt
# 人工核对预览的账号、页面、目标、消息原文、模式、模型和可见选项后，复用完全相同的参数
bytedcli --json doubao message send --cdp-port 19222 --new --allow-work-task --text-file ./message.txt --yes --confirm <confirm>
# 已有会话：ID 必须与当前打开的会话相同
bytedcli --json doubao message send --cdp-port 19222 --conversation-id <conversation-id> --text-file ./message.txt
```

- `--text` 与 `--text-file` 必须二选一，UTF-8 文本最多 32 KiB；私密内容优先使用文件，避免写入 shell 历史和进程参数。
- `--yes` 与匹配的 `--confirm` 才能提交；`--dry-run` 始终优先于 `--yes`。
- 多个聊天窗口同时存在时，按错误里的候选指定 `--target-id`，不会任意选中第一个。
- 默认有草稿时拒绝发送；只有用户明确选择的 `--resume-draft` 路径可提交完全匹配的保留草稿。附件、流式生成或弹窗仍拒绝发送；不替用户清空内容。
- 使用发送按钮，不依赖 Enter 快捷键，因此不会改变换行/发送设置。
- `--wait-ms` 单位毫秒，默认 60000，范围 0–300000；0 只短暂等待用户消息回显。
- `completed` 表示通过本次点击关联的用户消息 ID，观察到回复正文、结束标记和消息操作栏，并连续两次稳定；`submitted` 只确认页面已回显用户消息，不是服务端幂等或持久化承诺。
- 发送结果始终包含 `conversationId`、`userMessageId`、`reply`、`hint`，尚无值时为 `null`。等待回复期间出现另一条用户消息会停止本次回复关联并提示对账，不把后一轮回复作为本次完成结果；`--wait-ms 0` 仍只确认本次消息回显。
- 无法确认提交时，CLI 返回 `DOUBAO_SEND_UNCERTAIN` 和非零退出码，不包装成成功，也不能当作失败后重发。错误 `details` 固定包含 `state`、兼容别名 `observedState`、`conversationId`、`userMessageId`、`targetId`、`confirm`、`reason`；缺失标识和原因使用 `null`。文本模式的错误提示也展示已知状态和会话/消息/目标 ID，不需要重跑发送来获取 JSON。回显后断线时保留已知会话/消息 ID 供对账；超时提示区分“提交尚未确认”和“已回显但最终回复尚未确认”。
- 超时、断线或页面变化后先用 `message list` 对账。确认令牌由状态摘要和独立操作标识组成、单次使用；确认完成后，新的人工预览可以再次发送相同文本。不要在不确定结果后自动获取新令牌重试。
- 预览会在本地记录令牌签发信息；提交必须使用同一本地 bytedcli 数据目录签发的完整原令牌，修改随机部分不能产生新授权。`--profile` 不隔离这些本机签发/尝试记录和端口锁，也不切换豆包账号。落盘记录只含预览/尝试状态和时间，不含消息或 Cookie，目前不会自动过期或清理；不要单独删除尝试记录来复用令牌。锁清理失败不覆盖原发送结果；残留锁必须先人工核对再清理。
- 发送期间不要点击、输入或滚动豆包窗口；检测到人工干预时停止。页面上下文切换会使执行绑定失效，避免把文本输入到另一页面。
- 发送准备完成后，允许最旧的已渲染历史移出页面，但剩余项必须是原列表的非空后缀并保留最新消息 ID；新消息、重排、中间/末尾丢失或全部历史消失仍停止发送。预览到确认之间的状态变化仍要求重新核对。
- MCP 支持读取和预览，不允许真实发送。不要借助其他执行入口绕过这个限制。

## 显式提交保留草稿

这不是自动重试。先用 `message list` 对账；只有用户明确要求提交这份保留草稿、操作者已经核对目标和历史后，才能选择此路径。未知发送结果不能被当作“发送失败”，也不能自动追加本参数换令牌重发。

```bash
# 先读取当前会话并确认没有重复提交
bytedcli --json doubao message list --cdp-port 19222 --page 1 --page-size 20
# draft.txt 必须与当前草稿逐字一致，包括空白；只预览，不输入或清空
bytedcli --json doubao message send --cdp-port 19222 --conversation-id <conversation-id> --resume-draft --text-file ./draft.txt
# 核对预览里的 resumeDraft、账号、会话、原文和选项，再复用全部参数单次确认
bytedcli --json doubao message send --cdp-port 19222 --conversation-id <conversation-id> --resume-draft --text-file ./draft.txt --yes --confirm <confirm>
```

- 仅支持已有会话，必须使用 `--conversation-id`，不能与 `--new` 组合。豆包工作仍需添加 `--allow-work-task`，权限要求不变。
- `plan.resumeDraft` 明确标识操作模式，并参与确认摘要；普通发送令牌不能用于续发，续发令牌也不能改成普通发送。确认摘要还绑定历史消息 ID/角色、最近用户消息原文及最新回复完成状态，不在预览中暴露历史正文。旧的已消耗令牌和回执保持不变。
- 预览及提交都验证非空草稿与传入文本完全一致。提交只聚焦、复核并点击发送按钮，不重新输入、不编辑、不清空草稿；聚焦前后及点击前均再次检查。
- 必须能读取最近用户消息，历史中不能有未知角色，并且最新回复已明确完成。账号探活后、聚焦后及点击前都会重新读取并核对这些历史证据；准备完成后若最旧历史移出页面，最近用户消息和最新回复仍必须保留。若最近用户消息与草稿疑似相同，则拒绝续发；这项保守的重复检测忽略排版空白，但草稿原文校验不会忽略空白。
- 上述检查仅基于已渲染历史，不是服务端去重或“前次必未送达”的证明。续发仍可能返回 `DOUBAO_SEND_UNCERTAIN`；此时再次只读对账，不自动重试。

## 本机连接与登录

CLI 不自动启动、关闭或重启豆包，不读取/复制浏览器凭据，也不自动登录或退出。

macOS 已验证的启动参数如下。先人工确认原实例已退出并保留工作状态；使用独立、持久的自动化 Profile，不要把日常主 Profile 暴露给调试端口。

首次配置时，在 bytedcli 默认数据目录下创建 `doubao/desktop-profile`。这是为本集成新建的豆包桌面 Profile，不是豆包原有目录；登录态和桌面数据由豆包保存在此，不要当作可随时删除的缓存。

```bash
mkdir -p "$HOME/.local/share/bytedcli/data/doubao/desktop-profile" &&
chmod 700 "$HOME/.local/share/bytedcli/data/doubao/desktop-profile" &&
open -a Doubao --args --remote-debugging-address=127.0.0.1 --remote-debugging-port=19222 --user-data-dir="$HOME/.local/share/bytedcli/data/doubao/desktop-profile"
```

已有独立 Profile 时，继续使用原来的 `--user-data-dir` 路径，不自动迁移、复制凭据或重建。改用新目录意味着使用另一个 Profile，需要重新手动登录。此桌面目录不跟随 bytedcli 的 `--profile` 切换，也不替代 CLI 的发送确认记录与端口锁。

然后在豆包窗口完成扫码/验证码及必要的用户协议确认，再运行 `doubao status`。验证码、密码和账号切换由用户处理。`bytedcli auth login`、`--profile`、`--as` 和 `--site` 均不会切换豆包账号或个人/工作页面。

CDP 端口不是有鉴权的 API。只监听回环地址，不暴露到局域网、不转发；完成后人工关闭调试实例。CLI 只接受端口，不接受任意远程地址。HTTP 发现和 WebSocket 都不走代理或跟随重定向。

## 错误恢复

遇到连接失败、未登录、接口变化、状态不明时，读取 `references/desktop-recovery.md`；不要套用企业 SSO、生产网或代理登录指引。

## 范围与限制

- 仅支持经过识别的桌面聊天页面，不适用于普通浏览器网页、Dola 或任意 Electron 应用。
- 列表只覆盖当前已渲染的侧栏/消息，明确返回 `completeHistory: false`，不是全部历史记录。`--page` / `--page-size` 只分页这份渲染快照；消息第 1 页是最新消息、页内按时间正序。`rendered_count` 不是服务端历史总数，`truncated` 表示当前页未包含全部渲染项。
- 登录成功不代表订阅、模型、组织权限或配额足够。服务端拒绝、验证码和任务权限确认仍需在豆包中处理；CLI 不绕过。
- 可见控件摘要不是全部隐藏配置的枚举。不要在发送过程中手动切换账号、项目、连接器或模型；CLI 不承诺服务端/其他设备配置的原子锁定。
- 不支持附件、语音、导出、删除、重试生成、权限审批或自动切换模型。当前是实验性桌面 UI 合同，页面升级无法识别时应停止，不降级盲发。

## Markdown 多行换行（必读）

```bash
# 正确：真实换行；私密或长内容更适合 --text-file
bytedcli doubao message send --cdp-port 19222 --new --text $'第一行\n第二行'
# 不要使用 --text "第一行\n第二行"：bash/zsh 会把它当作反斜杠和 n
```
