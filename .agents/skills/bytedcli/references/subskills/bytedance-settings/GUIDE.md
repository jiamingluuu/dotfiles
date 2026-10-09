---
name: bytedance-settings
description: Operate ByteDance Settings with bytedcli across item, draft, review, deploy, whitelist, UT, var, and biz workflows. Use for Settings configuration management, space discovery, or keyword-to-space-ID lookup.
---

# Settings (bytedcli)

## 如何调用 bytedcli

推荐：先全局安装一次，后续所有命令直接调用 `bytedcli`。

```bash
# 推荐方式：先全局安装，后续直接调用 bytedcli
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npm install -g @bytedance-dev/bytedcli@latest
bytedcli <command> [options]
```

```bash
# Fallback：仅在无法全局安装时使用 npx 临时执行
NPM_CONFIG_REGISTRY=http://bnpm.byted.org npx -y @bytedance-dev/bytedcli@latest <command> [options]
```

## When to use

- 需要执行 Settings 全流程能力（配置、草稿、审核、发布、白名单、UT、变量、biz）
- 需要通过 `--from` / `--query-json` / `--body-json` 透传请求体或筛选条件
- 需要批量维护 `app_settings` 客户端配置流程

## 前置条件

- 按通用调用方式执行命令（含内网 registry）：`../../invocation.md`
- 需要鉴权的命令先登录：`bytedcli auth login`

## 功能分组命令

> 说明：请求体/查询参数可通过 `--from`、`--query-json`、`--body-json` 原样透传；请按命令参数与 payload 字段约定构造 JSON。

```bash
# item / draft
bytedcli settings item get --item-id "123456"
bytedcli settings item list --id "<space-id>" --page 1 --page-size 50
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"type\":\"integer\"}" --reviewers-json "[]"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "1"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "abc"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"s\":\"abc\"}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --scheme "{}"
bytedcli settings draft save --item-id "123456" --code "return true" --draft-type 1 --next-step 1

# review / deploy
bytedcli settings review list --item-id "123456"
bytedcli settings deploy list --item-id 123456 --page 1 --page-size 10

# whitelist
bytedcli settings whitelist add --item-id "123" --title "demo" --whitelist "u1" --whitelist "u2"
bytedcli settings whitelist list --item-id "123" --page-size 10 --page 1 --status 0 --type 0 --keyword ""
bytedcli settings whitelist biz-get --whitelist-id 1001

# ut / var / biz
bytedcli settings ut list --item-id 123456 --ut-status 0
bytedcli settings var list-item --item-id 123456
bytedcli --site cn --json settings biz search --keyword "sample-sdk-settings" --type sdk
bytedcli --site cn --json settings item search --id "<space-id>" --query "sample-config"
bytedcli settings biz search-id --appid "1001"
```

## Notes

- 需要结构化输出加 `--json`（全局选项，放在子命令之前，如 `bytedcli --json settings review list --item-id "123"`）
- `settings biz search` 返回候选集合；从 `.data.spaces` 读取结果，确认空间后再把 ID 传给 `settings item search`
- `settings biz search` 当前仅支持 CN；示例显式使用全局选项 `--site cn` 以锁定站点
- `--type` 只过滤上游本次返回的候选；空间名称不保证唯一，候选集合也不保证完整
- SDK 搜索无结果时不会回退到 AppID
- `settings item list` 的 `pagination.total` 可能包含已逻辑删除配置；按 `total` 翻完所有页，实际可见数以各页 `data` 按 `item_id` 聚合去重后为准
- 大多数 `settings` 子命令支持 `--from <path>` / `--query-json` / `--body-json` 组合透传
- `settings item create --schema/--scheme` 支持 schema JSON 或示例值自动推断类型（`1 -> integer`，`abc -> string`，`{} -> 宽松 object`，`{"s":"abc"} -> 严格 object schema`）
- `settings item apply` 作为兼容别名保留，推荐使用 `settings item create`
- 分页命令优先使用 `--page`（1-based）；`--page-no` 仅兼容旧用法

- `settings review create`、`settings whitelist add/save` 未指定 `--support-harmony-os` 时读取并保留现有鸿蒙开关：review 和新增白名单取配置 `latest_info.extra`，保存白名单取其 `whitelist_info.extra`。读取失败或缺少布尔值时停止提交，可用 `--support-harmony-os true|false` 显式指定。
- review 的 JSON 输入和 whitelist add 的 `--from` 支持 `support_harmony_os` 或 `extra.support_harmony_os`；显式 CLI 参数优先，顶层字段优先于 extra，最终请求中的两处值保持一致。
- whitelist add 会检查创建结果的鸿蒙开关；值不一致时，按新记录的内容和状态补充保存，再回读确认，成功输出最终详情。后续保存或回读失败会返回 `SETTINGS_WHITELIST_PARTIAL_WRITE` 和已创建的 `whitelist_id`；先用 whitelist get 核对，再保存该记录，避免重复执行 add。补充保存沿用后端代码校验，代码需要有有效返回值。

## References

- `references/settings.md`
- `../../invocation.md`
- `references/review-create.sample.json`
- `references/review-create-open.sample.json`
