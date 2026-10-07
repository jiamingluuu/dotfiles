# DevFlow 服务部署引用文档

本引用文档用于通过本仓库 CLI 在 DevFlow 中创建任务并发起服务部署或泳道部署。

## 何时使用

当用户明确表达以下意图时使用本引用文档：

- 创建新的 DevFlow 任务并部署服务
- 在当前仓库或当前分支上发起一次服务部署
- 在当前仓库或当前分支上发起一次泳道部署

## 目标参数

参考 `DeployRequest`，以下参数在 skill 层都视为非必要参数；如果用户对话中没有明确指出，则可以不传，请求需要的所有参数都不需要主动询问用户：

- `title`：部署任务标题，用于描述这次部署要做什么；如果用户对话中没有明确指出，则可以不传
- `service_name`：指定项目名称；当用户明确提到“项目”“前端项目”“Goofy 项目”“Ufra 项目”“Gecko 项目”“Lego插件”“Lambda服务”并且句子里包含项目名时，应优先抽取项目名作为 `service_name`；如果用户对话中没有明确指出，则可以不传
- `repo_name`：仓库名称，例如 `iesarch/devflow_admin`；如果用户对话中没有明确指出，则可以不传
- `psm`：服务对应的 PSM 标识；如果用户对话中没有明确指出，则可以不传
- `branch`：目标分支名称；如果用户对话中没有明确指出，则可以不传
- `use_old_branch`：是否复用旧分支进行部署，布尔值；如果用户对话中没有明确指出，则可以不传
- `region`：部署区域，仅支持 `cn`、`i18n`；可将其视为控制面或部署大区，而不是具体机房。如果用户对话中没有明确指出，则可以不传
- `dc`：部署机房，对应具体 VDC/机房缩写，例如 `LF`（廊坊）、`HL`（怀来）、`LQ`（灵丘）、`GL`（广灵）、`XH`（宣化）、`ZB`（张北）、`GL2`（广灵2）、`HJ`（璜泾）、`ZJG`（张家港）、`JJ`（鸠江）；如果用户对话中没有明确指出，则可以不传。但需要遵循控制面限制：当用户未指定控制面，或控制面明确为 `cn` 时，`dc` 仅支持 `LF`、`LQ`、`HL`、`GL`、`XH`、`ZB`、`GL2`、`HJ`、`ZJG`、`JJ`；如果控制面为其他值，则不支持指定 `dc`
- `provider`：服务类型或部署提供方。**如果用户提到“前端”、“Goofy”，请直接固定传入 `--provider="GoofyDeploy"`**；提到“TCE”，传入 `--provider="TCE"`；提到“TCC”，传入 `--provider="TCC"`；提到“FaaS”，传入 `--provider="ByteFaaS"`； 提到“Ufra”、 “Gecko-Ufra”，传入 `--provider="Gecko-Ufra"`； 提到“添加repo/仓库”、 “部署依赖”，传入 `--provider="Repo"`； 提到“Gecko”，传入 `--provider="Gecko"`； 提到“Lambda”，传入 `--provider="Lambda"`； 提到“Lego”，传入 `--provider="Lego"`。如果未明确提及，则不传。
- `lane`：泳道名称，通常以 `boe_` 或 `ppe_` 开头；如果用户对话中没有明确指出，则可以不传；如果用户只说“在 ppe/boe 上部署”但没有给出具体泳道名，也不传
- `task_id`：已有 DevFlow 任务 ID；如果用户对话中没有明确指出，则可以不传；只有上下文已经明确某个任务时再一并传入
- `biz_id`：关联的空间 ID；如果用户对话中提供的是自然语言空间描述或空间名称，应优先按枚举映射规则转成对应 ID 再传入；如果用户对话中没有明确指出，则可以不传
- `meego_id`：关联的 Meego 任务 ID；用户明确提供时应优先传入；如果用户对话中没有明确指出，则可以不传
- `clusters`：部署集群列表；如果用户对话中没有明确指出，则可以不传
- `app_sides`：Gecko-Ufra 资源的 app 侧列表，多个值使用逗号分隔；当用户明确给出 `app_sides`，可以直接透传；如果用户对话中没有明确指出，则可以不传
- `pids`：Gecko-Ufra 资源的页面 pid 列表，多个值使用逗号分隔；当用户明确给出 `pids`，可以直接透传；如果用户对话中没有明确指出，则可以不传
- `dynamic_params`：动态参数字符串，供 Goofy 等资源使用；多个键值对使用 JSON 字符串透传，例如 `{"dependency_vmok":"a,b"}`；如果用户对话中没有明确指出，则可以不传
- `build_ctx_envs`：构建上下文环境变量字符串；如果用户对话中没有明确指出，则可以不传

