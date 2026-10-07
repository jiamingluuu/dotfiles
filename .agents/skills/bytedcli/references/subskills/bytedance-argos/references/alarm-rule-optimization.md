# 报警规则优化

报警规则优化只通过目标控制面的官方 `argos` Project 发起，不在本 skill 中复制底层 workflow、脚本或模板。

## 输入路由

- 1 个 13–16 位纯数字 `rule_uid`：单规则诊断与优化。
- 2–8 个 `rule_uid`：批量优化；超过 8 个时建议分批，或切换为 PSM 汇总诊断。
- 三段及以上点分名称（如 `example.argos.service`）：PSM 汇总诊断。两段名称只有在用户明确说明是 PSM 时才按 PSM 处理。
- `oc_` 开头的 `open_chat_id`，或用户明确要求分析某飞书群：群维度汇总诊断。
- 输入无法归类时，先询问 `rule_uid`、PSM 或 `open_chat_id`，不要自行搜索并选中同名规则。

```bash
# 单规则
bytedcli --site <site> argos run --project argos \
  --prompt "优化报警规则 <rule_uid>" --timeout-ms 600000

# 批量规则（2–8 条）
bytedcli --site <site> argos run --project argos \
  --prompt "批量优化报警规则 <uid1> <uid2> ..." --timeout-ms 600000

# PSM 或飞书群维度汇总诊断
bytedcli --site <site> argos run --project argos \
  --prompt "汇总诊断 <psm 或 open_chat_id> 的报警规则" --timeout-ms 600000
```

## 能力与安全边界

- “优化、诊断、降低误报、排查不报警、报警风暴、阈值/消抖/发送策略是否合理”属于优化意图。
- 单条和批量优化只生成**待采纳的优化方案**；运行成功不代表生产规则已修改。最终必须原样保留预览链接，并明确告知用户需要在预览页手动采纳后才生效。
- PSM 和飞书群模式只做汇总诊断，不逐条提交优化方案。若用户选定具体规则继续优化，再使用单条或批量模式。
- “把阈值改成 X”“关闭/开启规则”“改级别/通知人/通知方式”等给出明确目标值的请求属于直接配置写入，不得伪装成优化流程；切换到 `bytedance-apm`，使用 `bytedcli apm argos alarm rule update`。默认先以 `--dry-run` 展示 patch，获得明确确认后才可加 `--yes` 写入。
- “创建/新建报警规则”属于规则创建流程，不进入优化流程；切换到 `bytedance-apm`，使用默认预览的 `bytedcli apm argos alarm rule create`，获得明确确认后才可加 `--yes` 写入。

## 控制面

- `--site <site>` 选择 Agent/Project 控制面，必须与目标规则所属控制面一致；不同控制面的 Project 与规则数据彼此独立。
- 国内使用 `cn`；海外通用控制面使用 `i18n-tt`；海外 BD 控制面使用 `i18n-bd`。目标控制面的官方 `argos` Project 必须已提供报警规则优化能力。
- 其他控制面必须先确认当前官方 Project 已提供该能力；缺失时明确说明，不得静默回落到 CN 或其他控制面。
- 单 UID 可由后续流程定位规则数据面，但这不替代 CLI 入口对 Agent/Project 控制面的正确选择。
