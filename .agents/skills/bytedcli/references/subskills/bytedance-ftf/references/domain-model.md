# FTF 领域背景(L0 共享模型)

> 本文件收录 FTF diff 分析中**复用度 ≥2** 的共享背景:术语、录制回放模型、
> 任务形态、证据可见性。单一主题专属的背景内联在对应 L1 文件,不在这里。
> 引用方式:在编排层 / L1 / L2 中写 "术语见 domain-model#术语与表达规范"
> 这类锚点,不要复制本文件内容。

## 术语与表达规范

面向用户的报告统一使用"译法"列的说法,不要在正文直接写内部字段名。

| 内部字段 | 用户可读译法 | 维度 |
| --- | --- | --- |
| `total_diff_count` | 总 diff 流量数 | task 级 · 流量 |
| `noise_count` | 标记为噪音的流量数 | task 级 · 流量 |
| `need_confirm_count` | 待确认的 diff 流量数 | task 级 · 流量 |
| `logCount` / `log_count` | 命中流量数 | cluster 级 · 流量 |
| `diffCount` / `diff_count` | 累计 diff 明细条数 | 明细 · 非流量数 |
| `aggregate` | 汇总统计(任务 / PSM / 接口) | 聚合 |
| `diff cluster` / `cluster` | diff 聚类 | — |
| `top cluster` | Top diff 聚类 | — |
| `similarDiffId` | 正文不用;改用 method + diff path + 方向 + 样本值 + 链接 | — |

**必读辨析(极易搞反):**

1. `diffCount`(累计 diff 明细条数)是**字段级差异条数**,一条流量里的数组
   diff 会被元素数量放大,**不等于流量数**;判断影响面优先看"命中流量数"。
2. `total_diff_count`(task 级)≠ `logCount`(cluster 级),层级不同,不可混用。
3. `total_diff_count` / `noise_count` / `need_confirm_count` 都是 task 级流量
   计数,同一维度,可互相比较。

## 录制回放与 mock 边界

- FTF 对比 **base**(录制 / 线上基线)与 **replay**(回放 / 被测)两侧响应,产出 diff。
- **record**:一条被采集的流量样本,含 inbound 请求 / 响应,以及可选的 outbound 调用。
- **inbound**:被测服务对外提供的接口方向(它收到的请求 + 它返回的响应)。
- **outbound**:被测服务作为调用方发起的下游调用;回放时下游通常被 mock。
- **mock**:回放侧用录制的下游响应替代真实下游。命中 = 找到匹配的录制响应;
  未命中 = 找不到,回放走了真实下游或报错。
- diff 只在能对齐的字段上产生。对不齐(如 mock 未命中)通常表现为结构性差异
  或错误,而不是普通字段 diff。

## 任务形态判定(系统级 / 沙箱 / 混合)

判定依据顶层 `env`、`replay_env`、`mock_enable`(及任何冲突字段),三者需一并列出。

| 形态 | 特征 | outbound 期待 |
| --- | --- | --- |
| 系统级 | 对线上 / 线上镜像流量回放,一般不注入 mock,outbound 走真实下游 | **不期待 outbound diff**;聚焦 inbound 响应差异 |
| 沙箱 | 隔离环境回放,outbound 被 mock | 重点看 outbound request diff、mock 匹配状态、logid 错误 |
| 混合 / 不确定 | 判定字段冲突或缺失 | 按沙箱口径保守查 outbound,并在报告标注"形态不确定" |

## 采集源与证据可见性边界

outbound 证据是否可见,由三个条件共同决定,**任一缺失都只能得出"当前结果缺少
outbound 证据",不能断言"没有 outbound 问题"**:

1. **任务形态**——该不该有(见上一节)。
2. **采集源**——有没有采到:
   - `bytecopy` 采集通常**不含完整 outbound**,即使是沙箱形态也可能无 outbound 可下钻;
   - `sdk` 采集才适合下钻 outbound mock。
3. **结果展示**——看不看得到:未在任务结果 / 日志里出现的,一律不算已确认。

**外部待验证原则**:采集源、FTF 产物启动状态、组件支持、context 透传等前提,
只有在任务结果 / 日志中明确出现才作为已确认事实;否则一律列为"外部待验证项",
不要写成结论。inbound 证据一般可见;outbound 证据受上述三重条件约束。
