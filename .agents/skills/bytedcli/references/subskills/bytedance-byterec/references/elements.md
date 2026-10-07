# Elements / Darwin 特征工程

## 概念（不要混淆）

- **raw feature（抽前）**：特征数据从哪来、怎么解析（`source_psm` + parse/normalize）。主键是 `zion_name`。
- **extracted feature（抽后）**：哪个 Rosetta OP 把抽前特征转成 FID / 序列。抽后特征的 `depend` 引用抽前特征的 `output_column`。
- **feature group（bfs_app）**：一组抽前/抽后特征的应用分组（例如某个精排通道）。
- **Darwin feature group（生产特征组）**：`feature_engineering/feature_group/<numeric-id>` 页面对应的生产配置。它不是 Elements `bfs_app`；按生产 ID 使用 `byterec darwin feature-group get` 查询。
- **branch（分支）**：特征改动在分支上进行，`master` 是线上主干；写操作必须显式指定 `--branch`。
- **source（数据源）**：retriever 定义；同一 source 可有多个 app 版本（`other_version`）。
- **pack（打包）**：把某分支的特征配置打成一个可测试版本。

## 能力范围

- 查询/创建/更新/绑定/删除抽前特征：`byterec elements raw-feature list|create|update|bind|unbind|delete`
- 查询/创建/更新/绑定/删除抽后特征：`byterec elements feature list|create|update|bind|unbind|delete`
- 按生产 ID 查询 Darwin 特征组：`byterec darwin feature-group get --group-id <id>`
- 管理特征组（bfs_app）：`byterec elements feature-group list|create|delete`
- 管理分支：`byterec elements branch list|create|delete|pack|pack-info|diff`
- 查询数据源、Rosetta OP 目录、关联模型：`byterec elements source list`、`byterec elements rosetta-op list`、`byterec elements feature-models list`
- 需要机器可读结果供脚本或 Agent 继续处理时，加全局 `--json`

## 写入前置条件

- **所有写操作默认只输出 dry-run 预览完整 payload；必须显式加 `--yes` 才真正提交**
- 所有写命令（create/update/bind/unbind/delete/pack/feature-group create/delete）必须显式传 `--branch`，避免误写 `master`
- 抽前特征的 `--zion-name` 是主键；`raw-feature update` 用它选中要改的行（支持逗号分隔批量）

## Quick start

