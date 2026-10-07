# 在 DevFlow 中执行 API Design

当用户需要查看 IDL API 设计流水线、查看本地 IDL diff、获取目标服务 IDL、创建 API、新增接口、修改 IDL、更新本地依赖或提交本地 IDL 变更时，默认使用本能力。

只有在以下两类情况下不进入 DevFlow API Design 流程，本文档的编辑、`new_interface`、`idl pull`、`idl save` 等约束也不生效：

- 用户明确指定不使用 DevFlow，例如“不走 DevFlow”“不要用 bytedance-devflow skill”“只直接修改本地 IDL 仓库”。
- 当前需求明确不是 DevFlow skill 场景，即操作对象、工具或流程已明确属于其他系统，与 DevFlow 无关。

用户未主动提到 DevFlow，或者本地已有 IDL Git 仓库，都不能单独作为排除 DevFlow 流程的理由。不进入 DevFlow 流程时，回到当前场景的普通开发流程；本 skill 不对其 IDL 编辑、校验、codegen、commit 或 push 方式作出规定。
- 通过该能力会将 IDL 拉取到目录预检确定的目标业务仓库根目录 `TARGET_REPO_ROOT` 下，拉取到的本地文件包含两部分：
  1. IDL 工作区文件，存放在 `TARGET_REPO_ROOT` 下以 `idl_` + `repo_name` 转换结果开头的目录中
  2. IDL 配置与任务元信息，存放在 `TARGET_REPO_ROOT/.devflow/` 目录下
- **注意：** `.devflow/` 目录中的任务文件仅用于 CLI 记录 IDL 配置、任务上下文和基线信息，**禁止主动修改**。

## 执行目录预检

执行 Design API 前，必须先识别当前目录并确定 `TARGET_REPO_ROOT`。`devflow.sh` 不会自动切换目录，而 IDL 命令会把执行目录作为项目目录；在目标仓库未确定前，禁止执行会读取或写入本地状态的命令。

### 1. 当前位于 Git 仓库

先通过 `git rev-parse --show-toplevel` 获取仓库根目录：

- 命令成功时，将返回目录作为 `TARGET_REPO_ROOT`。
- 即使当前位于仓库子目录，也必须在仓库根目录执行后续命令，避免在子目录生成嵌套的 `.devflow/` 和 `idl_*`。
- 保持现有参数获取和 Design API 流程不变。

### 2. 当前位于 DevFlow 工作区

当前目录不是 Git 仓库，但满足以下任一条件时，可识别为 DevFlow 工作区根目录：

- 存在 devflow 工作区生成的 `.devflow-workspace.json`。
- 存在包含 DevFlow 任务信息的 `AGENTS.md`，且映射的业务仓库是当前目录的直接子目录。

在工作区中按以下顺序确定目标仓库，低优先级信息不能覆盖高优先级信息：

1. 用户显式提供的完整 `repo_name`。
2. 用户显式提供的 PSM，根据 PSM/仓库映射查找仓库。
3. 当前对话中已经由用户确认的仓库或 PSM。
4. 工作区中唯一通过本地校验的候选仓库。

映射来源和校验规则：

- 优先读取 `.devflow-workspace.json` 的 `service_info_list`，获取 `psm`、`repo` 和 `branch`。
- `.devflow-workspace.json` 缺失或不可读时，可使用 `AGENTS.md` 中明确的 PSM/仓库对应关系；不得依赖某一种固定自然语言句式。
- devflow 工作区使用完整仓库名最后一段作为工作区子目录名，例如 `iesarch/devflow_ai_platform` 对应 `<workspace>/devflow_ai_platform`。
- 候选目录必须存在且是 Git 仓库，并且其 remote 解析出的完整仓库名必须与映射中的 `repo` 一致。校验失败时禁止执行。
- 用户同时提供 `repo_name` 和 PSM，但两者映射到不同仓库时，必须指出冲突并请用户确认。

如果已明确当前目录是 DevFlow 工作区，但不能唯一确定要操作的 PSM 或仓库：

