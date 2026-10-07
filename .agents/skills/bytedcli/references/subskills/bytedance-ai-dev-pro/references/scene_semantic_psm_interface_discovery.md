# 场景：语义定位服务 PSM 及接口

本文件用于指导 agent 在**仅有业务语义描述、尚不知道具体 PSM** 时，通过 `bytedcli ai-dev-pro afs` 先定位候选服务 PSM，再在候选服务内定位接口。只有当用户需要接口出入参信息，或需要根据出入参进一步筛选接口时，才继续查询接口参数。

本文只列出语义定位服务与接口场景下的关键参数与推荐组合；完整参数、枚举值和最新说明以对应命令的 `--help` 输出为准。

## 场景描述：根据语义定位服务 PSM 及该服务下的接口

**适用对象**：用户没有提供明确 PSM、method ID 或代码实体 ID，只能通过自然语言描述业务能力、产品功能或实现意图来探索相关服务和接口。

例如：

- “帮我找一下负责创建订单的服务和接口”
- “我想找处理广告点击回传的服务，以及对应的接口”
- “查一下哪个服务负责库存查询，再看下接口入参出参”
- “根据‘商家计划审核’这个语义定位相关服务和接口”

**不适用对象**：

- 用户明确已经给出 PSM，只需要在该服务内找接口。此时可跳过 PSM 发现步骤，直接使用 `interface search --psm ...` 或加载 [scene_interface_discovery.md](scene_interface_discovery.md)。
- 用户明确是在找接口、接口方法或接口入参出参，而不是先寻找服务/PSM。此时优先加载 [scene_interface_discovery.md](scene_interface_discovery.md)。
- 用户已经给出 method ID 或代码实体 ID，应直接使用对应 ID 查询类命令，不要重复做语义服务发现。

**执行逻辑**：

1. **语义检索候选 PSM**：根据业务语义寻找可能承载该能力的服务。
2. **读取 PSM 服务摘要**：获取候选服务的详细功能摘要，用于人工或机器精筛。
3. **在选定 PSM 内语义检索接口**：限定 PSM 范围后，根据接口功能描述定位具体方法。
4. **按需获取接口参数**：仅当用户意图表现出需要接口出入参信息，或需要根据出入参进一步筛选接口时，才根据 `psm + method_name` 或 `psm + method_id` 查询接口描述、请求参数、响应参数与 IDL 路径。

---

## 1. 根据业务语义检索候选 PSM

### 功能说明

根据服务职责、业务功能或产品语义进行全局 PSM 检索，按照相关度返回候选 PSM 及其摘要信息。此步骤用于回答“哪个服务可能负责这个能力”。

### bytedcli 指令

```bash
bytedcli ai-dev-pro afs psm search --q "订单创建" --limit 3
```

### 入参说明

| 参数名    | 类型   | 是否必填 | 示例值     | 描述                                 |
| :-------- | :----- | :------- | :--------- | :----------------------------------- |
| `--q`     | string | 是       | `"下单"` | PSM 的描述信息或关键字，用于语义匹配。 |
| `--limit` | int    | 否       | `3`        | 返回的 PSM 数量。                    |

### 返参说明

返回候选 PSM 列表。结果通常包含：

| 字段           | 说明                                  |
| :------------- | :------------------------------------ |
| `Summary`      | PSM 的摘要信息，用于理解服务主要职责。 |
| `Metadata.psm` | 服务的 PSM 名称。                     |
| `Metadata._score` | 检索相关度分数。                  |

---

## 2. 查询候选 PSM 的服务摘要

### 功能说明

根据上一步拿到的候选 PSM，进一步读取服务摘要，用于判断该服务是否真的承载用户描述的业务能力。若候选 PSM 较多，可批量查询后对比职责边界。

### bytedcli 指令

查询单个 PSM 的详细摘要：

```bash
bytedcli ai-dev-pro afs psm summary get --psm example.order.core --type 2
```

批量查询多个候选 PSM：

```bash
bytedcli ai-dev-pro afs psm summary get --psm example.order.core,example.order.gateway --type 2
```

### 入参说明

| 参数名   | 类型         | 是否必填 | 示例值                                      | 描述                                                     |
| :------- | :----------- | :------- | :------------------------------------------ | :------------------------------------------------------- |
| `--psm`  | list<string> | 是       | `example.order.core,example.order.gateway` | 要查询的 PSM，多个值之间逗号分隔。                       |
| `--type` | int          | 否       | `2`                                         | 摘要类型。`2` 表示详细功能描述，`3` 表示简略描述。       |

### 返参说明

返回 PSM 的详细摘要或简略摘要，通常用于确认服务职责、业务边界、是否适合作为下一步接口检索范围。

---

## 3. 在选定 PSM 内语义检索接口

### 功能说明

在确认候选服务后，将接口检索限定在该 PSM 范围内，根据接口功能的自然语言描述检索具体方法。此步骤用于回答“这个服务里的哪个接口实现该能力”。

### bytedcli 指令

```bash
bytedcli ai-dev-pro afs interface search --method-desc "创建订单" --psm example.order.core --limit 3
```

### 入参说明

| 参数名          | 类型         | 是否必填 | 示例值               | 描述                                         |
| :-------------- | :----------- | :------- | :------------------- | :------------------------------------------- |
| `--method-desc` | string       | 是       | `"下单"`           | 接口功能描述，用于语义匹配。                 |
| `--psm`         | list<string> | 否       | `example.order.core` | 限定接口检索范围的 PSM，多个值之间逗号分隔。 |
| `--limit`       | int          | 否       | `3`                  | 返回接口数量。                               |

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

