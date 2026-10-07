# Lego 状态与错误

<!-- Load: MANDATORY when classifying compile/order/step status or handling a Lego error code; CONDITIONAL for polling and release tracking; Do NOT Load for command discovery that does not interpret status or errors. -->

## 枚举

> 这些枚举仅用于文本输出展示（原始值 + 标签）；`--json` 输出保留原始数值。

### PublishStatus（工单 / 发布状态 `status`）

CLI 过滤参数 `--order-status` 使用单个语义值，不直接接收后端数字编码；API 层仍按后端字段名发送 `order_status_list`。

| 值  | 含义                          | 是否终态                           |
| --- | ----------------------------- | ---------------------------------- |
| `0` | PublishOff 创建未发布         | 否                                 |
| `1` | PublishFinish 发布完成        | **是（最终完成）**                 |
| `2` | PublishOnline 灰度中          | 否                                 |
| `3` | PublishCancel 发布取消        | 是                                 |
| `4` | PublishReady 灰度完成准备上线 | **否（收尾中间态，别误判为完成）** |
| `5` | PublishWait 等待下一步        | 否                                 |
| `6` | PublishBuilding 准备灰度环境  | 否                                 |
| `7` | PublishCanceling 回滚中       | 否（流程已终止方向）               |
| `8` | PublishSuspend 暂停中         | 否                                 |

### StepType（步骤类型 `type`）

| 值  | 含义                                     |
| --- | ---------------------------------------- |
| `1` | Lane 泳道                                |
| `2` | Canary 小流量                            |
| `3` | SingleDC 单机房                          |
| `4` | Percentage 灰度百分比                    |
| `5` | **ManualConfirm 人工确认（需 confirm）** |
| `6` | PublishCheck 发布检测                    |
| `7` | Rebuild 重启节点                         |
| `8` | **Audit 审核节点（需人工）**             |

> 步骤 `type in {5, 8}` 时停止自动轮询，转人工。

### CheckTaskStatus（发布检测 `check_task_status`）

| 值   | 含义                             |
| ---- | -------------------------------- |
| `1`  | StartCheck 创建                  |
| `2`  | Checking 检测中                  |
| `3`  | CheckSuccess 检测成功            |
| `4`  | CheckFail 检测失败               |
| `5`  | CommitCheckFail 提交检测任务失败 |
| `6`  | SkipCheck 跳过检测               |
| `7`  | CheckWarning 检测告警            |
| `8`  | ConfirmWarning 告警已确认        |
| `9`  | ConfirmFailed 检测失败已确认     |
| `10` | CommitPending 等待提交           |

### TaskStatus（步骤任务 `task_status`）

| 值  | 含义               |
| --- | ------------------ |
| `0` | TaskRunning 进行中 |
| `1` | TaskPassed 已通过  |
| `2` | TaskFailed 已失败  |

### PipelineKind（流水线类型 `pipeline_kind`）

| 值  | 含义                                        |
| --- | ------------------------------------------- |
| `1` | PluginPublish 插件发布（创单选这个）        |
| `2` | ConfPublish 配置发布                        |
| `3` | AdaptiveSwitchInitPhase 自适应切换初始化    |
| `4` | AdaptiveSwitchRuntimePhase 自适应切换运行时 |

> `pipeline list --pipeline-kind` 取值 `plugin_publish` / `conf_publish` / `adaptive_switch_init_phase` / `adaptive_switch_runtime_phase` 分别对应 1/2/3/4。

### FlowType（flow 类型 `type`）

| 值  | 含义                 |
| --- | -------------------- |
| `1` | WhiteList 白名单PSM  |
| `2` | Level 服务等级       |
| `3` | All 全量发布         |
| `4` | BlackList 黑名单PSM  |
| `5` | Dimension 自定义维度 |

### PluginKind（插件类型 `kind`）

