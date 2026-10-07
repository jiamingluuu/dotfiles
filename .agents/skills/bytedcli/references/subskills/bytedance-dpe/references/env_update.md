# DPE Env Update API Snapshot

本文件记录 DPE 环境助手的环境更新接口，供后续设计 CLI、排查重新部署逻辑，或对已创建 DPE 环境按 PSM / 集群维度更新服务版本时参考。

## Endpoint

- Method: `POST`
- Path: `/dpe/env/assitant/jupiter/update_env`
- Full URL: `https://bytedpe.bytedance.net/dpe/env/assitant/jupiter/update_env`
- Content-Type: `application/json`
- Controller: `com.bytedance.adqa.dpeEnvAssitant.controller.JupiterEnvApi#updateEnvInfo`
- Service: `com.bytedance.adqa.dpeEnvAssitant.service.jupiterService.JupiterEnvService#updateEnvInfo`
- Request model: `com.bytedance.adqa.dpeEnvAssitant.internalModel.DpeEnvInfoModel`

## Authentication

该接口走 `EnvAssistJupiterJwtFilter`：

- URL patterns:
  - `/dpe/env/assitant/jupiter/*`
  - `/dpe/env/assitant/api/*`
- 调用方携带 ByteCloud JWT。
- Filter 从 JWT 解析用户名并注入 `x-tt-username`。
- Controller 会从 `x-tt-username` 取当前用户并覆盖请求体中的 `env_creator`。
- 调用方不应自行伪造 `x-tt-username`。

## Request body

请求体为 `DpeEnvInfoModel` snake_case。`update_env` 主流程实际使用的顶层字段：

| 字段             | 类型                  | 必填 | 说明                                                           |
| ---------------- | --------------------- | ---- | -------------------------------------------------------------- |
| `env_id`         | Long                  | 是   | 要更新的 DPE 环境 ID。                                         |
| `env_scene_type` | String                | 是   | 场景类型，映射到 `DpeEnvSceneType`，例如 `multi` / `everest`。 |
| `env_creator`    | String                | 否   | 服务端会用 `x-tt-username` 覆盖。                              |
| `env_psm_config` | List<DpeEnvPsmConfig> | 是   | 本次要重新部署的 PSM / 集群列表。                              |

`env_psm_config[]` 的核心字段：

| 字段           | 类型   | 必填 | 说明                                                                       |
| -------------- | ------ | ---- | -------------------------------------------------------------------------- |
| `psm`          | String | 是   | 服务 PSM，环境里必须存在对应实例。                                         |
| `cluster`      | String | 否   | 为空表示 PSM 下全部集群；非空则只作用于指定集群。                          |
| `version_type` | String | 是   | 只允许 `git_branch` / `git_commit` / `scm_version`。                       |
| `version_info` | String | 是   | 与 `version_type` 对应的分支名、commit ID 或 SCM 版本号。                  |
| `user_env`     | String | 否   | 用户自定义环境变量，会作为 header `user_env` 透传到状态机的 SCM 编译任务。 |

`scm` / `env_params` / `ab_params` / `case_id` / `pillars_test_id` / `dynamic_op_versions` 等字段在 `update_env` 主流程中不直接使用，属于同 Controller 下其它接口字段。

## Processing notes

1. 参数与权限校验
   - 解析 `env_scene_type`，非法值返回 `ENV_UNKNOWN_SCENE_TYPE`。
   - 拉取该环境全部未删除实例。
   - 校验当前用户是否有环境权限，非授权用户返回 `ENV_UN_AUTHED`。
   - 环境当前状态若为 `PREPARING` / `PREPARING_FAILD` / `SENDING_TRAFFIC`，返回 `ENV_NOT_PREPARED`。
2. 逐条 PSM 前置校验
   - PSM / 集群在当前环境中必须有实例。
   - 集群状态若为 `DEPLOYING`，不允许再次触发部署。
   - `version_type` 只允许 `git_branch` / `git_commit` / `scm_version`。
   - `version_info` 不能为空。
   - PSM 必须在 `DpePsmInfo` 中配置好 `scm_name` / `scm_id` / `git_name`。