补充说明：

- `region` 只允许传单个标准值 `cn` 或 `i18n`，不支持 `boe`、`boe-i18n`、`i18n-bd` 或逗号分隔的多个值
- 如果用户明确指定了不支持的 `region`，不要调用 CLI，也不要静默省略或改写；应明确告知用户当前仅支持 `cn`、`i18n`，并请用户重新指定
- `dc`、`lane`、`clusters` 支持多个值，多个值使用逗号分隔
- `region` 与 `dc` 不是同一层级：`region` 是控制面，`dc` 是具体机房；用户说“部署到 `cn`”时优先理解为 `region`，用户说“部署到 LF/HL/LQ/HJ”时优先理解为 `dc`
- 对 CN 语境，可将机房进一步理解为 VRegion 下的 VDC：`LF`、`HL`、`LQ`、`GL` 属于 `China-North`（华北），`XH`、`ZB`、`GL2` 属于 `China-North6`（华北6），`HJ`、`ZJG`、`JJ` 属于 `China-East`（华东）
- 当用户同时给出控制面和机房时，两者都可以传；但如果 `region` 明确不是 `cn`，则不要传 `dc`
- 用户提到“华北三机房”时，通常指 `LF`、`HL`、`LQ`；提到“华东三机房”时，通常指 `HJ`、`ZJG`、`JJ`,用户提到“华北华东6机房”时通常指的是`LF`、`HL`、`LQ`、`HJ`、`ZJG`、`JJ`。如果用户只给这种集合口径而没有明确要求逐个机房展开，优先保留原始表述，不要自行猜测拆分
- `app_sides`、`pids` 支持多个值，多个值使用逗号分隔
- `dynamic_params` 透传为 JSON 字符串，不要在 skill 层改写成数组或对象参数列表
- `build_ctx_envs` 作为字符串原样透传，不要在 skill 层改写成数组或对象参数列表
- `biz_id` 支持直接传空间 ID，也支持先把空间名称转换为 ID；如果用户提供的是“抖音空间”“TikTok 空间”“豆包业务”这类自然语言描述，应先识别出对应空间，再传映射后的 `biz_id`
- skill 层不要为了补齐这些参数频繁追问用户；用户未明确给出的参数，优先省略
- 如果用户明确指定了 `dc`，但该值不在当前支持列表中，不要假装理解了，也不要静默省略；应明确告诉用户当前仅支持 `LF`、`LQ`、`HL`、`GL`、`XH`、`ZB`、`GL2`、`HJ`、`ZJG`、`JJ`，并请用户从中手动选择
- 当 provider 为 `Gecko-Ufra` 时，若用户未提供 `service_name`、`app_sides`、`pids`，优先依赖 CLI 的本地仓库识别与候选提示能力，不要在 skill 层自行猜测
- 当 provider 为 `GoofyDeploy` 且用户提到 vmok 或依赖 provider 参数时，将其写入 `dynamic_params`，例如 `{"dependency_vmok":"@scope/a,@scope/b"}`

## 枚举字段归一化规则

当用户输入中出现自然语言描述、缩写、别名或中文表述时，不要把整张映射表直接写死在推理文本中；应按“先识别字段，再查映射，再输出标准值”的方式处理。

### 需要按映射表归一化的字段

- `biz_id`

### 归一化流程

1. 先判断用户给出的值属于哪个字段，不要跨字段复用映射。
2. 如果用户已经给出标准枚举值或明显可直接透传的值，则直接使用，不要重复改写。
3. 如果用户给出的是自然语言别名、中文名称、常见简称，则先查对应字段的映射表，将其转换为标准值。
4. 如果一个输入能匹配多个候选值，视为有歧义，不要猜测；此时宁可省略该参数，也不要传错。
5. 如果完全无法命中映射，但原始值本身看起来像合法枚举或泳道/集群名称，可以保留原值透传。

### `biz_id` 结构化映射源

将下表视为 `biz_id` 字段的枚举数据源；实际推理时，应理解为“空间名称/别名 -> 标准 biz\_id”的映射，而不是要求在回答里展开背诵整张表。如果用户给的是明显自然语言空间名，优先映射成 ID；若无法唯一匹配，则不传。