## 4. 按需获取接口参数

### 功能说明

在定位到具体 PSM 与接口后，默认可以先向用户返回候选服务、接口名称、method ID 与接口摘要。只有当用户明确需要查看接口入参出参、需要确认请求/响应字段，或需要根据参数结构继续筛选接口时，才查询该接口在 BAM 上登记的方法名、接口描述、请求参数、响应参数，以及对应 IDL 仓库与路径信息。

### bytedcli 指令

按方法名查询：

```bash
bytedcli ai-dev-pro afs interface param get --psm example.order.core --method-name CreateOrder
```

按方法 ID 查询：

```bash
bytedcli ai-dev-pro afs interface param get --psm example.order.core --method-id 13893661
```

### 入参说明

| 参数名          | 类型   | 是否必填 | 示例值               | 描述                     |
| :-------------- | :----- | :------- | :------------------- | :----------------------- |
| `--psm`         | string | 是       | `example.order.core` | 服务 PSM。               |
| `--method-name` | string | 否       | `CreateOrder`        | 接口方法名或 HTTP path。 |
| `--method-id`   | string | 否       | `13893661`           | 接口方法 ID。            |

### 返参说明

返回接口描述、请求参数、响应参数以及 IDL 路径信息。常见字段包括：

| 字段                            | 说明                                           |
| :------------------------------ | :--------------------------------------------- |
| `idl_repo`                      | IDL 仓库地址。                                 |
| `idl_path`                      | IDL 文件路径列表，第一个通常优先为主入口 IDL。 |
| `Children[bam].content`         | BAM 上登记的接口方法名。                       |
| `Children[bam].summary`         | 接口描述。                                     |
| `Children[bam].request_params`  | 请求参数列表。                                 |
| `Children[bam].response_params` | 响应参数列表。                                 |

---

## 使用路径示例

### 场景 1：用户只描述业务能力，需要同时定位服务和接口

用户 query：**“帮我找一下负责创建订单的服务和接口”**

1. **Step 1: 发现候选服务**

   ```bash
   bytedcli ai-dev-pro afs psm search --q "创建订单" --limit 3
   ```

   产出：获得候选 PSM 列表和摘要信息。

2. **Step 2: 确认服务职责**

   假设候选 PSM 包含 `example.order.core` 和 `example.order.gateway`，执行：

   ```bash
   bytedcli ai-dev-pro afs psm summary get --psm example.order.core,example.order.gateway --type 2
   ```

   产出：对比服务摘要，选择更可能承载“创建订单”能力的 PSM。

3. **Step 3: 在选定 PSM 内定位接口**

   ```bash
   bytedcli ai-dev-pro afs interface search --method-desc "创建订单" --psm example.order.core --limit 3
   ```

   产出：获得候选接口名称、method ID 与接口摘要。

4. **Step 4: 按需查询接口参数**

   如果用户还需要接口出入参，或需要根据出入参判断接口是否匹配，再继续查询。假设已定位到 `method_name = CreateOrder`，执行：


   ```bash
   bytedcli ai-dev-pro afs interface param get --psm example.order.core --method-name CreateOrder
   ```

产出：返回接口描述、请求参数、响应参数以及 IDL 路径。

### 场景 2：用户描述业务链路，服务候选不唯一

用户 query：**“我想找处理广告点击回传的服务，以及对应的接口”**

1. **Step 1: 用多个同义表达检索服务**

   ```bash
   bytedcli ai-dev-pro afs psm search --q "广告点击回传" --limit 5
   ```

   如果结果不理想，可改写 query，例如“点击事件上报”“广告转化回传”“广告行为回调”。

2. **Step 2: 读取候选服务摘要**

   ```bash
   bytedcli ai-dev-pro afs psm summary get --psm example.ad.callback,example.ad.event --type 2
   ```

   产出：判断哪个 PSM 更符合“点击回传”的职责。

3. **Step 3: 在目标 PSM 内找接口**

   ```bash
   bytedcli ai-dev-pro afs interface search --method-desc "回传点击数据" --psm example.ad.callback --limit 3
   ```

4. **Step 4: 按需查询接口参数**

   仅当用户需要接口出入参，或需要根据出入参进一步筛选接口时执行：

   ```bash
   bytedcli ai-dev-pro afs interface param get --psm example.ad.callback --method-name SendClickEvent
   ```

---

## 注意事项

- 本 scene 的核心差异是**先做 PSM 语义发现与摘要确认**，再进入接口检索；如果用户已经明确 PSM 或只问接口，优先加载 [scene_interface_discovery.md](scene_interface_discovery.md)。
- `psm search` 用于召回候选服务，结果为空或相关度低时，应改写 query、提取关键词或扩展同义表达后重试。
- `psm summary get --type 2` 更适合精筛服务职责；若只需要快速浏览，可尝试 `--type 3`。
- `interface search` 在本 scene 中应尽量带 `--psm`，避免又退回全局接口检索，导致服务定位步骤失去意义。
- 查询接口参数不是本 scene 的必选步骤。只有当用户需要接口出入参信息，或需要根据出入参进一步筛选接口时，才调用 `interface param get`；调用时必须传 `--psm`，再配合 `--method-name` 或 `--method-id` 定位具体接口。
