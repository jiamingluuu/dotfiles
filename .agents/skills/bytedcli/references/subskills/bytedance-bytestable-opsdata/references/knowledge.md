# 知识检索、原文与证据

## RAG：发现语义相关片段

使用 `rag search --dataset NAME --query TEXT --limit 3`。查询包含关键实体、问题和必要场景，避免堆砌无关关键词。filters 只能使用 `retrieval.rag.filter_tags` 中公开的名字、类型和操作符；日期遵守其 format/timezone。

简单筛选可以使用 `--filters`。筛选 JSON 较长、需要多行或由 Agent 生成时，优先写入文件并使用 `--filters-file`，避免 shell 引号和转义错误；两个参数不能同时使用。

AST 叶子为 `{field,op,values}`，组合为 `{and:[...]}` / `{or:[...]}`。只有契约明确声明相应字段和操作符后才能用，例如：

```bash
bytedcli --as user --json bytestable opsdata rag search --dataset '<dataset_en_name_from_dataset_list>' \
  --query '服务超时的排查步骤' \
  --filters '{"field":"service","op":"eq","values":["example.service.api"]}' --limit 3
```

复杂筛选示例：

```bash
cat > /tmp/opsdata-filters.json <<'JSON'
{
  "field": "service",
  "op": "eq",
  "values": ["example.service.api"]
}
JSON
bytedcli --as user --json bytestable opsdata rag search --dataset '<dataset_en_name_from_dataset_list>' \
  --query '服务超时的排查步骤' \
  --filters-file /tmp/opsdata-filters.json --limit 3
```

`rag: {}` 表示可以检索，但没有公开筛选标签；此时省略 filters，不猜字段。
命中 content 可能是 JSON 包装，先解析并检查实际 markdown/text。只有标题、元数据或空白正文不足以支撑内容性结论。分数只用于同类结果的相对参考，不设置跨数据集/提供方统一可信阈值。保留命中中实际的来源链接（包括 tags 中的原文链接），不把 doc_id 当成 URL。

## OpenViking：定位、缩小范围、读取

OpenViking 的四个接口各自负责一个环节：

| 接口              | 什么时候用                             | 下一步                                       |
| ----------------- | -------------------------------------- | -------------------------------------------- |
| `document search` | 不知道文档位置，按自然语言找相关内容   | 对高相关命中的返回路径执行 `document read`   |
| `document list`   | 已知数据集或目录，需要浏览和缩小范围   | 继续 list 子目录，或依据 `grep_allowed` grep |
| `document grep`   | 已知错误码、配置项、字段名或精确短语   | 对命中文档执行 `document read`               |
| `document read`   | 已有服务端返回的文件路径，需要正文证据 | 回答，或按 `next_offset` 读取相邻上下文      |

### 未知文档位置：search → read

语义发现用 `document search --paths DATASET --query TEXT --limit 3`。query 同时包含稳定实体和问题意图，例如 PSM + 现象；不要只堆关键词。数据集根可从 en_name 构造，子路径必须从 search/list 响应中发现。先读取最相关的 1–3 个返回路径，证据不足再改写一次 query 或扩大候选数，不要一开始读取大量文件。

找到相关文档后用 `document read --paths RETURNED_PATH --offset 1 --limit 80` 核对正文。引用实际 source_url；无链接时以虚拟路径和行范围说明来源。按每篇文档的 has_more/next_offset 继续读取相关段落；has_more=true 但 next_offset 不推进等矛盾要报告，不能无限读取。不要默认 `--limit -1`，只在确实需要全文且规模合适时使用。

### 已知精确词：list → grep → read

1. `document list --paths DATASET --limit 20`，从返回目录进入相关子目录。
2. 对**实际要 grep 的每个范围**查看 `grep_allowed`、`estimated_entry_count`、`count_complete` 及建议。只有该范围 `grep_allowed=true` 才 grep；未知或 false 就继续 list 缩小或改语义搜索。多范围最好分别执行，避免组合范围超限。
3. 执行 `document grep --paths RETURNED_NARROW_PATH --pattern 'timeout' --limit 5`；pattern 适合错误码、配置项、字段名、日志短语等稳定字面值。这是精确文本匹配，不假设支持正则表达式或分词语义。
4. 对命中文件 read，获取足够上下文。

服务端会拒绝覆盖条目估计超过 100 或无法确定的 grep。直接使用其计数/许可，不累加子目录估算；父目录许可不能推导子目录也许可。计数与条目明显矛盾时重新 list 更小范围，不强行扫描。拒绝可能作为 executed=false 和 recommendations 返回，被 CLI 转为结构化错误；这不是“未匹配”。

### 调用与证据原则

- search 命中片段用于发现，最终内容性结论优先以 read 的正文和来源为证据。
- list 是路径发现与范围控制，不代表内容命中；grep 是字面匹配，不代表语义相关或因果关系。
- 一次 read 最多 3 个路径。优先分别读取并保留每篇文档的来源，避免把多篇内容混成一个无法追溯的结论。
- 同一问题不要机械执行 search、list、grep 全套。未知位置走 search；已知目录和精确词才走 list/grep；两条路径最终都在需要正文时汇合到 read。
- 排查现场事实应来自结构化记录或其他实时数据；OpenViking 文档用于解释机制、步骤和历史经验。用 PSM、环境、事件 ID、错误码等标识关联两类证据，并明确时间差。

## 没有有效证据时

先区分：真正空集、过滤/范围错误、索引或正文质量不足、权限/工具失败。

- 语义结果不相关：保留实体，改写一次问题或换一个更具体概念。
- RAG 命中为空正文：若数据集有 openviking，可搜索/list 定位同主题文档并 read；不能把飞书链接直接传给 document read。
- OpenViking 空集：根据目录相关性 list 缩小范围，或切换该数据集确实支持的 RAG。
- 无可用能力/无授权数据集：报告当前范围无法回答，不访问猜测出来的未授权路径。
- 查到互相冲突或过时的资料：优先考虑明确更新时间、对象一致性和原始资料，列出不能消除的冲突。

结论必须来自有效正文。知识检索的 top-k 和局部目录搜索都不是穷尽证明；措辞用“在本次检索范围内未找到有效证据”，不要用“该功能不存在”。
