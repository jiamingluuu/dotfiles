# DPE Env Create API Snapshot

本文件记录 DPE 单环境创建接口的请求结构与响应结构，供后续设计 CLI 或排查字段含义时参考。

## Endpoint

- Method: `POST`
- Path: `/dpe/env/assitant/jupiter/env`

## Required headers

```text
x-tt-username: <username>
X-Jwt-Token: <bytecloud_jwt>
Content-Type: application/json;charset=UTF-8
Referer: <dpe_env_page>
Accept: application/json, text/plain, */*
```

## Example request body

```json
{
  "env_idc": "*",
  "env_scene_type": "single",
  "env_creator": "example.user",
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

## Example success response

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "env_id": 123456,
    "env_scene_type": "single",
    "env_status": "preparing",
    "env_name": "[demo][DPE-example.service.api][123456]",
    "env_idc": "*",
    "env_tag": "ppe_dpeenv_single_123456",
    "env_creator": "example.user",
    "env_end_time": "2099-01-01T00:00:00",
    "env_lane_enable": false,
    "env_psm_infos": [
      {
        "psm": "example.service.api",
        "scm_version": "",
        "git_branch": "",
        "git_commit": "",
        "cluster_infos": [
          {
            "cluster_name": "default",
            "cluster_id": -1,
            "zone": "China-North",
            "resource": {
              "type": null,
              "package": null,
              "cpu": -1,
              "mem": -1
            },
            "env_vars": {},
            "sidecars": [],
            "service_mesh": {
              "quota_mode": null,
              "virtual_cluster": null,
              "dc_infos": null,
              "mem": null,
              "cpu": null,
              "socket": null,
              "package": null,
              "enable_sidecar_percent": null,
              "sidecar_ingress_enable": null,
              "sidecar_egress_enable": null,
              "sidecar_http_ingress_enable": null,
              "sidecar_http_egress_enable": null,
              "sidecar_mysql_egress_enable": null,
              "sidecar_mongo_egress_enable": null,
              "sidecar_redis_egress_enable": null
            },
            "instance_infos": null,
            "qps_value": null,
            "qps_update_time": null,
            "qps_last_active_time": null
          }
        ],
        "dynamic_op_versions": null,
        "user_env": null
      }
    ],
    "env_task_error_info": null
  },
  "total": null
}
```

## Field notes

- `env_scene_type`
  - 当前抓到的是 `single`
- `env_idc`
  - 当前抓到的是 `*`
- `env_psm_infos[].cluster_infos[].cluster_name`
  - 表示目标集群名，例如 `default`
- `env_psm_infos[].cluster_infos[].zone`
  - 当前抓到的是 `China-North`
- `resource.quota_mode`
  - 请求里出现，当前样例为 `0`
- `data.env_status`
  - 创建后初始状态样例为 `preparing`
- `data.env_psm_infos[].cluster_infos[].cluster_id`
  - 当前样例返回 `-1`

## Security notes

- 不要把真实 `X-Jwt-Token` 写入仓库。
- 不要把真实用户名、邮箱、员工号写入 skill 文档。
- 如果需要保留更多接口证据，优先保留字段结构与占位值，不保留可复用凭据。
