# Ratel CLI Reference

Ratel 命令覆盖 iOS setting 创建、setting 变更记录查询、Live SDK 版本日历查询，以及 general service 列表和服务判断。当前不覆盖 Android 操作或 iOS package 操作。

## 创建 iOS setting

```bash
bytedcli ratel ios setting create \
  --setting-key sample_feature_enabled \
  --name "Sample Feature Enabled" \
  --effect-version 4.1.7 \
  --value-type bool \
  --default-value false \
  --author sample.user \
  --author-nick-name "Sample User"
```

参数：

| Option                       | Description                                                                    |
| ---------------------------- | ------------------------------------------------------------------------------ |
| `--setting-key <key>`        | setting key，例如 `sample_feature_enabled`                                     |
| `--name <name>`              | setting 展示名称                                                               |
| `--effect-version <version>` | 生效版本号，例如 `4.1.7`                                                       |
| `--value-type <type>`        | 语义类型：`bool`、`int`、`double`、`dictionary`、`array`、`string`、`nsnumber` |
| `--default-value <value>`    | 默认值，按目标类型填写字符串形式                                               |
| `--author <name>`            | 作者用户名                                                                     |
| `--author-nick-name <name>`  | 作者展示名                                                                     |

创建 setting 是写操作。执行前先确认 setting key、类型、默认值、影响版本和作者信息。

当前 `setting create` 只覆盖最简稳定 Setting：`description` 与 `module_name` 固定为空、`pms` 固定为空数组、`stable=true`、`type=0`。不要向用户承诺可通过 CLI 传入这些固定字段；如需高级字段，当前 bytedcli Ratel 尚未暴露对应参数。

## 查询 setting 变更记录

```bash
bytedcli ratel ios setting-change search \
  --start 1720000000000 \
  --end 1720086400000
```

参数：

| Option              | Description          |
| ------------------- | -------------------- |
| `--start <epochMs>` | 起始时间戳，单位毫秒 |
| `--end <epochMs>`   | 结束时间戳，单位毫秒 |

`--start` 到 `--end` 的跨度最多 31 天；更长时间范围请拆分查询。

## 直播 SDK 版本日历

```bash
bytedcli ratel ios version get

bytedcli ratel ios version get --host-name SampleHost

bytedcli ratel ios version get \
  --sdk-version 3900 \
  --host-name SampleHost
```

参数：

| Option                    | Description                                                |
| ------------------------- | ---------------------------------------------------------- |
| `--sdk-version <version>` | 可选；SDK 版本号，使用 4 位版本号。省略时查询当前最新版本 |
| `--host-name <name>`      | 可选；只保留指定宿主的版本映射                             |

JSON 输出中的 `data.version.sdk_version` 是直播 SDK 版本；`data.version.hosts[]` 是该直播 SDK 版本对应的宿主版本映射。

## general-service

```bash
bytedcli ratel ios general-service list --sdk-version 3900

bytedcli ratel ios general-service get \
  --sdk-version 3900 \
  --service-name SampleService
```

参数：

| Option                    | Description                 |
| ------------------------- | --------------------------- |
| `--sdk-version <version>` | SDK 版本号，使用 4 位版本号 |
| `--service-name <name>`   | 待判断的 service 名称       |

## JSON 输出

所有命令支持全局 `--json`：

```bash
bytedcli --json ratel ios general-service get \
  --sdk-version 3900 \
  --service-name SampleService
```

查询当前最新直播 SDK 版本时也支持 `--json`：

```bash
bytedcli --json ratel ios version get
```
