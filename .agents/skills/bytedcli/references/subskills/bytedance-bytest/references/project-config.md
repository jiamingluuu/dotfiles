# ByteTest 项目级缺省配置模板

在仓库根目录放置 `.bytest/config.json`，`bytest task` 命令会自动读取其中的缺省值，省去每次重复传 `--biz` 和完整 create body。**显式 CLI flag 始终优先于配置文件。**

## 模板

`.bytest/config.json`：

```json
{
  "biz": 1,
  "createParamsFile": ".bytest/task.json"
}
```

或把完整 create body 直接内联（与 `createParamsFile` 二选一）：

```json
{
  "biz": 1,
  "createParams": {
    "biz": 1,
    "template_id": 123,
    "name": "demo-task",
    "app": { "url": "https://example.com/demo-app.ipa" },
    "run_param_map": { "demo_key": "demo_value" }
  }
}
```

配套的 create body 文件 `.bytest/task.json`（被 `createParamsFile` 引用）只放完整请求体：

```json
{
  "biz": 1,
  "template_id": 123,
  "name": "demo-task",
  "app": { "url": "https://example.com/demo-app.ipa" },
  "run_param_map": { "demo_key": "demo_value" }
}
```

## 字段说明

| 字段 | 类型 | 作用 |
|------|------|------|
| `biz` | number | `bytest task list` 的缺省业务线 id，省去 `--biz` |
| `createParamsFile` | string | `bytest task create` 缺省请求体文件路径（相对仓库根目录） |
| `createParams` | object | `bytest task create` 缺省请求体（内联；与 `createParamsFile` 二选一） |

## 解析优先级

- **create body**：`--params` / `--params-file` → `createParams` → `createParamsFile` → 约定文件 `.bytest/task.json`（存在即用） → 报错。
- **`--biz`（list）**：`--biz` → `config.biz` → 报错。

## 使用

```bash
# 复制模板后填入真实值
cp .bytest/config.example.json .bytest/config.json

# 配置生效后：
bytedcli bytest task list                 # 用 config.biz，无需 --biz
bytedcli bytest task create --dry-run      # 用 config 的 create body 预览
bytedcli bytest task create --yes          # 用 config 的 create body 创建
```

> 提示：`.bytest/` 是项目本地目录，请勿把含真实 app 包地址、业务 id 的 `config.json` / `task.json` 提交到公共仓库。可先对已有任务跑 `bytedcli bytest task get --id <id> -j` 参考真实字段结构。