- 多个候选时，向用户展示候选的 PSM 和完整仓库名，并请用户确认一个目标。
- 没有匹配候选时，请用户提供 PSM 或完整 `repo_name`。
- 不得按目录顺序、服务顺序或最近访问记录猜测目标。
- 用户确认前，不得在任一目录执行 `idl pull`、`idl search_api`、`idl diff`、`idl save`、`idl new_interface`、`codegen update`，也不得修改 IDL 文件。
- 用户确认后，将该选择作为本次 Design API 流程的目标；后续步骤复用该目标，除非出现新的映射冲突或用户主动变更目标，否则不重复询问。

### 3. 当前目录无法识别

当前目录既不属于 Git 仓库，也不能验证为 DevFlow 工作区时，必须停止本地相关流程，并请用户进入目标仓库，或提供足以定位目标的 PSM/完整 `repo_name`。禁止在当前目录创建 `.devflow/`、`idl_*` 或 `.gitignore`。

### 4. 在目标仓库中执行

涉及本地上下文的命令统一使用命令级工作目录，或通过子 Shell 执行：

```bash
(
  cd "<TARGET_REPO_ROOT>"
  bash "bytedcli devflow" --caller direct <command> --bytedcli-skill-dir="<skill所在目录>"
)
```

子 Shell 结束后调用者仍处于原目录。后续 IDL 文件编辑必须使用 `TARGET_REPO_ROOT` 下 `idl_*` 中的文件，不得把工作区根目录作为 IDL 项目目录。

`idl info` 是例外：显式提供足够的 `task_id` 或 PSM、无需本地 Git 推断时，可以直接在工作区执行纯远端查询，且不得产生本地文件。


## 何时调用

除非命中上述排除条件，以下场景默认调用本能力：

- 用户明确说要“拉取 IDL”“获取 IDL 文件”“把某个服务的 IDL 拉下来”
- 用户明确说要“查看 IDL API 设计流水线”“查看 API 流水线”“查看 IDL 设计状态”“查询当前 IDL codegen/info 结果”
- 用户明确说要“查看本地 IDL diff”“看一下本地所有 IDL 变更”“查看本地 git diff”“idl diff”
- 用户明确说要“创建 API”“新增接口”“新增一个接口”“加一个 rpc/method”“新增路由”“先生成接口模板”（→ 走"创建 API"，见强制约束）
- 用户明确说要“修改 IDL”“修改已有接口字段”，且需要先把目标服务 IDL 拉到本地
- 用户明确说要“更新本地依赖”“更新 codegen 依赖”“更新当前仓库 IDL 依赖”
- 用户明确说要“提交 IDL 变更”“保存 IDL 改动”“推送本地 IDL 修改”
- 用户明确提到 `idl info`、`idl diff`、`idl pull`、`idl new_interface`、`idl save`、`codegen update`

## 参数获取优先级

按下面顺序收集参数，后者只用于补全缺失值，不能覆盖前者：

1. 用户显式提供的完整 `repo_name`
2. 用户显式提供的 PSM 对应仓库
3. 当前对话中已经由用户确认的仓库或 PSM
4. 当前 Git 仓库
5. DevFlow 工作区中唯一通过校验的候选仓库
6. CLI 内部的自动推断逻辑

如果高优先级的 `repo_name` 与 PSM 映射冲突，或在工作区中无法得到唯一候选，必须先向用户确认。

## 子能力与调用方式

### 1. 拉取 IDL

- 对应命令：`idl pull`
- 当参数为空时，CLI 会优先读取当前业务代码仓库和分支信息，获取服务关联的 IDL 文件与元信息
- 支持透传 `psm`、`repo_name`、`branch`、`task_id`，如果用户没有明确提供，则不传
- 当用户说“我要修改某个服务的 IDL”时，先执行这一步把目标 IDL 拉到本地

```bash
(
  cd "<TARGET_REPO_ROOT>"
  bash "bytedcli devflow" --caller direct idl pull [--psm="<psm>"] [--repo_name="<repo_name>"] [--branch="<branch>"] [--task_id="<task_id>"] --bytedcli-skill-dir="<skill所在目录>"
)
```

### 2. 修改 IDL

