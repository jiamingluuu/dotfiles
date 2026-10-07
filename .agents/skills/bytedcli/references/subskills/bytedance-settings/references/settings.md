# Settings

```bash
bytedcli settings item get --item-id "123456"
bytedcli settings item list --id "<space-id>" --page 1 --page-size 50
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"type\":\"integer\"}" --reviewers-json "[]"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "1"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "abc"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --schema "{\"s\":\"abc\"}"
bytedcli settings item create --id 1001 --item-name "sample_item" --brief "sample brief" --scheme "{}"
bytedcli settings draft save --item-id "123456" --code "return true" --draft-type 1 --next-step 1
bytedcli settings review list --item-id "123456"
bytedcli settings deploy list --item-id 123456 --page 1 --page-size 10
bytedcli settings whitelist add --item-id "123" --title "demo" --whitelist "u1"
bytedcli settings whitelist list --item-id "123" --page-size 10 --page 1 --status 0 --type 0 --keyword ""
bytedcli settings whitelist biz-get --whitelist-id 1001
bytedcli settings ut list --item-id 123456 --ut-status 0
bytedcli settings var list-item --item-id 123456
bytedcli --site cn --json settings biz search --keyword "sample-sdk-settings" --type sdk
bytedcli --site cn --json settings item search --id "<space-id>" --query "sample-config"
bytedcli settings biz search-id --appid "1001"
```

`settings biz search` 返回候选集合。通过 `.data.spaces` 读取结果，确认空间后再把 ID 传给
`settings item search`。该命令当前仅支持 CN；示例显式使用全局选项 `--site cn` 以锁定站点。
`--type` 只过滤上游本次返回的候选；空间名称不保证唯一，结果也不保证完整。SDK 搜索无结果时
不会回退到 AppID。

`settings item list` 的 `pagination.total` 可能包含已逻辑删除的历史配置，`data` 只返回当前
可见配置。枚举时仍按 `total / page_size` 翻完所有页，不能因某页少于 `page_size` 提前停止；
实际可见数量以各页 `data` 按 `item_id` 聚合去重后的结果为准。