| `biz_id` | 空间名称                     |
| -------- | ------------------------ |
| `0`      | `抖音`                     |
| `1`      | `火山`                     |
| `2`      | `抖音-工具线`                 |
| `3`      | `DevFlow`                |
| `4`      | `DevFlow Demo`           |
| `7`      | `Affiliate FE`           |
| `8`      | `TikTok-UserCore`        |
| `9`      | `抖音 FE`                  |
| `10`     | `抖音系增长`                  |
| `11`     | `抖音IM`                   |
| `13`     | `Janus Portal`           |
| `14`     | `TikTok IM`              |
| `15`     | `Yumme`                  |
| `16`     | `剪映`                     |
| `17`     | `TikTok Studio (Client)` |
| `18`     | `devflow_test_wgb`       |
| `19`     | `TikTok-Passport`        |
| `20`     | `TikTok-Feeds`           |
| `21`     | `TikTok-RPC`             |
| `22`     | `Ecom`                   |
| `23`     | `OEC`                    |
| `24`     | `小说`                     |
| `27`     | `西瓜`                     |
| `30`     | `抖音-搜索`                  |
| `31`     | `用户中台`                   |
| `32`     | `公共`                     |
| `33`     | `豆包`                     |
| `34`     | `paladin`                |
| `35`     | `直播互动`                |
| `1180`   | `TikTok`                 |
| `1728`   | `Global live`            |
| `7633`   | `麦哲伦F项目`                 |
| `7743`   | `TikTok Shop`            |
| `10001`  | `tiktok_ic`              |
| `112889` | `抖音工具线模板业务`              |
| `319164` | `麦哲伦S项目`                 |
| `325528` | `西西里`                    |

### `biz_id` 使用示例

- “抖音空间”“抖音业务” -> `--biz_id=0`
- “豆包业务” -> `--biz_id=33`
- “TikTok 空间” -> `--biz_id=1180`
- “TikTok Shop” -> `--biz_id=7743`
- 用户直接给出数字 `33` -> 直接透传 `--biz_id=33`

## 执行原则

- `dc` 中的机房代码必须大写（如 `LF`、`HL`）；用户提供小写时先转为大写，多个机房逐项处理
- 在调用 CLI 之前不需要和用户进行任何交互
- 能从当前对话、仓库上下文，直接使用
- 不需要执行任何 git 命令来获取参数
- 如果用户未指定控制面，默认按“允许传中国控制面机房”的规则处理；此时只有 `LF`、`LQ`、`HL`、`GL`、`XH`、`ZB`、`GL2`、`HJ`、`ZJG`、`JJ` 可以作为 `dc` 透传
- 如果用户明确指定了 `region`，仅当值为 `cn` 或 `i18n` 时才允许调用 CLI；其他值必须提示用户重新指定
- 如果用户明确指定了控制面且值不是 `cn`，则不要传 `dc`
- 如果用户明确指定了机房，但是无法理解用户意图，请直接告知当前支持的机房列表 `LF`、`LQ`、`HL`、`GL`、`XH`、`ZB`、`GL2`、`HJ`、`ZJG`、`JJ`，并要求用户手动选择；这是少数需要主动追问的场景，不能静默忽略该参数
- 用户明确给了 `meego_id` 时，直接使用，不要改写；如果用户提供了类似 `https://meego.larkoffice.com/governance/story/detail/6999755050` 的 URL，提取出 `6999755050` 作为 `meego_id`
- 如果用户未明确指定 `title`、`service_name`、`psm`、`repo_name`、`use_old_branch`、`region`、`dc`、`provider`、`lane`、`task_id`、`biz_id`、`meego_id`、`clusters`、`app_sides`、`pids`、`dynamic_params`、`build_ctx_envs`，可以不传
- 如果用户提供的是“抖音空间”“TikTok 空间”“豆包业务”等自然语言描述，应先按上面的 `biz_id` 映射源归一化后再传参
- 如果在完成本 skill 任务过程中需要使用其他 skill，必须使用名称带有 `bytedance-devflow-` 前缀的 skill

## 调用方式

优先调用 `bytedcli devflow` 新增命令：

```bash
bytedcli devflow service deploy --title="<title>" --bytedcli-skill-dir="<skill所在目录>"
```

根据上下文补充参数，例如：

```bash
bytedcli devflow service deploy --title="<title>" --service_name="<service_name>" --repo_name="<repo_name>" --psm="<psm>" --branch="<branch>" --use_old_branch="<true|false>" --region="<region>" --dc="<dc1>,<dc2>" --provider="<provider>" --lane="<lane1>,<lane2>" --task_id="<task_id>" --biz_id="<biz_id>" --meego_id="<meego_id>" --clusters="<cluster1>,<cluster2>" --app_sides="<app_side1>,<app_side2>" --pids="<pid1>,<pid2>" --dynamic_params='<dynamic_params_json>' --build_ctx_envs='<build_ctx_envs>' --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- 尽量原样展示 `bytedcli devflow` 的原始输出
- 不主动对输出做总结、概要、改写、提炼或格式化
- 只有用户明确要求解释时，才补充说明
- 如果命令失败，优先保留原始错误信息，只补充最少量必要说明
