# FinOps 写操作安全

## 服务端写白名单

| 命令                                | 用途                                      |
| ----------------------------------- | ----------------------------------------- |
| `finops attribution ticket create` | 创建归因工单并绑定 Insight                |
| `finops attribution ticket update` | 回填结论、HTML、责任人、Oncall 或解决状态 |

`finops attribution report render` 写本地固定 Markdown 和 HTML，默认拒绝覆盖已有文件；只有用户确认才使用 `--force`。Insight Report/实例写入属于 [babi-bill 指南](../../babi-bill/GUIDE.md) 的独立白名单，需要另行读取其规则并授权。

## 执行顺序

1. 先只读取得稳定 `report_id`、`instance_id`、`ticket_id`；更新前读取当前工单。
2. 同时传命令级 `--confirm-write` 和全局 `--dry-run`，预览最终 method、target、headers 和 body；前者只开启写路径，不代表用户授权。
3. 说明将创建或修改的对象与核心字段。
4. 获得用户授权后去掉 `--dry-run`，保留 `--confirm-write`。
5. 更新时把 `--insights` 视为全量覆盖字段，保留当前工单已有的全部关联。
6. 更新后重新读取同一工单确认写入结果；`--is-resolved 1` 单独确认，不因归因完成自动关闭。
7. 成本归因回填必须使用同一次 renderer 生成的 `conclusion.md` 和 `report.html`，最终回复使用同次生成的 `final-reply.md`；禁止修改任一产物或用模型另写结论，记录并核对 `input_sha256`、`reply_sha256` 和 `conclusion_sha256`。

`--confirm-write` 是命令本地确认，不代表用户授权。不要把 JWT、Cookie、Authorization 或自定义 BaseURL 放进 `--data`。BOE 路由 headers 由命令元数据注入。
