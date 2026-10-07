# 结构化记录检索

## 构造查询

从 `data.retrieval.graphql` 取得 `root_field`、`arguments`、`required_argument_groups`、`response_fields`、`example_queries`、可能的 `result_order` 与 `record_reference`。

1. 选择与问题相近的 example query，保留该数据集的参数形式。只用声明的参数、类型和操作符；若 required_argument_groups 存在，满足至少一个完整必需参数组合，同时满足独立必填项。
2. 把对象标识、环境、时间等约束映射到有明确语义的参数；未支持的筛选条件不可伪装成已生效。先判断是否能小范围取回后本地筛选，否则向用户说明限制。
3. 仅选需要的 response_fields。对象/关系字段要按返回的子字段构造 selection。优先包含记录标识以及回答所需字段；需要引用时遵循 record_reference 的主键说明。
4. 这是单数据集、只读 OpsSQL GraphQL 子集。不要发送 SQL、mutation、variables、fragments、directives、多根查询；不臆造 count、聚合、排序、跨数据集 join 或 `limit/offset/where`。参数形式与关系能力以当前契约和示例为准。

仅当实时契约确实声明以下根、参数、字段时，可采用这个**合成示例**：

```bash
bytedcli --as user --json bytestable opsdata graphql query \
  --dataset demo_services \
  --query '{ demo_services(psm: "example.service.api", page_index: 1, page_size: 5) { psm owner level } }'
```

多数据集问题分别读取契约、查询，再以双方明确共有的标识核对。名称近似不能自动认定为同一实体；文档描述与实时记录冲突时展示差异与时间，不静默合并。

## 分页、统计与结果核验

- 分页只使用当前 arguments 中允许的字段，遵守默认值/最小值/最大值；不同数据源不一定支持分页。
- 每页检查外层错误和业务 `errors`。有部分错误时，标明哪些结果受影响，不能据此下“全部正常”“总共 N 条”的结论。
- 需要全量时保持过滤、字段、排序范围一致，按实际分页机制继续。优先使用服务端明确的 total/终止信号；没有终止标记时，只有确认页语义后才可依据短页/空页判断，并声明动态数据可能变化。
- 使用可用主键检查重复、缺页或多页无进展；不要无限翻页。不可分页、超时或预算不足时，明确只覆盖已取到的范围。
- `rows_returned` 是返回行数，不自动代表筛选全集总数。首个 5 条样本不能回答“所有服务里有多少”。服务端未提供聚合时，仅在完整取回授权且用户指定的集合后本地计算，并注明口径。
- 空记录先检查对象拼写、时间/环境、参数含义和实际授权目录；不要删除用户指定条件来制造结果。纠正条件或查询相邻数据集时，说明范围发生了什么变化。
- 引用优先使用实际 record_references；为空时用数据集、过滤条件和主键说明来源，不拼接平台 URL。
