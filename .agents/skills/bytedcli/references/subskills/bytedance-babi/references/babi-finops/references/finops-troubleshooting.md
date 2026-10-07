# FinOps 业务排障

通用安装、认证、JWT、网络和更新问题先按入口 SKILL 指定的公共/产品 skill 处理。这里只记录 FinOps 业务定位顺序。

## 定位顺序

1. `bytedcli babi <command-path> --help` 确认 flags、枚举和必填项。
2. 加全局 `--dry-run` 检查 method、target、headers 和 body。
3. 仍不清楚时加 `--debug`；诊断写入 stderr，不改变业务 stdout。
4. 区分本地校验、认证/权限、路由/header、后端业务错误和正常空数据。
5. 原样保留 `logId` / `RequestId`；未返回时明确说明。

## 常见问题

| 现象 | 常见原因 | 处理 |
|---|---|---|
| 团队候选不唯一 | 名称命中多个团队 | 展示 ID、名称和路径，等待选择 |
| CostDriver filter 失败 | `Filters[].Key` 使用了错误大小写 | 改为后端 snake_case；顶层字段不要随意改名 |
| 容量日期失败 | capacity 要求 `yyyy-MM-dd` | 不要传 Bill 毫秒时间戳 |
| 容量主体失败 | PSM、服务树、业务域未传或传了多种 | 三者必须且只能选一种 |
| 趋势天数失败 | `days` 不在 1-30 | 调整窗口，PSM 同时不超过 30 个 |
| 排序失败 | 字段与方向未成组 | suggestion 同时传 sort field/order；capacity 补资源类型 |
| 成功但空数据 | 对象、时间、区域、权限或分页不匹配 | 复核 dry-run，再报告空数据与 RequestId |

`--data` 必须是完整 JSON object。不要把 JWT、Cookie、Authorization 或内部 header 放进请求体、日志或回复。
