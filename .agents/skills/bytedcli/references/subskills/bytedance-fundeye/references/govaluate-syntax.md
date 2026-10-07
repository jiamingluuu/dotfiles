# Govaluate 基础语法

## 类型系统

govaluate 只有 4 类值：

- `float64`
- `bool`
- `string`
- `array`

数字字面量默认都是 `float64`。

## 常用运算符

### 比较

- `==`
- `!=`
- `>`
- `>=`
- `<`
- `<=`
- `=~`
- `!~`
- `in`
- `not in`
- `between`

### 逻辑

- `&&`
- `||`

### 算术

- `+`
- `-`
- `*`
- `/`
- `%`
- `**`

### 前缀

- `-`
- `!`
- `~`

### 三元

```javascript
condition ? value_if_true : value_if_false
```

## 常见模式

### 集合判断

```javascript
status in (1, 2, 3)
status not in (1, 2, 3)
```

### 范围判断

```javascript
amount between (100, 500)
```

### 正则匹配

```javascript
name =~ '^order_.*'
name !~ 'test'
```

### 判空

```javascript
field == nil
field == null
```

### Binlog 状态流转

```javascript
before__status == 'Init' &&
status == 'Success'
```

## 关键注意事项

- 日期字符串不要直接比较，统一先转时间戳
- 金额和浮点比较统一走 `float2i64`
- `+` 在任一侧为字符串时是拼接，不是数值加法
- `between` 左右边界都包含
- `in` / `not in` 的右侧必须是数组形式，如 `(1, 2, 3)`
