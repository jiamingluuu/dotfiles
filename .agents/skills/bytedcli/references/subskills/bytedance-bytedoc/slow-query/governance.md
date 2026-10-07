# ByteDoc 慢查治理文档模板

当 `slow-query overview` 已经返回慢查询数据，且用户明确要求治理方案、客户分享材料、整改文档，或已经描述 CPU 周期性升高、接口超时、任务耗时、写入变慢、客户投诉等业务问题场景时，使用本模板。

## 触发边界

- 默认先输出证据摘要，不要在用户只想看慢查询结果时强行展开完整文档。
- 用户没有说明业务问题场景时，先询问当前表象和目标，例如 CPU 周期性升高、接口超时、任务耗时变长、写入变慢、客户投诉等。
- 用户要求飞书、Wiki 或客户分享版时，先在 Markdown 中整理内容；是否创建外部文档和是否脱敏，必须等待用户明确确认。
- 如果 `truncated=true`、`fetch_all=false` 或 `exhaustive=false`，先说明当前结论基于采样；需要全量治理结论时建议先用 `--fetch-all` 或更窄时间窗重新拉取。若用户仍要求立即输出，`慢查描述` 必须显式标注“非全量样本”。

## 输出结构

### 慢查描述

必须写清：

- 目标库、backend、vregion、查询窗口、阈值。
- 数据完整性：`fetch_all`、`fetched_count`、`backend_total`、`truncated`、`exhaustive`、`incomplete_ranges`。
- 主要慢 query shape、collection、调用方、耗时、扫描量、返回量和出现次数。
- 证据表，至少包含 collection/query shape、count、max/avg time、docs/keys scanned、returned、caller/component。

### 问题分析

每个判断都必须绑定慢日志证据，不能只凭经验判断。重点区分：

- 索引未命中或索引顺序不匹配。
- 索引字段覆盖不全导致回表。
- `in`、范围条件、`$exists:false`、低选择性字段导致扫描范围过大。
- 大结果集返回、缺少 projection、缺少 limit 或分页方式不合理。
- 聚合、排序、distinct、count 等操作成本高。
- 周期任务并发、批量删除/写入放大、热点租户或热点 source。

### 整改方案

方案必须可执行，避免只说“优化索引”。常见动作：

- 按等值、排序、范围条件设计组合索引，并说明字段顺序。
- 对大字段或无需返回字段补 projection，收敛返回量。
- 对周期任务错峰、限并发、分批处理，避免同一窗口集中打满 CPU。
- 对全量扫描型逻辑改为增量游标、预聚合或离线物化。
- 对批量删除/写入改小批量、限速，并避开业务高峰。
- 对无法通过单个索引覆盖的多形态查询，拆分访问模式或增加专用索引。

### 验证标准

整改后必须用同一库、同一时间窗、同一阈值或同等业务峰值窗口复查：

- 慢日志数量、p95/最大耗时是否下降。
- `docsExamined/keysExamined`、返回行数、扫描/返回比是否下降。
- CPU 峰值、周期性峰值持续时间、调用方并发是否下降。
- 是否仍有 `truncated=true`、`exhaustive=false` 或新的热点 query shape。

