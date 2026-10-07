# Redis 服务说明

## AllowList 清理顺序

删除实例后立即 `DeleteAllowList` 可能返回 `AllowListBindInstanceCannotDelete`。先轮询 `DescribeDBInstanceDetail` 直到实例不存在，再删除 AllowList。

`DescribeAllowLists` 的名称过滤不适合作为清理证明；按 ID 调用详情并期待 `AllowListNotExist`：

```bash
ve redis DescribeAllowListDetail --body '{"AllowListId":"acl-<id>"}'
```

## ParameterGroup 需要分页

`DescribeParameterGroups` 要求 `RegionId`、`PageNumber`、`PageSize`，否则返回：

```text
Missing Params: PageNumber,PageSize
```

## 创建实例易错点

- `NoAuthMode` 关闭认证时使用 `close`，不是 `disabled`。
- `ConfigureNodes` 必须包含子网 AZ，例如 `{"AZ":"cn-beijing-b"}`。
- 临时实例必须关闭删除保护。
- 删除时轮询到详情接口返回不存在，再清理依赖 AllowList。

## Shell 清理陷阱

开启 `set -o pipefail` 时，`tr -dc ... | head -c 14` 可能因 head 提前关闭管道而返回 141，导致资源已创建但清理 trap 未执行。使用不会提前关闭管道的密码生成方式，且不得打印 Redis 密码。
