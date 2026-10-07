# RMQ Topic 权限申请

本流程用 `bytedcli rmq` 发现 Topic，再通过 RMQ 控制台 API 查重并创建权限审批单。`bytedcli rmq` 本身仍是只读能力，不要把控制台写请求描述成 bytedcli 命令。

这不是 Neptune ACL 流程。服务间 RPC ACL 应使用 `acl-generator` 或 bytedcli Neptune `strict-auth apply`。

## 权限语义

| 用户语义 | `perm_type` | `auth_type` |
| --- | ---: | --- |
| consumer / read / 消费 | `1` | `psm` |
| producer / write / 生产 | `2` | `psm` |

不要根据 PSM 名称、Topic 归属或常见用法推断权限方向。用户未说明时，先询问是 producer/write 还是 consumer/read。

## 1. 收集范围

在发送任何写请求前，确定：

- Topic 精确名称。
- 目标 PSM 列表。
- 每个 PSM 的权限方向。
- 站点：`cn` 或 `i18n-bd`。
- 精确 cluster 和 vregion，或用户明确给出的集合范围，例如“所有 `ee_normal` cluster”。

当用户用集合范围表达意图时，先展开成具体 Topic 列表，再让用户确认；不要把集合表达直接当成写入授权。

## 2. 用 bytedcli 发现精确 Topic

CN：

```bash
bytedcli --site cn --json rmq topic list \
  --vregion China-North \
  --search <topic-name> \
  --page 1 \
  --page-size 100
```

ByteIntl：

```bash
bytedcli --site i18n-bd --json rmq topic list \
  --vregion <vregion> \
  --search <topic-name> \
  --page 1 \
  --page-size 100
```

搜索是模糊匹配。只保留 `topicName` 与用户输入完全相等的项，并记录每项的：

- `topicId`
- `topicName`
- `vregion`
- `clusterName`
- `owner`
- `resourcePsm`

没有精确匹配时，报告未找到并停止；不要选用相似 Topic 替代。`topicId`、`vregion`、`clusterName` 或 owner 信息缺失时，先用 `rmq topic get --topic-id <topic-id> --vregion <vregion>` 补充；仍无法确定写入范围或 review user 时停止。

以下内容必须作为独立 scope，未经用户明确选择不得扩展：

- `<topic>__meshlane_lane-...` 等 lane Topic。
- mock Topic。
- `test`、`web_normal`、`ee_staging` 以及其他未点名 cluster。
- 同名但 vregion 不同的 Topic。

如果分页结果达到 `--page-size` 上限，继续翻页，直到完成精确匹配检索；不要将第一页当成全量结果。

## 3. 获取站点 JWT

对每个站点分别获取新鲜 ByteCloud JWT：

```bash
bytedcli --site <site> --json auth get-bytecloud-jwt-token
```

从 JSON 的 `data.jwt` 读取 token，只在当前请求进程内传递。不要回显、记录、写入文件或放进最终回复。

| site | origin | API base |
| --- | --- | --- |
| `cn` | `https://cloud.bytedance.net` | `https://cloud.bytedance.net/api/v1/rocketmq` |
| `i18n-bd` | `https://cloud.byteintl.net` | `https://cloud.byteintl.net/api/v1/rocketmq` |

权限申请流程目前只按上表两个站点执行。对 `boe`、`i18n-tt`、`us-ttp` 或 `eu-ttp` 不要猜测 host、tenant header 或写接口兼容性。

每个请求使用与 Topic 一致的：

```text
x-jwt-token: <site JWT>
x-bcgw-vregion: <topic vregion>
x-bcgw-tenant-id: bytedance
origin: <site origin>
referer: <site origin>/
accept: application/json
```

POST 额外使用 `content-type: application/json`。CN 和 ByteIntl 的 host、origin 或 JWT 不得交叉复用。

## 4. 查询已有权限

对每个 `topicId` 调用：

```text
GET <API base>/api/perm/topic?topic_id=<topicId>
```

仅当返回明确成功时才解析权限列表。明确的失败码、非 JSON 响应或结构无法识别时应停止，不要将“查询失败”当成“没有权限”。

对每个 Topic × PSM × 权限方向，用以下字段查重：

```text
auth_type = psm
auth_name = <target PSM>
perm_type = 1 | 2
```

已有相同权限的项标记为 `already_granted` 并跳过，不再创建审批单。

## 5. 生成最终确认表

在 POST 之前，展示所有待提交项：

| site | vregion | cluster | topic | topic_id | resource_psm | owner | target_psm | direction / perm_type | review_user |
| --- | --- | --- | --- | ---: | --- | --- | --- | --- | --- |

`review_user` 必须来自 Topic owner，优先选人类 owner，避免 `rocketmqtoken` 等服务账号。无法唯一确定人类 owner 时，列出候选并询问用户，不要猜测。

只有用户已明确要申请，并对展开后的最终目标表给出确认，才可继续。单纯询问“怎么申请”、“有没有 skill”、“帮我看看”或进行 Topic 发现，都不构成写入授权。

## 6. 创建审批单

在提交前再执行一次已有权限查询，避免确认期间发生的重复申请。对仍需申请的项逐个调用：

```text
POST <API base>/api/create/perm
```

```json
{
  "topic_id": 123456,
  "auth_type": "psm",
  "perm_type": 2,
  "auth_name": "example.service.producer",
  "review_user": "demo-owner"
}
```

一次只提交一个 Topic × PSM × 权限方向，并记录其返回的 `op_id`。只有响应明确成功且存在 `op_id` 时才标记为 `submitted`。

如某项失败，停止后续 POST，并分开报告：

- 已提交的项及 `op_id`。
- 失败项及后端错误。
- 尚未提交的项。

不要盲目重试 POST。重试前必须先重新查询已有权限或审批状态，避免重复创单。

## 7. 返回结果

按 `submitted`、`already_granted`、`failed`、`not_submitted` 分组返回。每个已提交项包含 Topic、cluster、vregion、PSM、权限方向、review user、`op_id` 和审批链接。

用户要求可复制输出时，将链接作为纯文本逐行返回：

```text
https://cloud.bytedance.net/rocketmq/approval/my_apply?op_id=<op_id>
https://cloud.byteintl.net/rocketmq/approval/my_apply?op_id=<op_id>
```

只返回与实际站点一致的链接，不要为未提交或无 `op_id` 的项生成链接。

## 安全边界

- 不推断 producer 或 consumer。
- 不从精确 Topic 自动扩展到 lane、mock、test、web 或其他 cluster。
- 不跨站点复用 JWT、host、origin 或 header。
- 不回显 Cookie、JWT 或完整认证 header。
- 不在用户确认最终目标表前 POST。
- 不宣称 bytedcli RMQ 提供权限申请命令。
