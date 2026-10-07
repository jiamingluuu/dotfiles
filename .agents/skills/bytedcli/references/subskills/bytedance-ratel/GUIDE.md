---
name: bytedance-ratel
description: "Operate Ratel iOS settings, Live SDK version calendar, and general-service checks via bytedcli. Use when tasks mention Ratel, ratel, iOS setting, setting changes, Live SDK latest version, calendar version, general-service, general service, or checking whether a service is a general service. This skill covers iOS setting create, setting-change search, Live SDK version get, and general-service list/get; it explicitly does not cover Android operations or iOS package operations."
---

# Ratel (bytedcli)

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

- 创建 Ratel iOS setting
- 查询 Ratel setting 变更记录
- 查询 Ratel iOS calendar 的当前最新直播 SDK 版本，以及宿主版本映射
- 按 SDK 版本列出 iOS general service
- 判断指定 service 在某 SDK 版本下是否属于 general service

## 前置条件

- 通用调用方式见 `../../invocation.md`
- 创建 setting 是写操作；执行前先向用户确认 setting key、类型、默认值、影响版本、作者信息
- `setting create` 当前只覆盖最简稳定 Setting：description 与 module_name 为空、pms 为空、stable=true、type=0；不要向用户承诺可传这些固定字段
- Android 操作与 `ratel ios package` 当前不由 bytedcli Ratel 覆盖

## 常用命令

```bash
# 创建 iOS setting
bytedcli ratel ios setting create \
  --setting-key sample_feature_enabled \
  --name "Sample Feature Enabled" \
  --effect-version 4.1.7 \
  --value-type bool \
  --default-value false \
  --author sample.user \
  --author-nick-name "Sample User"

# 查询 setting 变更记录，时间戳单位为毫秒
bytedcli ratel ios setting-change search \
  --start 1720000000000 \
  --end 1720086400000

# 查询当前最新直播 SDK 版本和宿主版本映射
bytedcli ratel ios version get

# 只保留某个宿主的版本映射
bytedcli ratel ios version get --host-name SampleHost

# 列出指定 SDK 版本的 general service
bytedcli ratel ios general-service list --sdk-version 3900

# 判断某个 service 是否是 general service
bytedcli ratel ios general-service get \
  --sdk-version 3900 \
  --service-name SampleService
```

## Agent Guidance

- 需要结构化输出时加 `--json`（全局选项，放在 domain 前，如 `bytedcli --json ratel ios general-service list --sdk-version 3900`）
- `--value-type` 使用语义值：`bool`、`int`、`double`、`dictionary`、`array`、`string`、`nsnumber`；不要向用户暴露后端数字编码
- `--effect-version` 使用 Ratel setting 生效版本格式，例如 `4.1.7`
- `--sdk-version` 使用 4 位版本号，例如 `3900`
- `ratel ios version get` 不传 `--sdk-version` 时查询 Ratel calendar 当前最新直播 SDK 版本；传 `--sdk-version` 时查询指定直播 SDK 版本的宿主映射
- `ratel ios version get --host-name <name>` 只过滤输出中的宿主版本映射；宿主名需要与 Ratel calendar 返回的 `hosts[].name` 一致
- `setting create` 只支持创建最简稳定 Setting；如果用户需要 description、module、权限、非 stable 或其它高级字段，说明当前 CLI 未暴露这些参数
- `setting-change search` 的 `--start` / `--end` 使用毫秒时间戳，跨度最多 31 天；用户给自然语言日期时先换算成毫秒时间戳
- 如果用户要求 Android 或 iOS package，说明当前 bytedcli Ratel 不覆盖该操作，避免编造命令

## References

- `references/ratel.md`
- `../../invocation.md`
- `../../troubleshooting.md`
