# 场景：接口检索

本文件用于指导 agent 在**仅需检索接口**时，通过 `bytedcli ai-dev-pro afs` 完成接口发现、接口确认以及接口参数获取。

本文只列出接口检索场景下的关键参数与推荐组合；完整参数、枚举值和最新说明以对应命令的 `--help` 输出为准。

## 场景描述：仅接口检索

**适用对象**：用户的 query 明确是在寻找某个接口，而**不是**先寻找服务。

例如：

- “帮我找一下创建订单的接口”
- “有没有更新广告状态的方法”
- “在 `example.service.gateway` 里找查询库存的接口”
- “帮我看看某个接口的入参出参”

**不适用对象**：

- 用户意图是先找服务/PSM，再进一步定位接口。
- 用户没有任何接口语义，只有服务职责描述，此时应优先使用 PSM/服务发现类命令，再进入接口检索。

**执行逻辑**：

1. **语义检索接口**：根据接口功能描述直接搜索相关接口，可选限定 PSM 范围。
2. **查询 PSM 下接口做精筛**：若用户已知 PSM，或语义检索结果需进一步确认，可查询该 PSM 下接口及描述。
3. **查询接口参数**：在已定位到具体 `psm + method_name` 或 `psm + method_id` 后，查询该接口的 IDL 路径、接口描述以及请求/响应参数。

---

## 1. 根据接口描述语义检索接口

### 功能说明

根据接口功能的自然语言描述，直接语义检索相关接口。可在全局范围检索，也可限定在一个或多个 PSM 范围内检索。

### bytedcli 指令

```bash
bytedcli ai-dev-pro afs interface search --method-desc "创建订单" --limit 20
```

限定 PSM 范围：

```bash
bytedcli ai-dev-pro afs interface search --method-desc "查询库存" --psm example.service.gateway --limit 20
```

按 method ID 限定检索范围：

```bash
bytedcli ai-dev-pro afs interface search --method-desc "查询库存" --method-id 2913012 --limit 20
```

### 入参说明

| 参数名          | 类型         | 是否必填 | 示例值                    | 描述                                                    |
| :-------------- | :----------- | :------- | :------------------------ | :------------------------------------------------------ |
| `--method-desc` | string       | 是       | `"下单"`                  | 接口功能描述，用于语义匹配。                            |
| `--psm`         | list<string> | 否       | `example.service.gateway` | 限定接口检索范围的 PSM，多个值之间逗号分隔。            |
| `--method-id`   | list<string> | 否       | `2913012`                 | 方法 ID，可用于进一步约束方法范围，多个值之间逗号分隔。 |
| `--limit`       | int          | 否       | `20`                      | 返回接口数量。                                          |

### 返参说明

返回候选接口列表。结果通常包含：

| 字段                 | 说明                                 |
| :------------------- | :----------------------------------- |
| `Summary`            | 接口摘要信息，描述该方法的主要功能。 |
| `Metadata.psm`       | 接口所属服务的 PSM 名称。            |
| `Metadata.method_id` | 接口在服务内的唯一方法 ID。          |
| `Metadata.method`    | 接口的方法名称。                     |
| `Metadata._score`    | 检索相关度分数。                     |

---

## 2. 查询 PSM 下的接口及接口描述

### 功能说明

当用户已经提供明确的 PSM，或者已经通过前一步定位到候选 PSM 后，可进一步查看该 PSM 下有哪些接口及其描述，用于人工或机器精筛。

### bytedcli 指令

查询某个 PSM 下的接口列表：

```bash
bytedcli ai-dev-pro afs interface list --psm example.service.gateway
```

按方法名筛选：

```bash
bytedcli ai-dev-pro afs interface list --psm example.service.gateway --method-name UpdateAdsOptStatus
```

按方法 ID 筛选：

```bash
bytedcli ai-dev-pro afs interface list --psm example.service.gateway --method-id 13893661
```

### 入参说明

| 参数名          | 类型   | 是否必填 | 示例值                    | 描述                         |
| :-------------- | :----- | :------- | :------------------------ | :--------------------------- |
| `--psm`         | string | 是       | `example.service.gateway` | 要查询的服务 PSM。           |
| `--method-id`   | string | 否       | `13893661`                | 接口方法 ID，用于精确筛选。  |
| `--method-name` | string | 否       | `UpdateAdsOptStatus`      | 接口方法名称，用于精确筛选。 |

### 返参说明

返回指定 PSM 下的接口列表及接口描述信息，通常用于确认目标接口名称、方法 ID 与功能说明是否匹配用户意图。

---

## 3. 根据 PSM 查询 IDL 路径和接口出入参

### 功能说明

在已经确认目标接口所属 PSM 后，进一步查询该接口在 BAM 上登记的方法名、接口描述、请求参数和响应参数，以及对应 IDL 仓库与路径信息。

