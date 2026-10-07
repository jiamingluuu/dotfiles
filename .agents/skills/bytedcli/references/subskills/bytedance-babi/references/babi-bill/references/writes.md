# BABI Bill Insight 写操作安全

## 服务端写白名单

| 命令                                             | 用途                                            |
| ------------------------------------------------ | ----------------------------------------------- |
| `bill insight report upsert`                    | 创建或修改 Insight Report 配置                  |
| `bill insight instance recalculate`             | 指定报告回溯生成实例                            |
| `bill insight instance prepare --confirm-write` | 仅执行候选里的 `report_modify` / `re_calculate` |

其他 Bill 命令只读。归因工单写入属于 [babi-finops 指南](../../babi-finops/GUIDE.md)。

## 执行顺序

1. 先只读查找，取得稳定 `report_id` / `instance_id`。
2. 同时传命令级 `--confirm-write` 和全局 `--dry-run`，预览最终 method、target、headers 和 body；前者只开启写路径，不代表用户授权。
3. 说明将创建或修改的对象与核心字段。
4. 获得授权后去掉 `--dry-run`，保留 `--confirm-write`。
5. 写入后轮询实例，只有 `status=release` 才作为最终证据。

`--confirm-write` 是本地确认，不等于用户授权。不要把 JWT、Cookie、Authorization 或自定义 BaseURL 放进 `--data`。

Insight 报告 owner 必须使用完整邮箱。`instance prepare` 自动解析当前用户时会将
`demo.user` 规范化为 `demo.user@example.com`；直接调用 `report upsert` 时也会规范化
不带域名的 owner。后端返回 `status_code=10201003` 表示至少一个 owner 对目标数据范围
缺少账单读取权限，不是可自动重试的二次确认码。此时命令必须停止，不创建实例，也不能
输出“等待实例 release”；先核对 owner 邮箱和目标账号的 `account_bill_read` 权限。重复
提交相同请求不会绕过该权限校验。
