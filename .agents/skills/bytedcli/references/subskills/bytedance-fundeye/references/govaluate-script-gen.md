# FundEye Govaluate 脚本生成工作流

这个参考只覆盖 `govaluate` 表达式脚本，不覆盖 Go/Yaegi 核对脚本。

## 何时使用

- 用户提到 `govaluate`
- 用户要写筛选条件、过滤表达式、join 条件、核对表达式
- 用户说“帮我配个规则”“帮我写个核对条件”“帮我写状态流转条件”
- 用户描述 Binlog 变更，例如“从 A 变成 B”“变化前后”“before__”

## 先分场景

### 1. 单数据源筛选

字段直接使用，不加前缀。

```javascript
biz_scene in (117, 118, 119) && status == 'INIT'
```

### 2. 双数据源核对

字段通过 `up.` 和 `down.` 区分。

```javascript
up.trade_amount == down.trade_amount &&
up.from_uid == down.from_uid &&
up.to_uid == down.to_uid
```

### 3. Binlog 变更

同一条记录同时包含变更前和变更后字段。变更前字段统一加 `before__` 前缀。

```javascript
before__status == 'Init' &&
status == 'Success'
```

## 多轮对话策略

每轮只收集 1 到 2 个关键信息，不要一次问太多。

### 第 1 轮：定场景

- 提到“上下游”“对比”“核对” → 双数据源
- 提到“筛选”“过滤”“条件” → 单数据源
- 提到“binlog”“变更”“状态从 A 到 B”“before__” → Binlog 变更
- 如果不确定，直接问用户

优先让用户提供：

- 字段列表，或
- JSON 样例，或
- 上下游各 1 条示例数据

### 第 2 轮：补细节

根据场景继续确认：

- 单数据源：哪些字段、什么条件、是否需要抽样
- 双数据源：哪些字段需要对比、字段名是否一致、是否涉及金额/时间/嵌套 JSON
- Binlog：哪些字段要看变化、变化前后的目标值、是否只关心“发生变化”

### 第 3 轮：生成脚本

输出：

- 完整脚本
- 逐条中文解释

注意：脚本代码块语言标识统一用 `javascript`，但代码块里不能写注释。

### 第 4 轮：编译检查

交付前必须先进入当前 skill 目录执行：

```bash
node -r ts-node/register/transpile-only scripts/check_govaluate.ts "<生成的脚本内容>"

如需走 PPE，只能通过 bytedcli 全局 `--http-header` 透传 `x-tt-env` / `x-use-ppe`；不要在脚本或命令模板里写死具体 PPE lane。
```

如果返回：

- `data.ok = true`：可以进入最终交付
- `data.ok = false`：要根据 `data.error` 修正脚本并重试，直到通过

### 第 5 轮：确认与迭代

- 编译通过后再交付给用户
- 如果用户只改一部分条件，尽量增量修改，不要整段重写

## 输出格式约束

- 代码块语言标识必须使用 `javascript`
- 代码块里不允许写注释
- 多个 `&&` 条件建议按语义换行

正确示例：

```javascript
status in (1, 2, 3) &&
amount > 100
```

## 必须遵守的避坑规则

### 日期字符串

任何日期比较都要先转时间戳：

- `str2time`
- `strWithT2time`
- `strWithTZ2time`

不要直接比较 `"2022-11-21"` 这种字符串。

### 金额与浮点精度

金额、费率、比例比较必须使用 `float2i64`，两边的保留位数要一致。

```javascript
float2i64(up.amount, 2) == float2i64(down.amount, 2)
```

### 字符串数字

需要参与数值运算时，先用：

- `str2d`
- `str2f`

### JSON 取数

统一使用路径语法：

- `a.b.c`
- `a.[0].b`
- `a.[?name="x"].[0].b`

不要使用已经废弃的 `jpath2(...)`。

### 空值防御

深层字段可能缺失时，优先提醒用户补充是否可能为空；必要时加空值保护。

### 抽样一致性

双数据源场景里，上下游必须对同一维度字段抽样。

### before__ 使用规范

- `before__` 只在 Binlog 变更场景存在
- “从 A 变为 B” → `before__field == 'A' && field == 'B'`
- “字段发生变化” → `before__field != field`

## 常用示例

### 单数据源

```javascript
sample(order_id, 5000) &&
status == 'PAY_SUCCESS'
```

### 双数据源金额核对

```javascript
float2i64(up.amount, 2) == float2i64(down.amount, 2)
```

### Binlog 状态流转

```javascript
before__status != 'Success' &&
status == 'Success'
```

## 深入参考

- UDF 函数：`references/udf_functions.md`
- 语法规则：`references/govaluate-syntax.md`
