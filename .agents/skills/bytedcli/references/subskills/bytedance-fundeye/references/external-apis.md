# Fullink 外部接口参考

Fullink 平台内置了主动查数客户端，直接使用即可，不需要 import。

## 1. TCC

### 方法

- `tcc.Get(psm, key string)`
- `tcc.GetWithNamespace(psm, namespace, key string)`

### 示例

```go
func Filter(data map[string]interface{}) (bool, error) {
    resp, err := tcc.GetWithNamespace("toutiao.author.tip_settlement", "activity", "activity_25")
    if err != nil {
        return false, err
    }
    log.Info(resp)
    return true, nil
}
```

## 2. RPC

推荐统一使用：

- `rpc.CallJsonWithEnv(psm, method, cluster, env, params string)`

### 示例

```go
func Verify(up, down string) (bool, error) {
    req := `{"Base":{"Extra":{"env":"prod"}},"diffIDList":["a"],"operator":"he","remark":""}`
    resp, err := rpc.CallJsonWithEnv("fund_eye.fullink.check_result", "BatchManualRetryCheck", "default", "", req)
    if err != nil {
        return false, err
    }
    log.Info(fmt.Sprintf("rpc resp: %s", resp))
    return true, nil
}
```

## 3. Redis

### 方法

- `redis.Command(psm, methodAndParams string)`
- `redis.Get(psm, key string)`
- `redis.HGet(psm, key, field string)`
- `redis.ZRange(psm, key string, start, end int64)`

### 示例

```go
func Verify(record map[string]interface{}) (bool, error) {
    key, ok := record["order_no"].(string)
    if !ok {
        return false, fmt.Errorf("field 'order_no' is not a string")
    }
    val, err := redis.Get("toutiao.redis.fullink_manage", key)
    if err != nil {
        return false, err
    }
    log.Info(fmt.Sprintf("redis val: %s", val))
    return val != "", nil
}
```

## 4. Abase

### 方法

- `abase.Command(psm, methodAndParams string)`
- `abase.Get(psm, key string)`
- `abase.HGet(psm, key, field string)`

注意：key 需要写成 `[表名]key` 格式。

```go
val, err := abase.Get("toutiao.redis.fullink_manage", "[sandbox]test_get")
```

## 5. Metrics

常见方法：

- `metrics.EmitCounter`
- `metrics.EmitRateCounter`
- `metrics.EmitMeter`
- `metrics.EmitTimer`
- `metrics.EmitStore`

### 示例

```go
func Verify(record map[string]interface{}) (bool, error) {
    kv := map[string]string{
        "channel": "demo",
        "status":  "ok",
    }
    if err := metrics.EmitCounter("sample_counter_metric", kv, 1); err != nil {
        return false, err
    }
    return true, nil
}
```

## 通用注意事项

- 这些客户端都不需要 import
- 不要用 `fmt.Println` 作为调试方式，优先用 `log.Info`
- 所有外部调用都要做 error 处理
- RPC 有 QPS 限流
