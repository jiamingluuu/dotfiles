# TokaDB Owner 资产盘点

`bytedcli tokadb report` 用于盘点当前账号作为 Owner 的全部 table，以及这些 table 实际关联的 cluster。需要本地 Markdown 或飞书文档时，直接使用 report 命令内置的标准模板，不要先调用 cluster/table list 再手工拼接。

## 标准调用

```bash
# 终端查看，未显式传 --region 时默认跨全部支持的 Region
bytedcli tokadb report

# 保存标准 Markdown
bytedcli tokadb report --output ./tokadb-owner-inventory.md

# 创建标准飞书文档
bytedcli tokadb report --feishu-doc

# 同时保存 Markdown 并创建飞书文档
bytedcli tokadb report \
  --output ./tokadb-owner-inventory.md \
  --feishu-doc \
  --doc-title "TokaDB Owner 资产盘点"

# 临时排除本次任务明确不需要的 Region
bytedcli tokadb report \
  --exclude-regions boe \
  --feishu-doc

# 保留完整结构化结果供程序消费
bytedcli --json tokadb report
```

## 数据口径

- Owner table 来自控制面 `tables?is_owner=true`，命令自动翻页获取全量结果。
- Cluster 是 Owner table 实际关联到的 cluster，不额外混入公共 cluster。
- 每张 table 会补充详情，每个关联 cluster 会去重后补充详情。
- 跨 Region 查询允许部分成功；失败 Region 不影响成功 Region 的报告生成。
- `usttp` / `euttp` 是默认支持范围，分别使用 `us-ttp` / `eu-ttp` ByteCloud Auth 凭证。
- `--exclude-regions` 在查询前生效，被排除 Region 不进入查询、统计、正文、错误或登录提示。

## 固定文档结构

飞书文档和本地 Markdown 必须保持以下顺序：

1. `TokaDB Owner 资产盘点`
2. 数据口径、覆盖范围、显式排除范围
3. `1. 核心概览`
4. `2. Region 覆盖`
5. `3. Cluster 清单`
6. `4. Table 清单`
7. `5. 数据限制`（仅有失败或告警时出现）

### 核心概览

使用两列表格，仅展示 Owner 表数、关联 Cluster 数、成功 Region 覆盖和查询范围。

### Region 覆盖

固定列为：

| Region | 状态 | Owner 表 | 关联 Cluster | 说明 |
| ------ | ---- | -------- | ------------ | ---- |

不得在后续章节为每个 Region 重复输出同一组 KPI。

### Cluster 清单

所有成功 Region 合并为一张表，固定列为：

| Region | Cluster | 表数 | 状态 | 类型 | 位置 | 负责人 |
| ------ | ------- | ---- | ---- | ---- | ---- | ------ |

Cluster 名称优先链接到可用的 Grafana / GroupMaster / TabletServer 监控页面。

### Table 清单

按成功 Region 分组，每个 Region 使用一张五列表：

| Cluster | DB.Table | 状态 | 类型 | 安全级别 |
| ------- | -------- | ---- | ---- | -------- |

DB.Table 名称优先链接到 table Grafana。正文不展示 ID、更新时间、完整 Owner 列表、原始 API 字段或其他低频信息；这些字段保留在 `--json` 输出。

### 数据限制

仅展示用户可理解、可行动的摘要，例如“需要补充登录”“当前网络不可达”和对应建议。不要把原始 HTTP body、异常堆栈或超长错误消息写入飞书正文。

## 版式约束

- 标题层级最多到三级，不为每个 Cluster 创建独立标题。
- 普通表格最多 7 列，Table 清单固定 5 列。
- 不使用超宽全字段表，不重复展示相同统计。
- 链接放在资源名称上，避免增加单独的“监控 URL”宽列。
- 文档正文服务人类阅读；完整性由 JSON 输出承担。
- 飞书创建失败时保留 Markdown/JSON 主结果，并按 `feishu_doc_error` 与 `feishu_doc_auth_command` 处理鉴权。

## 鉴权恢复

跨 Region 报告按实际 ByteCloud Auth site 获取凭证：

| TokaDB Region     | 登录命令                             |
| ----------------- | ------------------------------------ |
| `cn`              | `bytedcli auth login`                |
| `boe` / `boei18n` | `bytedcli auth login`                |
| `i18ntt`          | `bytedcli --site i18n-tt auth login` |
| `i18nbd`          | `bytedcli --site i18n-bd auth login` |
| `usttp`           | `bytedcli --site us-ttp auth login`  |
| `euttp`           | `bytedcli --site eu-ttp auth login`  |

`usttp` / `euttp` 不应错误收敛到 `i18n-tt` 登录，也不应作为“未接入区域”默认排除。只有当前交付明确不需要某些 Region 时，才使用 `--exclude-regions <region,...>` 临时跳过。

飞书文档创建返回 `invalid_grant` 或 `The refresh token has expired` 时：

```bash
bytedcli feishu login --qr-image /tmp/feishu-auth.png
```

授权完成后重跑原始 `tokadb report --feishu-doc`。飞书创建失败不影响已经成功生成的 TokaDB result、JSON 和本地 Markdown。

## 验收检查

生成后至少确认：

- 标题为 `TokaDB Owner 资产盘点`
- 章节顺序符合固定结构
- 没有四级及更深标题
- 没有旧式 `Region：xxx` 重复章节
- 没有“失败 Region 详情”原始错误宽表
- Table 清单不包含 `ID` 或“更新时间”列
- `--exclude-regions` 中的 Region 不出现在 queriedRegions 和正文
- 飞书创建结果能够解析出 `doc_url`
