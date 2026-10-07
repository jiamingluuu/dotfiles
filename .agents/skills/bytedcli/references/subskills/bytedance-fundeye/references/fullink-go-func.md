# Fullink Go 函数生成指南

用于生成符合 Fullink 平台规范的 Go 函数代码。

## 最重要的规则

### 1. 不要写 `package`

不要输出 `package main` 或任何 `package` 语句。

### 2. 不要 import 已预导入包

以下包平台已自动注入，写到 import 里会触发 `redeclared` 编译错误：

- `encoding/json`
- `fmt`
- `strings`
- `sort`
- `time`
- `strconv`
- `github.com/bytedance/sonic`
- `github.com/shopspring/decimal`
- `code.byted.org/ies_fund_eye/fund_eye_common/math/fraction`
- `github.com/pkg/errors`
- `code.byted.org/pipo/toolbox/identity`
- `github.com/xeipuuv/gojsonschema`
- `fund_eye/util/udf`
- `code.byted.org/ies_fund_eye/fund_eye_common/component`
- `fund_eye/log`
- `fund_eye/fetcher/rpc`
- `fund_eye/fetcher/tcc`
- `fund_eye/fetcher/redis`
- `fund_eye/fetcher/abase`
- `fund_eye/fetcher/metrics`

这些包只能直接用，不能 import。

### 3. 日志只能用 `log.Info`

不要使用：

- `log.Warn`
- `log.Error`
- `log.Debug`

## 只支持两种入参类型

- `map[string]interface{}`
- `string`

如果用户不确定：

- 字段少、结构浅 → 推荐 `map[string]interface{}`
- 字段多、嵌套复杂 → 推荐 `string`

## 支持的函数场景

### 1. 筛选条件：`Filter`

```go
func Filter(data map[string]interface{}) (bool, error) {
    return true, nil
}
```

```go
func Filter(data string) (bool, error) {
    return true, nil
}
```

### 2. 关联键：`Generate`

```go
func Generate(data map[string]interface{}) (string, error) {
    return "", nil
}
```

```go
func Generate(data string) (string, error) {
    return "", nil
}
```

### 3. 双参数核对：`Verify`

```go
func Verify(up, down map[string]interface{}) (bool, error) {
    return true, nil
}
```

```go
func Verify(up, down string) (bool, error) {
    return true, nil
}
```

### 4. 聚合核对：`Verify`

```go
func Verify(up map[string]interface{}, down []map[string]interface{}) (bool, error) {
    return true, nil
}
```

```go
func Verify(up string, down []string) (bool, error) {
    return true, nil
}
```

### 5. 单流核对：`Verify`

```go
func Verify(record map[string]interface{}) (bool, error) {
    return true, nil
}
```

```go
func Verify(record string) (bool, error) {
    return true, nil
}
```

## 生成步骤

1. 先确认函数场景
2. 再确认入参类型
3. 再确认业务逻辑
4. 如果用户提到主动查数，再读 `references/external-apis.md`
5. 生成代码
6. 交付前必须跑编译检查

## map 模式取值

```go
func Filter(data map[string]interface{}) (bool, error) {
    name, ok := data["name"].(string)
    if !ok {
        return false, fmt.Errorf("field 'name' is not a string")
    }
    amount, ok := data["amount"].(float64)
    if !ok {
        return false, fmt.Errorf("field 'amount' is not a number")
    }
    log.Info(fmt.Sprintf("name=%s amount=%v", name, amount))
    return true, nil
}
```

## string 模式解析

```go
func Filter(data string) (bool, error) {
    type Record struct {
        Name   string  `json:"name"`
        Amount float64 `json:"amount"`
    }

    var record Record
    if err := sonic.UnmarshalString(data, &record); err != nil {
        return false, fmt.Errorf("failed to parse data: %w", err)
    }
    return true, nil
}
```

## 金额比较

优先使用已预导入的 `decimal`。

```go
func Verify(up, down map[string]interface{}) (bool, error) {
    upAmount, _ := up["amount"].(float64)
    downAmount, _ := down["amount"].(float64)
    upDec := decimal.NewFromFloat(upAmount)
    downDec := decimal.NewFromFloat(downAmount)
    return upDec.Equal(downDec), nil
}
```

## 关联键拼接

```go
func Generate(data map[string]interface{}) (string, error) {
    orderNo, _ := data["order_no"].(string)
    bizType, _ := data["biz_type"].(string)
    return fmt.Sprintf("%s_%s", orderNo, bizType), nil
}
```

## 编译检查

交付前必须先进入当前 skill 目录执行：

```bash
node -r ts-node/register/transpile-only scripts/compile_check.ts \
  --script "func Verify(up map[string]interface{}, down map[string]interface{}) (bool, error) { return true, nil }" \
  --param-types "map[string]interface{}" "map[string]interface{}" \
  --func-name "Verify"
```

如果返回 `data.ok = false`，必须根据 `data.error` 自动修正代码并重新检查，直到通过。
