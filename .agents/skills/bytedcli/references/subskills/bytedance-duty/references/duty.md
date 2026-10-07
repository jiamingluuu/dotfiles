# Duty 命令参考

以下示例统一使用 `bytedcli duty`；全局参数放在 Domain 前面。

## 查询计划

```bash
bytedcli duty plan get --name demo-duty
bytedcli --json duty plan get --url https://example.com/duty/demo-duty/
```

- `--name` 与 `--url` 必须且只能选择一个。
- 返回计划基本信息、候选组和当前值班状态。
- URL selector 从 `/duty/<name>/` 中提取计划名称。
- 不确定目标组时，先查询并核对候选组的 1-based 序号。

## 按条件搜索计划

`plan search` 支持多条件筛选值班计划列表，适合不知道确切计划名、或需要按创建者/成员批量排查时使用：

```bash
# 按创建者精确筛选，并包含已停用计划
bytedcli duty plan search --creator zhangsan --status all

# 名称/显示名/描述模糊搜索，分页并输出 JSON
bytedcli --json duty plan search --keyword payment --page-size 50 --page 1

# 按候选人成员 + 订阅者筛选
bytedcli duty plan search --participant lisi --watcher team-a --watcher-type duty
```

- `--name`、`--creator` 为精确匹配；`--keyword`、`--participant` 为模糊匹配。
- `--keyword` 同时匹配计划名、显示名和描述。
- `--participant` 匹配候选组花名册中的成员（主值班或备值班）。
- `--watcher` 为订阅者筛选，配合 `--watcher-type`（`duty` 或 `person`，默认 `duty`）。
- `--status` 取值 `active`（默认，仅启用）、`disabled`（仅停用）或 `all`（全部）。
- `--page-size` 为每页数量（默认 20，上限 100，超过 100 按 100 传参），`--page` 为 1-based 页码（默认 1）。
- 默认表格输出关键列（NAME/DISPLAY/CREATOR/STATUS/ONCALL）；需要完整字段和分页元数据时加 `--json`。

## 预览候选组变更

执行真实修改前，必须先对目标计划、目标组和最终用户集合执行一次 `--dry-run`，确认预览结果无误后才能去掉 `--dry-run`。

```bash
# 只设主值班，备份会被清空
bytedcli duty plan set-users \
  --name demo-duty \
  --group-index 1 \
  --user zhangsan,lisi \
  --dry-run

# 设主值班并保留/指定备份
# zhangsan 主，备 lisi、wangwu；wangwu 主，无备
bytedcli duty plan set-users \
  --name demo-duty \
  --group-index 1 \
  --candidate zhangsan:lisi,wangwu \
  --candidate wangwu \
  --dry-run
```

- `--group-index` 从 1 开始，必须指向现有候选组。
- `--user` 与 `--candidate` 二选一，不能同时使用；至少提供一个。
- `--user` 可重复传入，也支持逗号分隔，会把每个主值班的备份清空。
- `--candidate` 形如 `primary` 或 `primary:backup1,backup2`，可重复；冒号后的备份会被保留。省略冒号时备份为空。
- 每个候选人恰好一个主值班；备值班可以为空或多个。多个主值班请重复传入 `--user`/`--candidate`，不要在单个 `--candidate` 的主值班段写多人。
- dry-run 读取当前计划并返回 before/after，不发送 PATCH。
- 执行真实修改前，必须先保留并核对这次 dry-run 返回的 before/after 预览。

## 执行候选组变更

只有在同一组参数的 dry-run 预览已经确认无误后，才允许移除 `--dry-run`：

```bash
# 组内设置两个候选人：
# 候选人 1 主 zhangsan、备 lisi；候选人 2 主 wangwu、备 zhaoliu
bytedcli duty plan set-users \
  --name demo-duty \
  --group-index 1 \
  --candidate zhangsan:lisi \
  --candidate wangwu:zhaoliu
```

真实更新执行三个阶段：

1. 读取当前计划和编辑访问数据。
2. PATCH 指定候选组，其余组保持不变。
3. 再次读取计划，返回更新后的状态。

需要稳定审计结果时使用 JSON：

```bash
bytedcli --json duty plan set-users --name demo-duty --group-index 1 --candidate zhangsan:lisi --dry-run
```

## 安全边界

- 不要在命令参数、日志、错误或结果中暴露 Duty 后端 token。
- 不要为了获得编辑 token 请求用户复制浏览器请求头。
- 没有编辑权限时停止并返回结构化错误，不要尝试绕过权限。
- 执行真实修改前必须保留 dry-run 结果，并明确核对计划名称、组序号和最终用户集合。


## 更新指定组的周期与执行起止范围

```bash
# 显式加 --dry-run 预览
bytedcli duty plan update --name demo-duty --group-index 1 --period-days 1 --dry-run
# 同时设置固定执行范围；核对同一组参数的预览后，去掉 --dry-run 提交
bytedcli duty plan update --name demo-duty --group-index 1 --period-days 1 --start '2026-09-25 00:00:00' --end '2026-10-07 23:59:59'
# 已是固定范围时，可只修改一端，保留另一端及周期
bytedcli duty plan update --name demo-duty --group-index 1 --end '2026-10-08 23:59:59'
```

- `--group-index` 默认 1，指现有值班组的一基序号；`--name` / `--url` 二选一。
- 至少提供 `--period-days`、`--start`、`--end` 之一。周期为每个候选人员组合连续执行的正整数天数，1 表示每日轮换，不是完整一轮天数。
- 起止时间必须为有效的 `YYYY-MM-DD HH:mm:ss`，按 Duty 本地时间提交，不做时区转换；结束时间包含在范围内。开始不得晚于结束。已有固定范围可只改一端；非固定类型必须同时给两端，转换为 `fixed`。
- 默认真实提交；显式 `--dry-run` 只预览，不发送 PATCH。执行真实修改前，先对相同参数运行 `--dry-run` 并核对结果。JSON 返回 `dry_run`、`applied`、`verified`、`unchanged` 和完整组摘要 `before` / `after`。文本显示目标组的变更前后配置。无变化时不发 PATCH，返回 `unchanged=true`。
- 保留候选人员、重复组合及其顺序、其他组、每日时段和跨天标志。更新生效范围不会重设轮换起算基准，也不会自动重排候选人员。
- 提交前再次读取组配置；发现并发修改报 `DUTY_CONCURRENT_UPDATE`，重新预览。此检查不等同于后端原子版本锁，避免同时编辑同一计划。
- 提交后验证各组的业务字段（忽略服务端重新生成的 ID）。`DUTY_READBACK_FAILED` / `DUTY_READBACK_MISMATCH` 表示不能确认变更完成；先用相同 selector 运行 `plan get` 检查实际状态，不盲目重试写入。