```bash
# Darwin 生产特征组：返回 ID、group_name、ref_namespace、group_type 和原始扩展字段
bytedcli --json --site i18n-tt byterec darwin feature-group get --group-id 1001

# 抽前特征：按 feature_space 列出（--name 支持逗号分隔与 --precise 精确匹配）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature list \
  --feature-space demo_space --branch dev --page 1 --page-size 20

BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli --json byterec elements raw-feature list \
  --feature-space demo_space --branch dev --name u_demo --precise true

# 抽前特征：创建（dry-run；确认后加 --yes）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature create \
  --feature-space demo_space --branch dev \
  --zion-name u_demo --source-psm example.data.source --feature-name demo_feat \
  --normalize-clazz "lagrange::bfs::DemoNorm<std::string>" \
  --output-column u_demo --shared true --need-dump false

# 抽前特征：批量更新（--zion-name 是主键，逗号分隔多个；同一批字段改动应用到每行）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature update \
  --feature-space demo_space --branch dev \
  --zion-name u_a,u_b --need-dump true

# 抽前特征：绑定/解绑到特征组
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature bind \
  --feature-space demo_space --branch dev --name u_demo --app-names tab2
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature unbind \
  --feature-space demo_space --branch dev --name u_demo --app-names tab2 --unbind-all false

# 抽前特征：删除（按 id）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements raw-feature delete \
  --feature-space demo_space --branch dev --ids 1001,1002 --yes

# 抽后特征：列出（支持 --slot / --shared / --model-name 等过滤）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature list \
  --feature-space demo_space --branch dev --page 1 --page-size 20

# 抽后特征：创建 / 更新（写操作必须带 --branch）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature create \
  --feature-space demo_space --branch dev --name demo_extracted --method demo_op
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature update \
  --feature-space demo_space --branch dev --feature-id 2001 --need-dump true

# 抽后特征：绑定/解绑到特征组
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature bind \
  --feature-space demo_space --branch dev --feature-id 2001 --app-names tab2

# 特征组（bfs_app）：列出 / 创建 / 删除
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature-group list \
  --feature-space demo_space --branch dev
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature-group create \
  --feature-space demo_space --branch dev --app-name tab2 --description "demo group"
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature-group delete \
  --feature-space demo_space --branch dev --app-name tab2 --yes

# 分支：列出 / 创建 / 删除
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch list --feature-space demo_space
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch create \
  --feature-space demo_space --branch dev
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch delete \
  --feature-space demo_space --branch dev --real-delete false --yes

# 分支：打包为测试版本 / 查看已有 pack
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch pack \
  --feature-space demo_space --branch dev --comment "demo pack" --yes
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch pack-info \
  --feature-space demo_space --branch dev

# 分支：diff 单个配置文件（默认对比 master）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements branch diff \
  --feature-space demo_space --from-branch dev --to-branch master \
  --file-name tab2_feature_list.conf

# 数据源：列出（含每个 app 实际使用的 retriever 版本）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements source list \
  --feature-space demo_space --branch dev --psm example.data.source

# Rosetta OP 目录（抽后 method 可选项）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements rosetta-op list

# 关联模型（改动前的影响分析：哪些模型消费该 feature_space 的特征）
BYTEDCLI_CLOUD_SITE=i18n-tt bytedcli byterec elements feature-models list \
  --feature-space demo_space --branch dev

# 等价的站点写法（--site 放在 byterec 之前）
bytedcli --site us-ttp-bdee byterec elements raw-feature list --feature-space demo_space
```

## 写操作与 dry-run

所有写操作（create / update / bind / unbind / delete / pack / feature-group create/delete）默认只打印 dry-run 计划（`method` / `url` / `body`），不发起真实写请求。确认 payload 无误后再加 `--yes` 提交。

- `raw-feature update` 与 `feature update` 是 read-modify-write：先按 `--zion-name` / `--feature-id` 拉取当前完整对象，叠加本次字段改动后整体回写，因此 `--zion-name`（主键）不会被覆盖。
- `raw-feature update` 也支持 `--features-json '[{"id":...,"zion_name":...}]'` 直接提供完整行对象（每个对象必须带 `id`）。
- 写操作会用登录态里的用户名作为 `modify_by`；如无法解析可显式传 `--username <you>`。

## 输出说明

- list 命令文本模式输出表格；`--json` 输出结构化结果，并回填 `page` / `page_size` 便于分页脚本判断当前页
- `source list` 会把每个 source 及其 `other_version[]` 展开成多行，方便看到各 app 实际使用的 retriever
- `feature-models list` 返回的是扁平的模型名数组
- `branch diff` 输出单个配置文件在两个分支间的差异文本
- 写命令 dry-run 模式输出 `dry_run: true` 与完整 `plan`；`--yes` 提交后输出服务端返回

## Notes

- `--json` 是全局参数，必须放在 `byterec` 之前
- 站点跟随全局 `--site` / `BYTEDCLI_CLOUD_SITE`：`us-ttp` 默认走 BDEE 通道（`us-ttp` 与 `us-ttp-bdee` 等价），与 `us-ttp-usts` 区分
- 抽前（raw feature）与抽后（extracted feature）是两个不同资源：抽前定义数据来源与解析，抽后定义 Rosetta OP 转换；抽后的 `depend` 指向抽前的 `output_column`
- 所有写操作默认 dry-run，必须显式 `--yes` 才提交；写操作必须显式传 `--branch`，避免误写 master
- `raw-feature list --name` 是客户端子串过滤（`--precise true` 精确匹配），会扫描分支，返回有上限截断标记

## 实现参考

- `src/cli/commands/byterec/elements.ts`
- `src/cli/handlers/byterec/elements.ts`
- `src/api/byterec/elements.ts`
- `src/services/byterec/elements.ts`
