# TeslaX Plan Scaffold Guide

本指南说明如何在 `bytedcli` 中手动搭建或组装类似 `teslax-cli` 的 TeslaX FTF Plan 创建草稿（Payload Scaffold），以应对包含复杂深层嵌套结构的 `plan create` / `plan update` 操作。

## 什么是 Plan Scaffold？

TeslaX FTF 的创建和更新接口要求传入结构极其复杂的 JSON，尤其是涉及到流量配置、回放目标机房/集群、Mock 规则时。手动在命令行敲 `--payload '{"psm_exec_params": {...}}'` 非常容易出错。
Scaffold（脚手架）的思路是：**在本地预先维护好若干种典型测试场景的 JSON 模板文件（如“全 Mock 回放”、“PPE 链路回放”等），执行命令时使用 `--payload @/path/to/scaffold.json` 来读取配置。**

## 如何搭建 Scaffold 模板

在当前工作目录下，可以创建多个 `.json` 模板文件，以下是三种常见解决方案的 Scaffold 模板示例：

### 1. 基础实时流量回放 (Base Realtime Replay)

创建一个名为 `scaffold-realtime.json` 的文件：

```json
{
  "test_scene": "研发自测",
  "enable_ftf": 1,
  "ftf_plan": {
    "enabled": true,
    "filter_mode": 1
  },
  "method_param_detail": [
    {
      "method": "YourMethodName",
      "new_method": "YourMethodName",
      "protocol": "thrift",
      "http_method": "",
      "flow_total": 100,
      "flow_type": 1,
      "mock_enable": 0
    }
  ],
  "psm_exec_params": {
    "your.target.psm": {
      "replay_env": "boe_test",
      "replay_cluster": "default",
      "replay_idc": "boe"
    }
  }
}
```

### 2. 全 Mock 历史流量回放 (Full Mock History Replay)

创建一个名为 `scaffold-full-mock.json` 的文件：

```json
{
  "test_scene": "研发自测",
  "enable_ftf": 1,
  "ftf_plan": {
    "enabled": true,
    "filter_mode": 2
  },
  "method_param_detail": [
    {
      "method": "YourMethodName",
      "new_method": "YourMethodName",
      "protocol": "thrift",
      "http_method": "",
      "flow_total": 50,
      "flow_type": 2,
      "mock_enable": 1
    }
  ],
  "psm_exec_params": {
    "your.target.psm": {
      "replay_env": "prod",
      "replay_cluster": "default",
      "replay_idc": "lf"
    }
  }
}
```

### 3. 智选流量规则回放 (Smart Modeling Replay)

创建一个名为 `scaffold-smart.json` 的文件：

```json
{
  "test_scene": "研发自测",
  "enable_ftf": 1,
  "ftf_plan": {
    "enabled": true,
    "filter_mode": 6
  },
  "advanced_filter_group_list": [
    {
      "filter_list": [
        {
          "filter_key": "feature_key_example",
          "filter_value": "feature_value_example",
          "filter_op": "in"
        }
      ]
    }
  ],
  "method_param_detail": [
    {
      "method": "YourMethodName",
      "protocol": "thrift",
      "flow_total": 100,
      "flow_type": 6,
      "mock_enable": 0
    }
  ]
}
```

## 如何使用 Scaffold 文件

`bytedcli` 的 `--payload` 参数原生支持读取本地 JSON 文件。你只需要在命令中传入 `@` 加上文件路径：

```bash
# 1. 拷贝并修改上面的模板为你需要的配置，保存为 my-scaffold.json
# 2. 使用 bytedcli 读取该 scaffold 文件进行创建
bytedcli tesla plan create \
  --space-id 1000 \
  --plan-name "My Scaffold Plan" \
  --psm your.target.psm \
  --payload @my-scaffold.json \
  --execute
```

> **注意：**
> 1. CLI 命令行指定的参数（如 `--plan-name`, `--psm`）会与 `@my-scaffold.json` 中的内容进行合并（Deep Merge）。
> 2. 如果两者有冲突，`--payload` 指定的内容优先级最高。
> 3. 推荐将与业务逻辑强相关的 `method_param_detail` 和 `psm_exec_params` 沉淀到 JSON 模板中，而将经常变动的 `plan-name` 留在命令行。