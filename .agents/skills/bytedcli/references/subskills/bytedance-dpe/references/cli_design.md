# DPE Env Create CLI Design

本文件基于 `POST /dpe/env/assitant/jupiter/env` 接口，整理当前 `bytedcli dpe env create` 的命令设计与请求体映射。

## 命令树建议

```text
bytedcli dpe
  └── env
      ├── create
      └── get
```

当前已接入：

```bash
bytedcli --site cn dpe env create
```

当前也已接入环境详情查询：

```bash
bytedcli --site cn dpe env get --env-id <id>
```

## 推荐命令

最小可用形式：

```bash
bytedcli --site cn dpe env create \
  --psm example.service.api \
  --cluster-name default \
  --zone China-North
```

显式展开全部当前已知关键参数：

```bash
bytedcli --site cn dpe env create \
  --psm example.service.api \
  --cluster-name default \
  --zone China-North \
  --scene-type single \
  --env-idc AUTO \
  --json
```

## 参数映射

| API 字段                              | CLI 参数              | 说明                               |
| ------------------------------------- | --------------------- | ---------------------------------- |
| `env_scene_type`                      | `--scene-type`        | 当前样例固定为 `single`            |
| `env_idc`                             | `--env-idc`           | 可选；省略时使用上游自动选择值     |
| `env_creator`                         | 内部自动填充          | 默认来自当前登录用户名，不建议暴露 |
| `env_psm_infos[].psm`                 | `--psm`               | 目标 PSM                           |
| `env_psm_infos[].scm_version`         | `--scm-version`       | 可选                               |
| `env_psm_infos[].git_branch`          | `--git-branch`        | 可选                               |
| `env_psm_infos[].git_commit`          | `--git-commit`        | 可选                               |
| `cluster_infos[].cluster_name`        | `--cluster-name`      | 目标集群名                         |
| `cluster_infos[].zone`                | `--zone`              | 例如 `China-North`                 |
| `cluster_infos[].resource.quota_mode` | 内部默认填充          | 结构化模式不暴露后端数字枚举       |
| `cluster_infos[].env_vars`            | `--env-var key=value` | 支持重复传参                       |

## 默认值建议

- `--scene-type`
  - 默认 `single`
- `--env-idc`
  - 省略时默认使用上游自动选择值 `*`
- `--site`
  - 使用全局 `--site cn`

## 不建议直接暴露给用户的字段

这些字段应由 CLI 内部自动处理，而不是让用户手工传：

- `X-Jwt-Token`
- `x-tt-username`
- `Referer`
- `Accept`
- `Content-Type`

推荐做法：

- `X-Jwt-Token`
  - 通过 `bytedcli auth get-bytecloud-jwt-token` 内部获取
- `x-tt-username`
  - 通过当前登录态推导
- `Referer`
  - 固定为 DPE env 页面

## 请求体组装建议

对于 flag 版命令，CLI 内部组装成：

```json
{
  "env_idc": "*",
  "env_scene_type": "single",
  "env_creator": "<current_user>",
  "env_psm_infos": [
    {
      "psm": "example.service.api",
      "scm_version": "",
      "git_branch": "",
      "git_commit": "",
      "cluster_infos": [
        {
          "psm": "example.service.api",
          "cluster_name": "default",
          "zone": "China-North",
          "env_vars": {},
          "sidecars": [],
          "service_mesh": {},
          "resource": {
            "quota_mode": 0
          }
        }
      ]
    }
  ]
}
```

## 文件入参建议

如果后续 `env_vars`、`sidecars`、`service_mesh` 变复杂，建议同时支持：

```bash
bytedcli --site cn dpe env create --request-file payload.json
```

设计原则：

- 简单场景优先 flags
- 复杂场景优先 `--request-file`
- 二者同时出现时，优先报错并要求二选一，避免歧义

## 文本输出建议

创建成功后，文本模式建议输出：

```text
Env created
- env_id: 123456
- env_name: [demo][DPE-example.service.api][123456]
- env_status: preparing
```

## JSON 输出建议

JSON 模式建议保留后端结构，但至少确保这些字段存在：

- `env_id`
- `env_name`
- `env_status`
- `env_tag`
- `env_psm_infos`

## 错误处理建议

- `code !== 0`
  - 直接抛结构化错误
- 非 JSON / HTML 响应
  - 抛带 endpoint 与响应预览的错误
- JWT 获取失败
  - 引导用户先执行 `bytedcli auth login` 或 `auth get-bytecloud-jwt-token`

## 当前代码落点

- `src/api/dpe/`
  - `client.ts`
  - `api.ts`
  - `types.ts`
  - `parsers.ts`
- `src/cli/commands/dpe/`
- `src/cli/handlers/dpe/`
- `test/api/dpe/`
- `test/cli/handlers/dpe/`
- `test/cli/commands/dpe/`
