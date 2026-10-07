# FundEye Govaluate UDF 函数参考

## 1. JSON 取数

统一使用路径语法，不要使用 `jpath2`。

### 基础路径

```javascript
extra.order_id
list.[0].name
list.[0].record.content.down
```

### 数组过滤

```javascript
list.[?name="fullink"].[0].level
list.[?level>2].[0].name
len(list.[?name="fullink"]) == 1
```

### Map / List 值提取

```javascript
"dou1" in anchor_room_id.[?values()]
"a1" in anchor_array.[?values()]
```

## 2. 精度处理

### float2i64(origin, retain)

将浮点数扩大 `10^retain` 后取整，金额比较必须优先使用。

```javascript
float2i64(up.amount, 2) == float2i64(down.amount, 2)
float2i64(amount, 2) > float2i64(100, 2)
```

## 3. 类型转换

### isNumberStr(str)

判断字符串是否是合法数字。

```javascript
isNumberStr(order_amount)
```

### toStr(any) / d2str(number)

转字符串。

```javascript
toStr(user_id)
d2str(uid)
```

### str2d(str) / str2f(str)

字符串转数字。

```javascript
str2d(order_id) > 0
str2f(rate) > 0.1
```

## 4. 字符串处理

### strLen(str)

```javascript
strLen(order_id) > 10
```

### substr(string, startIndex, endIndex)

左闭右开。

```javascript
substr(order_id, 0, 3) == 'ord'
```

### split(string, splitstr, index)

```javascript
split(biz_key, '#', 1) == 'trade'
```

### contains(string, substr)

```javascript
contains(scene_name, 'fund')
```

## 5. 时间函数

所有时间函数都返回 unix 时间戳（秒）。

### str2time

适用于 `2022-03-22 12:01:22`

```javascript
up.expire_time == str2time(down.expire_date)
```

### strWithT2time

适用于 `2022-03-22T12:01:22`

```javascript
strWithT2time(expire_time)
```

### strWithTZ2time

适用于 `2022-03-22T12:01:22Z`

```javascript
strWithTZ2time(expire_time)
```

### nowUnixSeconds

```javascript
nowUnixSeconds() - str2time(create_time) > 300
```

## 6. 其他函数

### len(object)

支持数组、map、字符串。

```javascript
len(items) > 0
len(ext) >= 2
```

### sample(field, rate)

按万分制抽样。

- `10000` = 100%
- `5000` = 50%
- `1000` = 10%

```javascript
sample(order_id, 5000) && status == 'PAY_SUCCESS'
```

双数据源场景中，上下游必须对同一维度字段抽样。

### 判空

优先使用 `nil` 或 `null`。

```javascript
field == nil
field == null
```

### IsSandboxAccount(uid)

```javascript
!IsSandboxAccount(uid)
```
