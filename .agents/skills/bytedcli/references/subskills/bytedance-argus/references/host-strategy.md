# 宿主策略规则与参数

处理 `host-strategy status` 查询，以及 `host-strategy apply` 策略接入、配置更新或删除时，先读取本文，再确定操作参数。

## 配置变更规则

- `container_config` / `global_config` 支持不同宿主、端、环境的不同 base 放在同一张工单中。每个目标独立拉取完整 base、应用同一份已确认的变更并生成自己的 `previewCompared`，不要求 base 或变更后的策略配置一致。删除策略也按各目标自己的切面绑定处理。
- 配置变更前必须明确操作意图。业务已明确“完整替换”且范围、完整配置已给出时，直接使用 `--config-mode replace`，不重复确认；它替换所选 `--strategy` 的配置对象（容器配置还受 `--sec-cid` 限定），未提供的策略字段会删除，其他策略、切面和容器仍保留。它不替换整个配置文件。
- 业务未明确操作时，先与业务确认替换还是 merge，以及变更字段/范围，确认后才生成工单；不要自行把“修改某配置”解释为替换。选择 merge 时还要明确对象按顶层合并还是递归合并、数组如何处理、是否有删除或重排需求。已有明确答案时沿用，不重复询问。不得使用高级 preview 或 `ticket create` 绕过操作意图确认。
- 普通策略更新必须显式提供 `--config-mode replace|merge`，无默认值。merge 还需 `--merge-mode shallow|deep`：shallow 保留未提供的顶层字段，所提供的嵌套对象及其中数组整体替换；deep 递归保留未提供的对象字段。合并层级内遇到数组时必须指定 `--array-mode replace|append|union`：整体替换、保留重复项按顺序追加、按完整 JSON 值合并去重（保持首次出现顺序，忽略对象键顺序）。不按数组下标或条目 ID 合并，数组内对象不递归合并。
- merge 中 `null` 是写入值，不代表删除；空数组在 replace 时清空，在 append 时不改变原列表，union 仍会去除已有重复项；空对象在 deep merge 中保留已有子字段。若业务要求删字段、按条目 ID 修改、重排等操作，先确认具体规则，再为每个目标从自己的完整 base 构造结果，使用完整策略替换或高级完整 preview，并逐目标核对 diff。不要用第一份 base 推导其他目标的完整替换配置。append/union 遇到已有非数组值时会报错并阻止整张工单生成。
- `--config-mode` / `--merge-mode` / `--array-mode` 仅用于本地生成的 container/global 策略更新；删除策略、高级完整 preview、常量和内容安全通道使用各自的操作参数，混传会报错。`--dry-run` 与正式建单使用相同规则校验，每个 preview 的变更分析会记录操作方式。

## 参数

