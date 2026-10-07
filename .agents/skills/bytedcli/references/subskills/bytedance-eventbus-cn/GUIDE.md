---
name: bytedance-eventbus-cn
description: "Operate domestic CN-only Eventbus via bytedcli eventbus-cn: query event, client, storage, mirror info, search messages, and create producer or consumer clients on domestic CN regions or BOE. Do not use for i18n, US, or EU users because those regions are not supported by this skill."
---

# bytedcli Eventbus

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

本 skill 仅适用于国内 CN 区域 Eventbus；i18n、US、EU 用户不支持使用本 skill。

- 查询 Eventbus event 详情
- 查询 producer/consumer client 详情
- 搜索 event 下的 producer/consumer clients
- 查询 event 下的消息
- 查询 event storage 绑定和 MQ mirror 信息
- 创建 producer 或 consumer client
- 快速确认 event 所属 region、owner、namespace、topic 绑定情况
- 验证国内生产或 BOE Eventbus OpenAPI 和 skill 调用链路是否可用

## 前置条件

- 按 Quick start 示例直接调用 `bytedcli eventbus-cn`；如需切换 BOE，可使用全局 `--site boe` 或环境变量 `BYTEDCLI_CLOUD_SITE=boe`。
- 当前命令仅限国内 CN 区域使用；i18n、US、EU 用户不支持该 skill。

## Quick start

```bash
# 文本输出
bytedcli eventbus-cn event info --event "demo.event" --region "CN"
bytedcli eventbus-cn event info --event "demo.event" --region "China-East"
bytedcli eventbus-cn event info --event "demo.event" --region "China-North6"

# 结构化输出
bytedcli --json eventbus-cn event info --event "demo.event" --region "CN"

# Client 查询
bytedcli eventbus-cn client get --event "demo.event" --role consumer --id "123456"
bytedcli eventbus-cn client get --event "demo.event" --role producer --id "demo.producer.psm" --region "CN"
bytedcli eventbus-cn client search --event "demo.event" --psm "demo.psm" --region "CN" --client-type consumer

# Storage / mirror
bytedcli eventbus-cn event storage list --event "demo.event" --region "CN" --skip-rmq-quota
bytedcli eventbus-cn event storage list --event-id 9988 --region "CN"
bytedcli eventbus-cn mirror info --event "demo.event"

# 消息查询
bytedcli eventbus-cn message search --event "demo.event" --region "CN" --type msg_key --msg-key "demo_key" --start-time 1777365563000 --end-time 1777365603000 --json
bytedcli eventbus-cn message search --event "demo.event" --region "CN" --type time_range --start-time 1713849600000 --end-time 1713853200000 --json
bytedcli eventbus-cn message search --event "demo.event" --region "CN" --type offset_range --partition "3" --start-offset 11 --end-offset 999 --json

# 创建 producer / consumer。写接口必须显式确认。
bytedcli eventbus-cn producer create --event "demo.event" --owner "alice" --psm "demo.psm" --desc "demo" --region "CN" --print-body
bytedcli eventbus-cn producer create --event "demo.event" --data '{"owner":"alice","psm":"demo.psm","desc":"demo","region":"CN"}' --yes
bytedcli eventbus-cn consumer create --event "demo.event" --owner "alice" --psm "demo.psm" --group "demo_group" --desc "demo" --region "CN" --print-body
bytedcli eventbus-cn consumer create --event "demo.event" --data-file ./consumer-create.json --yes

# 切换站点
bytedcli --site boe eventbus-cn event info --event "demo.event" --region "BOE"
```

## Notes

- `--event` 传 event name，`--region` 传 Eventbus region
- `client get --id` 支持 client ID；按 producer PSM 或 consumer group 查询时需要传 `--region`
- `client search` 使用 Eventbus OpenAPI `client/base/list`；单次请求支持一个 event、一个 psm、一个 region 和一个 role，精确 consumer group 查询请使用 `client get`
- `event storage list` 接受 `--event-id <id>` 或 `--event <name>` 二选一；不需要 RocketMQ quota 明细时可加 `--skip-rmq-quota`
- `message search` 使用 Eventbus OpenAPI `search/msg_v2`；支持 `time_range`、`offset_range`、`msg_key` 三种结构化查询，不支持原始 JSON passthrough
- 创建命令通过 `--data` 或 `--data-file` 传 JSON object，请求体字段参考 `references/eventbus.md`
- `producer create` 未传 `--data/--data-file` 时，可通过结构化参数组装请求体；默认填充推荐发送/告警参数，并按 PSM 从 ByteTree 派生 `service_tree_id` / `product_line`
- `consumer create` 未传 `--data/--data-file` 时，可通过结构化参数组装请求体；默认填充推荐消费/告警参数，并按 PSM 从 ByteTree 派生 `service_tree_id` / `product_line`
- `producer create --print-body` 和 `consumer create --print-body` 只打印最终请求体，不发起创建请求；可用 `--no-fill-defaults` 或 `--no-derive-bytetree` 关闭默认填充或 ByteTree 派生
- 创建命令必须传 `--yes` 才会发起真实写请求
- 需要稳定机器可读输出时，使用全局 `--json`；消息查询在 JSON 模式保留 OpenAPI 返回的 header/body/origin_body
- Eventbus CN-only 版本仅支持 `cn` 和 `boe` 站点；国内生产 `--region` 支持 `CN`（华北）、`China-East`（华东）、`China-North6`（华北6），BOE 站点使用 `BOE`；i18n、US、EU 用户不支持该 skill

## References

- `references/eventbus.md`