| 值  | 含义                    |
| --- | ----------------------- |
| `0` | NativeKind 原生模式     |
| `1` | IPCKind IDL接口模式     |
| `2` | JsonKind JSON模式       |
| `3` | MulVerNative 多版本插件 |

> `kind = 3`、`is_adaptive = true` 或 `is_multi_ver === true` 视为多版本插件（这些字段均来自 `plugin get` 返回的插件详情，不是用户输入；`order create` 的 `--version` 会按 `commit_tag` 下发）。
> `plugin register --plugin-type` 取值 `ipc` / `json` / `mul_ver_native` 分别对应 IPCKind / JsonKind / MulVerNative。

### OrderType（工单类型 `order_type`）

| 值  | 含义                                                        |
| --- | ----------------------------------------------------------- |
| `1` | OrderTypeHotUpgrade 热升级（`order create` 当前仅支持此值） |
| `2` | OrderTypeConfUpgrade 配置升级                               |
| `3` | OrderTypeAdaptiveSwitchPluginConfUpdate 自适应切换插件配置  |
| `4` | OrderTypeAdaptiveSwitchPSMConfUpdate 自适应切换PSM配置      |

> `order create --order-type` 当前仅支持 `hot_upgrade`；`order list --order-type` 取值 `hot_upgrade` / `conf_upgrade` / `adaptive_switch_plugin_conf` / `adaptive_switch_psm_conf` 分别对应 1/2/3/4。

### AdaptiveRunMode（自适应运行模式）

| 值  | 含义            |
| --- | --------------- |
| `1` | IPC IPC模式     |
| `2` | Native 原生模式 |

> `plugin register --default-adaptive-run-mode` 取值 `ipc` / `native` 分别对应 1/2。

### PluginStatus（插件 `status`）

| 值  | 含义                  |
| --- | --------------------- |
| `0` | StatusOff 未上线      |
| `1` | StatusOnline 上线中   |
| `2` | StatusCancel 上线取消 |
| `3` | StatusFinish 上线完成 |

### ScmBuildStatus（编译版本 `status` / `status_arm`，字符串）

| 值             | 含义                     | 是否终态 |
| -------------- | ------------------------ | -------- |
| `build_ok`     | 编译成功                 | **是**   |
| `success`      | 编译成功（部分接口返回） | **是**   |
| `build_failed` | 编译失败                 | **是**   |
| `prepare`      | 准备中                   | 否       |
| `building`     | 编译中                   | 否       |
| `queue`        | 排队中                   | 否       |
| `not_build`    | 未参与本次编译（未排期） | **是**   |
| `wait`         | 等待（lego 自有态）      | 否       |

> 轮询 `plugin compile-detail get` 时，`build_ok` / `success` 表示成功，`build_failed` 表示失败。`not_build` 表示该架构未参与本次编译（例如未开 `--multi-arch` 时的 `status_arm`），既不是进行中也不是失败，判断成功时直接忽略。只对被排期的架构判终态：被排期架构全部成功即可停止轮询，任一仍在 `prepare` / `building` / `queue` / `wait` 才继续等待；两个架构都是 `not_build` 属异常，转人工检查。

## 错误码

| code                              | 触发场景                                         | 处理                                   |
| --------------------------------- | ------------------------------------------------ | -------------------------------------- |
| `LEGO_INPUT_ERROR`                | 多 region 站点缺 `--region` / 非法 `--region` 等 | 按 `hint` 补正确参数                   |
| `LEGO_AUTH_REQUIRED`              | 获取 JWT / 鉴权失败                              | `bytedcli auth login`（注意目标 site） |
| `LEGO_ENVELOPE_ERROR`             | 后端业务报错                                     | 检查参数与工单状态，按 `hint` 重查     |
| `LEGO_ORDER_DETAIL_MISSING_FIELD` | 工单详情缺关键字段                               | 按 `hint` 重新查询工单详情             |
| `LEGO_INTERNAL_ERROR`             | dry-run 请求体缺失等内部异常                     | 重试；持续失败检查实现                 |