### bytedcli 指令

按方法名查询：

```bash
bytedcli ai-dev-pro afs interface param get --psm example.arch.knowledge_graph --method-name Sync
```

按方法 ID 查询：

```bash
bytedcli ai-dev-pro afs interface param get --psm example.arch.knowledge_graph --method-id 10889725
```

### 入参说明

| 参数名          | 类型   | 是否必填 | 示例值                         | 描述                     |
| :-------------- | :----- | :------- | :----------------------------- | :----------------------- |
| `--psm`         | string | 是       | `example.arch.knowledge_graph` | 服务 PSM。               |
| `--method-name` | string | 否       | `Sync`                         | 接口方法名或 HTTP path。 |
| `--method-id`   | string | 否       | `10889725`                     | CodeGraph 入口方法 ID。  |

### 返回字段说明

返回接口描述、请求参数、响应参数以及 IDL 路径信息。常见字段包括：

| 字段                            | 说明                                           |
| :------------------------------ | :--------------------------------------------- |
| `idl_repo`                      | IDL 仓库地址。                                 |
| `idl_path`                      | IDL 文件路径列表，第一个通常优先为主入口 IDL。 |
| `Children[bam].content`         | BAM 上登记的接口方法名。                       |
| `Children[bam].summary`         | 接口描述。                                     |
| `Children[bam].request_params`  | 请求参数列表。                                 |
| `Children[bam].response_params` | 响应参数列表。                                 |

其中 `request_params` / `response_params` 的参数对象通常包含：

- `name`：参数名
- `type`：参数类型
- `desc`：参数描述
- `optional`：是否可选
- `children`：子字段定义

---

## 使用路径示例

### 场景 1：用户只描述接口功能，不限定 PSM

用户 query：**“帮我找一下创建订单的接口”**

1. **Step 1: 语义检索接口**

   ```bash
   bytedcli ai-dev-pro afs interface search --method-desc "创建订单" --limit 20
   ```

   产出：返回候选接口列表，包含 `psm`、`method`、`method_id`、接口摘要。

2. **Step 2: 查询接口参数**

   假设已定位到：
   - `psm = example.order.core`
   - `method_name = CreateOrder`

   执行：

   ```bash
   bytedcli ai-dev-pro afs interface param get --psm example.order.core --method-name CreateOrder
   ```

   产出：返回接口描述、请求参数、响应参数以及 IDL 路径。

---

### 场景 2：用户已知 PSM，只想找该服务下的某个接口

用户 query：**“在 `example.service.gateway` 里找查询库存的接口”**

1. **Step 1: 在指定 PSM 内语义检索接口**

   ```bash
   bytedcli ai-dev-pro afs interface search --method-desc "查询库存" --psm example.service.gateway --limit 20
   ```

   产出：返回该 PSM 内与“查询库存”语义相近的候选接口。

2. **Step 2: 必要时查询 PSM 下接口进一步确认**

   若候选接口仍不够明确，可执行：

   ```bash
   bytedcli ai-dev-pro afs interface list --psm example.service.gateway
   ```

   也可以按方法名 / 方法 ID 进一步筛选。

3. **Step 3: 查询接口参数**

   在确定目标接口后，执行：

   ```bash
   bytedcli ai-dev-pro afs interface param get --psm example.service.gateway --method-name QueryStock
   ```

   产出：获取该接口在 BAM 上登记的出入参信息。

---

### 场景 3：用户已拿到 method_id，想直接看接口详情

用户 query：**“帮我看下 `example.service.gateway` 里 method_id=13893661 的接口参数”**

1. **Step 1: 先确认接口信息**

   ```bash
   bytedcli ai-dev-pro afs interface list --psm example.service.gateway --method-id 13893661
   ```

   产出：确认接口名称与描述。

2. **Step 2: 查询接口参数**

   ```bash
   bytedcli ai-dev-pro afs interface param get --psm example.service.gateway --method-id 13893661
   ```

   产出：返回方法描述、请求参数、响应参数、IDL 仓库和路径。

---

## 注意事项

- 仅接口检索时，优先使用 `interface search` 召回候选接口；已知 PSM 时可用 `--psm` 限定范围。
- `interface list` 可查询 PSM 下接口，也可用 `--method-name` 或 `--method-id` 做精确筛选；若 PSM 下接口很多，优先先用 `interface search --psm ...` 缩小范围。
- 查询接口出入参时，使用 `interface param get`，并传入 `--psm`，再配合 `--method-name` 或 `--method-id` 定位具体接口。
- 语义检索接口时，若检索结果与用户 query 的匹配度较低，应基于对 query 语义的理解，对原始描述进行适当改写、关键词提取与同义表达扩展，并视情况进行多轮补充检索，以提升接口召回与定位准确性。