- 当需要修改IDL时，请先执行 `idl pull` 拉取 IDL再修改本地文件。如果本地已经有IDL文件了也需要执行一次 `idl pull`, 确保本地文件是最新的。

- 【注意】可以通过 `idl search_api` 查找接口定义所在文件
        - 对应命令：`idl search_api`
        - 必须传入 `pattern`，用于匹配接口名称、RpcMethod、path、请求结构体名称、响应结构体名称中的任意一个字段返回的接口定义，不区分大小写，支持模糊匹配，例如 `pattern="test"` 会匹配 `test_api`、`test_api_v2` 等接口，该参数不能为空。
        - 支持指定 `psm`、`repo_name`；如果用户没有明确提供，则不传
- 【强制】当编写字段时，需要结合上下文为该字段添加注释用于解释该字段的含义，例如 
	- protobuf文件中: `optional bool test = 1; //测试`。
	- thrift文件中: `12: optional string psm, // 服务标识`

```bash
(
  cd "<TARGET_REPO_ROOT>"
  bash "bytedcli devflow" --caller direct idl search_api --pattern="test" --psm="<psm>" --repo_name="<idl_repo>" --bytedcli-skill-dir="<skill所在目录>"
)
```
- 如果在当前 DevFlow API Design 流程中新增接口，请先使用 `idl new_interface` 创建接口，具体使用参考 [创建 API / 新增接口](#4-创建-api-新增-接口) 章节，等待接口创建完成之后再修改 DevFlow IDL 工作区中的接口定义。

### 3. 查看 IDL API 设计流水线

- 对应命令：`idl info`
- 当用户需要查看某个任务、某个 psm，或当前仓库分支对应的 IDL API 设计流水线状态时，使用该能力
- 支持透传 `task_id`、`psm`、`repo_name`、`branch`；如果用户没有明确提供，则只依赖 CLI 的本地推断逻辑补全 `repo_name` / `branch`
- 该指令底层仍查询 API 设计流水线信息，但对外统一归到 `idl info`

```bash
(
  cd "<TARGET_REPO_ROOT>"
  bash "bytedcli devflow" --caller direct idl info [--task_id="<task_id>"] [--psm="<psm>"] [--repo_name="<repo_name>"] [--branch="<branch>"] --bytedcli-skill-dir="<skill所在目录>"
)
```

如果显式提供 `task_id` 或 PSM 且仅做远端查询，可以省略 `cd`，直接在工作区执行。

### 4. 创建 API / 新增 接口

- 对应命令：`idl new_interface`
- 命中“创建 API / 新增接口”场景时，应先告知用户：该技能可以根据当前业务线配置的新建接口规则，在 IDL 中快速实现接口定义文件
- **新增接口的首选动作就是本命令；禁止用手改本地 proto 代替**（见强制约束小结）。
- `idl new_interface` 需要传入 `psm`
- 当 `--form_json` 缺失或不合法时，CLI 会返回当前服务创建接口所需的完整模板；把模板里要求的字段全部填入 `--form_json` 后再次执行即可
- 该指令会直接在远端创建 API 接口，不会在本地修改 IDL 文件，创建成功后，CLI 会自动更新本地 IDL 文件，拉取新增的接口文件
- 用户若未明确要求“修改 IDL”或“新增接口定义文件”，不要默认继续进入本地 IDL 编辑；需要先确认用户是否希望在 IDL 中同步补充对应定义文件

#### 标准执行步骤（缺参也要按此走，不要退回手改）

1. **确定 `psm`**：
   - 优先用用户显式提供的 `psm`。
   - 用户没给时，优先让 CLI 自动推断 `psm`
2. **获取模板**：首次可不带 `--form_json`（或带不完整的 `form_json`）先执行一次，拿到 CLI 返回的接口创建模板。
3. **填充模板并再次执行**：把用户已提供的信息（HTTP method、url、接口名等）填入模板要求的字段，组成完整 `--form_json` 后再次执行 `idl new_interface`。
4. **创建成功后**：CLI 会自动回写本地 IDL，无需手动新建/编辑 proto。
5. **判断是否还需要本地 IDL 变更**：
   - 如果用户明确要求“修改 IDL”或“在 IDL 中新增接口定义文件”，再进入 `idl pull` / 本地修改 / `idl save` 流程。
   - 如果用户只说“新增接口 / 创建 API”，但没提 IDL 变更，则先询问用户是否还需要在 IDL 中同步新增接口定义文件，不要默认继续修改本地 IDL。

```bash
(
  cd "<TARGET_REPO_ROOT>"
  bash "bytedcli devflow" --caller direct idl new_interface --psm="<psm>" [--task_id="<task_id>"] [--git_repo="<git_repo>"] --form_json='<form_json>' --bytedcli-skill-dir="<skill所在目录>"
)
```

最小执行样例（字段名以 CLI 返回模板为准，此处仅示意首选动作是调用命令而非改文件）：

```bash
# 第一步：先空跑取模板
(cd "<TARGET_REPO_ROOT>" && bash "bytedcli devflow" --caller direct idl new_interface --psm="example.example.example") --bytedcli-skill-dir="<skill所在目录>"

# 第二步：按模板补全 form_json 后再次执行
(cd "<TARGET_REPO_ROOT>" && bash "bytedcli devflow" --caller direct idl new_interface --psm="example.example.example" --form_json='{"http_method":"POST","url":"/api/v1/example/sample/v1"}') --bytedcli-skill-dir="<skill所在目录>"
```

### 5. 查看本地 IDL 变更

- 对应命令：`idl diff`
- 当用户需要查看当前项目下所有本地 IDL 工作区相对基线的变更时，使用该能力
- CLI 会先按 `idl save` 相同口径打印变更汇总，再对每个 IDL 工作区执行 `git diff --no-index`，直接展示 diff 内容
- 该命令只读取本地 `.devflow` 基线和 `idl_*` 工作区，不会提交、拉取或修改本地文件

```bash
(cd "<TARGET_REPO_ROOT>" && bash "bytedcli devflow" --caller direct idl diff) --bytedcli-skill-dir="<skill所在目录>"
```

### 6. 提交 IDL 变更

- 对应命令：`idl save`
- 当用户需要提交当前项目下所有本地 IDL 变更时，使用该能力
- 在本地修改完通过 `idl pull` 拉取下来的 IDL 后，可提示用户是否需要执行该命令提交本地变更，**禁止在修改完后直接自动执行**
- 默认无需参数，会提交当前项目目录下本地所有 IDL 变更
- 如有需要，可额外透传 `psm`、`task_id`、`commit_msg`，如果用户没有明确提供，则不传
- 提交前 CLI 会执行 IDL Check：规范/编译检查发现 error 或兼容性检查调用失败时会阻断提交
- 如果 CLI 提示可使用 `--force`，必须由 RD 明确确认后再传该参数；agent 不应自行替用户追加 `--force`

```bash
(cd "<TARGET_REPO_ROOT>" && bash "bytedcli devflow" --caller direct idl save) --bytedcli-skill-dir="<skill所在目录>"
```

### 7. 更新本地依赖

- 对应命令：`codegen update`
- 当用户需要更新当前业务仓库本地 codegen 依赖时，使用该能力
- 必须在目标业务仓库根目录下执行该命令
- 如果用户没有明确提供额外参数，则直接在目标业务仓库根目录执行，不主动补传 `task_id`、`psm`、`repo_name`、`branch`
- 该指令一般在用户修改完本地 IDL 提交后执行，因此当用户执行完 `idl save` 后，可以询问用户是否需要更新本地依赖，若用户确认则执行该指令

```bash
(cd "<TARGET_REPO_ROOT>" && bash "bytedcli devflow" --caller direct codegen update) --bytedcli-skill-dir="<skill所在目录>"
```

## 输出处理

- `idl pull`：优先原样返回 CLI 输出的文件更新结果和元信息
- `idl info`：优先原样返回 CLI 输出的 API 设计流水线信息
- `idl diff`：优先原样返回 CLI 输出的本地变更汇总和 git diff 内容
- `idl new_interface`：成功时直接返回 CLI 输出；输入缺失或不合法时，优先返回 CLI 打印的完整模板
- `idl save`：优先原样返回 CLI 输出的提交结果
- `codegen update`：优先原样返回 CLI 输出的依赖更新结果
- 若命令返回 `pending` 或明确错误，优先原样展示 CLI 返回内容

## 强制约束（必须遵守，禁止自由裁量）

- **修改文件只能修改IDL工作区文件**，idl工作区为 `idl_` + `repo_name` 转换结果开头的目录中。
  - 不能修改 `.devflow/` 目录下的配置文件。
- **执行任何本地相关 Design API 动作前必须完成目录预检。**
  - 在 Git 仓库中统一使用仓库根目录。
  - 在 DevFlow 工作区中先确定并校验目标仓库；无法唯一确定时必须向用户确认。
  - 在未知目录中禁止执行会读取或写入本地状态的 Design API 动作。
- **在 DevFlow API Design 流程内，新增接口（创建 API）只能走 `idl new_interface`，禁止手动编辑 DevFlow 拉取的本地 `.proto` / IDL 工作区来“实现”新接口。**
  - 除非用户明确指定不使用 DevFlow，或当前需求明确不是 DevFlow skill 场景，“新增接口”“创建 API”“加一个 rpc/method”“新增路由”等表达默认触发本流程。
  - 进入本流程后，对新增接口场景，`idl pull` 和“用 Edit/Write 直接改 proto”都不是首选；唯一首选是 `idl new_interface`。
  - 只有当 `idl new_interface` 明确失败、且 CLI 返回信息显示必须人工编辑本地文件时，才允许 fallback 到手改 IDL，并需先把失败原文返回给用户。
- **新增接口不等于一定要修改本地 IDL 定义文件**：
  - `idl new_interface` 用于创建接口；是否还需要在本地 IDL 工作区新增/修改接口定义文件，取决于用户是否明确提出“修改 IDL”“新增接口定义文件”等额外诉求。
  - 当用户只表达“新增接口 / 创建 API”，但没有明确说明还要修改 IDL 时，先按“创建 API”处理；若后续需要进入本地 IDL 编辑流程，应先询问用户是否需要在 IDL 中同步新增接口定义文件。
- **缺参不是手改的理由**：执行 `idl new_interface` 缺少 `psm` 或 `form_json` 时，按下方"创建 API"小节自动补全（`psm` 从当前 service proto 提取、`form_json` 先空跑取模板），不要因为参数不全就退回手工编辑。
- 区分两类场景，避免误用：
  - **新增接口 / 新增 rpc / 新增 method（结构上多一个接口）** → 创建 API（`idl new_interface`）。
  - **修改已有接口（改字段、改参数、改注释等）**，或用户明确要求“在 IDL 中新增/补充接口定义文件” → 先 `idl pull`，再执行下一步动作
- **提交 IDL 变更**：在本地修改完通过 `idl pull` 拉取下来的 IDL 后，可通过 `idl save` 命令提交本地变更，**禁止在修改完后直接自动执行**。

## 备注

- API Design 相关底层命令统一是 `idl info`、`idl diff`、`idl pull`、`idl new_interface`、`idl save`、`codegen update`、`idl search_api`
- **在 DevFlow API Design 流程内，新增接口（创建 API）禁止用手改 DevFlow IDL 工作区实现，首选动作只能是 `idl new_interface`**；该硬约束仅在 DevFlow 流程内生效，不适用于非 DevFlow 的本地 IDL 仓库。
- “修改 IDL”不是单独命令，先拉取目标服务 IDL 到本地，再由用户或后续步骤修改，最后执行 `idl save`；该路径适用于“修改已有接口”，以及用户明确要求“在 IDL 中新增/补充接口定义文件”的场景。
- 用户只说“新增接口 / 创建 API”时，不默认等价为“还要修改本地 IDL 定义文件”；是否需要这一步，应先向用户确认。
- “更新本地依赖”不是修改 `.devflow/` 或 IDL 工作区内容，而是在目标业务仓库根目录执行 `codegen update`
- 如果需要修改本地 IDL，默认只修改拉取后生成的 IDL 工作区目录，不主动编辑 `.devflow/` 下的任务文件
