---
name: bytedance-duty
description: "Use bytedcli Duty for 值班计划/候选组 rosters, 值班人/当前 Oncall, candidate reassignment, and one duty group's rotation period or fixed active range (执行周期/起止时间)."
---

# Duty CLI

平台入口：[Duty 值班平台](https://cloud.bytedance.net/duty)

## When to use

- 按计划名称或 Duty 页面 URL 查询值班计划
- 按创建者、成员、订阅者等多条件搜索值班计划列表
- 查看候选组、当前值班人与计划元数据
- 预览某个候选组的人员替换结果
- 在确认后更新候选组，并读取更新后的状态
- 修改指定组的轮换周期（天）与固定执行起止时间，保留人员和其他组配置

## Quick start

使用 `bytedcli duty`；首次调用会按锁定版本安装 Companion：

```bash
# 预览指定组的周期和固定执行范围；核对后去掉 --dry-run 提交并回读校验
bytedcli duty plan update --name demo-duty --group-index 1 --period-days 1 --start '2026-09-25 00:00:00' --end '2026-10-07 23:59:59' --dry-run

# 查询计划
bytedcli duty plan get --name demo-duty
bytedcli --json duty plan get --url https://example.com/duty/demo-duty/

# 多条件搜索计划（name/creator 精确，keyword/participant 模糊）
bytedcli duty plan search --creator demo-user-a --status all
bytedcli --json duty plan search --keyword payment --page-size 50

# 执行真实修改前，必须先预览候选组变更（--user 会清空备份）
bytedcli duty plan set-users --name demo-duty --group-index 1 --user demo-user-a,demo-user-b --dry-run

# 保留/指定备份时改用 --candidate primary:backup1,backup2
bytedcli duty plan set-users --name demo-duty --group-index 1 --candidate demo-user-a:backup-a,backup-b --dry-run

# 只有在 dry-run 预览确认无误后，才允许去掉 --dry-run 执行真实修改
bytedcli duty plan set-users --name demo-duty --group-index 1 --candidate demo-user-a:backup-a --candidate demo-user-b
```

## Agent guidance

- 使用 `--name` 或 `--url` 定位计划，两者必须且只能选择一个。
- 不确定计划名时用 `plan search` 按 `--creator`/`--keyword`/`--participant`/`--watcher` 等条件筛选；`--name`/`--creator` 精确，`--keyword`/`--participant` 模糊，`--status` 默认仅 active，`all` 含停用。
- 执行 `plan set-users` 的真实修改前，必须先对同一组参数执行一次 `--dry-run` 并确认预览结果；真实更新会执行读取、PATCH 和再次读取。
- `--user` 与 `--candidate` 二选一：`--user` 只设主值班并清空备份；`--candidate primary:backup1,backup2` 会保留指定备份。每个候选人恰好一个主值班，备值班可空或多个；多个主值班请重复传入。
- `--group-index` 从 1 开始，默认 1，修改前根据 `plan get` 核对目标组。
- 更新执行时间用 `plan update --group-index N`，至少提供 `--period-days`、`--start`、`--end` 之一；默认执行；真实修改前先加 `--dry-run` 预览并核对，再去掉该参数提交。它保留主备人员及其顺序（包括重复组合）、其他组、每日时段和跨天设置。
- `--period-days` 是每个候选人员组合连续值班的正整数天数。固定范围可只改一端，非固定范围必须同时提供两端以转换为固定范围。日期格式为 `YYYY-MM-DD HH:mm:ss`，按 Duty 本地时间原样提交，不自动转换时区。
- 生效起止范围不等于轮换起算基准；逐日对齐必须确认实际起算日，不能默认生效首日对应候选组 1。
- 不要请求、输出或记录 Duty 后端 token；CLI 会从有权限的计划访问结果中处理它。
- 认证状态按 Binary/Host 隔离；`bytedcli duty` 由宿主注入 JWT，统一 Binary 基于该 JWT 获取 userinfo，其他入口使用各自 Binary 的登录态。
- 稳定消费结果时使用 `--json`，并把全局参数放在 domain/command 前面。

## References

- [duty.md](./references/duty.md)
- [invocation.md](./../../invocation.md)
- [troubleshooting.md](./../../troubleshooting.md)