| 参数                      | 说明                                                                                                                                                 |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `--hosts`                 | 目标宿主，支持宿主详情页 URL、`id:name` 或 label-only；label-only / 纯数字使用 Argus Hybrid suggest 解析。                                             |
| `--env`                   | 环境，`Online` 或 `Inhouse`；多个值用逗号分隔。                                                                                                      |
| `--os`                    | 端，支持 `android`、`ios`、`harmony_os`、`mac_os`、`windows`；多个值用逗号分隔。                                                                      |
| `--config`                | 配置通道。查询和变更支持 `container_config`、`global_config`、`web_content_verify_config`、`const_conf`；变更都走 `host-strategy apply`。 |
| `--sec-cid`               | 容器安全域，默认 `host`；主要用于 `container_config`。                                                                                                |
| `--strategy`              | 策略 key。`container_config` 查询未命中时会按中文 label/策略名查唯一候选并使用候选 value；策略变更时表示要新增或更新的策略 key。                    |
| `--source`                | 查询配置来源：`auto`、`open-api` 或 `cdn`。`auto` 先用 latest-config，失败且版本齐全时对 `container_config` fallback CDN。                           |
| `--aid`                   | CDN fallback 的 Android/Harmony aid；不传时默认使用宿主 id。                                                                                         |
| `--app-id`                | CDN fallback 的 iOS app_id；也支持前端应用详情页 URL；不传时默认使用宿主 id。                                                                        |
| `--android-version`       | Android `container_config` CDN fallback 的 `version_name`。                                                                                          |
| `--harmony-version`       | Harmony `container_config` CDN fallback 的 `version_name`。                                                                                          |
| `--ios-version`           | iOS `container_config` CDN fallback 的 `app_version`。                                                                                                |
| `--gecko-bkt`             | CDN fallback 的 Gecko bucket，默认 `9`。                                                                                                             |
| `--aspect`                | 可选切面 key。新增切面或把策略挂到切面时使用。                                                                                                       |
| `--switch`                | 切面开关，传 `off`、`report` 或 `on`，分别表示关闭、仅上报、开启。                                                                                    |
| `--aspect-async`          | 设置切面异步执行。                                                                                                                                   |
| `--strategy-switch`       | 切面规则里的策略开关，传 `off`、`report` 或 `on`，分别表示关闭、仅上报、开启。                                                                        |
| `--strategy-type`         | 策略规则类型，通常是 `client` 或 `ttm`。                                                                                                             |
| `--strategy-version`      | 策略规则版本。                                                                                                                                       |
| `--strategy-index`        | 策略规则执行顺序，允许 0。                                                                                                                           |
| `--strategy-config-json`  | 策略配置 JSON object；按显式 `--config-mode` 替换或合并到每个目标自己的 base，并生成完整 `previewCompared`。                                            |
| `--strategy-config-file`  | 从文件读取策略配置 JSON object；操作方式由 `--config-mode` 决定。                                                                                       |
| `--config-mode`           | 普通 container/global 策略更新必填：`replace` 完整替换所选策略配置（可传 `{}`）；`merge` 按指定规则合并。无默认值。                                     |
| `--merge-mode`            | `config-mode=merge` 必填：`shallow` 顶层合并、嵌套对象整体替换；`deep` 递归合并对象。                                                                   |
| `--array-mode`            | 合并层级内有数组时必填：`replace` 整体替换、`append` 追加、`union` 按完整 JSON 值去重合并。                                                             |
| `--strategies-json`       | 高级用法：直接传完整 `params.strategies`。                                                                                                           |
| `--strategies-file`       | 从文件读取完整 `params.strategies`。                                                                                                                 |
| `--aspects-json`          | 高级用法：直接传完整 `params.aspects`。                                                                                                              |
| `--aspects-file`          | 从文件读取完整 `params.aspects`。                                                                                                                    |
| `--preview-compared-json` | 高级用法：直接传完整 `params.previewCompared`；使用时跳过本地 latest-config diff 生成。                                                              |
| `--preview-compared-file` | 从文件读取完整 `params.previewCompared`。                                                                                                            |
| `--const-key`             | `const_conf` 常量 key。                                                                                                                              |
| `--const-value`           | `const_conf` 常量字符串值。                                                                                                                          |
| `--const-value-json`      | `const_conf` 常量 JSON 值。                                                                                                                          |
| `--replace-json`          | 完整替换 `const_conf` 的 JSON object。                                                                                                                |
| `--replace-file`          | 从文件读取完整 `const_conf` 替换 JSON object。                                                                                                       |
| `--rule-json`             | `web_content_verify_config.rules` 中追加或替换的内容安全规则 object / array；默认会按 `contentType`、`type`、`mode` 唯一匹配已有规则并合并 `patterns`。 |
| `--rule-file`             | 从文件读取要追加或替换的内容安全规则 object / array。                                                                                                |
| `--config-json`           | 完整 `web_content_verify_config` JSON object，或按 OS 分组的 object。                                                                                 |
| `--config-file`           | 从文件读取完整 `web_content_verify_config` JSON object。                                                                                             |
| `--replace-rules`         | 内容安全变更时替换 rules，而不是追加 rules。                                                                                                         |
| `--append-new-rule`       | 内容安全变更时强制新增 rule，不按 `contentType`、`type`、`mode` 合并到已有规则。                                                                       |
| `--publish-by-group`      | 设置 `params.needPublishByGroup=true`，按宿主组发布。                                                                                                |
| `--group-hosts`           | 显式写入 `params.groupHosts`；不传时，`--publish-by-group` 会使用解析出的宿主 id。                                                                    |
| `--impact`                | 写入 `previewCompared.changeAnalysis.impact` 的中文影响说明。                                                                                        |
| `--risk`                  | 写入 `previewCompared.changeAnalysis.overallAssessment` 的中文风险判断。                                                                              |
| `--high-risk`             | 标记 `previewCompared.changeAnalysis.hasHighRiskChange=true`。                                                                                        |
