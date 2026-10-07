# 正式计量版本查询与切换

本指南用于计量 VersionID，不用于商品价格版本、CLI 软件版本或推量上报。
先应用 bytedcli 宿主安装与认证规则，再检查 `bytedcli babi raw-measure version --help`。
如当前已发布版本没有命令，应明确能力未发布，不手写 HTTP 绕过。

## 输入与范围

- 收集稳定商品 ID（推荐）或商品编码，二选一；商品名称先通过商品领域解析并消歧。
- 收集单日/完整自然月账期及 normal（正式用量）或 estimated（预估用量）。
- begin/end 为北京时间零点，end 是下一日/下月一日；不是月末最后一秒。
- 只支持正式版本 Env=0。Env 与 CLI 站点/部署环境不是同一概念；不支持草稿版本切换。
- 所有请求使用相同商品、账期、计量类型和路由，不扩大查询或切换范围。

## 环境与路由

当前 bytedcli 宿主仅支持本指南的国内线上 / CN 路由。环境必须来自用户当前请求或已明确的会话范围；无法确定时先询问，不自行选择线上。
每次 overview、ack 预检、确认切换及独立复查都使用 `bytedcli --site cn babi ...`，将站点参数放在 `babi` 前，同一流程保持相同站点。

BOE、PRE、海外或自定义业务地址需求当前不受 hosted 模式支持，应停止并说明路由限制；不要改成 CN 执行，也不要手写 HTTP 或请求头绕过。
宿主禁用 `--base-url` 并隔离 standalone 配置；不修改全局配置，不读取或转发 JWT。路由错误不能解释为版本列表为空。

例如查询已明确为 CN 的日账期：

```bash
bytedcli --site cn babi raw-measure version overview \
  --product-id 123 --begin 2026-09-19 --end 2026-09-20 --measure-type normal
```
## 操作顺序

以下命令均须在 `babi` 前添加 `--site cn`；只用于上节已明确的 CN 范围。

1. `bytedcli babi raw-measure version overview --product-id <id> --begin <YYYY-MM-DD> --end <YYYY-MM-DD> --measure-type normal`。
2. 展示 active_version_id、available_versions 的 version_id/count/active/configured。
   空字符串显示“默认空版本”；Configured 不代表可用数据完整。
3. 用户选择目标后，执行 `... version ack <相同范围> --version-id <目标>`。
   这次只有 overview → count，返回 confirmation_required，尚未切换。
4. 向用户展示范围、旧版本、目标和最新 ES 条数。用户对具体操作确认后，
   重新执行同一命令，增加 `--confirm-write --expected-active-version <预检旧版本> --expected-count <预检条数>`。
   预检旧版本为空时显式传 `--expected-active-version ''`。
5. CLI 内部重跑 overview → count，条件一致才 ack → overview。
   CLI 不读取终端交互输入；变化时停止，重新展示并取得确认，不自动修改预期条件重试。

向用户解释方案时，先明确“仅支持正式版本 Env=0，不支持草稿 Env=1”。
必须说明未确认的 ack 内部执行 overview → count，
确认后的 ack 内部执行 overview → count → ack → overview；最后一次 overview 是成功依据。
count 是内置接口步骤，没有独立的 CLI count 子命令，不要虚构独立调用。

目标已生效时输出 already_active，不提交。非空目标本次未发现时停止；候选最多 1000 个，
不能断言目标绝对不存在。count 是 ES 记录数，不证明推量完整、MySQL 一致或账单重算完成。

## 默认空版本与零条数

回退默认空版本必须用 `--default-version`，不能省略目标，也不要传展示文案当版本 ID。
零条数默认阻止；只有用户明确确认零数据切换，才增加 `--allow-zero-count`，仍需完整确认。
默认空版本 overview/count 不一致时停止，核对历史缺失 VersionID 字段的计数口径；
allow-zero-count 不能跳过差异检查。

## 输出与失败

- confirmation_required：已复核，未提交。
- already_active：已经生效，无需切换。
- switched：ack 成功且复查一致，才表述“切换成功”。
- unconfirmed：提交/复查结果未确认，不能说成功，也不能断言后端未写入。
  不自动重试 ack，不自动回滚；仅可再次 overview。
- 签名/权限拒绝：检查 BABI AK/SK 身份和商品 ReportMeasure 权限；用户 JWT 登录不是同一检查。
- 账期/封账失败：按后端错误说明停止，不能用强制参数绕过。
- `--dry-run` 是零业务请求的静态计划；它不证明路由、权限或当前版本状态。

CLI 的 expected-active-version 只是写前预检条件，不是后端事务中的并发条件锁。
结果仅代表复查时观察到的生效版本。只有用户请求且另有数据证据时才延伸到计费链路。
