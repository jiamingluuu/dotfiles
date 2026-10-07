# Argus OpenAPI（bytedcli）

`bytedcli argus openapi ...` 通过 Argus Service Account 调用 Argus 平台的 OpenAPI，覆盖资产 / 扫描 / 安全 / DeepVuln 四大子域。



## 认证

Argus OpenAPI 走 ByteCloud 应用账号身份（AK / SK）鉴权。AK / SK 来自 **ByteCloud 开放平台 > 我的应用/我的账号 > 凭证与基础信息**。

首次使用需一次性配置（三选一）：

```bash
# 姿势 A：pipe SK（推荐脚本化 / CI）
printf %s "$BYTECLOUD_APP_SK" | bytedcli --site cn auth app set --access-key-id <cn-access-key-id>

# 姿势 B：环境变量 + set
BYTECLOUD_APP_SK=<sk> bytedcli --site cn auth app set --access-key-id <cn-access-key-id>

# 姿势 C：直接用 BYTEDCLI_SERVICE_ACCOUNT_* 环境变量兜底（不写入 credential store）
export BYTEDCLI_SERVICE_ACCOUNT_CN_ACCESS_KEY_ID=<ak>
export BYTEDCLI_SERVICE_ACCOUNT_CN_SECRET_ACCESS_KEY=<redacted>
```

配置完自查：

```bash
bytedcli --site cn auth app status            # 查看 AK / SK 是否已配置
bytedcli --site cn auth app status --refresh  # 强制刷新一次 JWT，验证 AK / SK 有效
```

## 命令总览

四大 resource 分组（`bytedcli argus openapi <resource> --help` 看完整子命令）：

| 分组       | 覆盖                                                                                                         |
| ---------- | ------------------------------------------------------------------------------------------------------------ |
| `asset`    | 代码仓库 / SCM / API / Goofy / 二级域名 / URL 关联 / 挂树信息查询                                            |
| `scan`     | 页面扫描任务创建/查询、Codebase / SCM / BNPM 扫描触发与结果、规则与问题维护、tar 包检查                      |
| `security` | 项目信息查询                                                                                                 |
| `deepvuln` | Codebase / SCM / PSM / Domain / URL / BNPM / Font / Hybrid URL / 平台 owner/产品搜索 / 用户负责资产 详情查询 |

## 常用 flag pattern

- 分页：`--page <n>`（1-based，默认 1）+ `--page-size <n>`（默认 20）
- 时间范围（`scan task list` / `scan rule task-result-branch` 等）：
  - `--last-days <n>` 查询最近 N 天
  - 或 `--start <YYYY-MM-DD>` + `--end <YYYY-MM-DD>` 指定绝对区间
  - 二选一；`--start` 和 `--end` 必须同时提供
- 资产类型：`--asset-type codebase|scm|psm|domain`（或对应数字 `1/4/6/11`）
- 数组类参数：逗号分隔，例如 `--rule-id 100,200,300`
- JSON 类参数（如 `--callback-params`、`--assets`）：单引号包裹的 JSON 字符串

## 代表性示例

```bash
# GET：查询扫描任务状态
bytedcli --json argus openapi scan task get --task-id 12345

# POST + direct body：代码仓库列表 + 分页
bytedcli --json argus openapi asset codebase list --page 1 --page-size 20

# POST + bodyShape=params：SCM 列表（body 自动包一层 { params: ... }）
bytedcli --json argus openapi asset scm list --page 1 --page-size 20

# 时间范围：最近 7 天扫描任务
bytedcli --json argus openapi scan task list --last-days 7

# 时间范围：绝对区间
bytedcli --json argus openapi scan task list --start 2025-06-01 --end 2025-06-07

# DeepVuln：仓库漏洞详情
bytedcli --json argus openapi deepvuln codebase get --name demo-org/demo-repo
```

## 常见错误码

| code                             | 含义                                                                                          | 处理                                                                                                                                                     |
| :------------------------------- | :-------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ARGUS_OPENAPI_INPUT_ERROR`      | 命令参数错误（互斥冲突、必填缺失、JSON 解析失败等）                                           | 按 hint 修正参数                                                                                                                                         |
| `ARGUS_OPENAPI_RESPONSE_INVALID` | 后端返回体不符合 envelope schema                                                              | 检查网关是否返回 HTML / 非 JSON 登录跳转                                                                                                                 |
| `ARGUS_OPENAPI_ERROR`            | 后端返回 status 非 0 业务错误                                                                 | 详情看 `details.status` 与 `.message`                                                                                                                    |
| ByteCloud auth 相关报错          | AK / SK 未配置、AK / SK 无效、`bytecloud-auth` RPC 失败、`BYTEDCLI_SERVICE_ACCOUNT_*` 只设一半 | 跑 `bytedcli --site cn auth app status` 自查；按 hint 重新 `bytedcli --site cn auth app set --access-key-id <ak>`（SK 走 stdin）或成对设置 AK / SK 环境变量 |

以上表格外的鉴权类错误按 bytedcli 抛出的 `code` / `hint` 处理。

## 更多细节

Argus OpenAPI 官方文档：https://bytedance.larkoffice.com/wiki/DFR4wkt6ei7jsNkeYeOcV0Qnnoc
