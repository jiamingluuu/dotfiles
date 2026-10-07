# Oncall 排障

本文仅记录 Oncall 组件特有问题。安装、认证、JWT、站点/地域路由、网络和通用输出问题返回 `bytedcli`。

## 定位顺序

1. 用 `bytedcli oncall --help` 确认组件命令。
2. 用 `bytedcli oncall "<command>" --help` 确认当前版本的参数。
3. 命令缺失或参数与实际行为不一致时，重新检查 `bytedcli oncall --help` 和叶子命令帮助。
4. 如果帮助中没有对应能力，明确说明当前 CLI 不支持；不要猜测或调用未暴露的底层接口。

## 错误速查

| 现象 | 原因 | 处理 |
|---|---|---|
| `at least one flow filter is required` | `flow list` 只有分页/排序，没有业务筛选 | 传 `--tenant-id`、`--mine`、`--assigned-to-me` 或其他筛选条件 |
| `tenant_id or --mine is required` | `flow search` 没有限定租户或当前用户 | 传 `--tenant-id` 搜指定租户，或传 `--mine` 只搜当前用户的历史工单 |
| `time_range must match <number><unit>` | `--range` 不是正整数加小写 `d/h` | 改用 `5d`、`7d`、`2h` 等格式 |
| `time_range cannot be used...` | 相对时间与绝对时间同时使用 | 在 `--range` 与 `--created-after/--created-before` 中二选一 |
| 布尔参数解析失败 | 值不是 `true/false/1/0` | 使用 `--solved=false`、`--union-duty=true` |
| ID 解析失败 | ID 不是正整数 | 检查工单、租户或问题分类 ID |
| `region ... is not available` | 区域不属于该租户 | 先用 `question-type list --regions-only` 查可用区域 |
| 缺少 `oncall_flow_id` | 群聊、问答记录和总结依赖工单 ID | 先用 `flow list` 定位，候选不唯一时请用户确认 |
| `--sort-order` 单独使用 | 缺少排序字段 | 同时传 `--sort-by` |
| 安装后没有新命令/新参数 | 主 CLI 中的组件版本过旧 | 用本仓库开发入口确认，或更新主 CLI 组件 |

## 特殊行为

- `flow list --stage launch_oncall` 表示人工 Oncall 阶段；不存在通用的 `processing` 阶段映射。
- `tenant search --managed-only` 包含没有问题分类的管理租户，但平台超级租户仍由服务端过滤。
- 关单失败时，保留 `flow close` 返回的创建人、已关联群聊或已解决等原因；不得绕过校验。