3. Pillars 兜底解绑
   - 尝试通知 Pillars 侧解绑环境和算子。
   - 若实例上残留 `op_info`，清空 Pillars 算子信息。
   - 该步骤失败仅打日志，不影响主流程。
4. 触发 SCM 编译与部署
   - 软删该 PSM / 集群下旧的 SCM / Mercury / Mars / Minerva 等部署任务。
   - 生成 `groupId = generateGroupId(timestamp, sceneType, envId, DEPLOYING)`。
   - 以 `psm -> groupId` 写入返回体 `group_id`。
   - 发送 `EventEnums.START_SCM_BUILD`，headers 包括 `branch` / `commit_id` / `scm_version` / `user_name` / `instance_info_list` / `object_type_index` / `env_tag` / `group_id` / `user_env`。

## Success response

```json
{
  "code": 200,
  "group_id": {
    "example.dpe.service": "example-group-id"
  },
  "message": "update env success"
}
```

`group_id` 是按 PSM 聚合的 map，每个 PSM 一个 groupId。后续可用于查询部署任务组状态：

```text
GET /dpe/env/assitant/jupiter/env/task/status?group_id=<groupId>
```

## Failure response

常见失败场景：

| 错误码 / 场景                                            | 触发条件                                                                |
| -------------------------------------------------------- | ----------------------------------------------------------------------- |
| `ENV_UNKNOWN_SCENE_TYPE`                                 | `env_scene_type` 非法。                                                 |
| `ENV_UN_AUTHED`                                          | 当前用户对该环境无权限。                                                |
| `ENV_NOT_PREPARED`                                       | 环境处于 `PREPARING` / `PREPARING_FAILD` / `SENDING_TRAFFIC`。          |
| `ERROR`                                                  | PSM / 集群不存在、正在部署中、版本字段非法、PSM 缺 SCM 配置等业务错误。 |
| `{"code":500,"message":"update fail, exception occurs"}` | Controller / Service 层兜底异常。                                       |

业务错误的 `message` 通常会带具体原因，调用方应直接展示。

## Request examples

按分支重新部署单个 PSM / 集群：

```json
{
  "env_id": 123456,
  "env_scene_type": "multi",
  "env_psm_config": [
    {
      "psm": "example.dpe.service",
      "cluster": "default",
      "version_type": "git_branch",
      "version_info": "feature/demo",
      "user_env": "FOO=bar"
    }
  ]
}
```

按 SCM 版本部署 PSM 下所有集群：

```json
{
  "env_id": 123456,
  "env_scene_type": "multi",
  "env_psm_config": [
    {
      "psm": "example.dpe.service",
      "version_type": "scm_version",
      "version_info": "1.0.0.123"
    }
  ]
}
```

多 PSM 更新：

```json
{
  "env_id": 123456,
  "env_scene_type": "multi",
  "env_psm_config": [
    {
      "psm": "example.dpe.service.a",
      "version_type": "git_commit",
      "version_info": "abcdef1234567890"
    },
    {
      "psm": "example.dpe.service.b",
      "cluster": "canary",
      "version_type": "git_branch",
      "version_info": "master"
    }
  ]
}
```

## CLI relationship

当前 `bytedcli dpe env update` 已接入该接口，用于对已有 DPE 环境重新部署服务版本：

```bash
bytedcli dpe env update \
  --env-id <env_id> \
  --scene-type multi \
  --psm <psm> \
  --cluster <cluster> \
  --version-type git_branch \
  --version-info <branch> \
  --json
```

`--cluster` 可选；不传时表示更新该 PSM 下所有集群。`--version-type` 只支持 `git_branch` / `git_commit` / `scm_version`。

多 PSM 更新建议使用完整请求 JSON：

```bash
bytedcli dpe env update --request-file ./dpe-env-update.json --json
```
