# Resource Center：跨产品资源发现与统计

## 入口与认证

要求 `ve >= 1.1.5`。服务状态、支持类型、资源搜索和分组统计默认使用 `ve resourcecenter` 的只读 OpenAPI（`2023-06-01`），即下面的 ve 命令。`bytedcli volcano resource ...` 作为兼容入口继续保留，场景边界是：需要在单条命令里显式传入 AK/SK/STS（`--access-key-id` / `--secret-access-key` / `--session-token`）且没有可用 ve profile 时使用它；它只接受 AK/SK/STS，不使用 Babi 会话，也不提供 ve 之外的额外能力。

| 任务                   | ve Action                 |
| ---------------------- | ------------------------- |
| 查询服务是否就绪       | `GetResourceCenterStatus` |
| 获取支持的资源类型目录 | `ListResourceTypes`       |
| 搜索一页账号资源       | `SearchResources`         |
| 按类型或地域统计       | `GetResourceCounts`       |

先按主 Skill 确认 ve 身份；已通过 Babi 设备码流程建立的 ve Console Login profile 可作为凭据来源。只有用户明确选择 profile 时才加 `--profile <name>`，后续调用沿用同一个 profile。不要把 bytedcli 的 `--volc-account-id` 传给 ve。

服务地址使用 `--endpoint resourcecenter.volcengineapi.com`。系统参数 `--region` 是签名地域；资源的地域筛选放在 body 的 `Filter` 中（`Key=Region`）。不设置该筛选可返回各地域及 `global` 的资源。

服务需已开通且初始化完成，身份需有对应只读权限。不会自动开通、关闭或修改服务；支持类型目录和资源同步进度决定查询覆盖范围。

## 从发现到统计

```bash
# 就绪条件：Result.ServiceStatus=Enabled 且 Result.InitStatus=Finished
ve resourcecenter GetResourceCenterStatus --body '{}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com

# 支持类型目录，不是当前账号拥有的资源列表
ve resourcecenter ListResourceTypes --body '{}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com

# ResourceType 使用目录给出的 Service:ResourceType，保留大小写
ve resourcecenter SearchResources \
  --body '{"MaxResults":10,"Filter":[{"Key":"ResourceType","MatchType":"Equals","Values":["vefaas:function"]},{"Key":"Region","MatchType":"Equals","Values":["cn-beijing"]}]}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com

# 相同 Key 的 Values 是 OR，不同 Key 的筛选条件是 AND
ve resourcecenter SearchResources \
  --body '{"MaxResults":20,"Filter":[{"Key":"Region","MatchType":"Equals","Values":["cn-beijing","cn-shanghai"]},{"Key":"ProjectName","MatchType":"Equals","Values":["demo-project"]}]}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com

# 按地域统计项目资源；统计覆盖匹配资源，与搜索页大小无关
ve resourcecenter GetResourceCounts \
  --body '{"GroupByKey":"Region","Filter":[{"Key":"ProjectName","MatchType":"Equals","Values":["demo-project"]}]}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com

# 使用完全相同的筛选条件，改为按资源类型统计
ve resourcecenter GetResourceCounts \
  --body '{"GroupByKey":"ResourceType","Filter":[{"Key":"ProjectName","MatchType":"Equals","Values":["demo-project"]}]}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com
```

## 筛选与分页

`SearchResources` 和 `GetResourceCounts` 共用 `Filter` 数组，每项包含 `Key`、`MatchType`、字符串数组 `Values`。以下是对应上游 bytedcli 查询语义的映射；其他匹配方式先查 ve 详细帮助。

| 查询含义     | Filter.Key         | MatchType  | Values 内容                                        |
| ------------ | ------------------ | ---------- | -------------------------------------------------- |
| 资源类型     | `ResourceType`     | `Equals`   | `service:type`，大小写以目录为准                   |
| 资源地域     | `Region`           | `Equals`   | 如 `cn-beijing`、`global`                          |
| 资源 ID      | `ResourceID`       | `Equals`   | 完整资源 ID                                        |
| 名称包含文本 | `ResourceName`     | `Contains` | 名称关键词                                         |
| 项目名称     | `ProjectName`      | `Equals`   | 如 `demo-project`                                  |
| 标签         | `Tags`             | `Contains` | JSON 字符串：`{"key":"owner","value":"demo-team"}` |
| 内网 IP      | `PrivateIpAddress` | `Equals`   | IPv4 或 IPv6 地址                                  |
| 公网 IP      | `PublicIpAddress`  | `Equals`   | IPv4 或 IPv6 地址                                  |

标签的 `Values` 元素是 JSON 编码的字符串，不是对象。构造整个 body 时需再次转义内部双引号；允许空标签值，标签值中的空白和 `=` 保持原样。

`MaxResults` 取值 1–100，默认 10。每次只返回一页，没有资源总数。只要 `Result.NextToken` 非空，就保留所有筛选条件，把它原样传入下一次请求的 `NextToken`；不得解析、截断或 trim token。没有 `--page`：

```bash
ve resourcecenter SearchResources \
  --body '{"MaxResults":10,"NextToken":"<next-token>","Filter":[{"Key":"ResourceType","MatchType":"Equals","Values":["vefaas:function"]},{"Key":"Region","MatchType":"Equals","Values":["cn-beijing"]}]}' \
  --region cn-beijing --endpoint resourcecenter.volcengineapi.com
```

`GetResourceCounts` 的 `GroupByKey` 为 `Region` 或 `ResourceType`，不传分页参数。

## 输出与判读

ve 返回原始 OpenAPI envelope，字段位于 `Result`，不是 bytedcli 的 `data`：

- 状态：读取 `Result.ServiceStatus` 和 `Result.InitStatus`；只有去除首尾空白后的 `Enabled + Finished` 代表就绪，缺字段或未知状态不视为就绪。ve 不生成 `ready`。
- 类型：`Result.ResourceTypes` 的 `Service` 与 `ResourceType` 构成 selector；目录不代表当前账号拥有该类型资源。
- 搜索：`Result.Resources` 保留资源定位字段；`Result.NextToken` 为空才代表分页结束。ve 不生成 `hasMore`；若响应缺少 NextToken，不能当作完整清单。
- 统计：核对 `Result.GroupByKey` 与请求一致，读取 `Result.ResourceCounts[].GroupName/Count`；需要总数时对 Count 求和。计数可能包含 IAM、global 和默认资源，不能当作计费实例数或费用。
- 所有结果都先检查命令退出状态和 `ResponseMetadata.Error`；请求失败不能展示为空列表。

## 排错

- 未就绪：检查服务开通与初始化进度，状态查询不会自动开通。
- 凭据错误：遵循主 Skill 的 ve 身份检查和登录流程；不要导出或粘贴真实 key/token。
- 权限错误：检查当前 ve 身份对上述 Resource Center 只读 Action 的权限。
- 空结果：核对类型目录、大小写和筛选条件；资源增删改后索引可能尚未同步。
- 结果比预期少：先按 NextToken 继续翻页；需要聚合数量时，用相同筛选条件调用 GetResourceCounts。
