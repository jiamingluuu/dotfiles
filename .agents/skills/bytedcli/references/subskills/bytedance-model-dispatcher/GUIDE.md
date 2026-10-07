---
name: bytedance-model-dispatcher
description: "Query the Model Dispatcher control plane through bytedcli. Use for 模型下发, Model Dispatcher, scenario discovery, exact model metadata, model revision history, or scenario version history. This skill is read-only and uses a dedicated site web session exchanged from the saved ByteDance SSO browser session, not ByteCloud JWT."
---

# bytedcli Model Dispatcher

## 前置条件

- 当前能力全部只读：场景列表、模型信息、模型历史、场景版本历史。
- 认证是模型下发站点独立 Web Session，不是 ByteCloud JWT。首次使用先保存 BDSSO 浏览器会话，再换取站点 Cookie：

```bash
# CN
bytedcli --site cn auth login --session
bytedcli --site cn model-dispatcher auth login
bytedcli --site cn --json model-dispatcher auth status

# US：控制面在 US，但换票仍使用 ByteDance SSO
bytedcli --site us-ttp --auth-site bytedance auth login --session
bytedcli --site us-ttp model-dispatcher auth login
bytedcli --site us-ttp --json model-dispatcher auth status
```

- 普通查询会自动复用缓存；缓存失效时自动换票并只重试一次。不要手工复制 Cookie。
- `--json` 是全局参数，放在 `model-dispatcher` 前。
- `--site cn|us-ttp` 选择控制面；CN 与 US 的站点 Cookie 分开缓存，切换站点不会复用另一站的 Web Session。下面示例默认 CN；查询 US 时在每条命令的 `model-dispatcher` 前加 `--site us-ttp`。

## Quick start

```bash
# 当前用户可见的场景
bytedcli model-dispatcher scenario list

# 精确查询模型聚合信息
bytedcli --json model-dispatcher model get \
  --scenario-id 101 \
  --name demo_model

# 查询模型修订历史；继续翻页时传回 next_page_token
bytedcli --json model-dispatcher model history list \
  --scenario-id 101 \
  --name demo_model \
  --page-size 20 \
  --page-token 0

# 查询场景版本历史
bytedcli --json model-dispatcher version list \
  --scenario-id 101 \
  --page-size 20 \
  --page-token 0

# US 示例：同一套只读命令覆盖场景、模型、模型历史和场景版本历史
bytedcli --site us-ttp model-dispatcher scenario list
bytedcli --site us-ttp --json model-dispatcher model get \
  --scenario-id 101 \
  --name demo_model
bytedcli --site us-ttp --json model-dispatcher model history list \
  --scenario-id 101 \
  --name demo_model \
  --page-size 20 \
  --page-token 0
bytedcli --site us-ttp --json model-dispatcher version list \
  --scenario-id 101 \
  --page-size 20 \
  --page-token 0
```

## 核心概念

- **场景（scenario / business）**：平台的数据与权限最高隔离单位。版本、模型映射、下发数据统计等围绕场景组织；场景可按 App、项目或端拆分。
- **模型（model）**：实际下发的原子文件实体。名称、场景、大版本、小版本、类别和环境状态共同描述具体实体。
- **大版本与小版本**：同名但不同大版本通常表示不兼容升级；同名同大版本下的小版本变化通常表示兼容升级或热更新。
- **类别 / 分级**：同一模型可依据设备性能或业务参数向不同设备下发不同类别。版本映射主要记录模型名与大版本，具体小版本和类别由服务端匹配。
- **环境与泳道**：核心数据区分内测和线上；内测阶段可以用独立测试泳道隔离变更。默认内测泳道汇总待上线变更，线上环境对应实际线上映射。
- **版本（version）**：场景下的一张模型映射表。版本历史用于确认某个场景的映射演进，不等同于单个模型的小版本历史。

## Agent Guidance

- 不知道场景 ID 时先执行 `scenario list`。
- 已知模型名时用精确 `model get`；需要逐条变更记录时用 `model history list`。
- `model history list` 的分页由 CLI 对聚合响应中的修订列表稳定排序后提供；`pageToken` 是从 0 开始的数字游标。
- `version list` 的 `page_token` 直接映射控制台版本接口的 cursor；下一页继续传 JSON 返回的 `next_page_token`。
- 模型列表接口即使在个别环境中匿名可读，也不能据此判断认证成功。认证状态只以 `/api/user/info` 返回有效用户 email 为准。
- US 控制面同样使用 `platform=bytedance` 和 ByteDance SSO；不要按全局 `us-ttp` 默认映射改用 TikTok SSO。
- 当前不提供上传、上线、删除、版本编辑、泳道合并等写操作。

## References

- 需要完整字段与分页语义时，读取 `references/model-dispatcher.md`。
- 不确定 bytedcli 安装方式、全局参数或 HTTP 调试方式时，读取 `../../invocation.md`。
- 命令执行失败或认证过期时，读取 `../../troubleshooting.md`。
