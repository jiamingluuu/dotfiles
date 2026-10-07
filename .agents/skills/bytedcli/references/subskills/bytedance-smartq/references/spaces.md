# 空间与应用配置

这些命令使用 SmartQ UI OpenAPI 认证。`space get` 读取一个空间的设置：`--space-id` 按 ID 获取，`--meego-space` 按 Meego projectName 获取第一个关联空间。两个参数必须且只能提供一个。

```bash
bytedcli --json smartq space get --meego-space demo-project
bytedcli --json smartq space get --space-id 1000

# parent-id 为 0 时，在空间根目录下创建；默认预览，--yes 才提交
bytedcli smartq space directory create --space-id 1000 --name demo-directory --parent-id 0

# 移动端、桌面端和 Web 分别读取各自的配置
bytedcli --json smartq space package list --space-id 1000 --page 1 --page-size 20
bytedcli --json smartq space pc-config list --space-id 1000 --page 1 --page-size 20
bytedcli --json smartq space domain list --space-id 1000 --page 1 --page-size 20

# 标签与 Mock 场景默认查询第一页，使用 --all 获取全部匹配记录
bytedcli --json smartq space tag list --space-id 1000 --scopes case --name demo --page 1 --page-size 20
bytedcli --json smartq space mock-scene list --space-id 1000 --app-type web --name-keyword demo --page 1 --page-size 20
bytedcli --json smartq space tag list --space-id 1000 --scopes case --all
bytedcli --json smartq space mock-scene list --space-id 1000 --app-type web --all
```

应用配置列表保留包名、默认包标记和完整 PC 启动配置；服务端返回的敏感配置字段会脱敏。分页结果回显 `page`、`page_size` 和当前页条数，后端没有返回总数时不推算 `total`。

所有列表的 `--page` 从 1 开始，默认查询第一页；标签默认每页 20 条，其余列表默认每页 10 条。标签与 Mock 场景支持 `--all`，不能同时传入 `--page`，页大小在此模式下不生效。`--all` 映射到后端的 `page_num=0`，结果中的 `page` 因而为 0，`has_more` 为 `false`。

`--scopes` 使用 `execution-failure`、`assertion-failure`、`case`，分别表示执行失败、断言失败和用例标签。Mock 场景的 `--app-type` 使用 `mobile`、`web`、`pc`。`--name` 精确匹配场景名，`--name-keyword` 模糊匹配。

Mock 场景还支持 `--belongs`、`--creators`、`--updaters`；创建人和更新人列表使用逗号分隔的用户邮箱前缀。

创建目录需要空间写权限。`--operator` 为用户邮箱前缀，省略时在提交阶段解析当前登录用户。`--dry-run` 与 `--yes` 不能同时使用。
